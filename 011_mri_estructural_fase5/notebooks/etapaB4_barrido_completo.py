"""
ETAPA B4 — Completar el barrido estructura ↔ conducta/clínica.

La etapa B cubrió los índices de red y las ROIs de prioridad ALTA. Aquí se cierra
el hueco: **ROIs de prioridad MEDIA y subestructuras** (subcampos hipocampales,
núcleos talámicos y amigdalinos), contra los cuatro outcomes de interés, en los
dos ejes que pide la hipótesis:

  · **Navegación espacial** — CSE y Entropy-Ratio, marcadores de disfunción de
    navegación alocéntrica. Se analizan en la muestra completa (N=46), con Grupo
    como covariable.
  · **Severidad de enfermedad** — Niigata y DHI. Solo dentro de pacientes
    (MPPP + Vestibular, n≈31): en un voluntario sano el puntaje es piso, no
    información.

FDR por familia = (medida × outcome), como en el resto del proyecto.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaB4_barrido_completo.py
"""

# %% ── setup ────────────────────────────────────────────────────────────────
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

import config as cfg
import correlaciones as co
import figuras as fg
import multiplicidad as mult
import rois

fg.aplicar_estilo()
FIGS = cfg.FIGS / "etapaB4"
FIGS.mkdir(parents=True, exist_ok=True)

m = cfg.cargar_master()
X = pd.concat([rois.construir_matriz(m, "alta"), rois.construir_matriz(m, "media")], axis=1)
datos = pd.concat([m.drop(columns=[c for c in X.columns if c in m.columns]), X], axis=1)

plan_alta = rois.plan_de_pruebas("alta")
plan_media = rois.plan_de_pruebas("media")

# subestructuras (mismo plan que la etapa A3)
BLOQUES = [("hipocampo_posterior", "hipp", rois.SUBCAMPOS_HIPOCAMPO_POSTERIOR),
           ("talamo_anterior", "thal", rois.NUCLEOS_TALAMO_ANTERIOR),
           ("amigdala", "amyg", rois.NUCLEOS_AMIGDALA)]
filas = []
for familia, pref, estructuras in BLOQUES:
    for est in estructuras:
        for hemi in ("lh", "rh"):
            filas.append({"variable": f"{pref}_{hemi}_{est}", "roi": est.replace("_", " "),
                          "hemi": hemi, "medida": "volume", "ajusta_etiv": True,
                          "bloque": familia})
plan_sub = pd.DataFrame(filas)

NAV = ["CSE_NI", "EntropyRatio_NI"]        # disfunción de navegación espacial
SEV = ["Niigata", "DHI"]                   # severidad de enfermedad
COVAR = ["Edad", "Genero", "Grupo"]
COVAR_TIV = COVAR + ["eTIV"]
GRUPOS = ["MPPP", "Vestibular", "Voluntario Sano"]
pacientes = datos[datos["Grupo"].isin(["MPPP", "Vestibular"])].copy()

# %% ── B4a · navegación, muestra completa ───────────────────────────────────
t0 = time.time()
plan_nuevo = pd.concat([plan_media[["variable", "roi", "hemi", "medida", "ajusta_etiv"]],
                        plan_sub[["variable", "roi", "hemi", "medida", "ajusta_etiv"]]],
                       ignore_index=True)
print(f"▸ B4a · navegación (N=46) · {len(plan_nuevo)} variables × {len(NAV)} outcomes")
B4a = co.barrido(datos, plan_nuevo, NAV, COVAR, covariables_etiv=COVAR_TIV,
                 grupos=GRUPOS, n_boot=1_500)
B4a = mult.aplicar_fdr(B4a, col_p="p", familia=["etapa", "familia_fdr"])
B4a = co.coherencia_simpson(B4a, GRUPOS)
print(f"   {len(B4a)} pruebas en {time.time()-t0:.0f}s · "
      f"sobreviven: {int(B4a.sobrevive_fdr.sum())}")

# %% ── B4b · severidad, dentro de pacientes ─────────────────────────────────
t0 = time.time()
plan_todo = pd.concat([plan_alta[["variable", "roi", "hemi", "medida", "ajusta_etiv"]],
                       plan_nuevo], ignore_index=True)
print(f"\n▸ B4b · severidad (n={len(pacientes)}) · {len(plan_todo)} variables × {len(SEV)}")
B4b = co.barrido(pacientes, plan_todo, SEV, COVAR, covariables_etiv=COVAR_TIV,
                 grupos=["MPPP", "Vestibular"], n_boot=1_500)
B4b = mult.aplicar_fdr(B4b, col_p="p", familia=["etapa", "familia_fdr"])
B4b = co.coherencia_simpson(B4b, ["MPPP", "Vestibular"])
print(f"   {len(B4b)} pruebas en {time.time()-t0:.0f}s · "
      f"sobreviven: {int(B4b.sobrevive_fdr.sum())}")

# %% ── B4c · navegación dentro de pacientes ─────────────────────────────────
t0 = time.time()
print(f"\n▸ B4c · navegación dentro de pacientes (n={len(pacientes)})")
B4c = co.barrido(pacientes, plan_todo, NAV, COVAR, covariables_etiv=COVAR_TIV,
                 grupos=["MPPP", "Vestibular"], n_boot=1_500)
B4c = mult.aplicar_fdr(B4c, col_p="p", familia=["etapa", "familia_fdr"])
B4c = co.coherencia_simpson(B4c, ["MPPP", "Vestibular"])
print(f"   {len(B4c)} pruebas en {time.time()-t0:.0f}s · "
      f"sobreviven: {int(B4c.sobrevive_fdr.sum())}")

