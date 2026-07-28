"""
ETAPA A5 (paso 2) — Ajustar el GLM vertex-wise y corregir por clusters.

Para cada medida × diseño × hemisferio:
  1. `mri_glmfit --doss` ajusta el modelo en los ~164.000 vértices de fsaverage.
  2. `mri_glmfit-sim --cache 3 abs --cwp 0.05 --2spaces` compara el tamaño de cada
     cúmulo supraumbral contra la distribución nula simulada por Monte Carlo, y
     corrige además por los dos hemisferios.

Umbral de formación de cluster: p<0,001 (`--cache 3`), que es el recomendado por
FreeSurfer y el que evita los cúmulos inflados que motivaron la crítica clásica a
los umbrales laxos (Eklund et al., 2016).

Requiere haber corrido antes `etapaA5_vertexwise_preparar.py`.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaA5_vertexwise_glm.py
"""

# %% ── setup ────────────────────────────────────────────────────────────────
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

import config as cfg
import glmfit as gf

MEDIDAS = ["thickness", "area", "volume", "pial_lgi"]
DISENOS = ["tres_grupos", "dirigido"]
HEMIS = ["lh", "rh"]

# %% ── ajustar y simular ────────────────────────────────────────────────────
filas, faltantes = [], []
for medida in MEDIDAS:
    for diseno in DISENOS:
        base = gf.GLM_DIR / medida / diseno
        fsgd = base / "diseno.fsgd"
        contrastes = sorted(base.glob("*.mtx"))
        if not fsgd.exists() or not contrastes:
            faltantes.append(f"{medida}/{diseno}: sin diseño")
            continue

        for hemi in HEMIS:
            entrada = base / f"{hemi}.{medida}.fwhm{gf.fwhm_de(medida)}.mgh"
            if not entrada.exists():
                faltantes.append(f"{medida}/{diseno}/{hemi}: falta el concatenado")
                continue
            salida = base / f"glm.{hemi}"

            if not (salida / "beta.mgh").exists():
                t0 = time.time()
                print(f"▸ glmfit {medida}/{diseno}/{hemi} …", end="", flush=True)
                cmd = ["mri_glmfit",
                       "--y", str(entrada), "--fsgd", str(fsgd), "doss",
                       "--surf", "fsaverage", hemi,
                       "--cortex",                       # restringe a la corteza
                       "--glmdir", str(salida)]
                for c in contrastes:
                    cmd += ["--C", str(c)]
                r = gf.correr(cmd, log=base / f"log_glmfit_{hemi}.txt")
                ok = (salida / "beta.mgh").exists()
                print(f" {'OK' if ok else 'FALLÓ'} ({time.time()-t0:.0f}s)")
                if not ok:
                    faltantes.append(f"{medida}/{diseno}/{hemi}: glmfit falló")
                    continue
            else:
                print(f"▸ glmfit {medida}/{diseno}/{hemi} — ya existe")

            # corrección por clusters (Monte Carlo cacheado)
            hechos = list(salida.glob("*/cache.th*.abs.sig.cluster.summary"))
            if not hechos:
                t0 = time.time()
                print(f"  ▸ sim …", end="", flush=True)
                r = gf.correr(
                    ["mri_glmfit-sim", "--glmdir", str(salida),
                     "--cache", str(gf.CLUSTER_THR), "abs",
                     "--cwp", str(gf.CWP), "--2spaces"],
                    log=base / f"log_sim_{hemi}.txt")
                hechos = list(salida.glob("*/cache.th*.abs.sig.cluster.summary"))
                print(f" {'OK' if hechos else 'sin salida'} ({time.time()-t0:.0f}s)")

            # recoger los clusters de cada contraste
            for c in contrastes:
                nombre = c.stem
                cands = sorted((salida / nombre).glob("cache.th*.abs.sig.cluster.summary"))
                cl = gf.leer_clusters(cands[0]) if cands else pd.DataFrame()
                if cl.empty:
                    filas.append({"medida": medida, "diseno": diseno, "hemi": hemi,
                                  "contraste": nombre, "n_clusters": 0,
                                  "CWP_min": None, "size_mm2_max": None,
                                  "anotacion_pico": None})
                else:
                    sig = cl[cl.CWP < gf.CWP]
                    filas.append({
                        "medida": medida, "diseno": diseno, "hemi": hemi,
                        "contraste": nombre, "n_clusters": len(sig),
                        "CWP_min": float(cl.CWP.min()),
                        "size_mm2_max": float(cl.size_mm2.max()),
                        "anotacion_pico": cl.iloc[0].get("anotacion", ""),
                    })

