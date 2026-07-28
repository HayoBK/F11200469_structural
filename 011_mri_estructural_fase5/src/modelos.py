"""
Motor estadístico de la FASE 5 — ANCOVA de 3 grupos con covariables.

Implementa el modelo de `docs/PLAN_ANALISIS_FASE5.md` §2.1:

    medida ~ C(Grupo) + Edad + C(Genero) + N_Educacional  [+ eTIV si volumen/área]

1. **Omnibus** de 3 grupos: F de tipo II, con p paramétrico, p robusto (HC3) y
   **p de permutación (Freedman-Lane)** — este último es el defendible con n=10 en un brazo.
2. **Tamaño de efecto siempre**: η²ₚ para el omnibus, d de Cohen ajustada para los post-hoc,
   ambos con **IC 95% bootstrap BCa estratificado por grupo**.
3. **Post-hoc preespecificados**: MPPP vs Sano y MPPP vs Vestibular (no los tres pares).

Nota de implementación: el ajuste principal usa `statsmodels` (para HC3 y diagnósticos),
pero la permutación y el bootstrap usan álgebra directa en NumPy con las matrices de
proyección precomputadas. Sin eso, 58 pruebas × 10.000 permutaciones × 10.000 bootstraps
sería inviable; con eso, la etapa completa corre en segundos.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from scipy import stats

SEED = 11200469  # el número del proyecto, para que el azar sea reproducible y trazable


# ════════════════════════════════════════════════════════════════════════════
# RESULTADO
# ════════════════════════════════════════════════════════════════════════════


@dataclass
class ResultadoANCOVA:
    variable: str
    n: int
    n_por_grupo: dict[str, int]
    formula: str
    # omnibus
    F: float
    df_num: int
    df_den: int
    p_param: float
    p_hc3: float
    p_perm: float
    eta2p: float
    eta2p_ic: tuple[float, float]
    # post-hoc: contraste -> métricas
    posthoc: dict[str, dict] = field(default_factory=dict)
    # robustez / diagnóstico
    p_kw: float = np.nan  # Kruskal-Wallis crudo, sin covariables
    shapiro_p: float = np.nan  # normalidad de los residuos
    levene_p: float = np.nan  # homocedasticidad entre grupos
    medias_ajustadas: dict[str, float] = field(default_factory=dict)
    medias_crudas: dict[str, float] = field(default_factory=dict)

    def fila(self) -> dict:
        """Aplana el resultado a una fila de tabla (§6 del plan: trazabilidad completa)."""
        f = {
            "variable": self.variable, "n": self.n, "formula": self.formula,
            "F": self.F, "df_num": self.df_num, "df_den": self.df_den,
            "p_param": self.p_param, "p_hc3": self.p_hc3, "p_perm": self.p_perm,
            "eta2p": self.eta2p, "eta2p_ic_low": self.eta2p_ic[0], "eta2p_ic_high": self.eta2p_ic[1],
            "p_kw": self.p_kw, "shapiro_p": self.shapiro_p, "levene_p": self.levene_p,
        }
        for g, v in self.n_por_grupo.items():
            f[f"n_{g}"] = v
        for g, v in self.medias_crudas.items():
            f[f"media_{g}"] = v
        for nombre, d in self.posthoc.items():
            f[f"{nombre}_dif"] = d["diferencia"]
            f[f"{nombre}_d"] = d["d"]
            f[f"{nombre}_d_ic_low"] = d["d_ic"][0]
            f[f"{nombre}_d_ic_high"] = d["d_ic"][1]
            f[f"{nombre}_p"] = d["p"]
        return f


# ════════════════════════════════════════════════════════════════════════════
# NÚCLEO DE ÁLGEBRA
# ════════════════════════════════════════════════════════════════════════════


def _rss(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Suma de cuadrados residual de y ~ X. Vectorizado sobre columnas de y."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    return np.sum(resid**2, axis=0)


def _f_desde_rss(rss1: np.ndarray, rss0: np.ndarray, df_num: int, df_den: int) -> np.ndarray:
    """F del contraste entre modelo completo (1) y reducido (0)."""
    return ((rss0 - rss1) / df_num) / (rss1 / df_den)


def _permutacion_freedman_lane(
    X: np.ndarray, X0: np.ndarray, y: np.ndarray, F_obs: float,
    df_num: int, df_den: int, n_perm: int, rng: np.random.Generator,
) -> float:
    """p de permutación por el método de Freedman-Lane.

    Permuta los residuos del **modelo reducido** (el que no contiene el efecto de
    interés) y los re-suma a sus valores ajustados. Así se destruye el efecto de
    grupo conservando la estructura de las covariables — que es justo lo que hace
    falta cuando el diseño no está balanceado.
    """
    beta0, *_ = np.linalg.lstsq(X0, y, rcond=None)
    ajustado0 = X0 @ beta0
    resid0 = y - ajustado0

    idx = np.argsort(rng.random((len(y), n_perm)), axis=0)  # una permutación por columna
    Y = ajustado0[:, None] + resid0[idx]  # (n, n_perm)

    F_perm = _f_desde_rss(_rss(X, Y), _rss(X0, Y), df_num, df_den)
    # El +1 evita p=0: con n_perm remuestreos, el p mínimo alcanzable es 1/(n_perm+1).
    return float((1 + np.sum(F_perm >= F_obs)) / (1 + n_perm))


def _bca(
    theta_obs: float, theta_boot: np.ndarray, theta_jack: np.ndarray, alpha: float = 0.05
) -> tuple[float, float]:
    """IC bootstrap BCa (corregido por sesgo y acelerado).

    Preferido al percentil simple porque corrige la asimetría de la distribución
    bootstrap — relevante con n pequeño y grupos desbalanceados.
    """
    theta_boot = theta_boot[np.isfinite(theta_boot)]
    if len(theta_boot) < 100:
        return (np.nan, np.nan)

    prop = np.mean(theta_boot < theta_obs)
    prop = min(max(prop, 1e-9), 1 - 1e-9)  # evita z0 infinito
    z0 = stats.norm.ppf(prop)

    jack_mean = np.mean(theta_jack)
    dif = jack_mean - theta_jack
    denom = 6.0 * (np.sum(dif**2) ** 1.5)
    a = np.sum(dif**3) / denom if denom > 0 else 0.0

    def ajusta(z):
        return stats.norm.cdf(z0 + (z0 + z) / (1 - a * (z0 + z)))

    lo = ajusta(stats.norm.ppf(alpha / 2))
    hi = ajusta(stats.norm.ppf(1 - alpha / 2))
    return (
        float(np.percentile(theta_boot, 100 * lo)),
        float(np.percentile(theta_boot, 100 * hi)),
    )


# ════════════════════════════════════════════════════════════════════════════
# ANCOVA
# ════════════════════════════════════════════════════════════════════════════


def construir_formula(
    y: str, covariables: list[str], grupo: str = "Grupo", ajusta_etiv: bool = False,
    referencia: str = "Voluntario Sano",
) -> str:
    """Fórmula patsy. Las covariables categóricas se envuelven en C().

    `referencia` fija el nivel base del factor de grupo. En el análisis de 3 grupos
    es "Voluntario Sano"; en el contraste dirigido MPPP-vs-Vestibular pasa a ser
    "Vestibular", de modo que el coeficiente de grupo se lee directamente como
    "MPPP respecto de Vestibular".
    """
    CATEGORICAS = {"Genero", "Grupo"}
    terminos = [f"C({grupo}, Treatment(reference='{referencia}'))"]
    for c in covariables:
        terminos.append(f"C({c})" if c in CATEGORICAS else c)
    if ajusta_etiv:
        terminos.append("eTIV")
    return f"Q('{y}') ~ " + " + ".join(terminos)


def ancova(
    df: pd.DataFrame,
    y: str,
    covariables: list[str],
    ajusta_etiv: bool = False,
    grupo: str = "Grupo",
    contrastes: list[tuple[str, str]] | None = None,
    referencia: str = "Voluntario Sano",
    n_perm: int = 10_000,
    n_boot: int = 10_000,
    seed: int = SEED,
) -> ResultadoANCOVA:
    """Ajusta la ANCOVA de 3 grupos y devuelve omnibus + post-hoc con efectos e IC.

    Eliminación listwise: el N efectivo se calcula sobre las filas completas en
    `y` y todas las covariables, y se reporta explícitamente (nunca se imputa).
    """
    contrastes = contrastes or [("MPPP", "Voluntario Sano"), ("MPPP", "Vestibular")]
    cols = [y, grupo] + covariables + (["eTIV"] if ajusta_etiv else [])
    d = df[cols].dropna().copy()

    formula = construir_formula(y, covariables, grupo, ajusta_etiv, referencia)
    modelo = sm.OLS.from_formula(formula, data=d).fit()

    # --- matrices de diseño: completa y reducida (sin el efecto de grupo) ---
    yv, X = patsy.dmatrices(formula, d, return_type="dataframe")
    yv = np.asarray(yv).ravel()
    cols_grupo = [c for c in X.columns if c.startswith(f"C({grupo}")]
    X_full = np.asarray(X)
    X_red = np.asarray(X.drop(columns=cols_grupo))

    df_num = len(cols_grupo)
    df_den = len(d) - X_full.shape[1]

    rss1 = float(_rss(X_full, yv))
    rss0 = float(_rss(X_red, yv))

    # Una variable constante (o perfectamente explicada por las covariables) deja
    # RSS = 0 y el modelo deja de estar definido. Pasa en barridos masivos sobre
    # estructuras del aseg que valen lo mismo en todos los sujetos. Se devuelve un
    # resultado vacío en vez de fallar, para no abortar un barrido de miles.
    if not np.isfinite(rss1) or (rss1 + abs(rss0 - rss1)) <= 0:
        return ResultadoANCOVA(
            variable=y, n=len(d), n_por_grupo=d[grupo].value_counts().to_dict(),
            formula=formula, F=np.nan, df_num=df_num, df_den=df_den,
            p_param=np.nan, p_hc3=np.nan, p_perm=np.nan,
            eta2p=np.nan, eta2p_ic=(np.nan, np.nan), posthoc={},
        )

    F = float(_f_desde_rss(np.array([rss1]), np.array([rss0]), df_num, df_den)[0])
    p_param = float(stats.f.sf(F, df_num, df_den))

    # η²ₚ de tipo II = SS_efecto / (SS_efecto + SS_residual)
    ss_efecto = rss0 - rss1
    eta2p = float(ss_efecto / (ss_efecto + rss1))

    # --- omnibus robusto (HC3): test de Wald sobre los coeficientes de grupo ---
    modelo_hc3 = sm.OLS.from_formula(formula, data=d).fit(cov_type="HC3")
    R = np.zeros((df_num, X_full.shape[1]))
    for i, c in enumerate(cols_grupo):
        R[i, list(X.columns).index(c)] = 1.0
    p_hc3 = float(modelo_hc3.f_test(R).pvalue)

    # --- p de permutación (Freedman-Lane) ---
    rng = np.random.default_rng(seed)
    p_perm = _permutacion_freedman_lane(X_full, X_red, yv, F, df_num, df_den, n_perm, rng)

    # --- post-hoc + bootstrap ---
    sigma = float(np.sqrt(rss1 / df_den))
    grupos = d[grupo].to_numpy()
    posthoc = {}
    for a, b in contrastes:
        nombre = f"{a}_vs_{b}".replace(" ", "")
        dif, p_c = _contraste(modelo, X.columns, grupo, a, b)
        d_cohen = dif / sigma
        boot, jack = _remuestrear_d(X_full, yv, grupos, X.columns, grupo, a, b,
                                    df_den, n_boot, seed)
        posthoc[nombre] = {
            "diferencia": dif, "d": d_cohen, "d_ic": _bca(d_cohen, boot, jack), "p": p_c,
        }

    # --- η²ₚ con IC bootstrap ---
    boot_eta, jack_eta = _remuestrear_eta2(X_full, X_red, yv, grupos, df_num, df_den,
                                           n_boot // 2, seed)
    eta2p_ic = _bca(eta2p, boot_eta, jack_eta)

    # --- diagnósticos y robustez no-paramétrica ---
    muestras = [d.loc[d[grupo] == g, y].to_numpy() for g in d[grupo].unique()]
    # Con 2 grupos, Kruskal-Wallis equivale a Mann-Whitney: sirve igual de robustez.
    p_kw = float(stats.kruskal(*muestras).pvalue) if len(muestras) >= 2 else np.nan
    shapiro_p = float(stats.shapiro(modelo.resid).pvalue) if len(d) >= 3 else np.nan
    resid_por_grupo = [modelo.resid[d[grupo].to_numpy() == g] for g in d[grupo].unique()]
    levene_p = float(stats.levene(*resid_por_grupo).pvalue)

    return ResultadoANCOVA(
        variable=y, n=len(d), n_por_grupo=d[grupo].value_counts().to_dict(),
        formula=formula, F=F, df_num=df_num, df_den=df_den,
        p_param=p_param, p_hc3=p_hc3, p_perm=p_perm,
        eta2p=eta2p, eta2p_ic=eta2p_ic, posthoc=posthoc,
        p_kw=p_kw, shapiro_p=shapiro_p, levene_p=levene_p,
        medias_crudas=d.groupby(grupo)[y].mean().to_dict(),
        medias_ajustadas=_medias_ajustadas(modelo, d, grupo, covariables, ajusta_etiv),
    )


def _vector_contraste(columnas, grupo: str, a: str, b: str) -> np.ndarray:
    """Vector c tal que c'β = media(a) − media(b), con codificación Treatment."""
    c = np.zeros(len(columnas))
    for i, col in enumerate(columnas):
        if not col.startswith(f"C({grupo}"):
            continue
        nivel = col.split("T.")[-1].rstrip("]")
        if nivel == a:
            c[i] += 1.0
        if nivel == b:
            c[i] -= 1.0
    return c


