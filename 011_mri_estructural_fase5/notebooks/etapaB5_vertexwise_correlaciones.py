"""
ETAPA B5 — Vertex-wise de las correlaciones estructura ↔ conducta y severidad.

Lo mismo que la etapa A5, pero en vez de contrastar grupos se contrasta la
**pendiente de un regresor continuo**: para cada vértice se pregunta si la medida
morfométrica escala con el outcome. El contraste es un 1 en la columna del
outcome y ceros en el resto, así que prueba directamente H0: pendiente = 0.

Cuatro outcomes en dos ejes:
  · navegación espacial — `CSE_NI`, `EntropyRatio_NI`
  · severidad de enfermedad — `Niigata`, `DHI`

Y dos contextos:
  · **global** (N=46, Grupo como clase) para navegación
  · **pacientes** (MPPP+Vestibular, n≈31) para severidad y también para navegación

Igual que en A5, el LGI va sin suavizado adicional (ver `glmfit.py`).

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaB5_vertexwise_correlaciones.py
"""

# %% ── setup ────────────────────────────────────────────────────────────────
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

import config as cfg
import figuras as fg
import glmfit as gf

fg.aplicar_estilo()
FIGS = cfg.FIGS / "etapaB5"
FIGS.mkdir(parents=True, exist_ok=True)

m = cfg.cargar_master()
m["Genero_M"] = (m["Genero"] == "Masculino").astype(int)
lgi_cols = [c for c in m.columns if c.startswith("lgi_")]
m["tiene_lgi"] = m[lgi_cols].notna().any(axis=1)

COVAR = ["Edad", "Genero_M", "N_Educacional"]
MEDIDAS = ["thickness", "area", "volume", "pial_lgi"]

# Un diseño por (outcome × contexto). El outcome entra como variable continua y
# el contraste prueba su pendiente.
DISENOS = {
    "nav_global_CSE":       dict(outcome="CSE_NI", clases=["Voluntario Sano", "Vestibular", "MPPP"]),
    "nav_global_EntRatio":  dict(outcome="EntropyRatio_NI", clases=["Voluntario Sano", "Vestibular", "MPPP"]),
    "nav_pac_CSE":          dict(outcome="CSE_NI", clases=["Vestibular", "MPPP"]),
    "nav_pac_EntRatio":     dict(outcome="EntropyRatio_NI", clases=["Vestibular", "MPPP"]),
    "sev_pac_Niigata":      dict(outcome="Niigata", clases=["Vestibular", "MPPP"]),
    "sev_pac_DHI":          dict(outcome="DHI", clases=["Vestibular", "MPPP"]),
}

# %% ── generar diseños y preprocesar ────────────────────────────────────────
print("=== DISEÑOS ===")
inventario = []
for nombre, d in DISENOS.items():
    outcome = d["outcome"]
    for medida in MEDIDAS:
        usa_tiv = medida in ("area", "volume")
        # el outcome va AL FINAL de las variables: su contraste es la última columna
        covs = COVAR + (["eTIV"] if usa_tiv else []) + [outcome]
        base = gf.GLM_DIR / medida / nombre
        base.mkdir(parents=True, exist_ok=True)
        datos = m[m.tiene_lgi] if medida == "pial_lgi" else m

        incluidos = gf.escribir_fsgd(datos, base / "diseno.fsgd",
                                     f"{medida}_{nombre}",
                                     d["clases"], covs)
        # contraste: 0 en cada clase y cada covariable, 1 en el outcome
        vector = [0.0] * (len(d["clases"]) + len(covs) - 1) + [1.0]
        gf.escribir_contraste(base / f"pendiente_{outcome}.mtx", vector)
        if medida == "thickness":
            inventario.append({"diseno": nombre, "outcome": outcome, "n": len(incluidos),
                               "clases": len(d["clases"]),
                               "n_por_grupo": str(incluidos["Grupo"].value_counts().to_dict())})
inventario = pd.DataFrame(inventario)
print(inventario.to_string(index=False))