resumen = pd.DataFrame(filas)
print("\n" + "=" * 84)
print("RESULTADO VERTEX-WISE — clusters que sobreviven (CWP < 0,05, 2 hemisferios)")
print("=" * 84)
if resumen.empty:
    print("sin resultados: revisar el preprocesamiento")
else:
    print(resumen.to_string(index=False))
    resumen.to_csv(cfg.RESULTS / "etapaA5_resultados_vertexwise.csv", index=False)
    tot = int(resumen.n_clusters.sum())
    print(f"\n→ clusters significativos en total: {tot}")
    if tot:
        print(resumen[resumen.n_clusters > 0].to_string(index=False))

if faltantes:
    print("\n⚠️  pendientes o fallidos:")
    for f in faltantes:
        print("   ", f)

# %% ── detalle de los clusters significativos ───────────────────────────────
detalle = []
for f in (resumen[resumen.n_clusters > 0].itertuples() if not resumen.empty else []):
    cands = sorted((gf.GLM_DIR / f.medida / f.diseno / f"glm.{f.hemi}" / f.contraste)
                   .glob("cache.th*.abs.sig.cluster.summary"))
    cl = gf.leer_clusters(cands[0]) if cands else pd.DataFrame()
    cl = cl[cl.CWP < gf.CWP]
    for c in cl.itertuples():
        detalle.append({
            "medida": f.medida, "diseno": f.diseno, "hemi": f.hemi,
            "contraste": f.contraste, "cluster": c.cluster,
            "size_mm2": c.size_mm2, "CWP": c.CWP, "max": c.max,
            "MNI": f"{c.MNIX:.0f}, {c.MNIY:.0f}, {c.MNIZ:.0f}",
            "anotacion": c.anotacion,
        })
detalle = pd.DataFrame(detalle)
if not detalle.empty:
    print("\n=== DETALLE DE LOS CLUSTERS SIGNIFICATIVOS ===")
    print(detalle.to_string(index=False))
    detalle.to_csv(cfg.RESULTS / "etapaA5_clusters_resultados.csv", index=False)

# %% ── al documento ─────────────────────────────────────────────────────────
with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion("Etapa A5 · Whole-brain vertex-wise (mri_glmfit)",
            "El mismo modelo ajustado en cada uno de los ~164.000 vértices de la "
            "superficie, sin depender de la parcelación del atlas.")
doc.chips({"Vértices por hemisferio": "163.842", "Suavizado": f"fwhm {gf.FWHM}",
           "Umbral de cluster": "p<0,001", "Corrección": "Monte Carlo + 2 hemisferios",
           "Clusters significativos": int(resumen.n_clusters.sum()) if not resumen.empty else 0})
doc.texto(
    "Se ajusta <code>--doss</code> (un intercepto por grupo, pendiente común para las "
    "covariables), que es exactamente el modelo de las etapas A. La corrección es "
    "<b>por clusters</b>: el tamaño de cada cúmulo de vértices contiguos supraumbral se "
    "compara con la distribución nula simulada por Monte Carlo, y se corrige además por los "
    "dos hemisferios. El umbral de formación es p&lt;0,001, el recomendado por FreeSurfer para "
    "evitar los cúmulos inflados de los umbrales laxos."
)
if not resumen.empty:
    doc.h3("Resumen por medida, diseño y contraste")
    doc.tabla(resumen)
if not detalle.empty:
    doc.h3("Clusters significativos")
    doc.tabla(detalle)

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print("\n→ documento actualizado")
