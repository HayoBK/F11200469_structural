"""
ETAPA A3 — Sub-análisis a-priori de subestructuras (segmentaciones bayesianas).

Tres familias con FDR propio:
  · subcampos del hipocampo del eje POSTERIOR (body + tail) — 9 × 2 = 18
  · núcleos talámicos ANTERIORES (head-direction: AV, LD, VA, VAmc) — 4 × 2 = 8
  · núcleos de la amígdala — 10 × 2 = 20

Todas son volúmenes → todas se ajustan por eTIV.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaA3_subestructuras.py
"""

# %% ── setup ────────────────────────────────────────────────────────────────
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

import config as cfg
import figuras as fg
import multiplicidad as mult
import pipeline as pl
import rois

fg.aplicar_estilo()
FIGS = cfg.FIGS / "etapaA3"

m = cfg.cargar_master()

# %% ── plan de pruebas ──────────────────────────────────────────────────────
BLOQUES = [
    ("hipocampo_posterior", "hipp", rois.SUBCAMPOS_HIPOCAMPO_POSTERIOR, "Subcampo hipocampal"),
    ("talamo_anterior", "thal", rois.NUCLEOS_TALAMO_ANTERIOR, "Núcleo talámico"),
    ("amigdala", "amyg", rois.NUCLEOS_AMIGDALA, "Núcleo amigdalino"),
]
filas = []
for familia, pref, estructuras, etiqueta in BLOQUES:
    for est in estructuras:
        for hemi in ("lh", "rh"):
            col = f"{pref}_{hemi}_{est}"
            if col not in m.columns:
                raise KeyError(f"falta {col}")
            filas.append({
                "etapa": "A3", "familia_fdr": familia, "variable": col,
                "roi": est.replace("_", " "), "hemi": hemi, "medida": "volume",
                "atlas": pref, "tipo": "S", "ajusta_etiv": True,
                "n_esperado": 46, "bloque": etiqueta,
            })
plan = pd.DataFrame(filas)
print(f"A3 · {len(plan)} pruebas · familias: {plan.familia_fdr.value_counts().to_dict()}")

# %% ── modelos ──────────────────────────────────────────────────────────────
print("\n▸ Modelo A (N=46)")
A = pl.correr_bloque(m, plan, pl.COVAR_BASE, "A_sin_ansiedad")
print("\n▸ Modelo B (N≈34, con ansiedad)")
B = pl.correr_bloque(m, plan, pl.COVAR_ANSIEDAD, "B_con_ansiedad")
pd.concat([A, B], ignore_index=True).to_csv(
    cfg.RESULTS / "etapaA3_resultados_ancova.csv", index=False)

# %% ── lectura ──────────────────────────────────────────────────────────────
resumen_A = mult.resumen_familias(A, familia=["etapa", "familia_fdr"])
print("\n=== RESUMEN POR FAMILIA ===")
print(resumen_A.to_string(index=False))

enriquecimiento = pl.enriquecimiento_de_familias(m, plan, pl.COVAR_BASE)
print("\n=== ENRIQUECIMIENTO ===")
print(enriquecimiento.round(4).to_string(index=False))
enriquecimiento.to_csv(cfg.RESULTS / "etapaA3_enriquecimiento_resultados.csv", index=False)

dir_vest = pl.resumen_direccional(A, "MPPP_vs_Vestibular_d")
dir_sano = pl.resumen_direccional(A, "MPPP_vs_VoluntarioSano_d")
print("\n=== CONSISTENCIA DIRECCIONAL (MPPP vs Vestibular) ===")
print(dir_vest.round(3).to_string(index=False))

A_orden = A.sort_values("p_perm")
print("\n=== 12 con menor p ===")
print(A_orden[["familia_fdr", "roi", "hemi", "eta2p", "p_perm", "p_fdr",
               "MPPP_vs_VoluntarioSano_d", "MPPP_vs_Vestibular_d",
               "sobrevive_fdr"]].head(12).round(4).to_string(index=False))
