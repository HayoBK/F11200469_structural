"""
ETAPA D — Figuras de superficie de los clusters vertex-wise.

Dibuja los mapas corregidos por clusters sobre `fsaverage` inflado, en vistas
lateral y medial de cada hemisferio. Usa `nilearn` sobre la geometría local de
FreeSurfer (no descarga nada).

Se muestra el mapa **enmascarado por los clusters que sobreviven**
(`cache.th*.abs.sig.masked.mgh`), no el mapa de p sin corregir: pintar el mapa
crudo daría una impresión visual de extensión que la corrección no respalda.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaD_figuras_superficie.py
"""

# %% ── setup ────────────────────────────────────────────────────────────────
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import pandas as pd
from nilearn import plotting

import config as cfg
import figuras as fg
import glmfit as gf

fg.aplicar_estilo()
FIGS = cfg.FIGS / "etapaD"
FIGS.mkdir(parents=True, exist_ok=True)

SD = gf.SUBJECTS_DIR


def malla(hemi: str, superficie: str = "inflated"):
    """Geometría de fsaverage desde FreeSurfer, sin descargar nada."""
    coords, faces = nib.freesurfer.read_geometry(str(SD / "fsaverage" / "surf" /
                                                     f"{hemi}.{superficie}"))
    return coords, faces


def fondo(hemi: str):
    """Sombreado de curvatura bajo el mapa.

    Se usa la curvatura CRUDA recortada a percentiles, no binarizada: binarizarla
    produce un damero blanco/negro que compite visualmente con los clusters. El
    recorte deja un gradiente gris suave que da relieve sin robar atención.
    """
    curv = nib.freesurfer.read_morph_data(str(SD / "fsaverage" / "surf" / f"{hemi}.curv"))
    lo, hi = np.percentile(curv, [5, 95])
    return np.clip(curv, lo, hi)


def mapa_enmascarado(diseno: str, hemi: str, contraste: str = "MPPP_vs_Vestibular"):
    d = gf.GLM_DIR / "pial_lgi" / diseno / f"glm.{hemi}" / contraste
    cands = sorted(d.glob("cache.th*.abs.sig.masked.mgh"))
    if not cands:
        return None
    return np.asarray(nib.load(str(cands[0])).get_fdata()).ravel()


# %% ── figuras por diseño ───────────────────────────────────────────────────
salidas = []
for diseno, etiqueta in [("dirigido", "MPPP vs Vestibular · n=36"),
                         ("tres_grupos", "MPPP vs Vestibular · N=45, 3 grupos")]:
    datos_hemi = {h: mapa_enmascarado(diseno, h) for h in ("lh", "rh")}
    if all(v is None for v in datos_hemi.values()):
        continue

    vmax = max(np.nanmax(np.abs(v)) for v in datos_hemi.values() if v is not None)
    fig, axes = plt.subplots(2, 2, figsize=(9.2, 7.0),
                             subplot_kw={"projection": "3d"})
    for i, hemi in enumerate(("lh", "rh")):
        stat = datos_hemi[hemi]
        if stat is None:
            continue
        coords, faces = malla(hemi)
        for j, vista in enumerate(("lateral", "medial")):
            plotting.plot_surf_stat_map(
                (coords, faces), stat, hemi="left" if hemi == "lh" else "right",
                view=vista, colorbar=False, bg_map=fondo(hemi), bg_on_data=True,
                threshold=1.3, vmax=vmax,
                cmap="cold_hot", axes=axes[i, j], figure=fig,
            )
            axes[i, j].set_title(f"{'izquierdo' if hemi=='lh' else 'derecho'} · {vista}",
                                 fontsize=9, color=fg.INK_2)
    fig.suptitle(f"Girificación (LGI) · clusters corregidos · {etiqueta}",
                 x=0.02, y=0.985, ha="left", va="top", fontsize=12, color=fg.INK)
    fig.text(0.02, 0.945, "azul = menor en MPPP · solo se muestran los clusters que "
                          "sobreviven (CWP<0,05, corregido por 2 hemisferios)",
             fontsize=8, color=fg.MUTED, va="top")
    fig.subplots_adjust(top=0.90, wspace=0.02, hspace=0.06)
    salidas.append((fg.guardar(fig, FIGS / f"superficie_LGI_{diseno}"),
                    f"LGI · {etiqueta}", ""))
    print(f"  figura: superficie_LGI_{diseno}")

# %% ── al documento ─────────────────────────────────────────────────────────
comp = pd.read_csv(cfg.RESULTS / "etapaA5_composicion_clusters_resultados.csv")
detalle = pd.read_csv(cfg.RESULTS / "etapaA5_clusters_resultados.csv")

with open(cfg.DOCS / "_reporte.pkl", "rb") as f:
    doc = pickle.load(f)

doc.seccion("Etapa D · Mapas de superficie",
            "Dónde caen exactamente los clusters, sobre fsaverage inflado.")
doc.texto(
    "Se muestra el mapa <b>enmascarado por los clusters que sobreviven</b> a la corrección, "
    "no el mapa de p sin corregir: pintar el mapa crudo daría una impresión visual de "
    "extensión que la corrección no respalda. Azul = menor en MPPP."
)
for ruta, titulo, _ in salidas:
    doc.figura(ruta, titulo, "")

doc.h3("Composición anatómica de cada cluster")
doc.texto("El pico de un cluster cae en una sola región, pero el cluster puede abarcar varias. "
          "Esto es lo que determina si converge o no con las ROIs a-priori.")
doc.tabla(comp)
doc.tabla(detalle)

doc.escribir(cfg.DOCS / "REPORTE_EXPLORATORIO.html")
with open(cfg.DOCS / "_reporte.pkl", "wb") as f:
    pickle.dump(doc, f)
print("\n→ documento actualizado")
