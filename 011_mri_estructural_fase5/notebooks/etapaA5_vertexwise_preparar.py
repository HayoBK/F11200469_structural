"""
ETAPA A5 (paso 1) — Preparar el análisis vertex-wise.

Genera los FSGD y los contrastes, y lanza los `mris_preproc` (concatenación de los
sujetos sobre fsaverage + suavizado). Para grosor, área y volumen esto es rápido
porque `recon-all -qcache` ya dejó los datos remuestreados; para el **LGI** hay que
hacer el remuestreo desde cero, que es la parte lenta.

Dos diseños, los mismos de las etapas A:
  · `tres_grupos`  — Sano / Vestibular / MPPP, N=46 (45 en LGI)
  · `dirigido`     — MPPP vs Vestibular, n=36 (35 en LGI)

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaA5_vertexwise_preparar.py
"""

# %% ── setup ────────────────────────────────────────────────────────────────
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

import config as cfg
import glmfit as gf

m = cfg.cargar_master()
m["Genero_M"] = (m["Genero"] == "Masculino").astype(int)

# Sujetos con LGI (P14 no tiene): se filtran solo en los diseños de LGI.
lgi_cols = [c for c in m.columns if c.startswith("lgi_")]
m["tiene_lgi"] = m[lgi_cols].notna().any(axis=1)
print(f"N total {len(m)} · con LGI {int(m.tiene_lgi.sum())}")

COVAR = ["Edad", "Genero_M", "N_Educacional"]
COVAR_TIV = COVAR + ["eTIV"]

DISENOS = {
    "tres_grupos": {
        "clases": ["Voluntario Sano", "Vestibular", "MPPP"],
        "pares": [("MPPP", "Voluntario Sano"), ("MPPP", "Vestibular"),
                  ("Vestibular", "Voluntario Sano")],
    },
    "dirigido": {
        "clases": ["Vestibular", "MPPP"],
        "pares": [("MPPP", "Vestibular")],
    },
}
MEDIDAS = ["thickness", "area", "volume", "pial_lgi"]

# %% ── generar FSGD y contrastes ────────────────────────────────────────────
inventario = []
for medida in MEDIDAS:
    usa_tiv = medida in ("area", "volume")
    covs = COVAR_TIV if usa_tiv else COVAR
    datos = m[m.tiene_lgi] if medida == "pial_lgi" else m

    for nombre, cfgd in DISENOS.items():
        base = gf.GLM_DIR / medida / nombre
        base.mkdir(parents=True, exist_ok=True)

        incluidos = gf.escribir_fsgd(
            datos, base / "diseno.fsgd", f"{medida}_{nombre}",
            cfgd["clases"], covs,
        )
        # Las clases van al FSGD con guion bajo; el contraste usa el mismo orden.
        clases_fsgd = [c.replace(" ", "_") for c in cfgd["clases"]]
        pares_fsgd = [(a.replace(" ", "_"), b.replace(" ", "_")) for a, b in cfgd["pares"]]
        contrastes = gf.contrastes_para(clases_fsgd, len(covs), pares_fsgd)
        for cname, vec in contrastes.items():
            gf.escribir_contraste(base / f"{cname}.mtx", vec)

        inventario.append({
            "medida": medida, "diseno": nombre, "n": len(incluidos),
            "clases": " / ".join(cfgd["clases"]),
            "n_por_clase": str(incluidos["Grupo"].value_counts().to_dict()),
            "covariables": " ".join(covs),
            "contrastes": " ".join(contrastes),
            "ancho_diseno": len(clases_fsgd) + len(covs),
        })

inventario = pd.DataFrame(inventario)
print("\n=== DISEÑOS GENERADOS ===")
print(inventario[["medida", "diseno", "n", "n_por_clase", "ancho_diseno",
                  "contrastes"]].to_string(index=False))
cfg.RESULTS.mkdir(parents=True, exist_ok=True)
inventario.to_csv(cfg.RESULTS / "etapaA5_disenos_resultados.csv", index=False)

# comprobación: el FSGD del diseño dirigido, tal cual queda
print("\n=== ejemplo · thickness/dirigido/diseno.fsgd (primeras líneas) ===")
print("\n".join((gf.GLM_DIR / "thickness" / "dirigido" / "diseno.fsgd")
                .read_text().splitlines()[:8]))

# %% ── mris_preproc ─────────────────────────────────────────────────────────
# Concatena a todos los sujetos del FSGD en un solo volumen sobre fsaverage.
# thickness/area/volume: `--cache-in` reutiliza lo que dejó recon-all -qcache.
# pial_lgi: no hay caché → hay que remuestrear y suavizar desde cero (lo lento).
print("\n=== mris_preproc ===")
tareas = []
for medida in MEDIDAS:
    for nombre in DISENOS:
        base = gf.GLM_DIR / medida / nombre
        for hemi in ("lh", "rh"):
            fwhm = gf.fwhm_de(medida)
            salida = base / f"{hemi}.{medida}.fwhm{fwhm}.mgh"
            if salida.exists():
                print(f"  ya existe: {salida.relative_to(gf.GLM_DIR)}")
                continue
            cmd = ["mris_preproc", "--fsgd", str(base / "diseno.fsgd"),
                   "--target", "fsaverage", "--hemi", hemi, "--out", str(salida)]
            if medida in gf.MEDIDAS_QCACHE:
                cmd += ["--cache-in", f"{medida}.fwhm{fwhm}.fsaverage"]
            else:
                cmd += ["--meas", medida] + (["--fwhm", str(fwhm)] if fwhm else [])
            tareas.append((medida, nombre, hemi, cmd, salida, base))

print(f"  {len(tareas)} concatenaciones por hacer")
for medida, nombre, hemi, cmd, salida, base in tareas:
    t0 = time.time()
    print(f"  ▸ {medida}/{nombre}/{hemi} …", end="", flush=True)
    r = gf.correr(cmd, log=base / f"log_preproc_{hemi}.txt")
    ok = salida.exists()
    print(f" {'OK' if ok else 'FALLÓ'}  ({time.time()-t0:.0f}s)")
    if not ok:
        print(f"    ver log: {base / f'log_preproc_{hemi}.txt'}")

print("\n→ preprocesamiento terminado")
print(f"→ salidas en {gf.GLM_DIR}")