def _contraste(modelo, columnas, grupo: str, a: str, b: str) -> tuple[float, float]:
    c = _vector_contraste(columnas, grupo, a, b)
    t = modelo.t_test(c)
    return float(np.squeeze(t.effect)), float(np.squeeze(t.pvalue))


def _remuestrear_d(X, y, grupos, columnas, grupo, a, b, df_den, n_boot, seed):
    """Bootstrap y jackknife de la d ajustada.

    El remuestreo es **estratificado por grupo**: preserva n=17/19/10 y evita
    remuestras degeneradas en las que un grupo desaparece.
    """
    c = _vector_contraste(columnas, grupo, a, b)
    niveles = np.unique(grupos)
    indices = {g: np.where(grupos == g)[0] for g in niveles}
    rng = np.random.default_rng(seed)

    def d_de(idx):
        Xi, yi = X[idx], y[idx]
        try:
            beta, *_ = np.linalg.lstsq(Xi, yi, rcond=None)
        except np.linalg.LinAlgError:
            return np.nan
        resid = yi - Xi @ beta
        gl = len(idx) - Xi.shape[1]
        if gl <= 0:
            return np.nan
        s = np.sqrt(np.sum(resid**2) / gl)
        return float(c @ beta / s) if s > 0 else np.nan

    boot = np.array([
        d_de(np.concatenate([rng.choice(indices[g], len(indices[g]), replace=True)
                             for g in niveles]))
        for _ in range(n_boot)
    ])
    jack = np.array([d_de(np.delete(np.arange(len(y)), i)) for i in range(len(y))])
    return boot, jack[np.isfinite(jack)]


