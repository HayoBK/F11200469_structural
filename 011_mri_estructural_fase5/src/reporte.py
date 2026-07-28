"""
Acumulador del MEGA-DOCUMENTO exploratorio (plan §5, Etapa E).

Cada etapa del análisis anexa su sección: pregunta, método, N efectivo, tabla
completa de resultados y **todas** las figuras candidatas. Deliberadamente
excesivo: es la superficie de elección visual del PI, no el paper.

- Se regenera con un comando; nunca se edita a mano.
- Las imágenes van embebidas en base64 → el HTML es un solo archivo portable.
- **No se versiona** (pesado). Al repo van solo las figuras elegidas, a `figs/`.
"""

from __future__ import annotations

import base64
import datetime as dt
import html
from pathlib import Path

import pandas as pd

CSS = """
:root {
  --surface: #fcfcfb; --plane: #f9f9f7; --ink: #0b0b0b; --ink2: #52514e;
  --muted: #898781; --grid: #e1e0d9; --rule: #c3c2b7;
  --sano: #2a78d6; --vest: #1baf7a; --mppp: #eb6834;
}
@media (prefers-color-scheme: dark) {
  :root { --surface: #1a1a19; --plane: #0d0d0d; --ink: #fff; --ink2: #c3c2b7;
          --grid: #2c2c2a; --rule: #383835; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--plane); color: var(--ink);
       font: 15px/1.65 system-ui, -apple-system, "Segoe UI", sans-serif; }
.wrap { max-width: 1180px; margin: 0 auto; padding: 40px 28px 100px; }
header.doc { border-bottom: 2px solid var(--rule); padding-bottom: 22px; margin-bottom: 34px; }
header.doc h1 { font-size: 27px; margin: 0 0 6px; letter-spacing: -0.02em; }
header.doc .sub { color: var(--ink2); font-size: 14px; }
header.doc .meta { color: var(--muted); font-size: 12.5px; margin-top: 10px; }
section.etapa { background: var(--surface); border: 1px solid var(--grid);
                border-radius: 12px; padding: 26px 28px; margin-bottom: 26px; }
section.etapa > h2 { font-size: 20px; margin: 0 0 4px; letter-spacing: -0.01em; }
section.etapa > .lead { color: var(--ink2); margin: 0 0 20px; font-size: 14px; }
h3 { font-size: 15px; margin: 28px 0 10px; color: var(--ink);
     text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; }
h3:first-of-type { margin-top: 6px; }
p { margin: 0 0 12px; }
.nota { border-left: 3px solid var(--rule); padding: 2px 0 2px 14px;
        color: var(--ink2); font-size: 14px; margin: 14px 0; }
.nota.alerta { border-left-color: var(--mppp); }
.tabla-scroll { overflow-x: auto; margin: 12px 0 18px; }
table { border-collapse: collapse; font-size: 12.5px; font-variant-numeric: tabular-nums;
        min-width: 100%; }
th, td { padding: 6px 11px; text-align: right; border-bottom: 1px solid var(--grid);
         white-space: nowrap; }
th { color: var(--ink2); font-weight: 600; text-align: right; position: sticky; top: 0;
     background: var(--surface); border-bottom: 1.5px solid var(--rule); }
td:first-child, th:first-child { text-align: left; }
tbody tr:hover { background: var(--plane); }
tr.destaca td { font-weight: 650; }
tr.destaca td:first-child::before { content: "● "; color: var(--mppp); }
figure { margin: 0 0 22px; }
figure img { max-width: 100%; height: auto; display: block;
             border: 1px solid var(--grid); border-radius: 8px; background: #fcfcfb; }
figcaption { color: var(--ink2); font-size: 12.5px; margin-top: 8px; }
figcaption b { color: var(--ink); font-weight: 600; }
.galeria { display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr));
           gap: 20px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 18px; }
.chip { background: var(--plane); border: 1px solid var(--grid); border-radius: 999px;
        padding: 4px 13px; font-size: 12.5px; color: var(--ink2); }
.chip b { color: var(--ink); font-weight: 600; }
nav.toc { background: var(--surface); border: 1px solid var(--grid); border-radius: 12px;
          padding: 18px 24px; margin-bottom: 26px; }
nav.toc ol { margin: 0; padding-left: 20px; }
nav.toc a { color: var(--ink); text-decoration: none; }
nav.toc a:hover { text-decoration: underline; }
code { background: var(--plane); border: 1px solid var(--grid); border-radius: 4px;
       padding: 1px 5px; font-size: 12.5px; }
"""


