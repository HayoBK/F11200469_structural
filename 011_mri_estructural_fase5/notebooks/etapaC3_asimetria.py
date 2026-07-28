"""
ETAPA C3 — Asimetría hemisférica L−R.

La literatura VBM en PPPD reporta hallazgos lateralizados a la izquierda, y en
nuestras propias etapas A y B varias de las señales más fuertes aparecieron en un
solo hemisferio (parahipocampal izq, supramarginal der). Esta etapa pregunta
directamente si el **grado de asimetría** difiere entre grupos.

Índice de asimetría por ROI y medida:

    AI = (L − R) / (L + R)

Positivo = mayor a la izquierda. Es adimensional y auto-normalizado, así que
**no se ajusta por eTIV**: el tamaño de la cabeza se cancela en el cociente.
Se mantienen edad, sexo y educación como covariables.

Se corre en los dos diseños: 3 grupos y contraste dirigido MPPP vs Vestibular.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaC3_asimetria.py
"""

# %% ── setup ────────────────────────────────────────────────────────────────
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

import config as cfg
import figuras as fg
import multiplicidad as mult
import pipeline as pl
import rois

fg.aplicar_estilo()
FIGS = cfg.FIGS / "etapaC3"
FIGS.mkdir(parents=True, exist_ok=True)

m = cfg.cargar_master()
X = pd.concat([rois.construir_matriz(m, "alta"), rois.construir_matriz(m, "media")], axis=1)
plan_rois = pd.concat([rois.plan_de_pruebas("alta"), rois.plan_de_pruebas("media")],
                      ignore_index=True)
datos = pd.concat([m.drop(columns=[c for c in X.columns if c in m.columns]), X], axis=1)

# %% ── construcción de los índices de asimetría ─────────────────────────────
filas, series = [], {}
for (roi_n, medida), sub in plan_rois.groupby(["roi_n", "medida"]):
    if set(sub.hemi) != {"lh", "rh"}:
        continue
    v_lh = sub.loc[sub.hemi == "lh", "variable"].iloc[0]
    v_rh = sub.loc[sub.hemi == "rh", "variable"].iloc[0]
    L, R = datos[v_lh], datos[v_rh]
    nombre = f"AI_{roi_n}_{medida}"
    series[nombre] = (L - R) / (L + R)
    info = sub.iloc[0]
    filas.append({
        "variable": nombre, "etapa": "C3", "roi_n": roi_n, "roi": info.roi,
        "hemi": "AI", "medida": medida, "familia_fdr": medida,
        "ajusta_etiv": False,          # el índice ya es adimensional
        "prioridad": "alta" if info.etapa == "A1" else "media",
    })
plan = pd.DataFrame(filas)
datos_ai = pd.concat([m, pd.DataFrame(series)], axis=1)
print(f"C3 · {len(plan)} índices de asimetría · "
      f"familias: {plan.familia_fdr.value_counts().to_dict()}")

# ¿Hay asimetría poblacional? (test de que AI != 0 en toda la muestra)
asim_global = []
from scipy import stats

for f in plan.itertuples():
    v = datos_ai[f.variable].dropna()
    t, p = stats.wilcoxon(v)
    asim_global.append({"roi": f.roi, "medida": f.medida, "AI_mediana": v.median(),
                        "p_wilcoxon": p, "lado": "izquierda" if v.median() > 0 else "derecha"})
asim_global = pd.DataFrame(asim_global)
asim_global["p_fdr_global"] = mult.multipletests(
    asim_global.p_wilcoxon, alpha=0.05, method="fdr_bh")[1]
print(f"\nROIs con asimetría poblacional significativa: "
      f"{int((asim_global.p_fdr_global < 0.05).sum())} de {len(asim_global)}")

# %% ── modelos ──────────────────────────────────────────────────────────────
print("\n▸ Tres grupos (N=46)")
C3 = pl.correr_bloque(datos_ai, plan, pl.COVAR_BASE, "A_tres_grupos")

pacientes = datos_ai[datos_ai["Grupo"].isin(["MPPP", "Vestibular"])].copy()
print(f"\n▸ Dirigido MPPP vs Vestibular (n={len(pacientes)})")
C3d = pl.correr_bloque(pacientes, plan, pl.COVAR_BASE, "dirigido_MPPP_vs_Vest",
                       contrastes=[("MPPP", "Vestibular")], referencia="Vestibular")

pd.concat([C3, C3d], ignore_index=True).to_csv(
    cfg.RESULTS / "etapaC3_resultados_asimetria.csv", index=False)

# %% ── lectura ──────────────────────────────────────────────────────────────
resumen = mult.resumen_familias(C3, familia=["etapa", "familia_fdr"])
resumen_d = mult.resumen_familias(C3d, familia=["etapa", "familia_fdr"])
print("\n=== RESUMEN · tres grupos ===")
print(resumen.to_string(index=False))
print("\n=== RESUMEN · dirigido ===")
print(resumen_d.to_string(index=False))