def _remuestrear_eta2(X, X0, y, grupos, df_num, df_den, n_boot, seed):
    niveles = np.unique(grupos)
    indices = {g: np.where(grupos == g)[0] for g in niveles}
    rng = np.random.default_rng(seed + 1)

    def eta_de(idx):
        try:
            r1 = float(_rss(X[idx], y[idx]))
            r0 = float(_rss(X0[idx], y[idx]))
        except np.linalg.LinAlgError:
            return np.nan
        ss = r0 - r1
        return float(ss / (ss + r1)) if (ss + r1) > 0 else np.nan

    boot = np.array([
        eta_de(np.concatenate([rng.choice(indices[g], len(indices[g]), replace=True)
                               for g in niveles]))
        for _ in range(n_boot)
    ])
    jack = np.array([eta_de(np.delete(np.arange(len(y)), i)) for i in range(len(y))])
    return boot, jack[np.isfinite(jack)]


def _medias_ajustadas(modelo, d, grupo, covariables, ajusta_etiv) -> dict[str, float]:
    """Medias marginales estimadas: predicción de cada grupo con las covariables
    fijadas en su valor medio (moda en las categóricas)."""
    base = {}
    for c in covariables + (["eTIV"] if ajusta_etiv else []):
        # pandas 3.0 usa dtype `str` (no `object`) para texto: preguntar por numérico.
        base[c] = d[c].mean() if pd.api.types.is_numeric_dtype(d[c]) else d[c].mode()[0]
    out = {}
    for g in d[grupo].unique():
        fila = pd.DataFrame([{**base, grupo: g}])
        out[g] = float(modelo.predict(fila).iloc[0])
    return out