class Reporte:
    """Documento HTML acumulativo. Cada etapa llama a `seccion()` y luego a
    `texto/nota/tabla/figura`; al final `escribir()`."""

    def __init__(self, titulo: str, subtitulo: str = ""):
        self.titulo = titulo
        self.subtitulo = subtitulo
        self.partes: list[str] = []
        self.secciones: list[tuple[str, str]] = []
        self._n = 0

    # ── estructura ──────────────────────────────────────────────────────────
    def seccion(self, titulo: str, lead: str = "") -> "Reporte":
        self._n += 1
        sid = f"s{self._n}"
        self.secciones.append((sid, titulo))
        if self._n > 1:
            self.partes.append("</section>")
        self.partes.append(
            f'<section class="etapa" id="{sid}"><h2>{html.escape(titulo)}</h2>'
            + (f'<p class="lead">{html.escape(lead)}</p>' if lead else "")
        )
        return self

    def h3(self, texto: str) -> "Reporte":
        self.partes.append(f"<h3>{html.escape(texto)}</h3>")
        return self

    def texto(self, txt: str) -> "Reporte":
        self.partes.append(f"<p>{txt}</p>")
        return self

    def nota(self, txt: str, alerta: bool = False) -> "Reporte":
        cls = "nota alerta" if alerta else "nota"
        self.partes.append(f'<div class="{cls}">{txt}</div>')
        return self

    def chips(self, pares: dict[str, str]) -> "Reporte":
        cs = "".join(f'<span class="chip">{html.escape(k)} <b>{html.escape(str(v))}</b></span>'
                     for k, v in pares.items())
        self.partes.append(f'<div class="chips">{cs}</div>')
        return self

    # ── contenido ───────────────────────────────────────────────────────────
    def tabla(self, df: pd.DataFrame, destacar: str | None = None,
              decimales: int = 3, max_filas: int | None = None) -> "Reporte":
        d = df if max_filas is None else df.head(max_filas)
        marcas = d[destacar].fillna(False).to_numpy() if destacar and destacar in d else None
        d = d.drop(columns=[destacar]) if destacar and destacar in d else d

        enc = "".join(f"<th>{html.escape(str(c))}</th>" for c in d.columns)
        filas = []
        for i, (_, fila) in enumerate(d.iterrows()):
            celdas = []
            for v in fila:
                if isinstance(v, float):
                    txt = "—" if pd.isna(v) else (
                        f"{v:.2e}" if (v != 0 and abs(v) < 10 ** -decimales) else f"{v:.{decimales}f}")
                else:
                    txt = "—" if pd.isna(v) else str(v)
                celdas.append(f"<td>{html.escape(txt)}</td>")
            cls = ' class="destaca"' if marcas is not None and bool(marcas[i]) else ""
            filas.append(f"<tr{cls}>{''.join(celdas)}</tr>")
        self.partes.append(
            f'<div class="tabla-scroll"><table><thead><tr>{enc}</tr></thead>'
            f"<tbody>{''.join(filas)}</tbody></table></div>"
        )
        return self

    def figura(self, ruta_png, titulo: str = "", pie: str = "") -> "Reporte":
        p = Path(ruta_png)
        if not p.exists():
            self.partes.append(f'<div class="nota alerta">Falta la figura: {p}</div>')
            return self
        b64 = base64.b64encode(p.read_bytes()).decode()
        cap = ""
        if titulo or pie:
            cap = (f"<figcaption>{'<b>' + html.escape(titulo) + '.</b> ' if titulo else ''}"
                   f"{pie}</figcaption>")
        self.partes.append(
            f'<figure><img src="data:image/png;base64,{b64}" alt="{html.escape(titulo)}">{cap}</figure>'
        )
        return self

    def galeria(self, figuras: list[tuple], columnas_min: int = 330) -> "Reporte":
        """Varias figuras en rejilla. `figuras` = [(ruta, titulo, pie), ...]"""
        self.partes.append('<div class="galeria">')
        for f in figuras:
            self.figura(*f)
        self.partes.append("</div>")
        return self

    # ── salida ──────────────────────────────────────────────────────────────
    def escribir(self, ruta) -> Path:
        if self._n:
            self.partes.append("</section>")
        toc = "".join(f'<li><a href="#{sid}">{html.escape(t)}</a></li>'
                      for sid, t in self.secciones)
        ahora = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(self.titulo)}</title><style>{CSS}</style></head>
<body><div class="wrap">
<header class="doc">
  <h1>{html.escape(self.titulo)}</h1>
  <div class="sub">{html.escape(self.subtitulo)}</div>
  <div class="meta">Generado {ahora} · FONDECYT 11200469 · documento exploratorio,
  no es el manuscrito · contiene solo resultados agregados</div>
</header>
<nav class="toc"><ol>{toc}</ol></nav>
{''.join(self.partes)}
</div></body></html>"""
        ruta = Path(ruta)
        ruta.write_text(doc, encoding="utf-8")
        return ruta
