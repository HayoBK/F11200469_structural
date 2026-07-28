"""
Análisis vertex-wise whole-brain con FreeSurfer (`mri_glmfit` + `mri_glmfit-sim`).

Qué hace y por qué, en corto: en vez de promediar cada medida dentro de una ROI del
atlas, ajusta el MISMO modelo de la etapa A en cada uno de los ~160.000 vértices de
la superficie cortical, alineados entre sujetos sobre `fsaverage`. El resultado es
un mapa, no una tabla — y no depende de que la parcelación del atlas coincida con
la extensión real del efecto.

**Modelo.** Se usa `--doss` (Different Offset, Same Slope): un intercepto por grupo
y una pendiente común para las covariables. Es exactamente `medida ~ Grupo + Edad +
Genero + N_Educacional [+ eTIV]`, el mismo modelo de las etapas A. (`--dods` estimaría
pendientes distintas por grupo, que es un modelo con interacción y no es el nuestro.)

**Corrección.** 160.000 pruebas por hemisferio hacen inútil un FDR estándar, así que
se usa corrección **por clusters**: `mri_glmfit-sim` compara el tamaño de cada cúmulo
de vértices contiguos supraumbral contra una distribución nula de tamaños de cúmulo
obtenida por simulación de Monte Carlo (precomputada en FreeSurfer para fwhm10).
Sobreviven solo los cúmulos más grandes de lo esperable por azar. Además se corrige
por los dos hemisferios (`--2spaces`).

Los datos derivados (concatenados, mapas) se escriben FUERA del repo, en
`~/FS_FONDECYT/glm/`: son imágenes, no resultados agregados.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd

FS_HOME = Path("/Applications/freesurfer/8.2.0")
SUBJECTS_DIR = Path.home() / "FS_FONDECYT" / "subjects"
GLM_DIR = Path.home() / "FS_FONDECYT" / "glm"          # fuera del repo: son imágenes

# Umbral de formación de cluster y umbral corregido por cluster.
CWP = 0.05          # p corregido del cluster
FWHM = 10           # suavizado por defecto (coincide con el qcache existente)
CLUSTER_THR = 3     # 3 → p<0.001 en la formación del cluster (recomendado por FS)

# ⚠️ El LGI va SIN suavizado adicional. Medido en estos datos:
#     LGI  fwhm0  → FWHM residual 10,5   ·  LGI fwhm10 → FWHM residual 37,0
#     thickness fwhm10 → 14,5 · volume fwhm10 → 14,5 · area fwhm10 → 20,1
# El LGI ya integra un parche de superficie amplio, así que sin suavizar tiene un
# FWHM residual comparable al de las otras medidas ya suavizadas. Añadirle fwhm10
# lo lleva a 37, fuera del rango de las tablas de Monte Carlo de FreeSurfer (llegan
# a fwhm30) y `mri_glmfit-sim --cache` no puede corregir. Suavizarlo es además
# redundante: duplicaría un promediado espacial que la medida ya hace.
FWHM_POR_MEDIDA = {"thickness": 10, "area": 10, "volume": 10, "pial_lgi": 0}


def fwhm_de(medida: str) -> int:
    return FWHM_POR_MEDIDA.get(medida, FWHM)

MEDIDAS_QCACHE = {                 # ya preprocesadas por recon-all -qcache
    "thickness": "thickness",
    "area": "area",
    "volume": "volume",
}
MEDIDA_LGI = "pial_lgi"            # NO tiene qcache: hay que preprocesarla


def entorno() -> dict:
    """Variables de entorno para invocar FreeSurfer desde subprocess."""
    import os

    env = os.environ.copy()
    env.update({
        "FREESURFER_HOME": str(FS_HOME),
        "SUBJECTS_DIR": str(SUBJECTS_DIR),
        "PATH": f"{FS_HOME}/bin:{FS_HOME}/fsfast/bin:{env.get('PATH','')}",
    })
    return env


def correr(cmd: list[str], log: Path | None = None) -> subprocess.CompletedProcess:
    """Ejecuta un comando de FreeSurfer, guardando su log."""
    r = subprocess.run(cmd, env=entorno(), capture_output=True, text=True)
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(f"$ {' '.join(cmd)}\n\n{r.stdout}\n--- stderr ---\n{r.stderr}")
    return r


# ════════════════════════════════════════════════════════════════════════════
# DISEÑO
# ════════════════════════════════════════════════════════════════════════════


def escribir_fsgd(
    datos: pd.DataFrame, ruta: Path, titulo: str, clases: list[str],
    covariables: list[str], col_sujeto: str = "Sujeto",
) -> pd.DataFrame:
    """Escribe el FSGD (Group Descriptor File) y devuelve las filas incluidas.

    El ORDEN de las clases aquí define el orden de las columnas del diseño, y por
    tanto el de los vectores de contraste. Se devuelve para poder construirlos sin
    ambigüedad.
    """
    d = datos[datos["Grupo"].isin(clases)].copy()
    d = d.dropna(subset=[col_sujeto, "Grupo"] + covariables)
    d = d.sort_values([col_sujeto])

    lineas = [
        "GroupDescriptorFile 1",
        f"Title {titulo}",
    ]
    for c in clases:
        lineas.append(f"Class {c.replace(' ', '_')}")
    if covariables:
        lineas.append("Variables " + " ".join(covariables))
    for f in d.itertuples():
        vals = " ".join(f"{getattr(f, c):g}" for c in covariables)
        lineas.append(f"Input {getattr(f, col_sujeto)} "
                      f"{getattr(f, 'Grupo').replace(' ', '_')} {vals}")

    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("\n".join(lineas) + "\n")
    return d


def escribir_contraste(ruta: Path, vector: list[float]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(" ".join(f"{v:g}" for v in vector) + "\n")


def contrastes_para(clases: list[str], n_covariables: int,
                    pares: list[tuple[str, str]]) -> dict[str, list[float]]:
    """Vectores de contraste con codificación DOSS.

    Con DOSS el diseño es [una columna por clase] + [una por covariable], así que un
    contraste entre dos grupos es +1 en una clase, −1 en la otra y 0 en el resto.
    """
    out = {}
    for a, b in pares:
        v = [0.0] * (len(clases) + n_covariables)
        v[clases.index(a)] = 1.0
        v[clases.index(b)] = -1.0
        nombre = f"{a}_vs_{b}".replace(" ", "")
        out[nombre] = v
    return out


# ════════════════════════════════════════════════════════════════════════════
# LECTURA DE RESULTADOS
# ════════════════════════════════════════════════════════════════════════════


def leer_clusters(ruta_summary: Path) -> pd.DataFrame:
    """Parsea el `.cluster.summary` de mri_glmfit-sim.

    Columnas de interés: Size(mm^2), MNIX/Y/Z, CWP (p corregido del cluster) y la
    anotación anatómica del pico.
    """
    if not ruta_summary.exists():
        return pd.DataFrame()
    filas = []
    for linea in ruta_summary.read_text().splitlines():
        if linea.startswith("#") or not linea.strip():
            continue
        p = linea.split()
        if len(p) < 10:
            continue
        try:
            filas.append({
                "cluster": int(p[0]), "max": float(p[1]), "vtxmax": int(p[2]),
                "size_mm2": float(p[3]),
                "MNIX": float(p[4]), "MNIY": float(p[5]), "MNIZ": float(p[6]),
                "CWP": float(p[7]), "CWPlow": float(p[8]), "CWPhi": float(p[9]),
                # Columnas: … CWPHi[9] NVtxs[10] WghtVtx[11] Annot[12]
                "n_vertices": int(p[10]) if len(p) > 10 else None,
                "peso": float(p[11]) if len(p) > 11 else None,
                "anotacion": p[12] if len(p) > 12 else "",
            })
        except (ValueError, IndexError):
            continue
    return pd.DataFrame(filas)