enr = pl.enriquecimiento_de_familias(pacientes, plan, pl.COVAR_BASE,
                                     grupos=["MPPP", "Vestibular"])
print("\n=== ENRIQUECIMIENTO (dirigido) ===")
print(enr.round(4).to_string(index=False))
enr.to_csv(cfg.RESULTS / "etapaC3_enriquecimiento_resultados.csv", index=False)

VISTA = ["roi", "medida", "prioridad", "n", "eta2p", "p_perm", "p_fdr",
         "MPPP_vs_Vestibular_d", "sobrevive_fdr"]
print("\n=== 12 con menor p · dirigido ===")
print(C3d.sort_values("p_perm")[VISTA].head(12).round(4).to_string(index=False))
print(f"\n→ sobreviven al FDR: tres grupos {int(C3.sobrevive_fdr.sum())}/{len(C3)} · "
      f"dirigido {int(C3d.sobrevive_fdr.sum())}/{len(C3d)}")

# %% ── figuras ──────────────────────────────────────────────────────────────
figs_forest = []
for medida in ["LGI", "thickness", "volume", "area"]:
    s = C3d[C3d.medida == medida].copy()
    if s.empty:
        continue
    s["etiqueta"] = s["roi"]
    s = s.sort_values("MPPP_vs_Vestibular_d")
    fig, _ = fg.forest(s, "MPPP_vs_Vestibular_d", "MPPP_vs_Vestibular_d_ic_low",
                       "MPPP_vs_Vestibular_d_ic_high", "etiqueta",
                       col_destaca="sobrevive_fdr",
                       titulo=f"Asimetría L−R · {medida} · MPPP vs Vestibular",
                       subtitulo=f"índice (L−R)/(L+R) · n=36 · familia de {len(s)} pruebas")
    figs_forest.append((fg.guardar(fig, FIGS / f"forest_AI_{medida}"),
                        f"Asimetría · {medida}", ""))

# perfil de asimetría poblacional
piv = asim_global.pivot_table(index="roi", columns="medida", values="AI_mediana")
marcas = (asim_global.assign(sig=asim_global.p_fdr_global < 0.05)
          .pivot_table(index="roi", columns="medida", values="sig", aggfunc="max")
          .reindex(index=piv.index, columns=piv.columns))
fig, _ = fg.heatmap_efectos(
    piv, titulo="Asimetría hemisférica en la muestra completa",
    subtitulo="mediana de (L−R)/(L+R) · rojo = mayor a la izquierda · "
              "• = asimetría significativa (FDR)",
    cbar_label="índice de asimetría", marcas=marcas)
ruta_perfil = fg.guardar(fig, FIGS / "perfil_asimetria_poblacional")

# %% ── al documento ─────────────────────────────────────────────────────────
with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion("Etapa C3 · Asimetría hemisférica L−R",
            "¿Difiere el grado de lateralización entre grupos?")
doc.chips({"Índices": len(plan), "Diseños": "3 grupos + dirigido",
           "Ajuste por eTIV": "no (el índice es adimensional)",
           "Sobreviven FDR": f"{int(C3.sobrevive_fdr.sum())} / {int(C3d.sobrevive_fdr.sum())}"})
doc.texto(
    "Índice <b>AI = (L−R)/(L+R)</b> por ROI y medida; positivo significa mayor a la izquierda. "
    "Al ser un cociente auto-normalizado, el tamaño de la cabeza se cancela y "
    "<b>no se ajusta por eTIV</b>. Se mantienen edad, sexo y educación."
)
doc.h3("Asimetría poblacional (¿existe lateralización, en toda la muestra?)")
doc.texto("Antes de preguntar si los grupos difieren, conviene saber qué ROIs están "
          "lateralizadas de por sí. Wilcoxon de AI ≠ 0 sobre los 46, con FDR.")
doc.tabla(asim_global.sort_values("p_fdr_global").round(4).head(20))
doc.figura(ruta_perfil, "Perfil de asimetría de la muestra", "")
doc.h3("¿Difiere la asimetría entre grupos?")
doc.tabla(resumen)
doc.texto("<b>Contraste dirigido MPPP vs Vestibular:</b>")
doc.tabla(resumen_d)
doc.tabla(enr.round(4))
doc.h3("Resultados completos · dirigido")
doc.tabla(C3d.sort_values("p_perm")[VISTA + ["MPPP_vs_Vestibular_d_ic_low",
                                             "MPPP_vs_Vestibular_d_ic_high"]].round(4),
          destacar="sobrevive_fdr")
doc.h3("Figuras")
doc.galeria(figs_forest)

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print("\n→ documento actualizado")
