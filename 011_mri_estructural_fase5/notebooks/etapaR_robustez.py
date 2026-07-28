"""
ETAPA R — Robustez de los dos hallazgos principales.

Las variantes R1 y R8 del plan (§2.3), que nunca se corrieron y que con n=31–36
son las que más pueden cambiar la lectura:

**R1 · réplica entre atlas.** Los resultados usan DKT. Si el efecto es real debe
verse también en DK (Desikan-Killiany) y en Destrieux, que parcelan el mismo manto
con criterios distintos. Si solo aparece en DKT, es un artefacto de la parcelación.

**R8 · leave-one-out.** Con n pequeño, un solo sujeto influyente puede sostener un
efecto entero. Se recalcula el estadístico quitando cada sujeto de uno en uno y se
mira cuánto se mueve. Es la comprobación más importante de todo este bloque: un
rho de −0,70 con n=31 es exactamente el escenario donde esto puede fallar.

Se aplica a los dos hallazgos que sostienen el trabajo:
  1. LGI de la red DCNN · MPPP vs Vestibular  (etapas AD y C1)
  2. Grosor ↔ severidad dentro de pacientes   (etapas B3 y B4)

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaR_robustez.py
"""

# %% ── setup ────────────────────────────────────────────────────────────────
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

import config as cfg
import correlaciones as co
import figuras as fg
import modelos
import pipeline as pl
import rois

fg.aplicar_estilo()
FIGS = cfg.FIGS / "etapaR"
FIGS.mkdir(parents=True, exist_ok=True)

m = cfg.cargar_master()
pacientes_idx = m["Grupo"].isin(["MPPP", "Vestibular"])

# ════════════════════════════════════════════════════════════════════════════
# R1 · RÉPLICA ENTRE ATLAS
# ════════════════════════════════════════════════════════════════════════════
# Las ROIs de prioridad alta que sobrevivieron en AD, con su equivalente en los
# otros dos atlas. DKT y DK comparten nomenclatura; Destrieux usa otra.
EQUIVALENCIAS = {
    "supramarginal":     {"DK": "supramarginal", "DS": "G_pariet_inf_Supramar"},
    "superiortemporal":  {"DK": "superiortemporal", "DS": "G_temp_sup_Lateral"},
    "parahippocampal":   {"DK": "parahippocampal", "DS": "G_oc_temp_med_Parahip"},
    "precuneus":         {"DK": "precuneus", "DS": "G_precuneus"},
    "isthmuscingulate":  {"DK": "isthmuscingulate", "DS": "G_cingul_Post_dorsal"},
    "entorhinal":        {"DK": "entorhinal", "DS": "G_oc_temp_med_Parahip"},
    "precentral":        {"DK": "precentral", "DS": "G_precentral"},
    "postcentral":       {"DK": "postcentral", "DS": "G_postcentral"},
}

print("=== R1 · réplica del efecto del LGI en los tres atlas ===")
filas = []
for region, equiv in EQUIVALENCIAS.items():
    for atlas, nombre in [("DKT", region), ("DK", equiv["DK"]), ("DS", equiv["DS"])]:
        for hemi in ("lh", "rh"):
            col = f"lgi_{atlas}_{hemi}_{nombre}"
            if col not in m.columns:
                continue
            r = modelos.ancova(
                m[pacientes_idx], col, pl.COVAR_BASE,
                contrastes=[("MPPP", "Vestibular")], referencia="Vestibular",
                n_perm=5_000, n_boot=2_000,
            )
            ph = r.posthoc["MPPP_vs_Vestibular"]
            filas.append({"region": region, "atlas": atlas, "hemi": hemi, "n": r.n,
                          "d": ph["d"], "ic_low": ph["d_ic"][0], "ic_high": ph["d_ic"][1],
                          "p_perm": r.p_perm})
r1 = pd.DataFrame(filas)
piv_r1 = r1.pivot_table(index=["region", "hemi"], columns="atlas", values="d")
print(piv_r1.round(3).to_string())

