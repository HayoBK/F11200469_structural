"""
ETAPA C2 — Covarianza estructural de la red DCNN.

Pregunta distinta de todo lo anterior: no si las regiones son más grandes o más
pequeñas, sino si están **organizadas** de la misma manera. Dos grupos pueden
tener ROIs de idéntico tamaño y aun así diferir en cuánto covarían entre sí, lo
que se interpreta como diferencias en la coordinación del desarrollo o en la
integridad de la red.

Procedimiento:
  1. Dentro de cada grupo, se residualiza cada ROI sobre edad, sexo (+eTIV en
     volumen y área). Se hace **dentro** de grupo para no inducir covarianza
     espuria por las diferencias de medias entre grupos.
  2. Matriz de correlación de Spearman entre las 14 ROIs de prioridad alta.
  3. Estadístico global = media de las 91 aristas en z de Fisher.
  4. Comparación entre grupos por **permutación de las etiquetas**.

⚠️ Limitación estructural de este análisis: una matriz de correlación de 14
variables estimada con n=10 (sanos) es muy inestable. El contraste interpretable
es MPPP vs Vestibular (17 vs 19); el grupo sano se muestra pero no se contrasta
formalmente.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaC2_covarianza_estructural.py
"""

# %% ── setup ────────────────────────────────────────────────────────────────
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

import config as cfg
import figuras as fg
import rois
from correlaciones import _matriz_covariables, _residualizar

fg.aplicar_estilo()
FIGS = cfg.FIGS / "etapaC2"
FIGS.mkdir(parents=True, exist_ok=True)

m = cfg.cargar_master()
X = rois.construir_matriz(m, "alta")
plan = rois.plan_de_pruebas("alta")
datos = pd.concat([m.drop(columns=[c for c in X.columns if c in m.columns]), X], axis=1)

MEDIDAS = ["LGI", "thickness", "volume", "area"]
COVAR = ["Edad", "Genero"]
SEED = 11200469


# %% ── construcción de las matrices ─────────────────────────────────────────
def matriz_covarianza(d: pd.DataFrame, variables: list[str], covariables: list[str]):
    """Matriz de correlación de Spearman entre ROIs, residualizadas sobre covariables."""
    sub = d[variables + covariables].dropna()
    if len(sub) < len(covariables) + 4:
        return None, 0
    C = _matriz_covariables(sub, covariables)
    R = np.column_stack([
        _residualizar(stats.rankdata(sub[v].to_numpy()), C) for v in variables
    ])
    return np.corrcoef(R, rowvar=False), len(sub)


def media_z(M: np.ndarray) -> float:
    """Media de las aristas en z de Fisher (evita promediar correlaciones crudas)."""
    iu = np.triu_indices_from(M, k=1)
    r = np.clip(M[iu], -0.999, 0.999)
    return float(np.mean(np.arctanh(r)))


resultados, matrices = [], {}
for medida in MEDIDAS:
    variables = plan.loc[plan.medida == medida, "variable"].tolist()
    cov = COVAR + (["eTIV"] if medida in ("volume", "area") else [])
    for grupo in cfg.GRUPOS:
        M, n = matriz_covarianza(datos[datos.Grupo == grupo], variables, cov)
        if M is None:
            continue
        matrices[(medida, grupo)] = M
        resultados.append({"medida": medida, "grupo": grupo, "n": n,
                           "media_z": media_z(M),
                           "r_medio": float(np.tanh(media_z(M)))})
tabla_grupos = pd.DataFrame(resultados)
print("=== Covarianza estructural media por grupo ===")
print(tabla_grupos.round(3).to_string(index=False))

# %% ── contraste MPPP vs Vestibular por permutación ─────────────────────────
pruebas = []
for medida in MEDIDAS:
    variables = plan.loc[plan.medida == medida, "variable"].tolist()
    cov = COVAR + (["eTIV"] if medida in ("volume", "area") else [])
    d = datos[datos.Grupo.isin(["MPPP", "Vestibular"])][
        variables + cov + ["Grupo"]].dropna()

    M_a, n_a = matriz_covarianza(d[d.Grupo == "MPPP"], variables, cov)
    M_b, n_b = matriz_covarianza(d[d.Grupo == "Vestibular"], variables, cov)
    obs = media_z(M_a) - media_z(M_b)

    # similaridad de la ESTRUCTURA (correlación entre los vectores de aristas)
    iu = np.triu_indices_from(M_a, k=1)
    sim = float(stats.spearmanr(M_a[iu], M_b[iu]).statistic)

    rng = np.random.default_rng(SEED)
    etiquetas = d["Grupo"].to_numpy()
    nulo = []
    for _ in range(2_000):
        perm = rng.permutation(etiquetas)
        dd = d.assign(G=perm)
        Ma, _ = matriz_covarianza(dd[dd.G == "MPPP"], variables, cov)
        Mb, _ = matriz_covarianza(dd[dd.G == "Vestibular"], variables, cov)
        if Ma is None or Mb is None:
            continue
        nulo.append(media_z(Ma) - media_z(Mb))
    nulo = np.array(nulo)
    p = float((1 + np.sum(np.abs(nulo) >= abs(obs))) / (1 + len(nulo)))

    pruebas.append({
        "medida": medida, "n_MPPP": n_a, "n_Vest": n_b,
        "r_medio_MPPP": float(np.tanh(media_z(M_a))),
        "r_medio_Vest": float(np.tanh(media_z(M_b))),
        "dif_z": obs, "p_perm": p, "similaridad_estructura": sim,
    })
contraste = pd.DataFrame(pruebas)
# Son 4 pruebas (una por medida): también aquí hay que corregir.
from statsmodels.stats.multitest import multipletests

