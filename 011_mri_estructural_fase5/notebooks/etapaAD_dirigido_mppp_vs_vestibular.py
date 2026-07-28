"""
ETAPA AD — Contraste DIRIGIDO MPPP vs Vestibular (dos grupos, n=36).

Justificación teórica (decisión del PI, 2026-07-28): ambos grupos comparten
historia de patología vestibular; lo que los distingue es la **cronificación
perceptual**. Preguntar directamente qué separa al que cronifica del que no es,
conceptualmente, la pregunta central del proyecto — y además esquiva el cuello de
botella estadístico de los 10 sanos: quedan **17 vs 19, balanceado**.

Comparado con el diseño de 3 grupos, aquí:
  · el N baja de 46 a 36, pero el contraste de interés gana potencia porque ya no
    depende del brazo de n=10;
  · el omnibus tiene 1 grado de libertad → es directamente el contraste, sin post-hoc;
  · la corrección FDR se aplica a las mismas familias de medida.

⚠️ Esta etapa NO reemplaza a A1/A2: las responde una pregunta distinta. Se reporta
junto a ellas, no en su lugar.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaAD_dirigido_mppp_vs_vestibular.py
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
FIGS = cfg.FIGS / "etapaAD"

m = cfg.cargar_master()
X = pd.concat([rois.construir_matriz(m, "alta"), rois.construir_matriz(m, "media")], axis=1)
datos = pd.concat([m.drop(columns=[c for c in X.columns if c in m.columns]), X], axis=1)

plan = pd.concat([rois.plan_de_pruebas("alta"), rois.plan_de_pruebas("media")],
                 ignore_index=True)
plan["etapa_origen"] = plan["etapa"]
plan["etapa"] = "AD"
# La familia FDR distingue prioridad alta de media: siguen siendo confirmatorio
# primario y secundario, también en este diseño.
plan["familia_fdr"] = plan["etapa_origen"] + "_" + plan["medida"]

PACIENTES = datos[datos["Grupo"].isin(["MPPP", "Vestibular"])].copy()
print(f"AD · {len(plan)} pruebas · n={len(PACIENTES)} "
      f"({PACIENTES['Grupo'].value_counts().to_dict()})")
print(f"familias: {plan.familia_fdr.value_counts().to_dict()}")

# %% ── modelos ──────────────────────────────────────────────────────────────
CONTRASTE = [("MPPP", "Vestibular")]
print("\n▸ Modelo A (n=36, sin ansiedad)")
A = pl.correr_bloque(PACIENTES, plan, pl.COVAR_BASE, "AD_sin_ansiedad",
                     contrastes=CONTRASTE, referencia="Vestibular")
print("\n▸ Modelo B (con STAI-Rasgo y BDI)")
B = pl.correr_bloque(PACIENTES, plan, pl.COVAR_ANSIEDAD, "AD_con_ansiedad",
                     contrastes=CONTRASTE, referencia="Vestibular")
pd.concat([A, B], ignore_index=True).to_csv(
    cfg.RESULTS / "etapaAD_resultados_dirigido.csv", index=False)

# %% ── lectura ──────────────────────────────────────────────────────────────
resumen_A = mult.resumen_familias(A, familia=["etapa", "familia_fdr"])
resumen_B = mult.resumen_familias(B, familia=["etapa", "familia_fdr"])
print("\n=== RESUMEN POR FAMILIA · modelo A ===")
print(resumen_A.to_string(index=False))
print("\n=== modelo B (con ansiedad) ===")
print(resumen_B.to_string(index=False))

enr = pl.enriquecimiento_de_familias(PACIENTES, plan, pl.COVAR_BASE,
                                     grupos=["MPPP", "Vestibular"])
print("\n=== ENRIQUECIMIENTO POR FAMILIA ===")
print(enr.round(4).to_string(index=False))
enr.to_csv(cfg.RESULTS / "etapaAD_enriquecimiento_resultados.csv", index=False)

direccional = pl.resumen_direccional(A, "MPPP_vs_Vestibular_d")
print("\n=== CONSISTENCIA DIRECCIONAL ===")
print(direccional.round(3).to_string(index=False))

A_orden = A.sort_values("p_perm")
print("\n=== 15 pruebas con menor p ===")
print(A_orden[["etapa_origen", "roi", "hemi", "medida", "n", "eta2p", "p_perm", "p_fdr",
               "MPPP_vs_Vestibular_d", "MPPP_vs_Vestibular_d_ic_low",
               "MPPP_vs_Vestibular_d_ic_high",
               "sobrevive_fdr"]].head(15).round(4).to_string(index=False))

sob = A[A.sobrevive_fdr]
print(f"\n→ SOBREVIVEN AL FDR: {len(sob)} de {len(A)}")
if len(sob):
    print(sob[["etapa_origen", "roi", "hemi", "medida", "eta2p", "p_perm", "p_fdr",
               "MPPP_vs_Vestibular_d"]].round(4).to_string(index=False))
sob_B = B[B.sobrevive_fdr]
print(f"→ sobreviven en el modelo B (con ansiedad): {len(sob_B)} de {len(B)}")
if len(sob_B):
    print(sob_B[["roi", "hemi", "medida", "p_fdr", "MPPP_vs_Vestibular_d"]].round(4)
          .to_string(index=False))

# %% ── figuras ──────────────────────────────────────────────────────────────
figs = pl.figuras_estandar(A, PACIENTES, FIGS, "AD",
                           "MPPP_vs_Vestibular", "MPPP vs Vestibular (dirigido)",
                           n_violines=8)

# comparación de potencia: mismo contraste, dos diseños
try:
    tres = pd.read_csv(cfg.RESULTS / "etapaA1_resultados_ancova.csv")
    tres = tres[tres.modelo == "A_sin_ansiedad"]
    otro = pd.read_csv(cfg.RESULTS / "etapaA2_resultados_ancova.csv")
    tres = pd.concat([tres, otro[otro.modelo == "A_sin_ansiedad"]], ignore_index=True)
    comp = A.merge(tres, on=["roi", "hemi", "medida"], suffixes=("_dir", "_3g"))
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(4.6, 4.3))
    for medida, color in zip(["LGI", "thickness", "volume", "area"],
                             ["#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"]):
        s = comp[comp.medida == medida]
        ax.scatter(s["MPPP_vs_Vestibular_d_3g"], s["MPPP_vs_Vestibular_d_dir"],
                   s=30, color=color, alpha=0.8, linewidth=0.6,
                   edgecolor=fg.SURFACE, label=medida)
    lims = [min(ax.get_xlim()[0], ax.get_ylim()[0]), max(ax.get_xlim()[1], ax.get_ylim()[1])]
    ax.plot(lims, lims, color=fg.BASELINE, linewidth=1, zorder=0)
    ax.axhline(0, color=fg.GRID, linewidth=0.8, zorder=0)
    ax.axvline(0, color=fg.GRID, linewidth=0.8, zorder=0)
    ax.set_xlabel("d · diseño de 3 grupos (N=46)")
    ax.set_ylabel("d · diseño dirigido (n=36)")
    ax.set_title("El mismo contraste en los dos diseños", loc="left", color=fg.INK,
                 pad=fg.PAD_TITULO)
    ax.text(0, 1.015, "si los puntos caen sobre la diagonal, el efecto es el mismo y "
                      "lo que cambia es la precisión",
            transform=ax.transAxes, fontsize=7.5, color=fg.MUTED, va="bottom")
    ax.legend()
    ax.grid(alpha=0.5)
    ax.set_axisbelow(True)
    ruta_comp = fg.guardar(fig, FIGS / "comparacion_disenos")
    corr = comp["MPPP_vs_Vestibular_d_3g"].corr(comp["MPPP_vs_Vestibular_d_dir"])
    print(f"\ncorrelación de las d entre diseños: r = {corr:.3f}")
except FileNotFoundError:
    ruta_comp, corr = None, float("nan")

# %% ── al documento ─────────────────────────────────────────────────────────
with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion("Etapa AD · Contraste dirigido MPPP vs Vestibular (n=36)",
            "¿Qué distingue al paciente vestibular que cronifica del que no?")
doc.chips({"Diseño": "2 grupos", "MPPP": 17, "Vestibular": 19, "n": 36,
           "Pruebas": len(plan), "Sobreviven FDR": int(A.sobrevive_fdr.sum())})
doc.texto(
    "Ambos grupos comparten historia de patología vestibular periférica; lo que los "
    "separa es la cronificación perceptual. Conceptualmente es la pregunta central del "
    "proyecto, y estadísticamente evita el cuello de botella del brazo de 10 sanos: "
    "aquí los dos grupos están balanceados (17 vs 19). "
    "<b>No reemplaza a A1/A2</b> — responde una pregunta distinta y se reporta junto a ellas."
)
doc.h3("Cuántas sobreviven, por familia")
doc.tabla(resumen_A)
doc.texto("<b>Modelo B</b> (ajustando además por STAI-Rasgo y BDI, n≈27):")
doc.tabla(resumen_B)
doc.h3("Enriquecimiento por familia")
doc.tabla(enr.round(4))
doc.h3("Consistencia direccional")
doc.tabla(direccional.round(3))
doc.h3("Resultados completos")
doc.tabla(A_orden[["etapa_origen", "roi", "hemi", "medida", "n", "eta2p", "p_perm",
                   "p_fdr", "p_kw", "MPPP_vs_Vestibular_d", "MPPP_vs_Vestibular_d_ic_low",
                   "MPPP_vs_Vestibular_d_ic_high", "sobrevive_fdr"]].round(4),
          destacar="sobrevive_fdr")
doc.h3("Figuras")
doc.figura(figs["heatmap"], "Mapa de efectos ROI × medida", "")
doc.figura(figs["volcan"], f"Volcán de las {len(A)} pruebas", "")
if ruta_comp:
    doc.figura(ruta_comp, "Comparación de diseños",
               f"Correlación de los tamaños de efecto entre ambos diseños: r = {corr:.3f}. "
               "Un r alto indica que el efecto estimado es el mismo y lo que cambia es "
               "la precisión con que se mide.")
doc.galeria(figs["forest"])
doc.galeria(figs["violines"])

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print("\n→ documento actualizado")