# concordancia entre atlas
concordancia = []
for a, b in [("DKT", "DK"), ("DKT", "DS"), ("DK", "DS")]:
    j = r1[r1.atlas == a].merge(r1[r1.atlas == b], on=["region", "hemi"],
                                suffixes=("_a", "_b"))
    concordancia.append({
        "par": f"{a} vs {b}", "n_rois": len(j),
        "r_pearson": float(j.d_a.corr(j.d_b)),
        "mismo_signo": f"{int((np.sign(j.d_a) == np.sign(j.d_b)).sum())}/{len(j)}",
        "d_medio_a": j.d_a.mean(), "d_medio_b": j.d_b.mean(),
    })
concordancia = pd.DataFrame(concordancia)
print("\nConcordancia entre atlas:")
print(concordancia.round(3).to_string(index=False))
r1.to_csv(cfg.RESULTS / "etapaR1_replica_atlas_resultados.csv", index=False)
concordancia.to_csv(cfg.RESULTS / "etapaR1_concordancia_resultados.csv", index=False)

# ════════════════════════════════════════════════════════════════════════════
# R8 · LEAVE-ONE-OUT
# ════════════════════════════════════════════════════════════════════════════
print("\n=== R8 · leave-one-out de los hallazgos principales ===")

X_alta = rois.construir_matriz(m, "alta")
X_media = rois.construir_matriz(m, "media")
datos = pd.concat([m.drop(columns=[c for c in list(X_alta.columns) + list(X_media.columns)
                                   if c in m.columns]), X_alta, X_media], axis=1)
plan_alta = rois.plan_de_pruebas("alta")
datos["idxred_LGI"] = pl.indice_compuesto(
    datos, plan_alta.loc[plan_alta.medida == "LGI", "variable"].tolist(), metodo="z")

HALLAZGOS_D = [   # (etiqueta, variable, descripción)
    ("Índice de red · LGI", "idxred_LGI", "MPPP vs Vestibular"),
    ("Ínsula posterior rh · LGI", "1_comp_LGI_rh", "MPPP vs Vestibular"),
    ("Temporal superior rh · LGI", "3_superiortemporal_LGI_rh", "MPPP vs Vestibular"),
]
HALLAZGOS_RHO = [  # (etiqueta, variable, outcome)
    ("Supramarginal rh · grosor", "2_supramarginal_thickness_rh", "Niigata"),
    ("Supramarginal rh · grosor", "2_supramarginal_thickness_rh", "DHI"),
    ("Temporal superior rh · grosor", "3_superiortemporal_thickness_rh", "DHI"),
    ("Postcentral lh · grosor", "16b_postcentral_thickness_lh", "DHI"),
]

pac = datos[pacientes_idx].copy()

# --- LOO de las diferencias de grupo (d) ---
loo_d = []
for etiqueta, var, desc in HALLAZGOS_D:
    r = modelos.ancova(pac, var, pl.COVAR_BASE, contrastes=[("MPPP", "Vestibular")],
                       referencia="Vestibular", n_perm=5_000, n_boot=1_000)
    d_obs = r.posthoc["MPPP_vs_Vestibular"]["d"]
    ds, ps = [], []
    for i in range(len(pac)):
        sub = pac.drop(pac.index[i])
        try:
            ri = modelos.ancova(sub, var, pl.COVAR_BASE,
                                contrastes=[("MPPP", "Vestibular")],
                                referencia="Vestibular", n_perm=1_000, n_boot=1)
            ds.append(ri.posthoc["MPPP_vs_Vestibular"]["d"])
            ps.append(ri.p_perm)
        except Exception:
            continue
    ds, ps = np.array(ds), np.array(ps)
    loo_d.append({
        "hallazgo": etiqueta, "contraste": desc, "estadistico": "d de Cohen",
        "observado": d_obs, "loo_min": ds.min(), "loo_max": ds.max(),
        "loo_rango": ds.max() - ds.min(),
        "p_max_loo": ps.max(), "veces_p_mayor_005": int((ps > 0.05).sum()), "n_loo": len(ds),
    })
    print(f"  {etiqueta:<32} d={d_obs:+.3f}  LOO [{ds.min():+.3f}, {ds.max():+.3f}]  "
          f"p max={ps.max():.4f}  ({int((ps > 0.05).sum())}/{len(ds)} pierden p<0,05)")

