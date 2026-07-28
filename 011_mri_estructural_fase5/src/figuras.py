"""
Sistema de figuras de la FASE 5 — un solo lenguaje visual para todo el paper.

Paleta categórica validada con el validador de la guía de visualización
(3 slots, modo claro, `--pairs all`): CVD ΔE 9.2 (deutan) y ΔE 24.0 en visión
normal, ambos por encima del piso. El aqua queda bajo 3:1 de contraste contra
la superficie, así que se aplica la **regla de relieve**: leyenda siempre
presente y etiquetas visibles — el color nunca porta la identidad en solitario.

Reglas que se respetan en todas las figuras:
  · el color sigue a la ENTIDAD (grupo), nunca al rango ni al orden de aparición;
  · marcas finas, rejilla y ejes recesivos, sin bordes de caja innecesarios;
  · un solo eje y por figura — nunca dos escalas;
  · para magnitudes con signo (d, diferencias) se usa la rampa **divergente**
    azul↔rojo con gris neutro en el cero, nunca un arcoíris.
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

# ════════════════════════════════════════════════════════════════════════════
# PALETA
# ════════════════════════════════════════════════════════════════════════════

# Categórica — asignada por entidad y fija. El grupo focal (MPPP) lleva el naranja.
COLOR_GRUPO = {
    "Voluntario Sano": "#2a78d6",  # slot 1 · azul
    "Vestibular": "#1baf7a",       # slot 3 · aqua
    "MPPP": "#eb6834",             # slot 2 · naranja
}
ORDEN_GRUPOS = ["Voluntario Sano", "Vestibular", "MPPP"]  # referencia → caso
ETIQUETA_GRUPO = {"Voluntario Sano": "Sano", "Vestibular": "Vestibular", "MPPP": "MPPP"}

# Chrome
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"

# Divergente para efectos con signo (azul = menor en MPPP, rojo = mayor)
CMAP_DIV = LinearSegmentedColormap.from_list(
    "div_bl_rd", ["#184f95", "#5598e7", "#f0efec", "#e8827f", "#b02b2b"]
)
# Secuencial de un solo hue para magnitudes sin signo
CMAP_SEQ = LinearSegmentedColormap.from_list(
    "seq_blue", ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#0d366b"]
)

DPI_PANTALLA = 130
# Separación del título cuando lleva subtítulo: el subtítulo se dibuja pegado al
# borde del axes, así que el título tiene que subir para no montarse encima.
PAD_TITULO = 26


def aplicar_estilo() -> None:
    """Estilo global. Se llama una vez al inicio de cada script de etapa."""
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 9,
        "axes.titlesize": 10.5,
        "axes.titleweight": "medium",
        "axes.labelsize": 9,
        "axes.labelcolor": INK_2,
        "axes.edgecolor": BASELINE,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK_2,
        "ytick.labelcolor": INK_2,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "grid.color": GRID,
        "grid.linewidth": 0.7,
        "legend.frameon": False,
        "legend.fontsize": 8.5,
        "figure.dpi": DPI_PANTALLA,
        "savefig.bbox": "tight",
        "savefig.dpi": 200,
    })


def guardar(fig, ruta_sin_ext, cerrar: bool = True) -> str:
    """Guarda PNG (para el documento exploratorio) y PDF vectorial (para el paper)."""
    ruta_sin_ext = str(ruta_sin_ext)
    fig.savefig(f"{ruta_sin_ext}.png", dpi=200)
    fig.savefig(f"{ruta_sin_ext}.pdf")
    if cerrar:
        plt.close(fig)
    return f"{ruta_sin_ext}.png"


# ════════════════════════════════════════════════════════════════════════════
# FORMAS
# ════════════════════════════════════════════════════════════════════════════


def violin_por_grupo(df: pd.DataFrame, y: str, titulo: str = "", subtitulo: str = "",
                     ylabel: str = "", ax=None):
    """Distribución por grupo: violín + caja + puntos individuales.

    Con n=10–19 por grupo, los puntos individuales NO son decoración: son la
    única forma honesta de mostrar de cuántas observaciones sale cada resumen.
    """
    creado = ax is None
    if creado:
        fig, ax = plt.subplots(figsize=(4.0, 3.2))
    else:
        fig = ax.figure

    grupos = [g for g in ORDEN_GRUPOS if g in df["Grupo"].unique()]
    datos = [df.loc[df["Grupo"] == g, y].dropna().to_numpy() for g in grupos]
    pos = np.arange(len(grupos))

    partes = ax.violinplot(datos, positions=pos, widths=0.72, showextrema=False)
    for cuerpo, g in zip(partes["bodies"], grupos):
        cuerpo.set_facecolor(COLOR_GRUPO[g])
        cuerpo.set_alpha(0.20)
        cuerpo.set_edgecolor("none")

    bp = ax.boxplot(datos, positions=pos, widths=0.16, showfliers=False,
                    patch_artist=True, medianprops=dict(color=INK, linewidth=1.4),
                    whiskerprops=dict(color=BASELINE, linewidth=0.9),
                    capprops=dict(color=BASELINE, linewidth=0.9))
    for caja in bp["boxes"]:
        caja.set(facecolor=SURFACE, edgecolor=BASELINE, linewidth=0.9)

    rng = np.random.default_rng(11200469)
    for i, (g, d) in enumerate(zip(grupos, datos)):
        jitter = rng.uniform(-0.13, 0.13, len(d))
        ax.scatter(i + jitter, d, s=17, color=COLOR_GRUPO[g], alpha=0.85,
                   linewidth=0.6, edgecolor=SURFACE, zorder=3)

    ax.set_xticks(pos)
    ax.set_xticklabels([f"{ETIQUETA_GRUPO[g]}\nn={len(d)}" for g, d in zip(grupos, datos)])
    ax.set_ylabel(ylabel or y)
    ax.grid(axis="y", alpha=0.6)
    ax.set_axisbelow(True)
    if titulo:
        ax.set_title(titulo, loc="left", color=INK, pad=PAD_TITULO if subtitulo else 6)
    if subtitulo:
        ax.text(0, 1.02, subtitulo, transform=ax.transAxes, fontsize=8,
                color=MUTED, va="bottom")
    return fig, ax


def forest(tabla: pd.DataFrame, col_efecto: str, col_lo: str, col_hi: str,
           col_etiqueta: str, titulo: str = "", subtitulo: str = "",
           xlabel: str = "d de Cohen ajustada (IC 95%)",
           col_destaca: str | None = None, figsize=None):
    """Forest plot de tamaños de efecto con IC.

    Con n pequeño ésta es la figura más informativa del análisis: muestra la
    magnitud y su incertidumbre, en vez de reducir todo a un p. Las filas que
    sobreviven al FDR se marcan con relleno sólido y etiqueta en negrita —
    identidad por forma y peso, no solo por color.
    """
    t = tabla.copy()
    n = len(t)
    fig, ax = plt.subplots(figsize=figsize or (5.6, max(2.2, 0.30 * n + 1.2)))
    y = np.arange(n)[::-1]

    destaca = t[col_destaca].to_numpy() if col_destaca else np.zeros(n, dtype=bool)
    for i, (yy, fila) in enumerate(zip(y, t.itertuples())):
        e = getattr(fila, col_efecto)
        lo, hi = getattr(fila, col_lo), getattr(fila, col_hi)
        # El color codifica la DIRECCIÓN del efecto (polaridad), no el rango.
        color = "#b02b2b" if e > 0 else "#184f95"
        ax.plot([lo, hi], [yy, yy], color=color, linewidth=1.6,
                alpha=0.95 if destaca[i] else 0.45, solid_capstyle="round")
        ax.scatter(e, yy, s=42 if destaca[i] else 26, color=color if destaca[i] else SURFACE,
                   edgecolor=color, linewidth=1.4, zorder=3)

    ax.axvline(0, color=BASELINE, linewidth=1.0, zorder=1)
    ax.set_yticks(y)
    etiquetas = ax.set_yticklabels(t[col_etiqueta])
    for etq, marcado in zip(etiquetas, destaca):
        if marcado:
            etq.set_fontweight("bold")
            etq.set_color(INK)
    ax.set_xlabel(xlabel)
    ax.set_ylim(-0.8, n - 0.2)
    ax.grid(axis="x", alpha=0.6)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    if titulo:
        ax.set_title(titulo, loc="left", color=INK, pad=PAD_TITULO if subtitulo else 6)
    if subtitulo:
        ax.text(0, 1.015, subtitulo, transform=ax.transAxes, fontsize=8,
                color=MUTED, va="bottom")
    return fig, ax


def heatmap_efectos(pivote: pd.DataFrame, titulo: str = "", subtitulo: str = "",
                    cbar_label: str = "d de Cohen ajustada",
                    marcas: pd.DataFrame | None = None, figsize=None):
    """Heatmap ROI × medida de efectos con signo (rampa divergente, cero en gris).

    `marcas` es un DataFrame booleano de la misma forma: marca con · las celdas
    que sobreviven al FDR (identidad por símbolo, no solo por color).
    """
    v = np.nanmax(np.abs(pivote.to_numpy(dtype=float)))
    v = 1.0 if not np.isfinite(v) or v == 0 else v
    fig, ax = plt.subplots(figsize=figsize or (1.05 * len(pivote.columns) + 3.4,
                                               0.30 * len(pivote) + 1.8))
    im = ax.imshow(pivote.to_numpy(dtype=float), cmap=CMAP_DIV,
                   norm=TwoSlopeNorm(vcenter=0, vmin=-v, vmax=v), aspect="auto")

    ax.set_xticks(range(len(pivote.columns)))
    ax.set_xticklabels(pivote.columns)
    ax.set_yticks(range(len(pivote)))
    ax.set_yticklabels(pivote.index)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    # separador de 2px entre celdas: la superficie respira entre marcas
    ax.set_xticks(np.arange(-0.5, len(pivote.columns), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(pivote), 1), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0)

    if marcas is not None:
        for i in range(len(pivote)):
            for j in range(len(pivote.columns)):
                if bool(marcas.iloc[i, j]):
                    ax.text(j, i, "•", ha="center", va="center", fontsize=15,
                            color=INK, zorder=4)

    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label(cbar_label, color=INK_2, fontsize=8.5)
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=2, labelcolor=INK_2, labelsize=8)
    if titulo:
        ax.set_title(titulo, loc="left", color=INK, pad=PAD_TITULO if subtitulo else 6)
    if subtitulo:
        ax.text(0, 1.02, subtitulo, transform=ax.transAxes, fontsize=8,
                color=MUTED, va="bottom")
    return fig, ax


def scatter_estructura_conducta(df: pd.DataFrame, x: str, y: str, titulo: str = "",
                                subtitulo: str = "", xlabel: str = "", ylabel: str = "",
                                recta_por_grupo: bool = True, ax=None):
    """Dispersión estructura ↔ conducta, coloreada por grupo.

    La recta se dibuja **por grupo**, no una sola global: con tres grupos que
    difieren en ambas variables, una recta única puede invertir el signo de la
    relación intra-grupo (paradoja de Simpson). Ver plan §3.2.
    """
    creado = ax is None
    if creado:
        fig, ax = plt.subplots(figsize=(4.3, 3.4))
    else:
        fig = ax.figure

    for g in ORDEN_GRUPOS:
        d = df[(df["Grupo"] == g)][[x, y]].dropna()
        if d.empty:
            continue
        ax.scatter(d[x], d[y], s=30, color=COLOR_GRUPO[g], alpha=0.85,
                   linewidth=0.7, edgecolor=SURFACE, zorder=3,
                   label=f"{ETIQUETA_GRUPO[g]} (n={len(d)})")
        if recta_por_grupo and len(d) >= 4:
            b = np.polyfit(d[x], d[y], 1)
            xs = np.linspace(d[x].min(), d[x].max(), 50)
            ax.plot(xs, np.polyval(b, xs), color=COLOR_GRUPO[g], linewidth=1.5,
                    alpha=0.75, zorder=2)

    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    ax.grid(alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="best", handletextpad=0.4)
    if titulo:
        ax.set_title(titulo, loc="left", color=INK, pad=PAD_TITULO if subtitulo else 6)
    if subtitulo:
        ax.text(0, 1.02, subtitulo, transform=ax.transAxes, fontsize=8,
                color=MUTED, va="bottom")
    return fig, ax


def volcan(tabla: pd.DataFrame, col_efecto: str, col_p: str, col_etiqueta: str,
           col_destaca: str | None = None, titulo: str = "", subtitulo: str = "",
           xlabel: str = "d de Cohen ajustada", n_etiquetas: int = 8):
    """Efecto vs −log₁₀(p). Solo se etiquetan los puntos más extremos: una etiqueta
    en cada punto sería ruido, no información."""
    t = tabla.copy()
    # sin guion bajo inicial: `itertuples` renombra esas columnas a _1, _2, …
    t["logp"] = -np.log10(t[col_p].astype(float).clip(lower=1e-12))
    fig, ax = plt.subplots(figsize=(5.2, 3.8))

    destaca = t[col_destaca].to_numpy() if col_destaca else np.zeros(len(t), dtype=bool)
    ax.scatter(t.loc[~destaca, col_efecto], t.loc[~destaca, "logp"], s=26,
               color=MUTED, alpha=0.55, linewidth=0, label="no sobrevive FDR")
    if destaca.any():
        colores = ["#b02b2b" if e > 0 else "#184f95" for e in t.loc[destaca, col_efecto]]
        ax.scatter(t.loc[destaca, col_efecto], t.loc[destaca, "logp"], s=52,
                   color=colores, linewidth=0.8, edgecolor=SURFACE, zorder=3,
                   label="sobrevive FDR")

    ax.axhline(-np.log10(0.05), color=BASELINE, linewidth=1.0, linestyle=(0, (4, 3)))
    ax.text(ax.get_xlim()[1], -np.log10(0.05), " p=0,05", va="center", fontsize=7.5,
            color=MUTED)
    ax.axvline(0, color=BASELINE, linewidth=0.9)

    extremos = t.reindex(t["logp"].sort_values(ascending=False).index).head(n_etiquetas)
    for fila in extremos.itertuples():
        ax.annotate(getattr(fila, col_etiqueta), (getattr(fila, col_efecto), fila.logp),
                    textcoords="offset points", xytext=(5, 3), fontsize=7, color=INK_2)

    ax.set_xlabel(xlabel)
    ax.set_ylabel("−log₁₀(p)")
    ax.grid(alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left")
    if titulo:
        ax.set_title(titulo, loc="left", color=INK, pad=PAD_TITULO if subtitulo else 6)
    if subtitulo:
        ax.text(0, 1.02, subtitulo, transform=ax.transAxes, fontsize=8,
                color=MUTED, va="bottom")
    return fig, ax


def barras_comparadas(categorias, series: dict[str, list], titulo: str = "",
                      subtitulo: str = "", ylabel: str = "", colores: list | None = None):
    """Barras agrupadas con separación de 2px entre barras adyacentes."""
    fig, ax = plt.subplots(figsize=(max(4.0, 0.9 * len(categorias) + 1.6), 3.1))
    n = len(series)
    ancho = 0.78 / n
    x = np.arange(len(categorias))
    paleta = colores or [COLOR_GRUPO[g] for g in ORDEN_GRUPOS][:n]
    for i, (nombre, valores) in enumerate(series.items()):
        ax.bar(x + (i - (n - 1) / 2) * ancho, valores, ancho * 0.94,
               label=nombre, color=paleta[i % len(paleta)], linewidth=0)
    ax.set_xticks(x)
    ax.set_xticklabels(categorias)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.6)
    ax.set_axisbelow(True)
    if n >= 2:
        ax.legend()
    if titulo:
        ax.set_title(titulo, loc="left", color=INK, pad=PAD_TITULO if subtitulo else 6)
    if subtitulo:
        ax.text(0, 1.02, subtitulo, transform=ax.transAxes, fontsize=8,
                color=MUTED, va="bottom")
    return fig, ax
