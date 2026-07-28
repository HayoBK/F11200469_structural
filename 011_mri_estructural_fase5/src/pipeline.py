"""
Pipeline común de las etapas de comparación entre grupos.

Cada etapa (A1, A2, A3, contraste dirigido…) es el mismo procedimiento sobre un
conjunto distinto de variables. Aquí vive una sola vez: ajustar la ANCOVA de cada
variable, aplicar FDR por familia, medir el enriquecimiento de cada familia y
volcar las figuras estándar al documento.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

import config as cfg
import figuras as fg
import modelos
import multiplicidad as mult

# Los dos modelos que se corren siempre en paralelo (decisión D5 del PI):
# uno sin ajustar por ansiedad/depresión y otro ajustando, cada uno con su FDR.
COVAR_BASE = ["Edad", "Genero", "N_Educacional"]
COVAR_ANSIEDAD = COVAR_BASE + ["STAI_Rasgo", "BDI"]


def correr_bloque(
    datos: pd.DataFrame,
    plan: pd.DataFrame,
    covariables: list[str],
    etiqueta_modelo: str,
    contrastes: list[tuple[str, str]] | None = None,
    referencia: str = "Voluntario Sano",
    n_perm: int = 10_000,
    n_boot: int = 5_000,
    verbose: bool = True,
) -> pd.DataFrame:
    """Ajusta una ANCOVA por fila de `plan` y devuelve la tabla con FDR aplicado.

    `plan` necesita las columnas: variable, etapa, familia_fdr, ajusta_etiv
    (más las descriptivas roi/medida/hemi que se copian al resultado).
    """
    t0 = time.time()
    filas = []
    for i, f in enumerate(plan.itertuples(), 1):
        r = modelos.ancova(
            datos, f.variable, covariables, ajusta_etiv=bool(f.ajusta_etiv),
            contrastes=contrastes, referencia=referencia,
            n_perm=n_perm, n_boot=n_boot, seed=modelos.SEED + i,
        )
        fila = r.fila()
        for c in plan.columns:
            if c not in fila:
                fila[c] = getattr(f, c)
        fila["modelo"] = etiqueta_modelo
        filas.append(fila)
        if verbose and i % 25 == 0:
            print(f"   [{etiqueta_modelo}] {i}/{len(plan)}  ({time.time()-t0:.0f}s)")

    t = pd.DataFrame(filas)
    t = mult.aplicar_fdr(t, col_p="p_perm", familia=["etapa", "familia_fdr"])
    if verbose:
        print(f"   [{etiqueta_modelo}] {len(plan)} pruebas en {time.time()-t0:.0f}s · "
              f"sobreviven al FDR: {int(t.sobrevive_fdr.sum())}")
    return t


def enriquecimiento_de_familias(
    datos: pd.DataFrame, plan: pd.DataFrame, covariables: list[str],
    grupos: list[str] | None = None, n_perm: int = 2_000,
) -> pd.DataFrame:
    """Test de enriquecimiento (permutación a nivel de familia) para cada familia."""
    d = datos if grupos is None else datos[datos["Grupo"].isin(grupos)]
    out = []
    for familia, sub in plan.groupby("familia_fdr"):
        r = mult.enriquecimiento_familia(
            d, sub["variable"].tolist(), covariables,
            ajusta_etiv=bool(sub["ajusta_etiv"].iloc[0]), n_perm=n_perm,
        )
        r["familia"] = familia
        out.append(r)
    cols = ["familia", "n_pruebas", "n_efectivo", "n_observado_p<0.05",
            "esperado_por_azar", "p_enriquecimiento"]
    return pd.DataFrame(out)[cols].sort_values("p_enriquecimiento")


def resumen_direccional(tabla: pd.DataFrame, col_d: str) -> pd.DataFrame:
    """Cuántos efectos apuntan en la misma dirección dentro de cada familia.

    Con n pequeño, la **consistencia direccional** de una familia entera suele ser
    más informativa que cualquier p individual: 14/14 efectos negativos dice algo
    que ningún test aislado captura.
    """
    out = []
    for familia, s in tabla.groupby("familia_fdr"):
        d = s[col_d].dropna()
        out.append({
            "familia": familia, "n": len(d),
            "d_mediana": d.median(),
            "n_negativos": int((d < 0).sum()),
            "n_positivos": int((d > 0).sum()),
            "consistencia": f"{max((d < 0).sum(), (d > 0).sum())}/{len(d)}",
            "d_min": d.min(), "d_max": d.max(),
        })
    return pd.DataFrame(out)


COLS_VISTA = [
    "roi", "hemi", "medida", "n", "F", "eta2p", "eta2p_ic_low", "eta2p_ic_high",
    "p_param", "p_perm", "p_fdr", "p_kw", "sobrevive_fdr",
]


def figuras_estandar(
    tabla: pd.DataFrame, datos: pd.DataFrame, carpeta, etapa: str,
    contraste_principal: str, etiqueta_contraste: str,
    contraste_secundario: str | None = None, etiqueta_secundario: str = "",
    medidas: list[str] | None = None, n_violines: int = 6,
) -> dict:
    """Genera el juego estándar de figuras de una etapa y devuelve sus rutas.

    `contraste_principal` es el prefijo de columna, p. ej. "MPPP_vs_Vestibular".
    """
    carpeta.mkdir(parents=True, exist_ok=True)
    medidas = medidas or [m for m in ["LGI", "thickness", "volume", "area"]
                          if m in tabla["medida"].unique()]
    salidas: dict = {"forest": [], "violines": []}

    def cols(pref):
        return f"{pref}_d", f"{pref}_d_ic_low", f"{pref}_d_ic_high"

    for medida in medidas:
        sub = tabla[tabla.medida == medida].copy()
        if sub.empty:
            continue
        sub["etiqueta"] = sub["roi"] + "  " + sub["hemi"]
        for pref, etq in [(contraste_principal, etiqueta_contraste)] + (
                [(contraste_secundario, etiqueta_secundario)] if contraste_secundario else []):
            c_d, c_lo, c_hi = cols(pref)
            if c_d not in sub:
                continue
            s = sub.sort_values(c_d)
            fig, _ = fg.forest(
                s, c_d, c_lo, c_hi, "etiqueta", col_destaca="sobrevive_fdr",
                titulo=f"{etq} · {medida}",
                subtitulo=f"d ajustada con IC 95% BCa · familia de {len(s)} pruebas · "
                          f"N={int(s['n'].iloc[0])}",
            )
            salidas["forest"].append(
                (fg.guardar(fig, carpeta / f"forest_{medida}_{pref}"),
                 f"{etq} · {medida}", "")
            )

    # heatmap ROI × medida
    t = tabla.copy()
    t["fila"] = t["roi"] + "  " + t["hemi"]
    c_d = f"{contraste_principal}_d"
    piv = t.pivot_table(index="fila", columns="medida", values=c_d)
    marcas = (t.pivot_table(index="fila", columns="medida", values="sobrevive_fdr",
                            aggfunc="max")
              .reindex(index=piv.index, columns=piv.columns).fillna(0))
    fig, _ = fg.heatmap_efectos(
        piv, titulo=f"{etapa} · tamaño de efecto {etiqueta_contraste}",
        subtitulo="d de Cohen ajustada · rojo = mayor en el primer grupo · "
                  "• = sobrevive al FDR de su familia",
        marcas=marcas,
    )
    salidas["heatmap"] = fg.guardar(fig, carpeta / f"heatmap_{contraste_principal}")

    # volcán
    t["etiqueta_corta"] = (t["roi"].str.slice(0, 14) + " " + t["hemi"] + " "
                           + t["medida"].str.slice(0, 4))
    fig, _ = fg.volcan(t, c_d, "p_perm", "etiqueta_corta", col_destaca="sobrevive_fdr",
                       titulo=f"{etapa} · {len(t)} pruebas · efecto vs evidencia",
                       subtitulo=f"p de permutación (Freedman-Lane) · {etiqueta_contraste}")
    salidas["volcan"] = fg.guardar(fig, carpeta / f"volcan_{contraste_principal}")

    # violines de las pruebas con menor p
    for f in tabla.sort_values("p_perm").head(n_violines).itertuples():
        fig, _ = fg.violin_por_grupo(
            datos, f.variable,
            titulo=f"{f.roi} · {f.hemi} · {f.medida}",
            subtitulo=(f"eta2p={f.eta2p:.3f} · p(perm)={f.p_perm:.4f} · "
                       f"p(FDR)={float(f.p_fdr):.3f} · N={f.n}"),
            ylabel=f.medida,
        )
        salidas["violines"].append(
            (fg.guardar(fig, carpeta / f"violin_{f.variable}"),
             f"{f.roi} {f.hemi} · {f.medida}", "")
        )
    return salidas


def indice_compuesto(datos: pd.DataFrame, variables: list[str],
                     metodo: str = "z") -> pd.Series:
    """Colapsa un conjunto de ROIs en un solo índice de red (análisis C1).

    `z`   → media de los z-scores de cada ROI (interpretable, robusto, sin pesos
            estimados de los datos).
    `pca` → primer componente principal sobre las ROIs estandarizadas (recoge más
            varianza, pero el signo y los pesos dependen de la muestra).

    Colapsar 14 pruebas en 1 multiplica la potencia y responde la hipótesis tal
    como está formulada — "la red DCNN está alterada" — en vez de preguntarla
    ROI por ROI.
    """
    X = datos[variables].dropna()
    Z = (X - X.mean()) / X.std(ddof=1)
    if metodo == "z":
        s = Z.mean(axis=1)
    elif metodo == "pca":
        U, S, Vt = np.linalg.svd(Z - Z.mean(), full_matrices=False)
        pc1 = U[:, 0] * S[0]
        # Orienta el componente para que correlacione positivo con la media de z:
        # sin esto el signo del PC1 es arbitrario y el resultado se lee al revés.
        if np.corrcoef(pc1, Z.mean(axis=1))[0, 1] < 0:
            pc1 = -pc1
        s = pd.Series(pc1, index=Z.index)
    else:
        raise ValueError(metodo)
    return s.reindex(datos.index)