# --- LOO de las correlaciones (rho) ---
loo_rho = []
for etiqueta, var, outcome in HALLAZGOS_RHO:
    cov = ["Edad", "Genero", "Grupo"]
    base = pac[[var, outcome] + cov].dropna()
    r_obs = co.spearman_parcial(pac, var, outcome, cov, n_boot=1)["rho"]
    rhos = []
    for i in range(len(base)):
        sub = base.drop(base.index[i])
        rhos.append(co.spearman_parcial(sub, var, outcome, cov, n_boot=1)["rho"])
    rhos = np.array([x for x in rhos if np.isfinite(x)])
    loo_rho.append({
        "hallazgo": etiqueta, "contraste": outcome, "estadistico": "rho parcial",
        "observado": r_obs, "loo_min": rhos.min(), "loo_max": rhos.max(),
        "loo_rango": rhos.max() - rhos.min(),
        "p_max_loo": np.nan, "veces_p_mayor_005": np.nan, "n_loo": len(rhos),
    })
    print(f"  {etiqueta:<32} ({outcome}) rho={r_obs:+.3f}  "
          f"LOO [{rhos.min():+.3f}, {rhos.max():+.3f}]")

loo = pd.DataFrame(loo_d + loo_rho)
loo.to_csv(cfg.RESULTS / "etapaR8_leaveoneout_resultados.csv", index=False)

# %% ── figuras ──────────────────────────────────────────────────────────────
fig, _ = fg.forest(
    r1.assign(etiqueta=r1.region + " " + r1.hemi + " · " + r1.atlas,
              sig=r1.p_perm < 0.05).sort_values("d"),
    "d", "ic_low", "ic_high", "etiqueta", col_destaca="sig",
    titulo="R1 · el efecto del LGI en los tres atlas",
    subtitulo="MPPP vs Vestibular · en negrita, p(perm) < 0,05 · misma región, tres parcelaciones",
    figsize=(6.0, 11.0))
ruta_r1 = fg.guardar(fig, FIGS / "forest_replica_atlas")

loo_plot = loo.copy()
loo_plot["etiqueta"] = loo_plot.hallazgo + " · " + loo_plot.contraste
fig, _ = fg.forest(loo_plot, "observado", "loo_min", "loo_max", "etiqueta",
                   titulo="R8 · leave-one-out",
                   xlabel="estadístico observado, con el rango al quitar cada sujeto",
                   subtitulo="las barras NO son intervalos de confianza: son el recorrido "
                             "del estadístico al eliminar un sujeto de cada vez")
ruta_r8 = fg.guardar(fig, FIGS / "forest_leave_one_out")

# %% ── al documento ─────────────────────────────────────────────────────────
with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion("Etapa R · Robustez de los hallazgos principales",
            "¿Depende el resultado de la parcelación elegida, o de un solo sujeto?")

doc.h3("R1 · réplica entre atlas")
doc.texto(
    "Todos los resultados usan DKT. Si el efecto es real debe verse también en "
    "<b>Desikan-Killiany</b> y en <b>Destrieux</b>, que parcelan el mismo manto cortical con "
    "criterios distintos. Si solo apareciera en DKT sería un artefacto de la parcelación."
)
doc.tabla(concordancia.round(3))
doc.figura(ruta_r1, "El mismo efecto en las tres parcelaciones", "")

doc.h3("R8 · leave-one-out")
doc.texto(
    "Con n=31–36, un solo sujeto influyente puede sostener un efecto entero. Se recalcula el "
    "estadístico quitando cada sujeto de uno en uno. <b>Las barras de la figura no son "
    "intervalos de confianza</b>: son el recorrido del estadístico a lo largo de las n "
    "reestimaciones. Un recorrido estrecho significa que ningún sujeto es decisivo."
)
doc.tabla(loo.round(4))
doc.figura(ruta_r8, "Leave-one-out de los hallazgos principales", "")

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print("\n→ documento actualizado")
