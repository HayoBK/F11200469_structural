"""
ETAPA A1 — Comparación de los tres grupos clínicos en las ROIs a-priori de
PRIORIDAD ALTA (confirmatorio primario de la hipótesis DCNN).

58 pruebas = 7 ROIs corticales × 2 hemisferios × 4 medidas + hipocampo × 2 hemisferios.
FDR de Benjamini-Hochberg **dentro de cada familia de medida** (14/14/16/14).

Se corren DOS modelos completos en paralelo (decisión D5 del PI):
  · Modelo A (N=46): Grupo + Edad + Genero + N_Educacional [+ eTIV en volumen y área]
  · Modelo B (N≈34): idéntico + STAI-Rasgo + BDI

Cada uno con su propio FDR. Correr la familia completa en ambos —en vez de
re-testear solo los supervivientes de A— evita condicionar el segundo análisis
al resultado del primero.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaA1_roi_alta.py
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
import figuras as fg
import modelos
import multiplicidad as mult
import rois

fg.aplicar_estilo()
FIGS = cfg.FIGS / "etapaA1"
FIGS.mkdir(parents=True, exist_ok=True)

N_PERM, N_BOOT = 10_000, 5_000
COVAR_A = ["Edad", "Genero", "N_Educacional"]           # D1: sin lateralidad
COVAR_B = COVAR_A + ["STAI_Rasgo", "BDI"]               # D5: modelo paralelo

m = cfg.cargar_master()
plan = rois.plan_de_pruebas("alta")
X = rois.construir_matriz(m, "alta")
datos = pd.concat([m.drop(columns=[c for c in X.columns if c in m.columns]), X], axis=1)
print(f"A1 · {len(plan)} pruebas · familias FDR: {plan.familia_fdr.value_counts().to_dict()}")


# %% ── ajuste de los dos modelos ────────────────────────────────────────────
def correr(covariables: list[str], etiqueta: str) -> pd.DataFrame:
    t0 = time.time()
    filas = []
    for i, f in enumerate(plan.itertuples(), 1):
        r = modelos.ancova(
            datos, f.variable, covariables, ajusta_etiv=f.ajusta_etiv,
            n_perm=N_PERM, n_boot=N_BOOT, seed=modelos.SEED + i,
        )
        fila = r.fila()
        fila.update({"etapa": f.etapa, "roi": f.roi, "medida": f.medida, "hemi": f.hemi,
                     "familia_fdr": f.familia_fdr, "atlas": f.atlas, "tipo": f.tipo,
                     "modelo": etiqueta, "ajusta_etiv": f.ajusta_etiv})
        filas.append(fila)
        if i % 15 == 0:
            print(f"   [{etiqueta}] {i}/{len(plan)}  ({time.time()-t0:.0f}s)")
    t = pd.DataFrame(filas)
    t = mult.aplicar_fdr(t, col_p="p_perm", familia=["etapa", "familia_fdr"])
    print(f"   [{etiqueta}] listo en {time.time()-t0:.0f}s")
    return t


print("\n▸ Modelo A (N=46, sin ansiedad/depresión)")
A = correr(COVAR_A, "A_sin_ansiedad")
print("\n▸ Modelo B (N≈34, con STAI-Rasgo y BDI)")
B = correr(COVAR_B, "B_con_ansiedad")

resultados = pd.concat([A, B], ignore_index=True)
resultados.to_csv(cfg.RESULTS / "etapaA1_resultados_ancova.csv", index=False)

# %% ── lectura de los resultados ────────────────────────────────────────────
print("\n" + "=" * 78)
print("RESUMEN POR FAMILIA — Modelo A")
print("=" * 78)
resumen_A = mult.resumen_familias(A, familia=["etapa", "familia_fdr"])
print(resumen_A.to_string(index=False))
resumen_B = mult.resumen_familias(B, familia=["etapa", "familia_fdr"])
print("\nModelo B")
print(resumen_B.to_string(index=False))

COLS_VISTA = ["roi", "hemi", "medida", "n", "F", "eta2p", "eta2p_ic_low", "eta2p_ic_high",
              "p_param", "p_perm", "p_fdr", "p_kw",
              "MPPP_vs_VoluntarioSano_d", "MPPP_vs_VoluntarioSano_d_ic_low",
              "MPPP_vs_VoluntarioSano_d_ic_high", "MPPP_vs_Vestibular_d",
              "sobrevive_fdr"]

A_orden = A.sort_values("p_perm")
print("\n=== MODELO A · 12 pruebas con menor p de permutación ===")
print(A_orden[["roi", "hemi", "medida", "n", "eta2p", "p_perm", "p_fdr",
               "MPPP_vs_VoluntarioSano_d", "MPPP_vs_Vestibular_d",
               "sobrevive_fdr"]].head(12).round(4).to_string(index=False))

sobreviven = A[A.sobrevive_fdr]
print(f"\n→ sobreviven al FDR (modelo A): {len(sobreviven)} de {len(A)}")
if len(sobreviven):
    print(sobreviven[["roi", "hemi", "medida", "eta2p", "p_perm", "p_fdr",
                      "MPPP_vs_VoluntarioSano_d"]].round(4).to_string(index=False))

# %% ── enriquecimiento de cada familia ──────────────────────────────────────
# Pregunta distinta de la del FDR: ¿hay más señal en la familia entera de la que
# habría por azar, aunque ninguna ROI individual aguante la corrección?
print("\n=== ENRIQUECIMIENTO POR FAMILIA (permutación a nivel de familia) ===")
enr = []
for medida in ["LGI", "thickness", "volume", "area"]:
    vars_fam = plan.loc[plan.medida == medida, "variable"].tolist()
    r = mult.enriquecimiento_familia(
        datos, vars_fam, COVAR_A, ajusta_etiv=(medida in ("volume", "area")),
        n_perm=2_000,
    )
    r["familia"] = medida
    enr.append(r)
enriquecimiento = pd.DataFrame(enr)[
    ["familia", "n_pruebas", "n_efectivo", "n_observado_p<0.05",
     "esperado_por_azar", "p_enriquecimiento"]
]
print(enriquecimiento.round(4).to_string(index=False))
enriquecimiento.to_csv(cfg.RESULTS / "etapaA1_enriquecimiento_resultados.csv", index=False)

# dirección del efecto dentro de la familia LGI
lgi = A[A.medida == "LGI"]
print(f"\nLGI · d(MPPP−Vestibular): mediana {lgi['MPPP_vs_Vestibular_d'].median():.3f}, "
      f"{int((lgi['MPPP_vs_Vestibular_d'] < 0).sum())}/{len(lgi)} negativas")
print(f"LGI · d(MPPP−Sano):       mediana {lgi['MPPP_vs_VoluntarioSano_d'].median():.3f}, "
      f"{int((lgi['MPPP_vs_VoluntarioSano_d'] < 0).sum())}/{len(lgi)} negativas")

# %% ── FIGURAS ──────────────────────────────────────────────────────────────
figs_forest, figs_heat = [], []

for medida in ["LGI", "thickness", "volume", "area"]:
    sub = A[A.medida == medida].copy()
    if sub.empty:
        continue
    sub["etiqueta"] = sub["roi"] + "  " + sub["hemi"]
    sub = sub.sort_values("MPPP_vs_VoluntarioSano_d")
    fig, ax = fg.forest(
        sub, "MPPP_vs_VoluntarioSano_d",
        "MPPP_vs_VoluntarioSano_d_ic_low", "MPPP_vs_VoluntarioSano_d_ic_high",
        "etiqueta", col_destaca="sobrevive_fdr",
        titulo=f"MPPP vs Sano · {medida}",
        subtitulo=f"d ajustada con IC 95% BCa · familia FDR de {len(sub)} pruebas · "
                  f"N={int(sub['n'].iloc[0])}",
    )
    figs_forest.append((fg.guardar(fig, FIGS / f"forest_{medida}_MPPP_vs_Sano"),
                        f"Forest · {medida} · MPPP vs Sano", ""))

    fig, ax = fg.forest(
        sub.sort_values("MPPP_vs_Vestibular_d"), "MPPP_vs_Vestibular_d",
        "MPPP_vs_Vestibular_d_ic_low", "MPPP_vs_Vestibular_d_ic_high",
        "etiqueta", col_destaca="sobrevive_fdr",
        titulo=f"MPPP vs Vestibular · {medida}",
        subtitulo=f"d ajustada con IC 95% BCa · N={int(sub['n'].iloc[0])}",
    )
    figs_forest.append((fg.guardar(fig, FIGS / f"forest_{medida}_MPPP_vs_Vest"),
                        f"Forest · {medida} · MPPP vs Vestibular", ""))

# heatmap ROI × medida (d de MPPP vs Sano)
A["fila"] = A["roi"] + "  " + A["hemi"]
piv = A.pivot_table(index="fila", columns="medida", values="MPPP_vs_VoluntarioSano_d")
marcas = A.pivot_table(index="fila", columns="medida", values="sobrevive_fdr",
                       aggfunc="max").reindex(index=piv.index, columns=piv.columns).fillna(0)
fig, ax = fg.heatmap_efectos(
    piv, titulo="Tamaño de efecto MPPP vs Sano en las ROIs de prioridad alta",
    subtitulo="d de Cohen ajustada · rojo = mayor en MPPP · • = sobrevive al FDR de su familia",
    marcas=marcas,
)
ruta_heat = fg.guardar(fig, FIGS / "heatmap_d_MPPP_vs_Sano")

# volcán
A["etiqueta_corta"] = A["roi"].str.slice(0, 14) + " " + A["hemi"] + " " + A["medida"].str.slice(0, 4)
fig, ax = fg.volcan(A, "MPPP_vs_VoluntarioSano_d", "p_perm", "etiqueta_corta",
                    col_destaca="sobrevive_fdr",
                    titulo="Las 58 pruebas de A1 · efecto vs evidencia",
                    subtitulo="p de permutación (Freedman-Lane) · modelo A, N=46")
ruta_volcan = fg.guardar(fig, FIGS / "volcan_A1")

# violines de las ROIs con menor p
figs_violin = []
for f in A_orden.head(6).itertuples():
    var = f.variable
    fig, ax = fg.violin_por_grupo(
        datos, var,
        titulo=f"{f.roi} · {f.hemi} · {f.medida}",
        subtitulo=(f"η²p={f.eta2p:.3f} · p(perm)={f.p_perm:.4f} · "
                   f"p(FDR)={float(f.p_fdr):.3f} · N={f.n}"),
        ylabel=f.medida,
    )
    figs_violin.append((fg.guardar(fig, FIGS / f"violin_{var}"),
                        f"{f.roi} {f.hemi} · {f.medida}", ""))

# comparación de efectos entre modelos A y B
comp = A.merge(B, on=["roi", "hemi", "medida"], suffixes=("_A", "_B"))
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(4.4, 4.2))
for medida, color in zip(["LGI", "thickness", "volume", "area"],
                         ["#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"]):
    s = comp[comp.medida == medida]
    ax.scatter(s["MPPP_vs_VoluntarioSano_d_A"], s["MPPP_vs_VoluntarioSano_d_B"],
               s=32, color=color, alpha=0.85, linewidth=0.6, edgecolor=fg.SURFACE,
               label=medida)
lims = [min(ax.get_xlim()[0], ax.get_ylim()[0]), max(ax.get_xlim()[1], ax.get_ylim()[1])]
ax.plot(lims, lims, color=fg.BASELINE, linewidth=1, zorder=0)
ax.axhline(0, color=fg.GRID, linewidth=0.8, zorder=0)
ax.axvline(0, color=fg.GRID, linewidth=0.8, zorder=0)
ax.set_xlabel("d · modelo A (N=46, sin ansiedad)")
ax.set_ylabel("d · modelo B (N≈34, con STAI-R y BDI)")
ax.set_title("¿Cambian los efectos al controlar ansiedad?", loc="left", color=fg.INK, pad=12)
ax.text(0, 1.015, "cada punto es una prueba · la diagonal = sin cambio",
        transform=ax.transAxes, fontsize=8, color=fg.MUTED, va="bottom")
ax.legend()
ax.grid(alpha=0.5)
ax.set_axisbelow(True)
ruta_comp = fg.guardar(fig, FIGS / "comparacion_modelos_A_B")

# %% ── AL DOCUMENTO ─────────────────────────────────────────────────────────
with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion(
    "Etapa A1 · ROIs a-priori de prioridad ALTA (confirmatorio primario)",
    "¿Difieren los tres grupos clínicos en las 8 regiones núcleo de la hipótesis DCNN?",
)
doc.chips({
    "Pruebas": len(plan), "Familias FDR": "4 (una por medida)",
    "Modelo A": "N=46", "Modelo B": "N≈34 (con ansiedad)",
    "Permutaciones": f"{N_PERM:,}", "Bootstrap": f"{N_BOOT:,}",
})
doc.texto(
    "Cada prueba es una ANCOVA de 3 grupos sobre (ROI × hemisferio × medida), ajustada por "
    "edad, sexo y nivel educacional, más eTIV en volumen y área. El p reportado es el de "
    "<b>permutación (Freedman-Lane, 10.000)</b>, que no depende del supuesto de normalidad; "
    "el paramétrico y el robusto HC3 quedan en la tabla para comparación. "
    "La corrección FDR de Benjamini-Hochberg se aplica <b>dentro de cada familia de medida</b>."
)

doc.h3("Cuántas pruebas sobreviven, por familia")
doc.tabla(resumen_A)
doc.texto("<b>Modelo B</b> (mismas pruebas, ajustando además por STAI-Rasgo y BDI):")
doc.tabla(resumen_B)

n_sobrevive = int(A.sobrevive_fdr.sum())
doc.nota(
    f"<b>Ninguna de las {len(A)} pruebas sobrevive al FDR de su familia</b> "
    f"({n_sobrevive}/{len(A)}). Es el resultado, y hay que leerlo tal cual: con "
    "n=10 sanos el estudio está subpotenciado para efectos moderados, y la corrección "
    "dentro de familias de 14–16 pruebas es exigente. Lo que sigue no son hallazgos "
    "confirmados sino <b>generadores de hipótesis</b>, sostenidos por el tamaño de "
    "efecto y por su coherencia interna.",
    alerta=True,
)

doc.h3("¿Está alguna familia enriquecida en su conjunto?")
doc.texto(
    "Pregunta distinta de la del FDR. El FDR pregunta <i>qué ROI concreta puedo declarar</i>; "
    "esto pregunta <i>si hay más señal en la familia entera de la esperable por azar</i>. "
    "El nulo permuta la etiqueta de grupo una vez por remuestreo y la aplica a todas las "
    "variables a la vez, de modo que preserva la correlación entre ROIs y hemisferios "
    "(un test binomial sobre los p asumiría independencia y sería anticonservador)."
)
doc.tabla(enriquecimiento.round(4))

doc.h3("Resultados completos · modelo A")
doc.tabla(A_orden[COLS_VISTA].round(4), destacar="sobrevive_fdr")

doc.h3("Tamaños de efecto")
doc.figura(ruta_heat, "Mapa de efectos ROI × medida",
           "Rojo = estructura mayor en MPPP; azul = menor. El punto marca las pruebas que "
           "sobreviven al FDR de su propia familia.")
doc.figura(ruta_volcan, "Volcán de las 58 pruebas",
           "Efecto contra evidencia. Con n=10 sanos, un efecto grande con p mediano es "
           "más informativo que lo contrario.")

doc.h3("Forest plots por familia de medida")
doc.texto("La figura más honesta con n pequeño: muestra la magnitud del efecto y su "
          "incertidumbre, en vez de reducirlo a un p.")
doc.galeria(figs_forest)

doc.h3("Distribuciones de las pruebas con menor p")
doc.galeria(figs_violin)

doc.h3("Modelo A vs modelo B · ¿el efecto sobrevive al control de ansiedad?")
doc.figura(ruta_comp, "Efectos con y sin ajuste por ansiedad/depresión",
           "Los puntos sobre la diagonal indican que el efecto no cambia al controlar "
           "STAI-Rasgo y BDI. Alejarse hacia abajo indicaría que la ansiedad explicaba "
           "parte del efecto.")

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print(f"\n→ documento actualizado: {cfg.DOCS / 'REPORTE_EXPLORATORIO.html'}")
