"""
ETAPA 0 — Descriptivos, supuestos y confundentes.
FONDECYT 11200469 · Fase 5.

Produce la Tabla 1 del paper y decide **empíricamente** qué covariables entran al
modelo, en vez de ajustar por costumbre. También verifica los supuestos de la
ANCOVA sobre las ROIs de la etapa A1.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapa0_descriptivos.py
En PyCharm: los marcadores `# %%` permiten correrlo por celdas (Scientific Mode).
"""

# %% ── imports y estilo ──────────────────────────────────────────────────────
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor

import config as cfg
import figuras as fg
import reporte as rp
import rois

fg.aplicar_estilo()
FIGS = cfg.FIGS / "etapa0"
FIGS.mkdir(parents=True, exist_ok=True)
cfg.RESULTS.mkdir(parents=True, exist_ok=True)

m = cfg.cargar_master()
print(f"Tabla maestra cargada: {m.shape[0]} sujetos × {m.shape[1]} columnas")
print(m["Grupo"].value_counts().to_string())

doc = rp.Reporte(
    "FASE 5 — Documento exploratorio",
    "MRI estructural en MPPP/PPPD · FONDECYT 11200469 · morfometría FreeSurfer (N=46)",
)

# %% ── 1. TABLA 1 ────────────────────────────────────────────────────────────
CONTINUAS = [
    ("Edad", "Edad (años)"), ("N_Educacional", "Nivel educacional (2–4)"),
    ("Edinburgo_imp", "Lateralidad (Edinburgh, imputado)"), ("eTIV", "eTIV (mm³)"),
    ("glob_SurfaceHoles", "SurfaceHoles (calidad de superficie)"),
    ("DHI", "DHI"), ("Niigata", "Niigata"), ("BDI", "BDI"),
    ("STAI_Rasgo", "STAI-Rasgo"), ("STAI_Estado", "STAI-Estado"), ("MOCA", "MOCA"),
    ("CSE_NI", "CSE no inmersivo"), ("EntropyRatio_NI", "Entropy-Ratio (NI)"),
    ("Htotal_NI", "Entropía total (NI)"),
]
CATEGORICAS = [("Genero", "Sexo")]


def fila_continua(col, etiqueta):
    d = m[["Grupo", col]].dropna()
    muestras = [d.loc[d.Grupo == g, col].to_numpy() for g in cfg.GRUPOS]
    fila = {"Variable": etiqueta, "N": len(d)}
    for g, s in zip(cfg.GRUPOS, muestras):
        fila[fg.ETIQUETA_GRUPO[g]] = (f"{np.median(s):.1f} [{np.percentile(s,25):.1f}–"
                                      f"{np.percentile(s,75):.1f}]" if len(s) else "—")
        fila[f"n_{fg.ETIQUETA_GRUPO[g]}"] = len(s)
    ok = [s for s in muestras if len(s) >= 2]
    fila["p (Kruskal-Wallis)"] = stats.kruskal(*ok).pvalue if len(ok) >= 2 else np.nan
    return fila


def fila_categorica(col, etiqueta):
    d = m[["Grupo", col]].dropna()
    tab = pd.crosstab(d[col], d["Grupo"])
    fila = {"Variable": etiqueta, "N": len(d)}
    for g in cfg.GRUPOS:
        col_g = tab[g] if g in tab else pd.Series(dtype=int)
        fila[fg.ETIQUETA_GRUPO[g]] = " / ".join(f"{i}:{int(v)}" for i, v in col_g.items())
        fila[f"n_{fg.ETIQUETA_GRUPO[g]}"] = int(col_g.sum())
    # Fisher exacto si alguna celda esperada < 5 (habitual con n=10 en un brazo)
    chi2, p, _, esperadas = stats.chi2_contingency(tab)
    fila["p (Kruskal-Wallis)"] = p
    fila["_test"] = "χ²" if esperadas.min() >= 5 else "χ² (celdas esperadas <5)"
    return fila


tabla1 = pd.DataFrame(
    [fila_continua(c, e) for c, e in CONTINUAS] + [fila_categorica(c, e) for c, e in CATEGORICAS]
)
cols_orden = (["Variable", "N"] + [fg.ETIQUETA_GRUPO[g] for g in cfg.GRUPOS]
              + ["p (Kruskal-Wallis)"])
tabla1_vista = tabla1[cols_orden]
print("\n=== TABLA 1 ===")
print(tabla1_vista.to_string(index=False))
tabla1_vista.to_csv(cfg.RESULTS / "etapa0_tabla1_resultados_descriptivos.csv", index=False)

