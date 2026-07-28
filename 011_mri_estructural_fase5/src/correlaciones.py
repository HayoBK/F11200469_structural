"""
Etapa B — asociación estructura ↔ conducta.

Estadística elegida y por qué (plan §3.2):

· **Spearman parcial.** Se rankean X e Y, se residualizan sobre las covariables y se
  correlacionan los residuos. Robusto a no-normalidad y a outliers, que es lo que hay
  con n<50. Implementado aquí en vez de usar `pingouin` para controlar exactamente
  cómo entran las covariables categóricas (dummies) y para poder reutilizar el mismo
  bootstrap BCa que el resto del proyecto.

· **Dos niveles, siempre ambos.** Global (con `Grupo` como covariable) e intra-grupo.
  ⚠️ Obligatorio por **paradoja de Simpson**: con tres grupos que difieren en estructura
  Y en conducta, una correlación global puede ser un artefacto de la separación entre
  grupos, e incluso tener signo opuesto al de la relación dentro de cada uno.

· **IC 95% bootstrap BCa** y **FDR-BH por familia**, igual que en las etapas A.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from modelos import SEED, _bca


def _residualizar(v: np.ndarray, C: np.ndarray) -> np.ndarray:
    """Residuos de v sobre las covariables C (con intercepto)."""
    beta, *_ = np.linalg.lstsq(C, v, rcond=None)
    return v - C @ beta


def _matriz_covariables(d: pd.DataFrame, covariables: list[str]) -> np.ndarray:
    """Matriz de diseño de covariables, con dummies para las categóricas."""
    partes = [np.ones((len(d), 1))]
    for c in covariables:
        s = d[c]
        if pd.api.types.is_numeric_dtype(s):
            partes.append(s.to_numpy(dtype=float).reshape(-1, 1))
        else:
            dummies = pd.get_dummies(s, drop_first=True).to_numpy(dtype=float)
            if dummies.size:
                partes.append(dummies)
    return np.hstack(partes)


def spearman_parcial(
    datos: pd.DataFrame, x: str, y: str, covariables: list[str],
    n_boot: int = 5_000, seed: int = SEED,
) -> dict:
    """rho de Spearman parcial con IC 95% BCa.

    El p es el paramétrico de la t asociada; el IC viene del bootstrap, que con n
    pequeño es más honesto sobre la incertidumbre real que la aproximación de Fisher.
    """
    cols = [x, y] + covariables
    d = datos[cols].dropna()
    n = len(d)
    k = 0 if not covariables else _matriz_covariables(d, covariables).shape[1] - 1
    if n < 10 + k:
        return {"n": n, "rho": np.nan, "p": np.nan, "ic_low": np.nan, "ic_high": np.nan}

    def rho_de(sub: pd.DataFrame) -> float:
        if sub[x].nunique() < 3 or sub[y].nunique() < 3:
            return np.nan
        rx = stats.rankdata(sub[x].to_numpy())
        ry = stats.rankdata(sub[y].to_numpy())
        if covariables:
            C = _matriz_covariables(sub, covariables)
            rx, ry = _residualizar(rx, C), _residualizar(ry, C)
        if np.std(rx) == 0 or np.std(ry) == 0:
            return np.nan
        return float(np.corrcoef(rx, ry)[0, 1])

    rho = rho_de(d)
    gl = n - 2 - k
    if np.isfinite(rho) and abs(rho) < 1 and gl > 0:
        t = rho * np.sqrt(gl / (1 - rho**2))
        p = float(2 * stats.t.sf(abs(t), gl))
    else:
        p = np.nan

    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    boot = np.array([rho_de(d.iloc[rng.choice(idx, n, replace=True)]) for _ in range(n_boot)])
    jack = np.array([rho_de(d.drop(d.index[i])) for i in range(n)])
    lo, hi = _bca(rho, boot, jack[np.isfinite(jack)])

    return {"n": n, "rho": rho, "p": p, "ic_low": lo, "ic_high": hi}


def correlacion_por_grupo(
    datos: pd.DataFrame, x: str, y: str, covariables: list[str],
    grupos: list[str], n_boot: int = 2_000, seed: int = SEED,
) -> dict:
    """rho intra-grupo. Con n=10–19 es frágil; se reporta con su n a la vista."""
    out = {}
    for g in grupos:
        sub = datos[datos["Grupo"] == g]
        r = spearman_parcial(sub, x, y, covariables, n_boot=n_boot, seed=seed)
        out[f"rho_{g}"] = r["rho"]
        out[f"n_{g}"] = r["n"]
    return out


def barrido(
    datos: pd.DataFrame,
    variables: pd.DataFrame,
    outcomes: list[str],
    covariables: list[str],
    covariables_etiv: list[str] | None = None,
    intra_grupo: bool = True,
    grupos: list[str] | None = None,
    familia: str = "medida_outcome",
    n_boot: int = 3_000,
) -> pd.DataFrame:
    """Correlaciona cada variable estructural con cada outcome.

    `variables` es un plan con columnas: variable, roi, hemi, medida, ajusta_etiv.
    Devuelve una fila por (variable × outcome) con rho global e intra-grupo.
    """
    grupos = grupos or ["MPPP", "Vestibular", "Voluntario Sano"]
    covariables_etiv = covariables_etiv if covariables_etiv is not None else covariables + ["eTIV"]

    filas = []
    for f in variables.itertuples():
        cov = covariables_etiv if bool(f.ajusta_etiv) else covariables
        for outcome in outcomes:
            r = spearman_parcial(datos, f.variable, outcome, cov, n_boot=n_boot)
            fila = {
                "variable": f.variable, "roi": getattr(f, "roi", "—"),
                "hemi": getattr(f, "hemi", "—"), "medida": f.medida,
                "outcome": outcome, "n": r["n"], "rho": r["rho"], "p": r["p"],
                "ic_low": r["ic_low"], "ic_high": r["ic_high"],
                "covariables": "+".join(cov),
            }
            if intra_grupo:
                # Dentro de un grupo, `Grupo` ya no puede ser covariable.
                cov_intra = [c for c in cov if c != "Grupo"]
                fila.update(correlacion_por_grupo(datos, f.variable, outcome,
                                                  cov_intra, grupos, n_boot=1_000))
            filas.append(fila)

    t = pd.DataFrame(filas)
    t["familia_fdr"] = (t["medida"] + "_" + t["outcome"] if familia == "medida_outcome"
                        else t[familia])
    t["etapa"] = "B"
    return t


def coherencia_simpson(tabla: pd.DataFrame, grupos: list[str]) -> pd.DataFrame:
    """¿Coincide el signo de la correlación global con el de las intra-grupo?

    Cuando no coincide, la correlación global es sospechosa de ser un artefacto de
    la separación entre grupos y NO debe interpretarse como una relación individual.
    """
    cols = [f"rho_{g}" for g in grupos if f"rho_{g}" in tabla]
    if not cols:
        return pd.DataFrame()
    signo_global = np.sign(tabla["rho"])
    signos_intra = np.sign(tabla[cols])
    coinciden = signos_intra.eq(signo_global, axis=0).sum(axis=1)
    validos = signos_intra.notna().sum(axis=1)
    t = tabla.copy()
    t["grupos_mismo_signo"] = coinciden
    t["grupos_validos"] = validos
    t["coherente"] = coinciden == validos
    return t
