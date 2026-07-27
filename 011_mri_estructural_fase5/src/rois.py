"""
Traducción de la lista CONGELADA de ROIs a-priori (`06_ROIs_apriori_DCNN.md` §2)
a columnas reales de `master_analitico.csv`.

⚠️ Esta lista se congeló el 2026-07-27 ANTES de mirar ningún resultado confirmatorio.
**No modificar** sin registrar una enmienda fechada en `06_ROIs_apriori_DCNN.md` y en
`REPORTE_METODOLOGICO.md`. Cambiarla después de ver resultados invalida el análisis.

Decisiones del PI del 2026-07-27 implementadas aquí:
  D2 · ROIs compuestas por varios labels se agregan **ponderando por área** en grosor y
       LGI (el promedio simple sesga hacia el label pequeño) y **sumando** en volumen y área.
  D3 · `precentral` y `postcentral` son **dos ROIs separadas**.
  D4 · Subcampos hipocampales = **eje posterior completo** (body + tail).
  D6 · Volumen cortical y subcortical comparten familia FDR.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# ════════════════════════════════════════════════════════════════════════════
# DEFINICIÓN DE LAS ROIs
# ════════════════════════════════════════════════════════════════════════════

MEDIDAS_CORTICALES = ["thickness", "area", "volume", "LGI"]
HEMIS = ["lh", "rh"]


@dataclass(frozen=True)
class ROI:
    """Una ROI de la lista congelada.

    `labels` tiene más de un elemento solo en las ROIs compuestas (ínsula posterior, ACC),
    que se agregan según D2.
    """

    n: str  # número en la tabla congelada
    nombre: str  # nombre legible para figuras y tablas
    prioridad: str  # "alta" | "media"
    tipo: str  # "C" cortical | "S" subcortical
    atlas: str  # "DKT" | "DS" | "aseg"
    labels: tuple[str, ...]
    nota: str = ""

    @property
    def compuesta(self) -> bool:
        return len(self.labels) > 1

    @property
    def medidas(self) -> list[str]:
        return MEDIDAS_CORTICALES if self.tipo == "C" else ["volume"]


# ─── Prioridad ALTA — 8 ROIs región (etapa A1) ──────────────────────────────
ROIS_ALTA: list[ROI] = [
    ROI("1", "Ínsula posterior", "alta", "C", "DS",
        ("G_Ins_lg_and_S_cent_ins", "S_circular_insula_sup"),
        "DKT no separa ínsula ant/post → Destrieux. Cotejar con ínsula DKT completa."),
    ROI("2", "Giro supramarginal", "alta", "C", "DKT", ("supramarginal",), "Nodo TPJ/vestibular."),
    ROI("3", "Temporal superior", "alta", "C", "DKT", ("superiortemporal",)),
    ROI("4", "Hipocampo", "alta", "S", "aseg", ("Hippocampus",),
        "+ subcampos posteriores como sub-análisis a-priori (etapa A3)."),
    ROI("5", "Corteza parahipocampal", "alta", "C", "DKT", ("parahippocampal",), "PPA."),
    ROI("6", "Corteza entorrinal", "alta", "C", "DKT", ("entorhinal",)),
    ROI("7", "Precúneo", "alta", "C", "DKT", ("precuneus",)),
    ROI("8", "Istmo del cíngulo", "alta", "C", "DKT", ("isthmuscingulate",),
        "Proxy DKT de retroesplenial; cotejar Destrieux G_cingul_Post_dorsal/ventral."),
]

# ─── Prioridad MEDIA — 11 ROIs región (etapa A2) ────────────────────────────
ROIS_MEDIA: list[ROI] = [
    ROI("9", "Parietal superior", "media", "C", "DKT", ("superiorparietal",)),
    ROI("10", "Parietal inferior", "media", "C", "DKT", ("inferiorparietal",)),
    ROI("11", "Occipital lateral", "media", "C", "DKT", ("lateraloccipital",), "Dependencia visual."),
    ROI("12", "Cuneus", "media", "C", "DKT", ("cuneus",)),
    ROI("13", "Temporal medio", "media", "C", "DKT", ("middletemporal",), "MT-V5, movimiento visual."),
    ROI("14", "Cingulada anterior", "media", "C", "DKT",
        ("caudalanteriorcingulate", "rostralanteriorcingulate"), "Ansiedad/saliencia."),
    ROI("15", "Prefrontal dorsolateral", "media", "C", "DKT", ("rostralmiddlefrontal",), "Aprox. DLPFC."),
    ROI("16a", "Precentral", "media", "C", "DKT", ("precentral",), "Control postural (D3: ROI propia)."),
    ROI("16b", "Postcentral", "media", "C", "DKT", ("postcentral",), "Control postural (D3: ROI propia)."),
    ROI("17", "Tálamo", "media", "S", "aseg", ("Thalamus",),
        "FreeSurfer 7.x+ renombró 'Thalamus-Proper' → 'Thalamus'. + núcleos anteriores en A3."),
    ROI("18", "Amígdala", "media", "S", "aseg", ("Amygdala",), "Eje ansiedad-vestibular."),
    ROI("19", "Cerebelo", "media", "S", "aseg", ("Cerebellum_Cortex",), "Calibración."),
]

ROIS = ROIS_ALTA + ROIS_MEDIA

# ─── Sub-análisis a-priori de subestructuras (etapa A3) ─────────────────────
# D4: eje hipocampal posterior completo = body + tail.
SUBCAMPOS_HIPOCAMPO_POSTERIOR = [
    "Hippocampal_tail", "Whole_hippocampal_body", "CA1_body", "CA3_body", "CA4_body",
    "GC_ML_DG_body", "molecular_layer_HP_body", "subiculum_body", "presubiculum_body",
]
# Núcleos talámicos anteriores / head-direction.
NUCLEOS_TALAMO_ANTERIOR = ["AV", "LD", "VA", "VAmc"]
# Núcleos de la amígdala (exploratorio dentro de A3).
NUCLEOS_AMIGDALA = [
    "Lateral_nucleus", "Basal_nucleus", "Accessory_Basal_nucleus", "Central_nucleus",
    "Medial_nucleus", "Cortical_nucleus", "Anterior_amygdaloid_area_AAA",
    "Corticoamygdaloid_transitio", "Paralaminar_nucleus", "Whole_amygdala",
]

# ════════════════════════════════════════════════════════════════════════════
# NOMBRES DE COLUMNA
# ════════════════════════════════════════════════════════════════════════════


def columna(atlas: str, medida: str, hemi: str, label: str) -> str:
    """Nombre de la columna en `master_analitico.csv` para un label simple."""
    if atlas == "aseg":
        lado = "Left" if hemi == "lh" else "Right"
        return f"aseg_{lado}_{label}"
    if medida == "LGI":
        return f"lgi_{atlas}_{hemi}_{label}"
    return f"ctx_{atlas}_{medida}_{hemi}_{label}"


def columnas_de(roi: ROI, medida: str, hemi: str) -> list[str]:
    """Columnas fuente de una ROI (varias solo si es compuesta)."""
    return [columna(roi.atlas, medida, hemi, lab) for lab in roi.labels]


def nombre_variable(roi: ROI, medida: str, hemi: str) -> str:
    """Nombre canónico de la variable analítica derivada. Se usa en tablas y figuras."""
    return f"{roi.n}_{roi.labels[0] if not roi.compuesta else 'comp'}_{medida}_{hemi}"


# ════════════════════════════════════════════════════════════════════════════
# AGREGACIÓN DE ROIs COMPUESTAS  (decisión D2)
# ════════════════════════════════════════════════════════════════════════════


def agregar(m: pd.DataFrame, roi: ROI, medida: str, hemi: str) -> pd.Series:
    """Devuelve la serie analítica de una (ROI × medida × hemisferio).

    ROI simple  → la columna tal cual.
    ROI compuesta (D2):
      - `volume`, `area`      → **suma** de los labels (son cantidades extensivas).
      - `thickness`, `LGI`    → **media ponderada por el área** de cada label
                                (son cantidades intensivas; el promedio simple daría
                                el mismo peso a un label grande y a uno pequeño).
    """
    cols = columnas_de(roi, medida, hemi)
    faltan = [c for c in cols if c not in m.columns]
    if faltan:
        raise KeyError(f"{roi.nombre} ({medida}, {hemi}): columnas ausentes {faltan}")

    if not roi.compuesta:
        return m[cols[0]].rename(nombre_variable(roi, medida, hemi))

    if medida in ("volume", "area"):
        serie = m[cols].sum(axis=1, skipna=False)
    else:
        pesos = m[[columna(roi.atlas, "area", hemi, lab) for lab in roi.labels]]
        serie = (m[cols].to_numpy() * pesos.to_numpy()).sum(axis=1) / pesos.to_numpy().sum(axis=1)
        serie = pd.Series(serie, index=m.index)
        # Un NaN en cualquier label (p. ej. P14 en LGI) debe propagarse.
        serie[m[cols].isna().any(axis=1)] = np.nan

    return serie.rename(nombre_variable(roi, medida, hemi))


# ════════════════════════════════════════════════════════════════════════════
# CONSTRUCCIÓN DEL PLAN DE PRUEBAS
# ════════════════════════════════════════════════════════════════════════════


def plan_de_pruebas(prioridad: str) -> pd.DataFrame:
    """Enumera las pruebas de una etapa: una fila por (ROI × medida × hemisferio).

    La columna `familia_fdr` define el grupo de corrección de Benjamini-Hochberg.
    D6: el volumen cortical y el subcortical comparten la familia "volume".
    """
    rois = {"alta": ROIS_ALTA, "media": ROIS_MEDIA}[prioridad]
    filas = []
    for roi in rois:
        for medida in roi.medidas:
            for hemi in HEMIS:
                filas.append({
                    "etapa": "A1" if prioridad == "alta" else "A2",
                    "roi_n": roi.n,
                    "roi": roi.nombre,
                    "tipo": roi.tipo,
                    "atlas": roi.atlas,
                    "medida": medida,
                    "hemi": hemi,
                    "familia_fdr": medida,  # D6
                    "variable": nombre_variable(roi, medida, hemi),
                    "compuesta": roi.compuesta,
                    "ajusta_etiv": medida in ("volume", "area"),
                    "n_esperado": 45 if medida == "LGI" else 46,
                })
    return pd.DataFrame(filas)


def construir_matriz(m: pd.DataFrame, prioridad: str) -> pd.DataFrame:
    """Devuelve un DataFrame con una columna por prueba, ya agregada, indexado como `m`."""
    plan = plan_de_pruebas(prioridad)
    rois = {r.n: r for r in ROIS}
    series = [
        agregar(m, rois[f.roi_n], f.medida, f.hemi)
        for f in plan.itertuples()
    ]
    return pd.concat(series, axis=1)


def verificar_disponibilidad(m: pd.DataFrame) -> pd.DataFrame:
    """Comprueba que TODA columna fuente de la lista congelada existe en la tabla maestra.

    Se ejecuta antes de cualquier modelo: si la lista congelada y los datos se
    desalinean, hay que saberlo aquí y no a mitad del análisis.
    """
    filas = []
    for roi in ROIS:
        for medida in roi.medidas:
            for hemi in HEMIS:
                cols = columnas_de(roi, medida, hemi)
                if roi.compuesta and medida in ("thickness", "LGI"):
                    cols = cols + [columna(roi.atlas, "area", hemi, lab) for lab in roi.labels]
                ausentes = [c for c in cols if c not in m.columns]
                filas.append({
                    "roi": roi.nombre, "prioridad": roi.prioridad, "medida": medida,
                    "hemi": hemi, "n_columnas": len(cols), "ausentes": ausentes or None,
                })
    return pd.DataFrame(filas)