print("\n=== mris_preproc ===")
for nombre in DISENOS:
    for medida in MEDIDAS:
        base = gf.GLM_DIR / medida / nombre
        fwhm = gf.fwhm_de(medida)
        for hemi in ("lh", "rh"):
            salida = base / f"{hemi}.{medida}.fwhm{fwhm}.mgh"
            if salida.exists():
                continue
            cmd = ["mris_preproc", "--fsgd", str(base / "diseno.fsgd"),
                   "--target", "fsaverage", "--hemi", hemi, "--out", str(salida)]
            if medida in gf.MEDIDAS_QCACHE:
                cmd += ["--cache-in", f"{medida}.fwhm{fwhm}.fsaverage"]
            else:
                cmd += ["--meas", medida] + (["--fwhm", str(fwhm)] if fwhm else [])
            t0 = time.time()
            gf.correr(cmd, log=base / f"log_preproc_{hemi}.txt")
            print(f"  {medida}/{nombre}/{hemi}: "
                  f"{'OK' if salida.exists() else 'FALLÓ'} ({time.time()-t0:.0f}s)")

# %% ── glmfit + sim ─────────────────────────────────────────────────────────
print("\n=== glmfit + sim ===")
filas = []
for nombre, d in DISENOS.items():
    outcome = d["outcome"]
    for medida in MEDIDAS:
        base = gf.GLM_DIR / medida / nombre
        contraste = base / f"pendiente_{outcome}.mtx"
        for hemi in ("lh", "rh"):
            entrada = base / f"{hemi}.{medida}.fwhm{gf.fwhm_de(medida)}.mgh"
            if not entrada.exists():
                continue
            salida = base / f"glm.{hemi}"
            if not (salida / "beta.mgh").exists():
                gf.correr(["mri_glmfit", "--y", str(entrada),
                           "--fsgd", str(base / "diseno.fsgd"), "doss",
                           "--surf", "fsaverage", hemi, "--cortex",
                           "--glmdir", str(salida), "--C", str(contraste)],
                          log=base / f"log_glmfit_{hemi}.txt")
            if not (salida / "beta.mgh").exists():
                print(f"  ⚠️ glmfit falló: {medida}/{nombre}/{hemi}")
                continue
            if not list(salida.glob("*/cache.th*.abs.sig.cluster.summary")):
                gf.correr(["mri_glmfit-sim", "--glmdir", str(salida),
                           "--cache", str(gf.CLUSTER_THR), "abs",
                           "--cwp", str(gf.CWP), "--2spaces"],
                          log=base / f"log_sim_{hemi}.txt")

            cands = sorted((salida / f"pendiente_{outcome}")
                           .glob("cache.th*.abs.sig.cluster.summary"))
            cl = gf.leer_clusters(cands[0]) if cands else pd.DataFrame()
            sig = cl[cl.CWP < gf.CWP] if not cl.empty else cl
            filas.append({
                "diseno": nombre, "outcome": outcome, "medida": medida, "hemi": hemi,
                "n_clusters": len(sig),
                "CWP_min": float(cl.CWP.min()) if not cl.empty else None,
                "size_mm2_max": float(cl.size_mm2.max()) if not cl.empty else None,
                "fwhm_residual": float((salida / "fwhm.dat").read_text().strip())
                if (salida / "fwhm.dat").exists() else None,
                "pico": cl.iloc[0].anotacion if not cl.empty else None,
            })
        print(f"  {medida}/{nombre}: hecho")

resumen = pd.DataFrame(filas)
resumen.to_csv(cfg.RESULTS / "etapaB5_resultados_vertexwise_correlaciones.csv", index=False)

print("\n" + "=" * 90)
print("VERTEX-WISE DE CORRELACIONES — clusters que sobreviven (CWP<0,05, 2 hemisferios)")
print("=" * 90)
print(resumen.to_string(index=False))
tot = int(resumen.n_clusters.sum())
print(f"\n→ clusters significativos en total: {tot}")

detalle = []
for f in resumen[resumen.n_clusters > 0].itertuples():
    cands = sorted((gf.GLM_DIR / f.medida / f.diseno / f"glm.{f.hemi}" /
                    f"pendiente_{f.outcome}").glob("cache.th*.abs.sig.cluster.summary"))
    cl = gf.leer_clusters(cands[0]) if cands else pd.DataFrame()
    for c in cl[cl.CWP < gf.CWP].itertuples():
        detalle.append({"diseno": f.diseno, "outcome": f.outcome, "medida": f.medida,
                        "hemi": f.hemi, "size_mm2": c.size_mm2, "CWP": c.CWP,
                        "max": c.max, "MNI": f"{c.MNIX:.0f}, {c.MNIY:.0f}, {c.MNIZ:.0f}",
                        "anotacion": c.anotacion})
