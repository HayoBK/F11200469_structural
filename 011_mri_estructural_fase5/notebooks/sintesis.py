"""
SÍNTESIS — lectura transversal de todas las etapas corridas.

Cierra el documento exploratorio con: qué resiste, qué no, y qué problemas quedan
abiertos. Lee los CSV de resultados de todas las etapas, así que debe ejecutarse
al final.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/sintesis.py
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

fg.aplicar_estilo()
FIGS = cfg.FIGS / "sintesis"
FIGS.mkdir(parents=True, exist_ok=True)

R = cfg.RESULTS
A1 = pd.read_csv(R / "etapaA1_resultados_ancova.csv")
A2 = pd.read_csv(R / "etapaA2_resultados_ancova.csv")
A3 = pd.read_csv(R / "etapaA3_resultados_ancova.csv")
AD = pd.read_csv(R / "etapaAD_resultados_dirigido.csv")
C1 = pd.read_csv(R / "etapaC1_resultados_indice_red.csv")
C1d = pd.read_csv(R / "etapaC1_resultados_dirigido.csv")
B1 = pd.read_csv(R / "etapaB1_resultados_correlaciones.csv")
B2 = pd.read_csv(R / "etapaB2_resultados_correlaciones.csv")
B3 = pd.read_csv(R / "etapaB3_resultados_correlaciones.csv")

# %% ── inventario de lo corrido ─────────────────────────────────────────────
inventario = []
for nombre, t, modelo, pregunta in [
    ("A1 · ROIs prioridad ALTA", A1, "A_sin_ansiedad", "3 grupos"),
    ("A2 · ROIs prioridad MEDIA", A2, "A_sin_ansiedad", "3 grupos"),
    ("A3 · Subestructuras", A3, "A_sin_ansiedad", "3 grupos"),
    ("AD · Dirigido MPPP vs Vestibular", AD, "AD_sin_ansiedad", "2 grupos, n=36"),
    ("C1 · Índice de red (3 grupos)", C1, "A_sin_ansiedad", "3 grupos"),
    ("C1 · Índice de red (dirigido)", C1d, "dirigido_MPPP_vs_Vest", "2 grupos, n=36"),
]:
    s = t[t.modelo == modelo]
    inventario.append({
        "Etapa": nombre, "Diseño": pregunta, "Pruebas": len(s),
        "p<0,05 nominal": int((s.p_perm < 0.05).sum()),
        "Sobreviven FDR": int(s.sobrevive_fdr.sum()),
    })
for nombre, t, pregunta in [
    ("B1 · Índices de red ↔ conducta", B1, "correlación, N=46"),
    ("B2 · ROIs alta ↔ conducta", B2, "correlación, N=46"),
    ("B3 · Dentro de pacientes ↔ clínica", B3, "correlación, n≈31"),
]:
    inventario.append({
        "Etapa": nombre, "Diseño": pregunta, "Pruebas": len(t),
        "p<0,05 nominal": int((t.p < 0.05).sum()),
        "Sobreviven FDR": int(t.sobrevive_fdr.sum()),
    })
C3 = pd.read_csv(R / "etapaC3_resultados_asimetria.csv")
C2 = pd.read_csv(R / "etapaC2_resultados_covarianza.csv")
for nombre, t, modelo, pregunta in [
    ("C3 · Asimetría L−R (3 grupos)", C3, "A_tres_grupos", "3 grupos"),
    ("C3 · Asimetría L−R (dirigido)", C3, "dirigido_MPPP_vs_Vest", "2 grupos, n=36"),
]:
    s = t[t.modelo == modelo]
    inventario.append({
        "Etapa": nombre, "Diseño": pregunta, "Pruebas": len(s),
        "p<0,05 nominal": int((s.p_perm < 0.05).sum()),
        "Sobreviven FDR": int(s.sobrevive_fdr.sum()),
    })
inventario.append({
    "Etapa": "C2 · Covarianza estructural", "Diseño": "2 grupos, permutación",
    "Pruebas": len(C2), "p<0,05 nominal": int((C2.p_perm < 0.05).sum()),
    "Sobreviven FDR": int(C2.sobrevive_fdr.sum()),
})
inventario = pd.DataFrame(inventario)
print("=== INVENTARIO ===")
print(inventario.to_string(index=False))

# %% ── todo lo que sobrevive al FDR, en un solo lugar ───────────────────────
sob = []
for nombre, t, modelo in [("A1", A1, "A_sin_ansiedad"), ("A2", A2, "A_sin_ansiedad"),
                          ("A3", A3, "A_sin_ansiedad"), ("AD", AD, "AD_sin_ansiedad"),
                          ("C1", C1, "A_sin_ansiedad"), ("C1d", C1d, "dirigido_MPPP_vs_Vest")]:
    s = t[(t.modelo == modelo) & (t.sobrevive_fdr)]
    for f in s.itertuples():
        sob.append({
            "etapa": nombre,
            "roi": getattr(f, "roi", "—"),
            "hemi": getattr(f, "hemi", "—"),
            "medida": getattr(f, "medida", "—"),
            "n": f.n, "eta2p": f.eta2p, "p_perm": f.p_perm, "p_fdr": f.p_fdr,
            "d": getattr(f, "MPPP_vs_Vestibular_d", np.nan),
            "d_ic_low": getattr(f, "MPPP_vs_Vestibular_d_ic_low", np.nan),
            "d_ic_high": getattr(f, "MPPP_vs_Vestibular_d_ic_high", np.nan),
        })
supervivientes = pd.DataFrame(sob).sort_values("p_fdr")
print(f"\n=== TODO LO QUE SOBREVIVE AL FDR ({len(supervivientes)} resultados) ===")
print(supervivientes.round(4).to_string(index=False))
supervivientes.to_csv(R / "SINTESIS_supervivientes_resultados.csv", index=False)

# %% ── consistencia direccional del LGI a través de todas las etapas ────────
lgi_ad = AD[(AD.modelo == "AD_sin_ansiedad") & (AD.medida == "LGI")]
lgi_a1 = A1[(A1.modelo == "A_sin_ansiedad") & (A1.medida == "LGI")]
lgi_a2 = A2[(A2.modelo == "A_sin_ansiedad") & (A2.medida == "LGI")]
todas_lgi = pd.concat([lgi_a1, lgi_a2])

resumen_lgi = pd.DataFrame([
    {"análisis": "3 grupos · A1 (prioridad alta)", "n_rois": len(lgi_a1),
     "d_mediana": lgi_a1.MPPP_vs_Vestibular_d.median(),
     "negativas": f"{int((lgi_a1.MPPP_vs_Vestibular_d < 0).sum())}/{len(lgi_a1)}"},
    {"análisis": "3 grupos · A2 (prioridad media)", "n_rois": len(lgi_a2),
     "d_mediana": lgi_a2.MPPP_vs_Vestibular_d.median(),
     "negativas": f"{int((lgi_a2.MPPP_vs_Vestibular_d < 0).sum())}/{len(lgi_a2)}"},
    {"análisis": "3 grupos · A1+A2", "n_rois": len(todas_lgi),
     "d_mediana": todas_lgi.MPPP_vs_Vestibular_d.median(),
     "negativas": f"{int((todas_lgi.MPPP_vs_Vestibular_d < 0).sum())}/{len(todas_lgi)}"},
    {"análisis": "dirigido n=36 · todas", "n_rois": len(lgi_ad),
     "d_mediana": lgi_ad.MPPP_vs_Vestibular_d.median(),
     "negativas": f"{int((lgi_ad.MPPP_vs_Vestibular_d < 0).sum())}/{len(lgi_ad)}"},
])
print("\n=== LGI · consistencia direccional (MPPP < Vestibular) ===")
print(resumen_lgi.round(3).to_string(index=False))

# %% ── ¿la ansiedad explica el efecto? ──────────────────────────────────────
comp_ans = []
for nombre, t, ma, mb in [("A1", A1, "A_sin_ansiedad", "B_con_ansiedad"),
                          ("A2", A2, "A_sin_ansiedad", "B_con_ansiedad"),
                          ("AD", AD, "AD_sin_ansiedad", "AD_con_ansiedad")]:
    a = t[(t.modelo == ma) & (t.medida == "LGI")]
    b = t[(t.modelo == mb) & (t.medida == "LGI")]
    j = a.merge(b, on=["roi", "hemi", "medida"], suffixes=("_A", "_B"))
    comp_ans.append({
        "etapa": nombre, "n_rois": len(j),
        "N_sin_ansiedad": int(j.n_A.median()), "N_con_ansiedad": int(j.n_B.median()),
        "|d| medio sin": j.MPPP_vs_Vestibular_d_A.abs().mean(),
        "|d| medio con": j.MPPP_vs_Vestibular_d_B.abs().mean(),
    })
comp_ans = pd.DataFrame(comp_ans)
comp_ans["cambio"] = comp_ans["|d| medio con"] - comp_ans["|d| medio sin"]
print("\n=== ¿La ansiedad explica el efecto del LGI? ===")
print(comp_ans.round(3).to_string(index=False))

# %% ── la doble disociación: LGI vs grosor ──────────────────────────────────
# Cruza las etapas A y B: ¿qué medida separa grupos y cuál se asocia a severidad?
corr_todo = pd.concat([B1, B2, B3], ignore_index=True)
filas_dis = []
for medida in ["LGI", "thickness", "volume", "area"]:
    dif = AD[(AD.modelo == "AD_sin_ansiedad") & (AD.medida == medida)]
    cor_cond = corr_todo[(corr_todo.medida == medida)
                         & (corr_todo.outcome.isin(["CSE_NI", "EntropyRatio_NI"]))]
    cor_clin = corr_todo[(corr_todo.medida == medida)
                         & (corr_todo.outcome.isin(["Niigata", "DHI"]))]
    filas_dis.append({
        "medida": medida,
        "|d| medio MPPP-Vest": dif.MPPP_vs_Vestibular_d.abs().mean(),
        "difs. que sobreviven": int(dif.sobrevive_fdr.sum()),
        "|rho| máx con conducta": cor_cond.rho.abs().max(),
        "corr. conducta que sobreviven": int(cor_cond.sobrevive_fdr.sum()),
        "|rho| máx con severidad": cor_clin.rho.abs().max(),
        "corr. severidad que sobreviven": int(cor_clin.sobrevive_fdr.sum()),
    })
disociacion = pd.DataFrame(filas_dis)
print("\n=== DOBLE DISOCIACIÓN · LGI vs grosor ===")
print(disociacion.round(3).to_string(index=False))
disociacion.to_csv(R / "SINTESIS_disociacion_resultados.csv", index=False)

# %% ── figura de síntesis ───────────────────────────────────────────────────
lgi_ad_s = lgi_ad.copy()
lgi_ad_s["etiqueta"] = lgi_ad_s["roi"] + "  " + lgi_ad_s["hemi"]
lgi_ad_s = lgi_ad_s.sort_values("MPPP_vs_Vestibular_d")
fig, _ = fg.forest(
    lgi_ad_s, "MPPP_vs_Vestibular_d", "MPPP_vs_Vestibular_d_ic_low",
    "MPPP_vs_Vestibular_d_ic_high", "etiqueta", col_destaca="sobrevive_fdr",
    titulo="Girificación (LGI) · MPPP vs Vestibular · las 32 ROIs a-priori",
    subtitulo="contraste dirigido, n=36 · en negrita, sobrevive al FDR de su familia",
    figsize=(6.2, 10.5),
)
ruta_sintesis = fg.guardar(fig, FIGS / "forest_LGI_todas_las_rois")

# ¿el efecto se concentra en la red de prioridad alta?
fig, ax = fg.barras_comparadas(
    ["A1 · alta", "A2 · media"],
    {"|d| medio en LGI": [lgi_ad[lgi_ad.etapa_origen == "A1"].MPPP_vs_Vestibular_d.abs().mean(),
                          lgi_ad[lgi_ad.etapa_origen == "A2"].MPPP_vs_Vestibular_d.abs().mean()]},
    titulo="El efecto se concentra en la red núcleo",
    subtitulo="tamaño de efecto medio del LGI, contraste dirigido",
    ylabel="|d| medio", colores=["#eb6834"],
)
ruta_concentracion = fg.guardar(fig, FIGS / "concentracion_efecto")

# %% ── al documento ─────────────────────────────────────────────────────────
with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion("Síntesis · qué resiste y qué no",
            "Lectura transversal de todas las etapas. Lo único que se sostiene es el LGI.")

doc.h3("Inventario de lo corrido")
doc.tabla(inventario)

doc.h3("Todo lo que sobrevive al FDR, en un solo lugar")
doc.texto(f"De <b>{int(inventario['Pruebas'].sum())} pruebas</b> en total, "
          f"<b>{len(supervivientes)}</b> sobreviven a la corrección de su familia. "
          "Todas son LGI, todas en el contraste dirigido MPPP vs Vestibular, y todas "
          "en ROIs de prioridad alta.")
doc.tabla(supervivientes.round(4))

doc.h3("La señal del LGI es direccionalmente consistente")
doc.texto("Ninguna corrección por multiplicidad captura esto, y es lo más llamativo del "
          "análisis: la girificación de MPPP es menor que la de Vestibular en "
          "prácticamente todas las ROIs a-priori, con independencia del diseño.")
doc.tabla(resumen_lgi.round(3))
doc.figura(ruta_sintesis, "Las 32 ROIs a-priori en LGI",
           "Contraste dirigido MPPP vs Vestibular. Casi todos los intervalos caen del "
           "lado negativo; los que sobreviven al FDR aparecen en negrita.")
doc.figura(ruta_concentracion, "El efecto se concentra en la red núcleo",
           "El tamaño de efecto medio es mayor en las ROIs de prioridad alta que en las "
           "de prioridad media — lo esperable si el fenómeno es de la red DCNN y no difuso.")

doc.h3("¿Explica la ansiedad el efecto? No.")
doc.texto(
    "Al añadir STAI-Rasgo y BDI, el tamaño de efecto <b>no disminuye</b> — en algunas "
    "etapas incluso aumenta. Lo que cae es el N (de 35 a 26 en el contraste dirigido), "
    "y con él la precisión. Por eso ninguna prueba sobrevive al FDR en el modelo B: es "
    "pérdida de potencia, no desaparición del efecto. Ésta es exactamente la razón por la "
    "que el plan exige comparar <b>tamaños de efecto</b> y no solo valores p."
)
doc.tabla(comp_ans.round(3))

doc.h3("La doble disociación · LGI es rasgo, grosor es estado")
doc.texto(
    "El resultado más elegante del análisis aparece al cruzar las dos etapas. "
    "<b>El LGI y el grosor cortical se comportan de forma exactamente complementaria:</b>"
)
doc.tabla(disociacion)
doc.texto(
    "<b>El LGI separa grupos pero no se asocia a nada.</b> Distingue MPPP de Vestibular con "
    "d ≈ −0,9, y sin embargo su correlación con la conducta y con la severidad es "
    "prácticamente nula (|rho| ≤ 0,22, ninguna sobrevive al FDR). Es decir: no varía con lo "
    "enfermo que esté el paciente.<br><br>"
    "<b>El grosor no separa grupos pero se asocia con todo.</b> No hay ni una diferencia de "
    "grosor entre grupos en las 136 pruebas de las etapas A, y sin embargo dentro de "
    "pacientes correlaciona fuertemente con la severidad sintomática (Niigata rho = −0,70; "
    "DHI rho = −0,69 en supramarginal derecho) y con la entropía de búsqueda."
)
doc.nota(
    "Esto encaja con lo que se sabe de cada medida. La <b>girificación se establece en el "
    "desarrollo temprano y es estable en la adultez</b>: no puede cambiar en los meses que "
    "dura un cuadro de MPPP, así que un efecto ahí apunta a <b>rasgo predisponente</b>. "
    "El <b>grosor cortical sí es plástico</b> y responde a procesos adquiridos, así que su "
    "asociación con la severidad actual se lee como <b>marcador de estado</b>. "
    "Dos medidas de la misma corteza contando dos historias distintas."
)
doc.texto(
    "<b>Lo que sostiene la lectura del grosor:</b> la correlación con Niigata se replica "
    "<b>dentro de cada grupo por separado</b> — MPPP rho = −0,70 (n=14, p=0,005) y "
    "Vestibular rho = −0,69 (n=17, p=0,002) — así que no es un artefacto de mezclar grupos. "
    "Y de las 19 correlaciones con p&lt;0,05, <b>ninguna</b> tiene signo incoherente con sus "
    "intra-grupo: no hay paradoja de Simpson en juego."
)
doc.nota(
    "<b>Cautela sobre los outcomes clínicos:</b> Niigata y DHI correlacionan entre sí "
    "<b>rho = 0,72</b>. Miden esencialmente el mismo constructo (severidad sintomática) y "
    "<b>no son dos hallazgos independientes</b>: cuentan como uno. En cambio, la severidad "
    "clínica NO correlaciona con el desempeño en navegación (CSE rho = 0,26 con Niigata, "
    "p = 0,17), de modo que el eje clínico y el eje conductual sí son dimensiones distintas.",
    alerta=True,
)

doc.h3("Problemas abiertos y cautelas")
doc.nota(
    "<b>1 · El contraste fuerte es contra Vestibular, no contra Sano.</b> El grupo "
    "vestibular tiene la girificación más alta y MPPP la más baja, con los sanos en medio "
    "(z: MPPP −0,28 · Sano +0,04 · Vestibular +0,24). Con n=10 sanos no se puede decidir "
    "si esto es <i>girificación reducida en MPPP</i> o <i>aumentada en Vestibular</i>. "
    "Es la limitación más seria del trabajo y hay que declararla sin rodeos.",
    alerta=True,
)
doc.nota(
    "<b>2 · Los intervalos de confianza rozan el cero.</b> Varias de las ROIs que "
    "sobreviven tienen el extremo superior del IC cerca de −0,02. El efecto es real en el "
    "sentido de que resiste la corrección, pero su magnitud está pobremente determinada.",
    alerta=True,
)
doc.nota(
    "<b>3 · El LGI se recalculó desde los <code>.stats</code>.</b> Las seis tablas "
    "originales de FreeSurfer contenían la desviación estándar intrarregional, no el LGI "
    "medio (bug documentado en la especificación §5.1). Se usa <code>lgi_*</code>, nunca "
    "<code>lgisd_*</code>. Conviene mencionarlo en Methods.",
)
doc.nota(
    "<b>4 · Nada sobrevive en el diseño de 3 grupos.</b> Los 58+78+46 contrastes de A1, "
    "A2 y A3 no producen ningún resultado que aguante su FDR. El diseño dirigido no "
    "«rescata» un hallazgo dudoso: estima el <b>mismo</b> efecto (r = 0,99 entre las d de "
    "ambos diseños) con más precisión. Pero eso hay que explicarlo bien en el manuscrito, "
    "porque un revisor puede leerlo como búsqueda selectiva de resultados.",
    alerta=True,
)
doc.nota(
    "<b>5 · Dos hipótesis descartadas limpiamente.</b> La <b>asimetría hemisférica</b> (C3) no "
    "difiere entre grupos en ninguna medida ni en ninguno de los dos diseños: 0 de 68 pruebas, "
    "ninguna familia enriquecida. Eso descarta la lectura lateralizada que sugería la "
    "literatura VBM en PPPD. La <b>covarianza estructural</b> (C2) solo muestra una señal en "
    "área (r = −0,02 en MPPP vs 0,22 en Vestibular, p = 0,018) que <b>no sobrevive al FDR de "
    "las 4 medidas</b> (p_FDR = 0,070) y no tenía hipótesis previa. Con n=17 vs 19 una matriz "
    "de 91 aristas se estima con mucho ruido: es una observación para replicar, no un resultado. "
    "Resultados nulos, pero informativos: acotan el espacio de lo que hay que explicar."
)
doc.nota(
    "<b>6 · Falta la convergencia con el exploratorio.</b> Todo lo anterior es análisis "
    "por ROI. Mientras el vertex-wise whole-brain no confirme el patrón, la evidencia "
    "descansa en una sola aproximación metodológica. El <code>-qcache</code> ya está "
    "completo para grosor, área y volumen; el LGI —justo la medida que importa— requiere "
    "un <code>mris_preproc</code> propio antes de poder correr <code>mri_glmfit</code>."
)

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print(f"\n→ documento final: {cfg.DOCS / 'REPORTE_EXPLORATORIO.html'}")
