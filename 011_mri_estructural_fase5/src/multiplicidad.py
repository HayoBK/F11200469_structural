"""
Corrección por comparaciones múltiples — FDR estructurado POR FAMILIA.

Regla del proyecto (`06_ROIs_apriori_DCNN.md` §4.2 y plan §2.2):
**Benjamini-Hochberg dentro de cada familia de medida, nunca todo junto.**

Una familia = una medida (grosor / área / volumen / LGI) dentro de una etapa.
El LGI —hipótesis ancla (Nigro)— se corrige así en su propia familia y no lo
diluyen las otras tres medidas. A1 (Prioridad Alta) y A2 (Media) se corrigen por
separado: son confirmatorio primario y secundario, no una sola familia de 136.

Nunca se corrige sobre las 2.530 columnas de ROI: los tres atlas son tres
parcelaciones del mismo manto cortical y están fuertemente correlacionados
(`06_ESPECIFICACION_TABLA_MAESTRA.md` §5.4).
"""

from __future__ import annotations

import pandas as pd
from statsmodels.stats.multitest import multipletests

ALPHA = 0.05


def aplicar_fdr(
    tabla: pd.DataFrame,
    col_p: str = "p_perm",
    familia: str | list[str] = "familia_fdr",
    alpha: float = ALPHA,
    sufijo: str = "",
) -> pd.DataFrame:
    """Añade `p_fdr{sufijo}` y `sobrevive_fdr{sufijo}`, corrigiendo dentro de cada familia.

    `familia` puede ser una columna o varias (p. ej. ["etapa", "familia_fdr"] para
    que A1 y A2 se corrijan por separado aunque compartan el nombre de la medida).

    Se corrige sobre `p_perm` por defecto: es el p defendible con n=10 en un brazo.
    Las columnas `p_param`/`p_hc3` quedan en la tabla para comparación, sin corregir.
    """
    t = tabla.copy()
    claves = [familia] if isinstance(familia, str) else list(familia)
    t[f"p_fdr{sufijo}"] = pd.NA
    t[f"sobrevive_fdr{sufijo}"] = False
    t[f"n_familia{sufijo}"] = pd.NA

    for _, idx in t.groupby(claves, dropna=False).groups.items():
        p = t.loc[idx, col_p].astype(float)
        validos = p.notna()
        if not validos.any():
            continue
        rechaza, p_corr, _, _ = multipletests(p[validos].to_numpy(), alpha=alpha, method="fdr_bh")
        t.loc[p[validos].index, f"p_fdr{sufijo}"] = p_corr
        t.loc[p[validos].index, f"sobrevive_fdr{sufijo}"] = rechaza
        t.loc[idx, f"n_familia{sufijo}"] = int(validos.sum())

    return t


def enriquecimiento_familia(
    datos: pd.DataFrame,
    variables: list[str],
    covariables: list[str],
    grupo: str = "Grupo",
    ajusta_etiv: bool = False,
    alpha_nominal: float = 0.05,
    n_perm: int = 2_000,
    seed: int = 11200469,
) -> dict:
    """¿Está la familia ENTERA enriquecida en efectos, aunque ninguna prueba
    sobreviva individualmente al FDR?

    Pregunta distinta de la del FDR. El FDR pregunta "¿qué ROI concreta puedo
    declarar?"; esto pregunta "¿hay más señal en esta familia de la que habría por
    azar?". Con n=46 y 14 pruebas correlacionadas, una familia puede estar
    claramente enriquecida sin que ninguna prueba individual aguante la corrección.

    El nulo se construye **permutando la etiqueta de grupo una sola vez por
    remuestreo y aplicándola a todas las variables de la familia a la vez**, de modo
    que se preserva la correlación entre ROIs, hemisferios y medidas. Un test
    binomial sobre los p asumiría independencia y sería anticonservador.

    Devuelve el número observado de p<α, la media esperada bajo el nulo y un p
    de permutación para ese conteo.
    """
    import numpy as np
    import patsy
    from scipy import stats

    cols = list(variables) + [grupo] + covariables + (["eTIV"] if ajusta_etiv else [])
    d = datos[cols].dropna()

    terminos = []
    for c in covariables:
        terminos.append(f"C({c})" if c in {"Genero"} else c)
    if ajusta_etiv:
        terminos.append("eTIV")
    rhs_cov = " + ".join(terminos) if terminos else "1"

    X0 = np.asarray(patsy.dmatrix(rhs_cov, d, return_type="dataframe"))
    Xg = np.asarray(patsy.dmatrix(f"C({grupo}) - 1", d, return_type="dataframe"))[:, 1:]
    Y = d[variables].to_numpy(dtype=float)

    n, k = Y.shape
    df_num = Xg.shape[1]
    df_den = n - (X0.shape[1] + df_num)

    def conteo(Xgrupo) -> int:
        X = np.hstack([X0, Xgrupo])
        rss1 = _rss_multi(X, Y)
        rss0 = _rss_multi(X0, Y)
        F = ((rss0 - rss1) / df_num) / (rss1 / df_den)
        return int(np.sum(stats.f.sf(F, df_num, df_den) < alpha_nominal))

    obs = conteo(Xg)
    rng = np.random.default_rng(seed)
    nulo = np.array([conteo(Xg[rng.permutation(n)]) for _ in range(n_perm)])

    return {
        "n_pruebas": k,
        "n_observado_p<0.05": obs,
        "esperado_por_azar": float(np.mean(nulo)),
        "p_enriquecimiento": float((1 + np.sum(nulo >= obs)) / (1 + n_perm)),
        "n_efectivo": n,
    }


def _rss_multi(X, Y):
    """Suma de cuadrados residual de cada columna de Y sobre X."""
    import numpy as np

    beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
    return np.sum((Y - X @ beta) ** 2, axis=0)


def resumen_familias(tabla: pd.DataFrame, familia: str | list[str] = "familia_fdr",
                     sufijo: str = "") -> pd.DataFrame:
    """Cuántas pruebas hay por familia y cuántas sobreviven. Va al reporte."""
    claves = [familia] if isinstance(familia, str) else list(familia)
    g = tabla.groupby(claves, dropna=False)
    out = pd.DataFrame({
        "n_pruebas": g.size(),
        "n_p_nominal_005": g.apply(lambda d: int((d["p_perm"].astype(float) < 0.05).sum()),
                                   include_groups=False),
        f"n_sobrevive_fdr{sufijo}": g[f"sobrevive_fdr{sufijo}"].sum(),
    }).reset_index()
    # Bajo H0 se esperarían ~5% de p nominales <0,05 por azar: útil como referencia.
    out["esperado_por_azar"] = (out["n_pruebas"] * 0.05).round(1)
    return out
