"""
ETAPA B — ¿Se asocia la estructura con la conducta y la clínica?

Misma escalera que la etapa A, pero preguntando por asociación en vez de por
diferencia entre grupos:

  B1 · Índices compuestos de red DCNN × outcomes   (pocas pruebas, alta potencia)
  B2 · ROIs individuales de prioridad ALTA × outcomes primarios
  B3 · Dentro de PACIENTES (MPPP+Vestibular, n≈36) — incluye Niigata y DHI,
       que en sanos no son interpretables. Corresponde al análisis C4 activado.

Outcomes (plan §3.1): CSE_NI y EntropyRatio_NI como primarios (N=46 completos),
el resto de la entropía y la réplica en RV como secundarios, Niigata y DHI solo
dentro de pacientes.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaB_estructura_conducta.py
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
import correlaciones as co
import figuras as fg
import multiplicidad as mult
import pipeline as pl
import rois

fg.aplicar_estilo()
FIGS = cfg.FIGS / "etapaB"
FIGS.mkdir(parents=True, exist_ok=True)

m = cfg.cargar_master()
X = pd.concat([rois.construir_matriz(m, "alta"), rois.construir_matriz(m, "media")], axis=1)
plan_alta = rois.plan_de_pruebas("alta")
plan_todo = pd.concat([plan_alta, rois.plan_de_pruebas("media")], ignore_index=True)
datos = pd.concat([m.drop(columns=[c for c in X.columns if c in m.columns]), X], axis=1)

# índices compuestos de red (los mismos de C1)
MEDIDAS = ["LGI", "thickness", "volume", "area"]
idx_cols = []
for medida in MEDIDAS:
    vs = plan_alta.loc[plan_alta.medida == medida, "variable"].tolist()
    nombre = f"idxred_{medida}"
    datos[nombre] = pl.indice_compuesto(datos, vs, metodo="z")
    idx_cols.append({"variable": nombre, "roi": "Red DCNN", "hemi": "bilat",
                     "medida": medida, "ajusta_etiv": medida in ("volume", "area")})
plan_idx = pd.DataFrame(idx_cols)

OUT_PRIMARIOS = ["CSE_NI", "EntropyRatio_NI"]
OUT_SECUNDARIOS = ["Htotal_NI", "Herror_NI", "Hpath_NI", "Entropia_Espacial_NI",
                   "CSE_RV", "Htotal_RV"]
OUT_CLINICOS = ["Niigata", "DHI"]

COVAR = ["Edad", "Genero", "Grupo"]        # global: Grupo entra como covariable
COVAR_TIV = ["Edad", "Genero", "Grupo", "eTIV"]
GRUPOS = ["MPPP", "Vestibular", "Voluntario Sano"]

print("Cobertura de los outcomes dentro de los 46:")
for o in OUT_PRIMARIOS + OUT_SECUNDARIOS + OUT_CLINICOS:
    print(f"  {o:<22} N={int(datos[o].notna().sum()):>2}  "
          f"{datos.groupby('Grupo')[o].count().to_dict()}")

# %% ── B1 · índices de red × todos los outcomes ─────────────────────────────
t0 = time.time()
print("\n▸ B1 · índices de red DCNN × outcomes")
B1 = co.barrido(datos, plan_idx, OUT_PRIMARIOS + OUT_SECUNDARIOS, COVAR,
                covariables_etiv=COVAR_TIV, grupos=GRUPOS, n_boot=3_000)
# familia = medida: cada medida se corrige con sus 8 outcomes
B1["familia_fdr"] = "idxred_" + B1["medida"]
B1 = mult.aplicar_fdr(B1, col_p="p", familia=["etapa", "familia_fdr"])
B1 = co.coherencia_simpson(B1, GRUPOS)
print(f"   {len(B1)} pruebas en {time.time()-t0:.0f}s · "
      f"sobreviven: {int(B1.sobrevive_fdr.sum())}")

# %% ── B2 · ROIs de prioridad alta × outcomes primarios ─────────────────────
t0 = time.time()
print("\n▸ B2 · ROIs prioridad alta × outcomes primarios")
B2 = co.barrido(datos, plan_alta, OUT_PRIMARIOS, COVAR,
                covariables_etiv=COVAR_TIV, grupos=GRUPOS, n_boot=2_000)
B2 = mult.aplicar_fdr(B2, col_p="p", familia=["etapa", "familia_fdr"])
B2 = co.coherencia_simpson(B2, GRUPOS)
print(f"   {len(B2)} pruebas en {time.time()-t0:.0f}s · "
      f"sobreviven: {int(B2.sobrevive_fdr.sum())}")

# %% ── B3 · dentro de PACIENTES (incluye Niigata y DHI) ─────────────────────
t0 = time.time()
pacientes = datos[datos["Grupo"].isin(["MPPP", "Vestibular"])].copy()
print(f"\n▸ B3 · dentro de pacientes (n={len(pacientes)}) — incluye Niigata y DHI")
plan_b3 = pd.concat([plan_idx, plan_alta[["variable", "roi", "hemi", "medida",
                                          "ajusta_etiv"]]], ignore_index=True)
B3 = co.barrido(pacientes, plan_b3, OUT_PRIMARIOS + OUT_CLINICOS, COVAR,
                covariables_etiv=COVAR_TIV, grupos=["MPPP", "Vestibular"],
                n_boot=2_000)
B3 = mult.aplicar_fdr(B3, col_p="p", familia=["etapa", "familia_fdr"])
B3 = co.coherencia_simpson(B3, ["MPPP", "Vestibular"])
print(f"   {len(B3)} pruebas en {time.time()-t0:.0f}s · "
      f"sobreviven: {int(B3.sobrevive_fdr.sum())}")

for nombre, t in [("B1", B1), ("B2", B2), ("B3", B3)]:
    t.to_csv(cfg.RESULTS / f"etapa{nombre}_resultados_correlaciones.csv", index=False)

# %% ── lectura ──────────────────────────────────────────────────────────────
VISTA = ["roi", "hemi", "medida", "outcome", "n", "rho", "ic_low", "ic_high",
         "p", "p_fdr", "sobrevive_fdr", "coherente"]

print("\n" + "=" * 90)
print("B1 · ÍNDICES DE RED × OUTCOMES — todas las pruebas")
print("=" * 90)
print(B1.sort_values("p")[VISTA].round(4).to_string(index=False))

print("\n" + "=" * 90)
print("B2 · 12 correlaciones más fuertes (ROIs individuales × outcomes primarios)")
print("=" * 90)
print(B2.sort_values("p")[VISTA].head(12).round(4).to_string(index=False))

print("\n" + "=" * 90)
print("B3 · DENTRO DE PACIENTES · 12 más fuertes")
print("=" * 90)
print(B3.sort_values("p")[VISTA].head(12).round(4).to_string(index=False))

# resumen de coherencia (paradoja de Simpson)
todo = pd.concat([B1, B2], ignore_index=True)
incoh = todo[(todo.p < 0.05) & (~todo.coherente)]
print(f"\n⚠️  correlaciones con p<0,05 cuyo signo NO coincide con el intra-grupo: "
      f"{len(incoh)} de {int((todo.p < 0.05).sum())}")
if len(incoh):
    print(incoh[["roi", "hemi", "medida", "outcome", "rho"]
                + [f"rho_{g}" for g in GRUPOS]].round(3).to_string(index=False))

# %% ── figuras ──────────────────────────────────────────────────────────────
figs_scatter = []
for f in pd.concat([B1, B3]).sort_values("p").head(6).itertuples():
    base = pacientes if f.n <= 36 else datos
    fig, _ = fg.scatter_estructura_conducta(
        base, f.variable, f.outcome,
        titulo=f"{f.roi} {f.hemi} · {f.medida} — {f.outcome}",
        subtitulo=(f"rho parcial = {f.rho:.3f} [{f.ic_low:.2f}, {f.ic_high:.2f}] · "
                   f"p={f.p:.4f} · p(FDR)={float(f.p_fdr):.3f} · N={f.n}"),
        xlabel=f"{f.medida} · {f.roi}", ylabel=f.outcome)
    figs_scatter.append((fg.guardar(fig, FIGS / f"scatter_{f.variable}_{f.outcome}"),
                         f"{f.roi} ↔ {f.outcome}", ""))

# heatmap índice de red × outcome
piv = B1.pivot_table(index="medida", columns="outcome", values="rho")
marcas = B1.pivot_table(index="medida", columns="outcome", values="sobrevive_fdr",
                        aggfunc="max").reindex(index=piv.index, columns=piv.columns)
fig, _ = fg.heatmap_efectos(
    piv, titulo="Índices de red DCNN y conducta",
    subtitulo="rho de Spearman parcial (edad, sexo, grupo; +eTIV en volumen y área) · "
              "• = sobrevive al FDR",
    cbar_label="rho parcial", marcas=marcas)
ruta_heat_b1 = fg.guardar(fig, FIGS / "heatmap_indices_outcomes")

# heatmap ROIs × outcomes primarios (LGI)
lgi_b2 = B2[B2.medida == "LGI"].copy()
lgi_b2["fila"] = lgi_b2["roi"] + "  " + lgi_b2["hemi"]
piv2 = lgi_b2.pivot_table(index="fila", columns="outcome", values="rho")
marcas2 = lgi_b2.pivot_table(index="fila", columns="outcome", values="sobrevive_fdr",
                             aggfunc="max").reindex(index=piv2.index, columns=piv2.columns)
fig, _ = fg.heatmap_efectos(
    piv2, titulo="LGI de cada ROI y outcomes primarios",
    subtitulo="rho de Spearman parcial · • = sobrevive al FDR de su familia",
    cbar_label="rho parcial", marcas=marcas2)
ruta_heat_b2 = fg.guardar(fig, FIGS / "heatmap_LGI_outcomes")

# forest de las correlaciones del índice LGI
lgi_idx = B1[B1.medida == "LGI"].copy()
lgi_idx["etiqueta"] = lgi_idx["outcome"]
lgi_idx = lgi_idx.sort_values("rho")
fig, _ = fg.forest(lgi_idx, "rho", "ic_low", "ic_high", "etiqueta",
                   col_destaca="sobrevive_fdr",
                   titulo="Índice de girificación de la red DCNN y conducta",
                   xlabel="rho de Spearman parcial (IC 95% BCa)",
                   subtitulo="global, N=46, ajustado por edad, sexo y grupo")
ruta_forest_b1 = fg.guardar(fig, FIGS / "forest_indice_LGI_conducta")

# %% ── al documento ─────────────────────────────────────────────────────────
with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion("Etapa B · Estructura ↔ conducta y clínica",
            "¿La morfometría se asocia con el desempeño en navegación, la entropía "
            "de búsqueda y la severidad sintomática?")
doc.chips({"B1 índices": len(B1), "B2 ROIs": len(B2), "B3 pacientes": len(B3),
           "Sobreviven FDR": int(B1.sobrevive_fdr.sum() + B2.sobrevive_fdr.sum()
                                 + B3.sobrevive_fdr.sum())})
doc.texto(
    "<b>Spearman parcial</b> (rankea, residualiza sobre covariables, correlaciona), "
    "robusto a no-normalidad y outliers. Se ajusta por edad, sexo y <b>grupo</b>, más eTIV "
    "en volumen y área. IC 95% bootstrap BCa y FDR-BH por familia."
)
doc.nota(
    "<b>Sobre la paradoja de Simpson.</b> Con tres grupos que difieren tanto en estructura "
    "como en conducta, una correlación global puede ser un artefacto de la separación entre "
    "grupos y llegar a tener signo opuesto al de la relación dentro de cada uno. Por eso "
    "toda correlación se reporta con su rho intra-grupo al lado y con la columna "
    "<code>coherente</code>, que marca si los signos concuerdan. "
    "<b>Una correlación fuerte pero incoherente no debe interpretarse como relación individual.</b>"
)

doc.h3("B1 · Índices compuestos de red × outcomes")
doc.tabla(B1.sort_values("p")[VISTA + [f"rho_{g}" for g in GRUPOS]].round(4),
          destacar="sobrevive_fdr")
doc.figura(ruta_heat_b1, "Índices de red ↔ conducta", "")
doc.figura(ruta_forest_b1, "Índice de girificación ↔ conducta", "")

doc.h3("B2 · ROIs individuales de prioridad alta × outcomes primarios")
doc.tabla(B2.sort_values("p")[VISTA].head(30).round(4), destacar="sobrevive_fdr")
doc.figura(ruta_heat_b2, "LGI por ROI ↔ outcomes primarios", "")

doc.h3("B3 · Dentro de pacientes (MPPP + Vestibular)")
doc.texto("Niigata y DHI solo son interpretables en pacientes: en un voluntario sano el "
          "puntaje es piso, no información. Analizarlos aquí es más potente y más limpio "
          "que forzar los 4–5 sanos con dato.")
doc.tabla(B3.sort_values("p")[VISTA].head(30).round(4), destacar="sobrevive_fdr")

doc.h3("Dispersiones")
doc.texto("La recta se ajusta <b>por grupo</b>, nunca una sola global — precisamente para "
          "que se vea si la relación existe dentro de cada grupo o solo entre ellos.")
doc.galeria(figs_scatter)

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print("\n→ documento actualizado")