rechaza, p_fdr, _, _ = multipletests(contraste.p_perm, alpha=0.05, method="fdr_bh")
contraste["p_fdr"] = p_fdr
contraste["sobrevive_fdr"] = rechaza
print("\n=== MPPP vs Vestibular · covarianza media (permutación, 2.000) ===")
print(contraste.round(4).to_string(index=False))
contraste.to_csv(cfg.RESULTS / "etapaC2_resultados_covarianza.csv", index=False)
tabla_grupos.to_csv(cfg.RESULTS / "etapaC2_matrices_resultados_por_grupo.csv", index=False)

# %% ── figuras ──────────────────────────────────────────────────────────────
etiquetas_roi = [r.split("_", 1)[1].rsplit("_", 2)[0][:18]
                 for r in plan.loc[plan.medida == "LGI", "variable"]]
etiquetas_roi = [f"{r.roi[:16]} {r.hemi}" for r in
                 plan[plan.medida == "LGI"].itertuples()]

figs = []
for medida in MEDIDAS:
    presentes = [g for g in cfg.GRUPOS if (medida, g) in matrices]
    fig, axes = plt.subplots(1, len(presentes),
                             figsize=(4.0 * len(presentes), 4.3))
    axes = np.atleast_1d(axes)
    for ax, grupo in zip(axes, presentes):
        M = matrices[(medida, grupo)]
        im = ax.imshow(M, cmap=fg.CMAP_DIV, vmin=-1, vmax=1)
        n = int(tabla_grupos[(tabla_grupos.medida == medida)
                             & (tabla_grupos.grupo == grupo)].n.iloc[0])
        ax.set_title(f"{fg.ETIQUETA_GRUPO[grupo]} (n={n})", loc="left",
                     color=fg.INK, fontsize=9.5)
        ax.set_xticks(range(len(etiquetas_roi)))
        ax.set_yticks(range(len(etiquetas_roi)))
        ax.set_xticklabels(etiquetas_roi, rotation=90, fontsize=5.5)
        ax.set_yticklabels(etiquetas_roi if ax is axes[0] else [], fontsize=5.5)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
    cb = fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02)
    cb.set_label("correlación entre ROIs", color=fg.INK_2, fontsize=8)
    cb.outline.set_visible(False)
    fig.suptitle(f"Covarianza estructural de la red DCNN · {medida}",
                 x=0.01, ha="left", color=fg.INK, fontsize=11)
    figs.append((fg.guardar(fig, FIGS / f"matrices_{medida}"),
                 f"Matrices de covarianza · {medida}", ""))

# resumen: covarianza media por grupo y medida
fig, ax = fg.barras_comparadas(
    MEDIDAS,
    {fg.ETIQUETA_GRUPO[g]: [float(tabla_grupos[(tabla_grupos.medida == med)
                                               & (tabla_grupos.grupo == g)].r_medio.iloc[0])
                            for med in MEDIDAS] for g in cfg.GRUPOS},
    titulo="Covarianza estructural media de la red DCNN",
    subtitulo="correlación media entre las 14 ROIs de prioridad alta, por grupo",
    ylabel="r medio entre ROIs")
ruta_barras = fg.guardar(fig, FIGS / "covarianza_media_por_grupo")

# %% ── al documento ─────────────────────────────────────────────────────────
with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion("Etapa C2 · Covarianza estructural de la red",
            "¿Están las regiones de la red DCNN organizadas de la misma manera en cada grupo?")
doc.chips({"ROIs": 14, "Aristas por matriz": 91, "Medidas": 4,
           "Permutaciones": "2.000", "Contraste": "MPPP vs Vestibular"})
doc.texto(
    "Pregunta distinta de las anteriores: no si las regiones son más grandes o más pequeñas, "
    "sino si <b>covarían entre sí</b> de la misma forma. Dos grupos pueden tener ROIs de "
    "idéntico tamaño y diferir en la coordinación de la red. Se residualiza <b>dentro</b> de "
    "cada grupo para no inducir covarianza espuria por las diferencias de medias."
)
doc.nota(
    "<b>Limitación estructural:</b> una matriz de correlación de 14 variables estimada con "
    "n=10 es muy inestable — el grupo sano se muestra pero <b>no se contrasta formalmente</b>. "
    "El único contraste interpretable aquí es MPPP vs Vestibular (17 vs 19).",
    alerta=True,
)
doc.h3("Covarianza media por grupo")
doc.tabla(tabla_grupos.round(3))
doc.figura(ruta_barras, "Covarianza media de la red por grupo", "")
doc.h3("Contraste MPPP vs Vestibular")
doc.texto("<code>similaridad_estructura</code> = correlación entre los vectores de 91 aristas "
          "de ambos grupos: mide si el <i>patrón</i> de la red es el mismo, "
          "con independencia de su intensidad media. "
          "Las 4 pruebas (una por medida) llevan su propio FDR.")
doc.tabla(contraste.round(4), destacar="sobrevive_fdr")
doc.nota(
    "<b>El único contraste con p nominal &lt; 0,05 es el de ÁREA</b> (p = 0,018): la "
    "covarianza entre las áreas de la red es prácticamente nula en MPPP (r = −0,02) "
    "y moderada en Vestibular (r = 0,22). <b>No sobrevive al FDR de las 4 medidas</b> "
    f"(p_FDR = {float(contraste.loc[contraste.medida == 'area', 'p_fdr'].iloc[0]):.3f}), "
    "y no había hipótesis previa sobre covarianza de área. "
    "Lo trataría como <b>exploratorio y frágil</b>: con n=17 vs 19, una matriz de 91 aristas "
    "se estima con mucho ruido. Es una observación para replicar, no un resultado.",
    alerta=True,
)
doc.h3("Matrices")
doc.galeria(figs)

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print("\n→ documento actualizado")
