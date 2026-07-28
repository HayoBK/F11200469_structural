"""
ETAPA C1 — Índice compuesto de la red DCNN.

En vez de preguntar ROI por ROI, colapsa las ROIs de la red en **un índice por
medida** y hace UNA prueba con cada uno. Con esto:

  · la familia pasa de 58 pruebas a 4 → la corrección deja de ser el cuello de botella;
  · la potencia sube mucho (promediar ROIs cancela ruido de medición);
  · y sobre todo, es la hipótesis tal como está formulada — "la red DCNN está
    alterada" — en vez de "esta ROI concreta lo está".

Se calculan tres alcances (ALTA, ALTA+MEDIA) y dos métodos (media de z, PC1),
para verificar que el resultado no depende de una elección arbitraria.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaC1_indice_red.py
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
import modelos
import multiplicidad as mult
import pipeline as pl
import rois

fg.aplicar_estilo()
FIGS = cfg.FIGS / "etapaC1"
FIGS.mkdir(parents=True, exist_ok=True)

m = cfg.cargar_master()
X_alta = rois.construir_matriz(m, "alta")
X_media = rois.construir_matriz(m, "media")
X = pd.concat([X_alta, X_media], axis=1)
plan_alta = rois.plan_de_pruebas("alta")
plan_media = rois.plan_de_pruebas("media")
plan_todo = pd.concat([plan_alta, plan_media], ignore_index=True)

datos = pd.concat([m.drop(columns=[c for c in X.columns if c in m.columns]), X], axis=1)

# %% ── construcción de los índices ──────────────────────────────────────────
MEDIDAS = ["LGI", "thickness", "volume", "area"]
indices, meta = {}, []
for alcance, plan_sub in [("alta", plan_alta), ("alta+media", plan_todo)]:
    for metodo in ["z", "pca"]:
        for medida in MEDIDAS:
            vs = plan_sub.loc[plan_sub.medida == medida, "variable"].tolist()
            nombre = f"idx_{alcance.replace('+','_')}_{metodo}_{medida}"
            indices[nombre] = pl.indice_compuesto(datos, vs, metodo=metodo)
            meta.append({"variable": nombre, "alcance": alcance, "metodo": metodo,
                         "medida": medida, "n_rois": len(vs)})
idx = pd.DataFrame(indices)
datos_idx = pd.concat([m, idx], axis=1)
meta = pd.DataFrame(meta)
print("Índices construidos:")
print(meta.to_string(index=False))

# consistencia interna de cada índice (¿las ROIs de la red covarían?)
alfa = []
for fila in meta.itertuples():
    vs = (plan_alta if fila.alcance == "alta" else plan_todo)
    vs = vs.loc[vs.medida == fila.medida, "variable"].tolist()
    Z = datos[vs].dropna()
    k = Z.shape[1]
    # alfa de Cronbach sobre las ROIs estandarizadas
    Zs = (Z - Z.mean()) / Z.std(ddof=1)
    a = k / (k - 1) * (1 - Zs.var(ddof=1).sum() / Zs.sum(axis=1).var(ddof=1))
    alfa.append({"medida": fila.medida, "alcance": fila.alcance, "n_rois": k,
                 "alfa_cronbach": a})
alfa = pd.DataFrame(alfa).drop_duplicates(subset=["medida", "alcance"])
print("\nConsistencia interna de la red (alfa de Cronbach):")
print(alfa.round(3).to_string(index=False))

# %% ── modelo sobre cada índice ─────────────────────────────────────────────
plan_idx = meta.copy()
plan_idx["etapa"] = "C1"
plan_idx["familia_fdr"] = plan_idx["alcance"] + "_" + plan_idx["metodo"]
plan_idx["ajusta_etiv"] = plan_idx["medida"].isin(["volume", "area"])
plan_idx["roi"] = "Red DCNN (" + plan_idx["alcance"] + ")"
plan_idx["hemi"] = "bilat"

print("\n▸ Modelo A (3 grupos, N=46)")
C1 = pl.correr_bloque(datos_idx, plan_idx, pl.COVAR_BASE, "A_sin_ansiedad")
print("\n▸ Modelo B (con ansiedad)")
C1b = pl.correr_bloque(datos_idx, plan_idx, pl.COVAR_ANSIEDAD, "B_con_ansiedad")
pd.concat([C1, C1b], ignore_index=True).to_csv(
    cfg.RESULTS / "etapaC1_resultados_indice_red.csv", index=False)

# %% ── contraste dirigido sobre el índice (MPPP vs Vestibular, n=36) ────────
solo_pac = datos_idx[datos_idx["Grupo"].isin(["MPPP", "Vestibular"])].copy()
print(f"\n▸ Contraste dirigido MPPP vs Vestibular sobre los índices (n={len(solo_pac)})")
C1d = pl.correr_bloque(
    solo_pac, plan_idx, pl.COVAR_BASE, "dirigido_MPPP_vs_Vest",
    contrastes=[("MPPP", "Vestibular")], referencia="Vestibular",
)
C1d.to_csv(cfg.RESULTS / "etapaC1_resultados_dirigido.csv", index=False)

# %% ── lectura ──────────────────────────────────────────────────────────────
VISTA = ["medida", "alcance", "metodo", "n_rois", "n", "eta2p", "eta2p_ic_low",
         "eta2p_ic_high", "p_param", "p_perm", "p_fdr", "sobrevive_fdr"]
print("\n" + "=" * 84)
print("C1 · TRES GRUPOS — índice de red por medida")
print("=" * 84)
print(C1.sort_values("p_perm")[
    VISTA + ["MPPP_vs_VoluntarioSano_d", "MPPP_vs_Vestibular_d"]].round(4).to_string(index=False))

print("\n" + "=" * 84)
print("C1 · DIRIGIDO MPPP vs VESTIBULAR (n=36, dos grupos balanceados)")
print("=" * 84)
print(C1d.sort_values("p_perm")[
    VISTA + ["MPPP_vs_Vestibular_d", "MPPP_vs_Vestibular_d_ic_low",
             "MPPP_vs_Vestibular_d_ic_high"]].round(4).to_string(index=False))

# %% ── figuras ──────────────────────────────────────────────────────────────
figs_violin = []
for fila in plan_idx[(plan_idx.metodo == "z")].itertuples():
    r3 = C1[C1.variable == fila.variable].iloc[0]
    rd = C1d[C1d.variable == fila.variable].iloc[0]
    fig, _ = fg.violin_por_grupo(
        datos_idx, fila.variable,
        titulo=f"Índice de red DCNN · {fila.medida} ({fila.alcance})",
        subtitulo=(f"{fila.n_rois} ROIs · 3 grupos: p(perm)={r3.p_perm:.4f} · "
                   f"dirigido MPPP-Vest: p={rd.p_perm:.4f}, d={rd.MPPP_vs_Vestibular_d:.2f}"),
        ylabel="índice (media de z)")
    figs_violin.append((fg.guardar(fig, FIGS / f"violin_{fila.variable}"),
                        f"Índice {fila.medida} ({fila.alcance})", ""))

# forest comparando los dos diseños
comp = []
for fila in plan_idx[plan_idx.metodo == "z"].itertuples():
    r3 = C1[C1.variable == fila.variable].iloc[0]
    rd = C1d[C1d.variable == fila.variable].iloc[0]
    comp.append({"etiqueta": f"{fila.medida} · {fila.alcance} · 3 grupos",
                 "d": r3.MPPP_vs_Vestibular_d, "lo": r3.MPPP_vs_Vestibular_d_ic_low,
                 "hi": r3.MPPP_vs_Vestibular_d_ic_high, "sig": bool(r3.p_perm < 0.05)})
    comp.append({"etiqueta": f"{fila.medida} · {fila.alcance} · dirigido n=36",
                 "d": rd.MPPP_vs_Vestibular_d, "lo": rd.MPPP_vs_Vestibular_d_ic_low,
                 "hi": rd.MPPP_vs_Vestibular_d_ic_high, "sig": bool(rd.p_perm < 0.05)})
comp = pd.DataFrame(comp).sort_values("d")
fig, _ = fg.forest(comp, "d", "lo", "hi", "etiqueta", col_destaca="sig",
                   titulo="Índice de red DCNN · MPPP vs Vestibular",
                   subtitulo="comparación del diseño de 3 grupos y el dirigido · "
                             "en negrita, p(perm) < 0,05")
ruta_forest = fg.guardar(fig, FIGS / "forest_indices_comparacion")

# %% ── al documento ─────────────────────────────────────────────────────────
with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion("Etapa C1 · Índice compuesto de la red DCNN",
            "La hipótesis dice que la RED está alterada. Este análisis la prueba como red, "
            "no región por región.")
doc.chips({"ROIs colapsadas": "14–18 por índice", "Pruebas": len(plan_idx),
           "Métodos": "media de z + PC1", "Alcances": "alta / alta+media"})
doc.texto(
    "Colapsar las ROIs en un índice por medida reduce la familia de 58 pruebas a 4 y "
    "aumenta la potencia, porque promediar regiones cancela ruido de medición. Se calculan "
    "dos métodos (media de z-scores y primer componente principal) y dos alcances, para "
    "comprobar que el resultado no depende de una elección arbitraria."
)
doc.h3("¿Se comportan las ROIs como una red? (consistencia interna)")
doc.texto("Un alfa alto indica que las ROIs covarían entre sujetos, que es la premisa "
          "para tratarlas como un índice único.")
doc.tabla(alfa.round(3))
doc.h3("Diseño de 3 grupos")
doc.tabla(C1.sort_values("p_perm")[VISTA + ["MPPP_vs_VoluntarioSano_d",
                                            "MPPP_vs_Vestibular_d"]].round(4),
          destacar="sobrevive_fdr")
doc.h3("Contraste dirigido MPPP vs Vestibular (n=36)")
doc.texto("Dos grupos balanceados (17 vs 19), sin el cuello de botella de los 10 sanos. "
          "Teóricamente es el contraste más informativo: ambos grupos comparten historia "
          "vestibular, y la pregunta es qué distingue al que cronifica.")
doc.tabla(C1d.sort_values("p_perm")[VISTA + ["MPPP_vs_Vestibular_d",
                                             "MPPP_vs_Vestibular_d_ic_low",
                                             "MPPP_vs_Vestibular_d_ic_high"]].round(4),
          destacar="sobrevive_fdr")
doc.h3("Figuras")
doc.figura(ruta_forest, "Índices de red en los dos diseños", "")
doc.galeria(figs_violin)

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print("\n→ documento actualizado")