print(f"\n→ sobreviven al FDR: {int(A.sobrevive_fdr.sum())} de {len(A)}")

# %% ── figuras ──────────────────────────────────────────────────────────────
FIGS.mkdir(parents=True, exist_ok=True)
figs_forest = []
for familia, sub in A.groupby("familia_fdr"):
    s = sub.copy()
    s["etiqueta"] = s["roi"] + "  " + s["hemi"]
    s = s.sort_values("MPPP_vs_Vestibular_d")
    fig, _ = fg.forest(
        s, "MPPP_vs_Vestibular_d", "MPPP_vs_Vestibular_d_ic_low",
        "MPPP_vs_Vestibular_d_ic_high", "etiqueta", col_destaca="sobrevive_fdr",
        titulo=f"MPPP vs Vestibular · {familia.replace('_', ' ')}",
        subtitulo=f"volumen ajustado por eTIV · familia de {len(s)} pruebas · N=46",
    )
    figs_forest.append((fg.guardar(fig, FIGS / f"forest_{familia}_MPPP_vs_Vest"),
                        familia.replace("_", " "), ""))
    fig, _ = fg.forest(
        s.sort_values("MPPP_vs_VoluntarioSano_d"), "MPPP_vs_VoluntarioSano_d",
        "MPPP_vs_VoluntarioSano_d_ic_low", "MPPP_vs_VoluntarioSano_d_ic_high",
        "etiqueta", col_destaca="sobrevive_fdr",
        titulo=f"MPPP vs Sano · {familia.replace('_', ' ')}",
        subtitulo=f"volumen ajustado por eTIV · N=46",
    )
    figs_forest.append((fg.guardar(fig, FIGS / f"forest_{familia}_MPPP_vs_Sano"),
                        familia.replace("_", " "), ""))

figs_violin = []
for f in A_orden.head(6).itertuples():
    fig, _ = fg.violin_por_grupo(
        m, f.variable, titulo=f"{f.roi} · {f.hemi}",
        subtitulo=(f"eta2p={f.eta2p:.3f} · p(perm)={f.p_perm:.4f} · "
                   f"p(FDR)={float(f.p_fdr):.3f}"),
        ylabel="volumen (mm³)")
    figs_violin.append((fg.guardar(fig, FIGS / f"violin_{f.variable}"),
                        f"{f.roi} {f.hemi}", ""))

# %% ── al documento ─────────────────────────────────────────────────────────
with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion("Etapa A3 · Subestructuras (subcampos hipocampales, núcleos talámicos y amigdalinos)",
            "Sub-análisis a-priori de las segmentaciones bayesianas de FreeSurfer.")
doc.chips({"Pruebas": len(plan), "Familias": 3, "Medida": "volumen (ajustado por eTIV)",
           "Sobreviven FDR": int(A.sobrevive_fdr.sum())})
doc.texto("La hipótesis es <b>posterior</b>: el eje hipocampal posterior (cuerpo y cola) "
          "es el implicado en representación espacial alocéntrica, y los núcleos talámicos "
          "anteriores son el sustrato de las células de dirección de la cabeza.")
doc.h3("Resumen y enriquecimiento por familia")
doc.tabla(resumen_A)
doc.tabla(enriquecimiento.round(4))
doc.h3("Consistencia direccional")
doc.texto("<b>MPPP vs Vestibular:</b>")
doc.tabla(dir_vest.round(3))
doc.texto("<b>MPPP vs Sano:</b>")
doc.tabla(dir_sano.round(3))
doc.h3("Resultados completos")
doc.tabla(A_orden[["familia_fdr", "roi", "hemi", "n", "eta2p", "p_perm", "p_fdr", "p_kw",
                   "MPPP_vs_VoluntarioSano_d", "MPPP_vs_Vestibular_d",
                   "sobrevive_fdr"]].round(4), destacar="sobrevive_fdr")
doc.h3("Figuras")
doc.galeria(figs_forest)
doc.galeria(figs_violin)

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print("\n→ documento actualizado")