# %% ── 2. ¿QUÉ CONFUNDENTES ESTÁN JUSTIFICADOS? ──────────────────────────────
CANDIDATOS = ["Edad", "N_Educacional", "eTIV", "glob_SurfaceHoles", "Edinburgo_imp"]
conf = []
for c in CANDIDATOS:
    d = m[["Grupo", c]].dropna()
    muestras = [d.loc[d.Grupo == g, c].to_numpy() for g in cfg.GRUPOS]
    H, p = stats.kruskal(*muestras)
    # epsilon² = tamaño de efecto del Kruskal-Wallis
    eps2 = (H - len(cfg.GRUPOS) + 1) / (len(d) - len(cfg.GRUPOS))
    conf.append({"covariable": c, "N": len(d), "H": H, "p": p, "epsilon2": max(eps2, 0),
                 "difiere_entre_grupos": p < 0.05})
# sexo, por separado (categórica)
tab_sexo = pd.crosstab(m["Genero"], m["Grupo"])
chi2, p_sexo, _, _ = stats.chi2_contingency(tab_sexo)
conf.append({"covariable": "Genero", "N": len(m), "H": chi2, "p": p_sexo,
             "epsilon2": np.nan, "difiere_entre_grupos": p_sexo < 0.05})
confundentes = pd.DataFrame(conf)
print("\n=== CONFUNDENTES: ¿difieren entre grupos? ===")
print(confundentes.round(4).to_string(index=False))
confundentes.to_csv(cfg.RESULTS / "etapa0_confundentes_resultados.csv", index=False)

# %% ── 3. COLINEALIDAD DE LAS COVARIABLES (VIF) ──────────────────────────────
X = m[["Edad", "N_Educacional", "eTIV"]].copy()
X["Genero_M"] = (m["Genero"] == "Masculino").astype(float)
X["const"] = 1.0
vif = pd.DataFrame({
    "covariable": [c for c in X.columns if c != "const"],
    "VIF": [variance_inflation_factor(X.to_numpy(), i)
            for i, c in enumerate(X.columns) if c != "const"],
})
print("\n=== VIF (colinealidad; >5 es problemático) ===")
print(vif.round(2).to_string(index=False))

# %% ── 4. SUPUESTOS SOBRE LAS ROIs DE A1 ─────────────────────────────────────
X_a1 = rois.construir_matriz(m, "alta")
plan_a1 = rois.plan_de_pruebas("alta")
sup = []
for var in X_a1.columns:
    d = pd.concat([m[["Grupo"]], X_a1[var]], axis=1).dropna()
    y = d[var].to_numpy()
    sw = stats.shapiro(y).pvalue
    lev = stats.levene(*[d.loc[d.Grupo == g, var].to_numpy() for g in cfg.GRUPOS]).pvalue
    z = np.abs((y - y.mean()) / y.std(ddof=1))
    sup.append({"variable": var, "shapiro_p": sw, "levene_p": lev,
                "no_normal": sw < 0.05, "heterocedastica": lev < 0.05,
                "n_outliers_z3": int((z > 3).sum())})
supuestos = pd.DataFrame(sup).merge(
    plan_a1[["variable", "medida", "roi", "hemi"]], on="variable", how="left")
print("\n=== SUPUESTOS EN LAS 58 VARIABLES DE A1 ===")
print(f"  no normales (Shapiro p<0,05):   {supuestos.no_normal.sum():>2} / {len(supuestos)}")
print(f"  heterocedásticas (Levene p<0,05): {supuestos.heterocedastica.sum():>2} / {len(supuestos)}")
print(f"  con outliers |z|>3:              {(supuestos.n_outliers_z3 > 0).sum():>2} / {len(supuestos)}")
print("\n  por medida:")
print(supuestos.groupby("medida")[["no_normal", "heterocedastica"]].sum().to_string())
supuestos.to_csv(cfg.RESULTS / "etapa0_supuestos_resultados.csv", index=False)

# %% ── 5. FIGURAS ────────────────────────────────────────────────────────────
figs = []
for col, etiqueta, nombre in [
    ("Edad", "Edad (años)", "edad"),
    ("eTIV", "eTIV (mm³)", "etiv"),
    ("glob_SurfaceHoles", "SurfaceHoles (n)", "surfaceholes"),
    ("CSE_NI", "CSE no inmersivo", "cse"),
]:
    fig, ax = fg.violin_por_grupo(m, col, titulo=etiqueta, ylabel=etiqueta)
    figs.append((fg.guardar(fig, FIGS / f"covariable_{nombre}"), etiqueta, ""))

