"""
Configuración central de la FASE 5 — FONDECYT 11200469 · MRI estructural.

Rutas, constantes del diseño y carga canónica de la tabla maestra.

⚠️ PRIVACIDAD: los datos viven FUERA de este repositorio, en ~/FS_FONDECYT/tablas/.
Este módulo solo contiene rutas y metadatos — ningún dato de paciente.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# ════════════════════════════════════════════════════════════════════════════
# RUTAS  (los datos NO se versionan; se leen por ruta absoluta)
# ════════════════════════════════════════════════════════════════════════════

FS_ROOT = Path.home() / "FS_FONDECYT"
TABLAS = FS_ROOT / "tablas"
SUBJECTS_DIR = FS_ROOT / "subjects"

MASTER = TABLAS / "master_analitico.csv"
MASTER_LONG = TABLAS / "master_analitico_long.csv"
DICCIONARIO = TABLAS / "diccionario_variables.csv"
COBERTURA = TABLAS / "cobertura_conductual.csv"

# Salidas — dentro del repo (solo agregados)
REPO = Path(__file__).resolve().parents[1]
FIGS = REPO / "figs"
RESULTS = REPO / "results"
DOCS = REPO / "docs"

# Documentación metodológica (OneDrive, fuera del repo)
ONEDRIVE = (
    Path.home() / "Library/CloudStorage/OneDrive-Personal/2-Casper/00-CurrentResearch"
    / "001-FONDECYT_11200469/011-MRI Estructural 2026.07"
)

# ════════════════════════════════════════════════════════════════════════════
# DISEÑO
# ════════════════════════════════════════════════════════════════════════════

GRUPOS = ["Voluntario Sano", "Vestibular", "MPPP"]  # orden: referencia → caso
GRUPO_REF = "Voluntario Sano"
N_ESPERADO = {"MPPP": 17, "Vestibular": 19, "Voluntario Sano": 10}
N_TOTAL = 46
N_LGI = 45  # P14 no tiene LGI

CONTRASTES = [("MPPP", "Voluntario Sano"), ("MPPP", "Vestibular")]

# Covariables del modelo principal — las 4 están completas en los 46
# (`lateralidad_diestro` tras la imputación descrita abajo).
COVARIABLES = ["Edad", "Genero", "N_Educacional", "lateralidad_diestro"]
COVAR_TIV = "eTIV"  # se añade SOLO en volumen y área, nunca en grosor ni LGI
MEDIDAS_CON_TIV = {"volume", "area"}

ALPHA_FDR = 0.05

# ════════════════════════════════════════════════════════════════════════════
# LATERALIDAD  — decisión del PI, 2026-07-27
# ════════════════════════════════════════════════════════════════════════════
# `Edinburgo` (índice −100…100) solo tiene 36/46. Incluirlo crudo dejaba el grupo
# Sano en n=5 por eliminación listwise. Decisión: **imputar "diestro" donde falta**.
#
# De los 36 observados: 33 diestros (≥40), 2 zurdos (≤−40), 1 ambidiestro
# → 92% diestros, coincidente con la prevalencia poblacional, lo que hace la
# imputación defendible. Faltantes: 5 Sanos, 3 MPPP, 2 Vestibulares.
#
# Resultado tras imputar: 43 diestros / 3 no-diestros, N=46 en los tres grupos.
# Se conserva `lateralidad_imputada` como flag para el análisis de sensibilidad
# (re-ajustar los modelos supervivientes solo en los 36 con dato real).

UMBRAL_DIESTRO = 40.0  # criterio estándar del Edinburgh Handedness Inventory
EDINBURGO_IMPUTADO = 100.0  # diestro puro; moda observada (13/36 casos)


def cargar_master(verificar: bool = True) -> pd.DataFrame:
    """Carga la tabla maestra y añade las variables derivadas de lateralidad.

    Añade tres columnas:
      - `lateralidad_imputada`  bool, True si `Edinburgo` estaba ausente
      - `Edinburgo_imp`         índice continuo con los faltantes en +100
      - `lateralidad_diestro`   1 = diestro (≥40), 0 = no-diestro  ← la del modelo
    """
    m = pd.read_csv(MASTER)

    # En un frame de 2.908 columnas, insertar de a una fragmenta el bloque interno.
    edinburgo_imp = m["Edinburgo"].fillna(EDINBURGO_IMPUTADO)
    m = pd.concat([m, pd.DataFrame({
        "lateralidad_imputada": m["Edinburgo"].isna(),
        "Edinburgo_imp": edinburgo_imp,
        "lateralidad_diestro": (edinburgo_imp >= UMBRAL_DIESTRO).astype(int),
    })], axis=1)

    if verificar:
        verificar_integridad(m)
    return m


def cargar_diccionario() -> pd.DataFrame:
    """Diccionario de las 2.907 variables morfométricas y conductuales."""
    return pd.read_csv(DICCIONARIO)


# Bloques que son ROIs verdaderas — excluye globales, eTIV y LGI_SD.
# Ver 06_ESPECIFICACION_TABLA_MAESTRA.md §5.3 (2.530 columnas).
BLOQUES_ROI = [
    "cortical", "LGI", "aseg", "wmparc",
    "subcampos_hipocampo", "nucleos_amigdala", "nucleos_talamo", "tronco_encefalico",
]


def verificar_integridad(m: pd.DataFrame) -> None:
    """Chequeos de 06_ESPECIFICACION §4.5. Falla ruidosamente si el merge se rompió."""
    assert m.shape[0] == N_TOTAL, f"N={m.shape[0]}, esperado {N_TOTAL}"

    n_grupo = m["Grupo"].value_counts().to_dict()
    assert n_grupo == N_ESPERADO, f"N por grupo {n_grupo} != {N_ESPERADO}"

    lgi = [c for c in m.columns if c.startswith("lgi_")]
    assert m[lgi].notna().any(axis=1).sum() == N_LGI, "N_LGI != 45"

    # El chequeo de cordura del merge estructura↔conducta.
    cse = m.groupby("Grupo")["CSE_NI"].median().round(1)
    esperado = {"MPPP": 60.9, "Vestibular": 38.0, "Voluntario Sano": 28.0}
    for g, v in esperado.items():
        assert abs(cse[g] - v) < 0.05, f"CSE_NI mediana {g}={cse[g]}, esperado {v} — merge roto"

    assert m[COVARIABLES].notna().all().all(), "Hay covariables con NaN"