detalle = pd.DataFrame(detalle)
if not detalle.empty:
    print("\n=== DETALLE ===")
    print(detalle.to_string(index=False))
    detalle.to_csv(cfg.RESULTS / "etapaB5_clusters_resultados.csv", index=False)

# %% ── figuras de superficie de lo que sobreviva ────────────────────────────
import matplotlib.pyplot as plt
import nibabel as nib
from nilearn import plotting

SD = gf.SUBJECTS_DIR


def malla(hemi):
    return nib.freesurfer.read_geometry(str(SD / "fsaverage" / "surf" / f"{hemi}.inflated"))


def fondo(hemi):
    curv = nib.freesurfer.read_morph_data(str(SD / "fsaverage" / "surf" / f"{hemi}.curv"))
    lo, hi = np.percentile(curv, [5, 95])
    return np.clip(curv, lo, hi)


figs = []
for (diseno, outcome, medida), _ in (resumen[resumen.n_clusters > 0]
                                     .groupby(["diseno", "outcome", "medida"])):
    mapas = {}
    for hemi in ("lh", "rh"):
        d = gf.GLM_DIR / medida / diseno / f"glm.{hemi}" / f"pendiente_{outcome}"
        cands = sorted(d.glob("cache.th*.abs.sig.masked.mgh"))
        mapas[hemi] = (np.asarray(nib.load(str(cands[0])).get_fdata()).ravel()
                       if cands else None)
    if all(v is None for v in mapas.values()):
        continue
    vmax = max(np.nanmax(np.abs(v)) for v in mapas.values() if v is not None)
    fig, axes = plt.subplots(2, 2, figsize=(9.2, 7.0), subplot_kw={"projection": "3d"})
    for i, hemi in enumerate(("lh", "rh")):
        if mapas[hemi] is None:
            continue
        coords, faces = malla(hemi)
        for j, vista in enumerate(("lateral", "medial")):
            plotting.plot_surf_stat_map(
                (coords, faces), mapas[hemi],
                hemi="left" if hemi == "lh" else "right", view=vista,
                colorbar=False, bg_map=fondo(hemi), bg_on_data=True,
                threshold=1.3, vmax=vmax, cmap="cold_hot",
                axes=axes[i, j], figure=fig)
            axes[i, j].set_title(f"{'izquierdo' if hemi=='lh' else 'derecho'} · {vista}",
                                 fontsize=9, color=fg.INK_2)
    fig.suptitle(f"{medida} — {outcome} · {diseno}", x=0.02, y=0.985, ha="left",
                 va="top", fontsize=12, color=fg.INK)
    fig.text(0.02, 0.945, "azul = correlación negativa · solo clusters corregidos "
                          "(CWP<0,05, 2 hemisferios)", fontsize=8, color=fg.MUTED, va="top")
    fig.subplots_adjust(top=0.90, wspace=0.02, hspace=0.06)
    figs.append((fg.guardar(fig, FIGS / f"superficie_{medida}_{diseno}"),
                 f"{medida} ↔ {outcome}", ""))
    print(f"  figura: superficie_{medida}_{diseno}")

# %% ── al documento ─────────────────────────────────────────────────────────
with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion("Etapa B5 · Vertex-wise de las correlaciones",
            "¿Dónde escala la morfometría con la navegación y con la severidad, "
            "vértice a vértice?")
doc.chips({"Diseños": len(DISENOS), "Medidas": len(MEDIDAS),
           "Outcomes": "CSE · Entropy-Ratio · Niigata · DHI",
           "Clusters": tot})
doc.texto(
    "Mismo procedimiento que la etapa A5, pero el contraste prueba la <b>pendiente de un "
    "regresor continuo</b> en vez de una diferencia entre grupos: en cada vértice se pregunta "
    "si la medida escala con el outcome. Dos ejes separados — navegación espacial "
    "(CSE, Entropy-Ratio) y severidad de enfermedad (Niigata, DHI) — y dos contextos, "
    "muestra completa y solo pacientes."
)
doc.h3("N de cada diseño")
doc.tabla(inventario)
doc.h3("Resumen")
doc.tabla(resumen)
if not detalle.empty:
    doc.h3("Clusters significativos")
    doc.tabla(detalle)
if figs:
    doc.h3("Mapas")
    doc.galeria(figs)

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print("\n→ documento actualizado")
