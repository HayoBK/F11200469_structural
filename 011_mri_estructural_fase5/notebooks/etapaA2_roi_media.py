"""
ETAPA A2 — ROIs a-priori de PRIORIDAD MEDIA (confirmatorio secundario).

78 pruebas = 9 ROIs corticales × 2 hemisferios × 4 medidas + 3 subcorticales × 2.
FDR dentro de cada familia de medida (18/18/24/18), separado del de A1: A1 es
confirmatorio primario y A2 secundario, no una sola familia de 136.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaA2_roi_media.py
"""

# %% ── setup ────────────────────────────────────────────────────────────────
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

import config as cfg
import figuras as fg
import pipeline as pl
import rois

fg.aplicar_estilo()
FIGS = cfg.FIGS / "etapaA2"

m = cfg.cargar_master()
plan = rois.plan_de_pruebas("media")
X = rois.construir_matriz(m, "media")
datos = pd.concat([m.drop(columns=[c for c in X.columns if c in m.columns]), X], axis=1)
print(f"A2 · {len(plan)} pruebas · familias: {plan.familia_fdr.value_counts().to_dict()}")

# %% ── los dos modelos ──────────────────────────────────────────────────────
print("\n▸ Modelo A (N=46, sin ansiedad/depresión)")
A = pl.correr_bloque(datos, plan, pl.COVAR_BASE, "A_sin_ansiedad")
print("\n▸ Modelo B (N≈34, con STAI-Rasgo y BDI)")
B = pl.correr_bloque(datos, plan, pl.COVAR_ANSIEDAD, "B_con_ansiedad")

pd.concat([A, B], ignore_index=True).to_csv(
    cfg.RESULTS / "etapaA2_resultados_ancova.csv", index=False)

# %% ── lectura ──────────────────────────────────────────────────────────────
import multiplicidad as mult

resumen_A = mult.resumen_familias(A, familia=["etapa", "familia_fdr"])
resumen_B = mult.resumen_familias(B, familia=["etapa", "familia_fdr"])
print("\n=== RESUMEN POR FAMILIA · modelo A ===")
print(resumen_A.to_string(index=False))

enriquecimiento = pl.enriquecimiento_de_familias(datos, plan, pl.COVAR_BASE)
print("\n=== ENRIQUECIMIENTO POR FAMILIA ===")
print(enriquecimiento.round(4).to_string(index=False))
enriquecimiento.to_csv(cfg.RESULTS / "etapaA2_enriquecimiento_resultados.csv", index=False)

dir_sano = pl.resumen_direccional(A, "MPPP_vs_VoluntarioSano_d")
dir_vest = pl.resumen_direccional(A, "MPPP_vs_Vestibular_d")
print("\n=== CONSISTENCIA DIRECCIONAL · MPPP vs Vestibular ===")
print(dir_vest.round(3).to_string(index=False))

A_orden = A.sort_values("p_perm")
print("\n=== 12 pruebas con menor p ===")
print(A_orden[["roi", "hemi", "medida", "n", "eta2p", "p_perm", "p_fdr",
               "MPPP_vs_VoluntarioSano_d", "MPPP_vs_Vestibular_d",
               "sobrevive_fdr"]].head(12).round(4).to_string(index=False))
print(f"\n→ sobreviven al FDR: {int(A.sobrevive_fdr.sum())} de {len(A)}")

# %% ── figuras ──────────────────────────────────────────────────────────────
figs = pl.figuras_estandar(
    A, datos, FIGS, "A2",
    "MPPP_vs_VoluntarioSano", "MPPP vs Sano",
    "MPPP_vs_Vestibular", "MPPP vs Vestibular",
)

# %% ── al documento ─────────────────────────────────────────────────────────
with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion("Etapa A2 · ROIs a-priori de prioridad MEDIA (confirmatorio secundario)",
            "Las mismas preguntas, extendidas a las 11 regiones de prioridad media.")
doc.chips({"Pruebas": len(plan), "Familias FDR": 4, "Modelo A": "N=46",
           "Modelo B": "N≈34", "Sobreviven FDR": int(A.sobrevive_fdr.sum())})
doc.h3("Cuántas sobreviven, por familia")
doc.tabla(resumen_A)
doc.texto("<b>Modelo B</b> (ajustando además por STAI-Rasgo y BDI):")
doc.tabla(resumen_B)
doc.h3("Enriquecimiento de cada familia")
doc.tabla(enriquecimiento.round(4))
doc.h3("Consistencia direccional")
doc.texto("Con n pequeño, que una familia entera apunte en la misma dirección suele "
          "ser más informativo que cualquier p individual.")
doc.texto("<b>MPPP vs Vestibular:</b>")
doc.tabla(dir_vest.round(3))
doc.texto("<b>MPPP vs Sano:</b>")
doc.tabla(dir_sano.round(3))
doc.h3("Resultados completos · modelo A")
doc.tabla(A_orden[pl.COLS_VISTA + ["MPPP_vs_VoluntarioSano_d", "MPPP_vs_Vestibular_d"]].round(4),
          destacar="sobrevive_fdr")
doc.h3("Figuras")
doc.figura(figs["heatmap"], "Mapa de efectos ROI × medida", "")
doc.figura(figs["volcan"], "Volcán de las 78 pruebas", "")
doc.galeria(figs["forest"])
doc.galeria(figs["violines"])

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print("\n→ documento actualizado")
