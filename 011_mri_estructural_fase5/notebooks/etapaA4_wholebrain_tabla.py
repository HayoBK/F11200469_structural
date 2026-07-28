"""
ETAPA A4 — Whole-brain masa-univariante sobre la tabla ("pesca milagrosa").

Barre TODAS las regiones de los tres atlas corticales y el aseg subcortical, sin
hipótesis previa. Es explícitamente exploratorio y así se reporta.

FDR **dentro de cada (atlas × medida)**, nunca sobre el total: los tres atlas son
tres parcelaciones del mismo manto cortical y sus columnas están fuertemente
correlacionadas (`06_ESPECIFICACION_TABLA_MAESTRA.md` §5.4). Corregir sobre las
2.530 columnas a la vez sería estadísticamente incorrecto además de brutal.

Se usa menos remuestreo que en las etapas confirmatorias (2.000 permutaciones,
1.000 bootstraps): con ~2.500 pruebas el coste se multiplica, y aquí no se busca
precisión en el IC de una ROI concreta sino un panorama.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaA4_wholebrain_tabla.py
"""

# %% ── setup ────────────────────────────────────────────────────────────────
import pickle
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

import config as cfg
import figuras as fg
import multiplicidad as mult
import pipeline as pl

fg.aplicar_estilo()
FIGS = cfg.FIGS / "etapaA4"
FIGS.mkdir(parents=True, exist_ok=True)

m = cfg.cargar_master()
dic = cfg.cargar_diccionario()

# %% ── plan: todas las ROIs corticales de los 3 atlas + aseg ────────────────
GLOBALES = ("MeanThickness", "WhiteSurfArea")   # no son ROIs (spec §5.3)
filas = []
for c in m.columns:
    mt = re.match(r"^ctx_(DK|DKT|DS)_(thickness|area|volume)_(lh|rh)_(.+)$", c)
    ml = re.match(r"^lgi_(DK|DKT|DS)_(lh|rh)_(.+)$", c)
    if mt and not mt.group(4).endswith(GLOBALES):
        atlas, medida, hemi, region = mt.groups()
    elif ml:
        atlas, hemi, region = ml.groups()
        medida = "LGI"
    else:
        continue
    filas.append({"variable": c, "etapa": "A4", "atlas": atlas, "medida": medida,
                  "hemi": hemi, "roi": region, "tipo": "C",
                  "familia_fdr": f"{atlas}_{medida}",
                  "ajusta_etiv": medida in ("volume", "area")})

# subcorticales del aseg (solo volumen), excluyendo globales y ventrículos
EXCLUIR = ("Vent", "CSF", "WM_hypo", "non_WM", "Optic", "vessel", "undetermined",
           "BrainSeg", "Cortex", "eTIV", "SurfaceHoles")
for c in m.columns:
    if c.startswith("aseg_") and not any(x in c for x in EXCLUIR):
        filas.append({"variable": c, "etapa": "A4", "atlas": "aseg", "medida": "volume",
                      "hemi": "lh" if "Left" in c else ("rh" if "Right" in c else "bilat"),
                      "roi": c.replace("aseg_", ""), "tipo": "S",
                      "familia_fdr": "aseg_volume", "ajusta_etiv": True})

plan = pd.DataFrame(filas)

# En un barrido masivo aparecen columnas sin varianza útil (estructuras del aseg
# que valen lo mismo en todos los sujetos, o casi). No aportan nada y rompen el
# modelo, así que se excluyen explícitamente y se declara cuántas fueron.
sd = m[plan.variable.tolist()].std(ddof=1)
media = m[plan.variable.tolist()].mean().abs()
# coeficiente de variación: detecta tanto varianza nula como despreciable
cv = (sd / media.where(media > 0)).fillna(0.0)
sin_varianza = [v for v in plan.variable if sd[v] <= 0 or cv[v] < 1e-6]
if sin_varianza:
    print(f"⚠️ excluidas {len(sin_varianza)} variables sin varianza útil: "
          f"{sin_varianza[:5]}{'…' if len(sin_varianza) > 5 else ''}")
    plan = plan[~plan.variable.isin(sin_varianza)].reset_index(drop=True)

print(f"A4 · {len(plan)} pruebas por diseño")
print(plan.familia_fdr.value_counts().to_string())

# %% ── correr los dos diseños ───────────────────────────────────────────────
N_PERM, N_BOOT = 2_000, 1_000

print(f"\n▸ Tres grupos (N=46) · {len(plan)} pruebas")
t0 = time.time()
A4 = pl.correr_bloque(m, plan, pl.COVAR_BASE, "A4_tres_grupos",
                      n_perm=N_PERM, n_boot=N_BOOT)
print(f"   {time.time()-t0:.0f}s")

pacientes = m[m["Grupo"].isin(["MPPP", "Vestibular"])].copy()
print(f"\n▸ Dirigido MPPP vs Vestibular (n={len(pacientes)})")
t0 = time.time()
A4d = pl.correr_bloque(pacientes, plan, pl.COVAR_BASE, "A4_dirigido",
                       contrastes=[("MPPP", "Vestibular")], referencia="Vestibular",
                       n_perm=N_PERM, n_boot=N_BOOT)
