"""
ETAPA D2 — Figuras anatómicas de publicación renderizadas con FreeSurfer.

`freeview` en modo batch produce renders muy superiores a los de nilearn: sombreado
3D real, curvatura en dos grises suaves y fondo transparente. Estas figuras
sustituyen a las provisionales de `figs/etapaD/` y `figs/etapaB5/`.

Cuatro figuras:
  1. Mapa anatómico de la red DCNN — las 19 ROIs a-priori coloreadas por prioridad.
     No existía ninguna equivalente; es la que sitúa la hipótesis antes de los resultados.
  2. Clusters de girificación (LGI), MPPP vs Vestibular.
  3. Clusters de grosor ↔ severidad (DHI), dentro de pacientes.
  4. Panel resumen de la doble disociación.

Se pinta siempre el mapa **enmascarado por clusters supervivientes**
(`cache.th*.abs.sig.masked.mgh`), nunca el mapa crudo: el crudo sugeriría una
extensión que la corrección por clusters no respalda.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python notebooks/etapaD2_figuras_freesurfer.py
"""

# %% ── setup ────────────────────────────────────────────────────────────────
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from PIL import Image

import config as cfg
import figuras as fg
import glmfit as gf
import rois

fg.aplicar_estilo()
SALIDA = cfg.FIGS / "etapaD2_freesurfer"
SALIDA.mkdir(parents=True, exist_ok=True)
TMP = Path(tempfile.mkdtemp(prefix="fsfig_"))
SD = gf.SUBJECTS_DIR

# azimuth 0 mira desde la izquierda: para lh es lateral, para rh es medial.
VISTAS = {
    ("lh", "lateral"): ["azimuth", "0"],
    ("lh", "medial"): ["azimuth", "180"],
    ("rh", "lateral"): ["azimuth", "180"],
    ("rh", "medial"): ["azimuth", "0"],
    ("lh", "dorsal"): ["azimuth", "0", "elevation", "90"],
    ("rh", "dorsal"): ["azimuth", "180", "elevation", "90"],
}


def render(hemi, vista, salida, overlay=None, umbral=None, custom=None,
           annot=None, magnificacion=2):
    """Una vista de un hemisferio con freeview en modo batch."""
    capas = [f"{SD}/fsaverage/surf/{hemi}.inflated", "curvature_method=binary"]
    if overlay:
        capas.append(f"overlay={overlay}")
        if umbral:
            capas.append(f"overlay_threshold={umbral}")
        if custom:
            capas.append(f"overlay_custom={custom}")
    if annot:
        capas.append(f"annot={annot}")
        capas.append("annot_outline=0")
    cmd = (["freeview", "-f", ":".join(capas), "-viewport", "3d", "-cam"]
           + VISTAS[(hemi, vista)]
           + ["-ss", str(salida), str(magnificacion), "autotrim"])
    r = subprocess.run(cmd, env=gf.entorno(), capture_output=True, text=True, timeout=300)
    if not Path(salida).exists():
        print(f"   ⚠️ falló {hemi}/{vista}: {r.stderr[-300:]}")
        return False
    return True


def sin_fondo(ruta):
    """Convierte el fondo negro de freeview en transparente.

    freeview escribe PNG en RGB con fondo negro sólido (no tiene canal alpha ni
    opción de fondo). No basta con volver transparente todo píxel negro: las
    sombras profundas del propio cerebro también lo son. Se identifica el fondo
    por CONECTIVIDAD con el borde de la imagen, de modo que solo desaparece lo
    que rodea al cerebro.
    """
    from scipy import ndimage

    a = np.array(Image.open(ruta).convert("RGB"))
    casi_negro = a.sum(axis=2) < 25
    etiquetas, n = ndimage.label(casi_negro)
    if n:
        borde = set(etiquetas[0, :]) | set(etiquetas[-1, :]) | \
                set(etiquetas[:, 0]) | set(etiquetas[:, -1])
        borde.discard(0)
        fondo = np.isin(etiquetas, list(borde))
    else:
        fondo = np.zeros_like(casi_negro)
    rgba = np.dstack([a, np.where(fondo, 0, 255).astype(np.uint8)])
    return Image.fromarray(rgba, mode="RGBA")