# sexo por grupo
tab = pd.crosstab(m["Grupo"], m["Genero"])
fig, ax = fg.barras_comparadas(
    [fg.ETIQUETA_GRUPO[g] for g in cfg.GRUPOS],
    {c: [int(tab.loc[g, c]) if c in tab.columns else 0 for g in cfg.GRUPOS] for c in tab.columns},
    titulo="Sexo por grupo", ylabel="n sujetos",
    colores=["#2a78d6", "#eb6834"],
)
ax.text(0.5, 0.97, f"χ² p = {p_sexo:.3f}", transform=ax.transAxes, ha="center",
        fontsize=8, color=fg.MUTED)
ruta_sexo = fg.guardar(fig, FIGS / "covariable_sexo")

# mapa de faltantes del bloque conductual/clínico
bloque = ["Edinburgo", "DHI", "BDI", "EVA", "Niigata", "STAI_Rasgo", "STAI_Estado", "MOCA",
          "CSE_NI", "CSE_RV", "Htotal_NI", "Htotal_RV", "EntropyRatio_NI",
          "HeadAngMag_RV", "ScanPath_time_NI", "ScanPath_time_RV"]
orden = m.sort_values("Grupo").index
mat = m.loc[orden, bloque].notna().astype(int)
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(7.4, 4.6))
ax.imshow(mat.T, aspect="auto", cmap=fg.CMAP_SEQ, vmin=0, vmax=1, interpolation="nearest")
ax.set_yticks(range(len(bloque)))
ax.set_yticklabels(bloque, fontsize=8)
lim = np.cumsum([(m.loc[orden, "Grupo"] == g).sum() for g in sorted(m["Grupo"].unique())])
for x in lim[:-1]:
    ax.axvline(x - 0.5, color=fg.INK, linewidth=1.2)
centros = np.concatenate([[0], lim[:-1]]) + np.diff(np.concatenate([[0], lim])) / 2
ax.set_xticks(centros - 0.5)
ax.set_xticklabels([fg.ETIQUETA_GRUPO[g] for g in sorted(m["Grupo"].unique())])
ax.set_title("Cobertura de datos conductuales y clínicos", loc="left", color=fg.INK, pad=10)
ax.text(0, 1.02, "azul oscuro = con dato · claro = ausente · una columna por sujeto",
        transform=ax.transAxes, fontsize=8, color=fg.MUTED, va="bottom")
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
ruta_falt = fg.guardar(fig, FIGS / "cobertura_conductual")

# %% ── 6. AL DOCUMENTO ───────────────────────────────────────────────────────
doc.seccion(
    "Etapa 0 · Descriptivos, confundentes y supuestos",
    "Quiénes son los 46, en qué difieren los grupos antes de mirar el cerebro, "
    "y si la ANCOVA es aplicable.",
)
doc.chips({
    "N total": 46, "MPPP": 17, "Vestibular": 19, "Sano": 10,
    "N con LGI": 45, "Variables morfométricas": "2.847",
})

doc.h3("Tabla 1 · características de la muestra")
doc.texto("Mediana [IQR] por grupo. El contraste es Kruskal-Wallis de 3 grupos "
          "(no paramétrico, apropiado con n=10 en un brazo); para sexo, χ².")
doc.tabla(tabla1_vista, decimales=3)

doc.h3("¿Qué covariables están justificadas?")
doc.texto("Cada candidata se contrasta entre grupos. Las que difieren justifican el ajuste; "
          "las que no, se declaran y quedan para análisis de sensibilidad. "
          "Así el ajuste responde a los datos y no a la costumbre.")
doc.tabla(confundentes.round(4), destacar="difiere_entre_grupos")
doc.tabla(vif.round(2))

doc.h3("Supuestos de la ANCOVA en las 58 variables de la etapa A1")
doc.tabla(supuestos.groupby("medida")[["no_normal", "heterocedastica"]].sum().reset_index())

doc.h3("Figuras")
doc.galeria(figs + [(ruta_sexo, "Sexo por grupo", ""),
                    (ruta_falt, "Cobertura conductual", "")])

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
print(f"\n→ documento: {cfg.DOCS / 'REPORTE_EXPLORATORIO.html'}")

# el objeto `doc` se serializa para que la etapa siguiente lo continúe
import pickle

with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print("→ estado del reporte guardado para la etapa siguiente")