print(f"   {time.time()-t0:.0f}s")

pd.concat([A4, A4d], ignore_index=True).to_csv(
    cfg.RESULTS / "etapaA4_resultados_wholebrain.csv", index=False)

# %% ── lectura ──────────────────────────────────────────────────────────────
for nombre, t in [("TRES GRUPOS", A4), ("DIRIGIDO MPPP vs VESTIBULAR", A4d)]:
    res = mult.resumen_familias(t, familia=["etapa", "familia_fdr"])
    print(f"\n=== {nombre} · resumen por familia ===")
    print(res.to_string(index=False))
    print(f"→ sobreviven al FDR: {int(t.sobrevive_fdr.sum())} de {len(t)}")
    s = t[t.sobrevive_fdr]
    if len(s):
        print(s.sort_values("p_perm")[["atlas", "roi", "hemi", "medida", "n", "eta2p",
                                       "p_perm", "p_fdr", "MPPP_vs_Vestibular_d"]]
              .head(20).round(4).to_string(index=False))

resumen_3g = mult.resumen_familias(A4, familia=["etapa", "familia_fdr"])
resumen_dir = mult.resumen_familias(A4d, familia=["etapa", "familia_fdr"])

# ¿en qué medida se concentran las señales, con independencia del atlas?
por_medida = (A4d.groupby("medida")
              .agg(pruebas=("p_perm", "size"),
                   p005=("p_perm", lambda x: int((x < 0.05).sum())),
                   sobreviven=("sobrevive_fdr", "sum"))
              .reset_index())
por_medida["esperado_azar"] = (por_medida.pruebas * 0.05).round(1)
print("\n=== CONCENTRACIÓN POR MEDIDA (diseño dirigido) ===")
print(por_medida.to_string(index=False))
por_medida.to_csv(cfg.RESULTS / "etapaA4_por_medida_resultados.csv", index=False)

# %% ── figuras ──────────────────────────────────────────────────────────────
A4d["etiqueta_corta"] = (A4d["roi"].str.slice(0, 16) + " " + A4d["hemi"])
fig, _ = fg.volcan(A4d, "MPPP_vs_Vestibular_d", "p_perm", "etiqueta_corta",
                   col_destaca="sobrevive_fdr",
                   titulo=f"A4 · barrido whole-brain · {len(A4d)} pruebas",
                   subtitulo="contraste dirigido MPPP vs Vestibular · exploratorio",
                   n_etiquetas=10)
ruta_volcan = fg.guardar(fig, FIGS / "volcan_A4_dirigido")

fig, ax = fg.barras_comparadas(
    list(por_medida.medida),
    {"observadas (p<0,05)": list(por_medida.p005),
     "esperadas por azar": list(por_medida.esperado_azar)},
    titulo="¿Dónde hay más señal de la esperable por azar?",
    subtitulo="barrido whole-brain, contraste dirigido",
    ylabel="n pruebas", colores=["#eb6834", "#898781"])
ruta_barras = fg.guardar(fig, FIGS / "senal_vs_azar_por_medida")

# %% ── al documento ─────────────────────────────────────────────────────────
with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion("Etapa A4 · Barrido whole-brain sobre la tabla (exploratorio)",
            "Todas las regiones de los tres atlas, sin hipótesis previa.")
doc.chips({"Pruebas por diseño": len(plan), "Atlas": "DK · DKT · DS · aseg",
           "FDR": "dentro de cada atlas × medida",
           "Sobreviven (3 grupos)": int(A4.sobrevive_fdr.sum()),
           "Sobreviven (dirigido)": int(A4d.sobrevive_fdr.sum())})
doc.texto(
    "Explícitamente exploratorio. La corrección se aplica <b>dentro de cada atlas × medida</b> "
    "y nunca sobre el total: los tres atlas son tres parcelaciones del mismo manto cortical y "
    "sus columnas están fuertemente correlacionadas, de modo que corregir sobre las 2.530 a la "
    "vez sería incorrecto además de brutal. Se usa menos remuestreo que en las etapas "
    "confirmatorias (2.000 permutaciones) porque aquí se busca un panorama, no precisión en el "
    "IC de una ROI concreta."
)
doc.h3("Resumen por familia · tres grupos")
doc.tabla(resumen_3g)
doc.h3("Resumen por familia · dirigido")
doc.tabla(resumen_dir)
doc.h3("Dónde se concentra la señal")
doc.tabla(por_medida)
doc.figura(ruta_barras, "Señal observada frente a la esperable por azar", "")
doc.figura(ruta_volcan, "Volcán del barrido completo", "")
if int(A4d.sobrevive_fdr.sum()):
    doc.h3("Lo que sobrevive (dirigido)")
    doc.tabla(A4d[A4d.sobrevive_fdr].sort_values("p_perm")[
        ["atlas", "roi", "hemi", "medida", "n", "eta2p", "p_perm", "p_fdr",
         "MPPP_vs_Vestibular_d"]].round(4))

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print("\n→ documento actualizado")