def igualar(imgs):
    """Centra cada imagen en un lienzo transparente común.

    `autotrim` recorta cada vista a la caja de su contenido, así que una vista
    dorsal (achatada) y una lateral (alta) salen con proporciones muy distintas y
    al montarlas quedan desalineadas y con escalas incomparables. Centrarlas en un
    lienzo común preserva el tamaño RELATIVO real de cada vista.
    """
    w = max(i.width for i in imgs)
    h = max(i.height for i in imgs)
    fuera = []
    for i in imgs:
        lienzo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        lienzo.paste(i, ((w - i.width) // 2, (h - i.height) // 2), i)
        fuera.append(lienzo)
    return fuera


def montar(paneles, salida, titulo, subtitulo, filas=None, etiquetas=None,
           colorbar=None, figsize=None):
    """Compone las vistas en una figura única con título y leyenda."""
    imgs = igualar([sin_fondo(p) for p in paneles if Path(p).exists()])
    if not imgs:
        return None
    n = len(imgs)
    filas = filas or (2 if n > 3 else 1)
    cols = int(np.ceil(n / filas))
    fig, axes = plt.subplots(filas, cols, figsize=figsize or (3.7 * cols, 2.9 * filas))
    axes = np.atleast_1d(axes).ravel()
    for ax, img, etq in zip(axes, imgs, etiquetas or [""] * n):
        ax.imshow(img)
        ax.axis("off")
        if etq:
            ax.set_title(etq, fontsize=9, color=fg.INK_2, pad=2)
    for ax in axes[len(imgs):]:
        ax.axis("off")
    fig.suptitle(titulo, x=0.02, y=0.985, ha="left", va="top", fontsize=13, color=fg.INK)
    fig.text(0.02, 0.945, subtitulo, fontsize=8.5, color=fg.MUTED, va="top")
    if colorbar:
        fig.subplots_adjust(right=0.88)
        cax = fig.add_axes([0.915, 0.18, 0.014, 0.26])
        norm, cmap, etiqueta = colorbar
        cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax)
        cb.set_label(etiqueta, fontsize=8, color=fg.INK_2)
        cb.outline.set_visible(False)
        cb.ax.tick_params(length=2, labelsize=7.5, labelcolor=fg.INK_2)
    fig.subplots_adjust(top=0.88, wspace=0.01, hspace=0.06)
    return fg.guardar(fig, salida)


# %% ── FIGURA 1 · mapa anatómico de la red DCNN ─────────────────────────────
print("▸ Figura 1 · mapa anatómico de la red DCNN")

# Regiones corticales de la lista congelada, por prioridad. Las subcorticales
# (hipocampo, tálamo, amígdala, cerebelo) no tienen representación en superficie.
ALTA_DKT = ["supramarginal", "superiortemporal", "parahippocampal", "entorhinal",
            "precuneus", "isthmuscingulate"]
MEDIA_DKT = ["superiorparietal", "inferiorparietal", "lateraloccipital", "cuneus",
             "middletemporal", "caudalanteriorcingulate", "rostralanteriorcingulate",
             "rostralmiddlefrontal", "precentral", "postcentral"]
# La ínsula posterior se define en Destrieux; se añade desde ese atlas.
ALTA_DS = ["G_Ins_lg_and_S_cent_ins", "S_circular_insula_sup"]

paneles_red, faltan = [], []
for hemi in ("lh", "rh"):
    # fsaverage no trae el annot de DKT, solo DK (aparc.annot) y Destrieux. Se usa
    # DK: los nombres de región son los mismos y sus límites casi idénticos — el
    # análisis de robustez R1 midió r = 0,997 entre ambas parcelaciones. Esto afecta
    # solo al dibujo de esta figura; todos los análisis se hicieron sobre DKT.
    etiquetas_dkt, ctab, nombres = nib.freesurfer.read_annot(
        str(SD / "fsaverage" / "label" / f"{hemi}.aparc.annot"))
    nombres = [n.decode() if isinstance(n, bytes) else n for n in nombres]
    etiquetas_ds, _, nombres_ds = nib.freesurfer.read_annot(
        str(SD / "fsaverage" / "label" / f"{hemi}.aparc.a2009s.annot"))
    nombres_ds = [n.decode() if isinstance(n, bytes) else n for n in nombres_ds]

    mapa = np.zeros(len(etiquetas_dkt), dtype=np.float32)
    for r in MEDIA_DKT:                      # media primero: alta puede sobrescribir
        if r in nombres:
            mapa[etiquetas_dkt == nombres.index(r)] = 2.0
        else:
            faltan.append(f"{hemi}/DKT/{r}")
    for r in ALTA_DKT:
        if r in nombres:
            mapa[etiquetas_dkt == nombres.index(r)] = 1.0
        else:
            faltan.append(f"{hemi}/DKT/{r}")
    for r in ALTA_DS:
        if r in nombres_ds:
            mapa[etiquetas_ds == nombres_ds.index(r)] = 1.0
        else:
            faltan.append(f"{hemi}/DS/{r}")

    ruta = TMP / f"{hemi}.red_dcnn.mgh"
    nib.save(nib.MGHImage(mapa[:, None, None].astype(np.float32), np.eye(4)), str(ruta))
    print(f"   {hemi}: {int((mapa == 1).sum())} vértices alta · "
          f"{int((mapa == 2).sum())} media")

    for vista in ("lateral", "medial"):
        p = TMP / f"red_{hemi}_{vista}.png"
        # naranja = prioridad alta · azul = prioridad media
        if render(hemi, vista, p, overlay=str(ruta), umbral="0.5,2.5",
                  custom="1,235,104,52,2,42,120,214"):
            paneles_red.append(p)

if faltan:
    print(f"   ⚠️ etiquetas no encontradas: {faltan}")

ruta_fig1 = montar(
    paneles_red, SALIDA / "fig1_mapa_red_DCNN",
    "Red de navegación visuoespacial-vestibular · regiones a priori",
    "naranja = prioridad alta · azul = prioridad media · lista congelada antes de ver "
    "resultados\nlas ROIs subcorticales (hipocampo, tálamo, amígdala, cerebelo) no "
    "aparecen en superficie",
    filas=2, etiquetas=["izquierdo · lateral", "izquierdo · medial",
                        "derecho · lateral", "derecho · medial"])
print(f"   → {ruta_fig1}")

# %% ── FIGURAS 2 y 3 · clusters ─────────────────────────────────────────────
from matplotlib.colors import LinearSegmentedColormap, Normalize

CMAP_AZUL = LinearSegmentedColormap.from_list("az", ["#9ec5f4", "#2a78d6", "#0d366b"])

CONTRASTES = [
    ("fig2_clusters_LGI", "pial_lgi", "dirigido", "MPPP_vs_Vestibular",
     "Girificación (LGI) · MPPP vs pacientes vestibulares",
     "azul = menor en MPPP · vertex-wise corregido por clusters "
     "(Monte Carlo, umbral p<0,001, CWP<0,05, corregido por 2 hemisferios) · n=35"),
    ("fig3_clusters_grosor_DHI", "thickness", "sev_pac_DHI", "pendiente_DHI",
     "Grosor cortical y severidad sintomática (DHI)",
     "azul = menos grosor con más síntomas · vertex-wise dentro de pacientes · n=30"),
]

rutas_clusters = {}
for nombre, medida, diseno, contraste, titulo, subtitulo in CONTRASTES:
    print(f"▸ {nombre}")
    paneles, etqs, vmax = [], [], 0.0
    for hemi in ("lh", "rh"):
        d = gf.GLM_DIR / medida / diseno / f"glm.{hemi}" / contraste
        cands = sorted(d.glob("cache.th*.abs.sig.masked.mgh"))
        if not cands:
            print(f"   ⚠️ sin mapa enmascarado en {d}")
            continue
        v = np.abs(np.asarray(nib.load(str(cands[0])).get_fdata()))
        vmax = max(vmax, float(np.nanmax(v)))
        for vista in ("lateral", "medial", "dorsal"):
            p = TMP / f"{nombre}_{hemi}_{vista}.png"
            if render(hemi, vista, p, overlay=str(cands[0]), umbral="1.3,5"):
                paneles.append(p)
                etqs.append(f"{'izquierdo' if hemi == 'lh' else 'derecho'} · {vista}")
    rutas_clusters[nombre] = montar(
        paneles, SALIDA / nombre, titulo, subtitulo, filas=2, etiquetas=etqs,
        colorbar=(Normalize(1.3, max(vmax, 5.0)), CMAP_AZUL, "−log₁₀(p)"))
    print(f"   → {rutas_clusters[nombre]}")

# %% ── FIGURA 4 · panel de la doble disociación ─────────────────────────────
print("▸ Figura 4 · panel resumen de la doble disociación")
paneles_dis, etqs_dis = [], []
for medida, diseno, contraste, fila in [
        ("pial_lgi", "dirigido", "MPPP_vs_Vestibular", "LGI"),
        ("thickness", "sev_pac_DHI", "pendiente_DHI", "grosor")]:
    for hemi in ("lh", "rh"):
        d = gf.GLM_DIR / medida / diseno / f"glm.{hemi}" / contraste
        cands = sorted(d.glob("cache.th*.abs.sig.masked.mgh"))
        if not cands:
            continue
        vista = "lateral" if fila == "grosor" else "dorsal"
        p = TMP / f"dis_{fila}_{hemi}.png"
        if render(hemi, vista, p, overlay=str(cands[0]), umbral="1.3,5"):
            paneles_dis.append(p)
            etqs_dis.append(f"{'izq' if hemi == 'lh' else 'der'} · {vista}")

fig, axes = plt.subplots(2, 2, figsize=(9.6, 6.0))
axes = axes.ravel()
for ax, im, etq in zip(axes, igualar([sin_fondo(p) for p in paneles_dis]), etqs_dis):
    ax.imshow(im)
    ax.axis("off")
    ax.set_title(etq, fontsize=8.5, color=fg.INK_2, pad=2)
for ax in axes[len(paneles_dis):]:
    ax.axis("off")
fig.text(0.015, 0.68, "GIRIFICACIÓN\ndiferencia\nentre grupos\n\nRASGO", fontsize=9.5,
         color="#eb6834", fontweight="bold", va="center", ha="left", linespacing=1.5)
fig.text(0.015, 0.26, "GROSOR\nasociación con\nla severidad\n\nESTADO", fontsize=9.5,
         color="#2a78d6", fontweight="bold", va="center", ha="left", linespacing=1.5)
fig.suptitle("Doble disociación: dos medidas de la misma corteza, dos fenómenos distintos",
             x=0.02, y=0.985, ha="left", va="top", fontsize=12.5, color=fg.INK)
fig.text(0.02, 0.94,
         "arriba: el LGI separa MPPP de pacientes vestibulares pero no se asocia con nada · "
         "abajo: el grosor no separa grupos pero sigue a la severidad",
         fontsize=8.5, color=fg.MUTED, va="top")
fig.subplots_adjust(top=0.86, left=0.155, right=0.99, wspace=0.01, hspace=0.02)
ruta_fig4 = fg.guardar(fig, SALIDA / "fig4_doble_disociacion")
print(f"   → {ruta_fig4}")

print(f"\n→ figuras en {SALIDA}")
print(f"   temporales en {TMP} (se pueden borrar)")