for nombre, t in [("B4a_navegacion_global", B4a), ("B4b_severidad_pacientes", B4b),
                  ("B4c_navegacion_pacientes", B4c)]:
    t.to_csv(cfg.RESULTS / f"etapa{nombre}_resultados_correlaciones.csv", index=False)

# %% ── lectura ──────────────────────────────────────────────────────────────
VISTA = ["roi", "hemi", "medida", "outcome", "n", "rho", "ic_low", "ic_high",
         "p", "p_fdr", "sobrevive_fdr", "coherente"]
for nombre, t in [("B4a · NAVEGACIÓN, muestra completa", B4a),
                  ("B4b · SEVERIDAD, dentro de pacientes", B4b),
                  ("B4c · NAVEGACIÓN, dentro de pacientes", B4c)]:
    print("\n" + "=" * 92)
    print(f"{nombre} — 12 correlaciones más fuertes")
    print("=" * 92)
    print(t.sort_values("p")[VISTA].head(12).round(4).to_string(index=False))
    s = t[t.sobrevive_fdr]
    print(f"→ sobreviven al FDR: {len(s)} de {len(t)}")

# ¿en qué medida se concentran los hallazgos?
todo = pd.concat([B4a, B4b, B4c], ignore_index=True)
por_medida = (todo.groupby(["medida"])
              .agg(pruebas=("rho", "size"), p005=("p", lambda x: int((x < 0.05).sum())),
                   sobreviven=("sobrevive_fdr", "sum"),
                   rho_abs_max=("rho", lambda x: x.abs().max()))
              .reset_index())
print("\n=== CONCENTRACIÓN POR MEDIDA (las tres etapas B4 juntas) ===")
print(por_medida.round(3).to_string(index=False))
por_medida.to_csv(cfg.RESULTS / "etapaB4_por_medida_resultados.csv", index=False)

incoh = todo[(todo.p < 0.05) & (~todo.coherente)]
print(f"\n⚠️  con p<0,05 y signo incoherente con el intra-grupo: "
      f"{len(incoh)} de {int((todo.p < 0.05).sum())}")

# %% ── figuras ──────────────────────────────────────────────────────────────
figs = []
for f in pd.concat([B4a, B4b, B4c]).sort_values("p").head(6).itertuples():
    base = pacientes if f.n <= 36 else datos
    fig, _ = fg.scatter_estructura_conducta(
        base, f.variable, f.outcome,
        titulo=f"{f.roi} {f.hemi} · {f.medida} — {f.outcome}",
        subtitulo=(f"rho parcial = {f.rho:.3f} [{f.ic_low:.2f}, {f.ic_high:.2f}] · "
                   f"p={f.p:.4f} · p(FDR)={float(f.p_fdr):.3f} · N={f.n}"),
        xlabel=f"{f.medida} · {f.roi}", ylabel=f.outcome)
    figs.append((fg.guardar(fig, FIGS / f"scatter_{f.variable}_{f.outcome}"),
                 f"{f.roi} ↔ {f.outcome}", ""))

# heatmap severidad × subestructuras
sub_sev = B4b[B4b.variable.str.startswith(("hipp_", "thal_", "amyg_"))].copy()
if not sub_sev.empty:
    sub_sev["fila"] = sub_sev["roi"] + "  " + sub_sev["hemi"]
    piv = sub_sev.pivot_table(index="fila", columns="outcome", values="rho")
    marcas = sub_sev.pivot_table(index="fila", columns="outcome", values="sobrevive_fdr",
                                 aggfunc="max").reindex(index=piv.index, columns=piv.columns)
    fig, _ = fg.heatmap_efectos(
        piv, titulo="Subestructuras y severidad de enfermedad",
        subtitulo="rho de Spearman parcial dentro de pacientes · • = sobrevive al FDR",
        cbar_label="rho parcial", marcas=marcas)
    ruta_sub = fg.guardar(fig, FIGS / "heatmap_subestructuras_severidad")
else:
    ruta_sub = None

# %% ── al documento ─────────────────────────────────────────────────────────
with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion("Etapa B4 · Barrido completo estructura ↔ navegación y severidad",
            "Cierra el hueco: ROIs de prioridad media y subestructuras, contra los "
            "cuatro outcomes.")
doc.chips({"B4a navegación (N=46)": len(B4a), "B4b severidad (n≈31)": len(B4b),
           "B4c navegación en pacientes": len(B4c),
           "Sobreviven FDR": int(B4a.sobrevive_fdr.sum() + B4b.sobrevive_fdr.sum()
                                 + B4c.sobrevive_fdr.sum())})
doc.texto(
    "Dos ejes distintos y deliberadamente separados: <b>CSE y Entropy-Ratio</b> como marcadores "
    "de disfunción de navegación espacial alocéntrica, y <b>Niigata y DHI</b> como marcadores "
    "de severidad de enfermedad. La severidad solo se analiza dentro de pacientes; en un "
    "voluntario sano el puntaje es piso, no información."
)
doc.h3("Dónde se concentran los hallazgos")
doc.tabla(por_medida.round(3))
doc.h3("B4a · Navegación, muestra completa")
doc.tabla(B4a.sort_values("p")[VISTA].head(25).round(4), destacar="sobrevive_fdr")
doc.h3("B4b · Severidad, dentro de pacientes")
doc.tabla(B4b.sort_values("p")[VISTA].head(25).round(4), destacar="sobrevive_fdr")
doc.h3("B4c · Navegación, dentro de pacientes")
doc.tabla(B4c.sort_values("p")[VISTA].head(25).round(4), destacar="sobrevive_fdr")
if ruta_sub:
    doc.figura(ruta_sub, "Subestructuras y severidad", "")
doc.galeria(figs)

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print("\n→ documento actualizado")
