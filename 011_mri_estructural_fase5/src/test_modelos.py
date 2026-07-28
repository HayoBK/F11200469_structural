"""
Tests del motor estadístico sobre DATOS SINTÉTICOS con efectos conocidos.

Se ejecutan antes de tocar los datos reales: si la ANCOVA, la permutación o los IC
están mal implementados, hay que descubrirlo aquí y no depurando sobre la muestra.

Ejecutar:  ~/FS_FONDECYT/.venv/bin/python src/test_modelos.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

import modelos

RNG = np.random.default_rng(20260728)
N_POR_GRUPO = {"MPPP": 17, "Vestibular": 19, "Voluntario Sano": 10}  # el diseño real
COVARIABLES = ["Edad", "Genero", "N_Educacional"]


def muestra_sintetica(efecto: dict[str, float], sigma: float = 1.0, n_extra: int = 0,
                      rng=RNG) -> pd.DataFrame:
    """Genera una muestra con la misma estructura que la real y un efecto de grupo conocido.

    y = efecto[grupo] + 0.03*Edad + 0.5*(Genero=='M') + 0.2*N_Educacional + ruido
    """
    filas = []
    for g, n in N_POR_GRUPO.items():
        for _ in range(n + n_extra):
            edad = rng.uniform(21, 65)
            genero = rng.choice(["Femenino", "Masculino"], p=[0.74, 0.26])
            educ = rng.integers(2, 5)
            y = (efecto[g] + 0.03 * edad + 0.5 * (genero == "Masculino")
                 + 0.2 * educ + rng.normal(0, sigma))
            filas.append({"Grupo": g, "Edad": edad, "Genero": genero,
                          "N_Educacional": educ, "y": y})
    return pd.DataFrame(filas)


def ok(cond: bool, msg: str) -> bool:
    print(f"  {'✅' if cond else '❌'} {msg}")
    return cond


# ════════════════════════════════════════════════════════════════════════════


def test_error_tipo_I(n_sim: int = 300) -> bool:
    """Bajo H0 los p deben ser ~uniformes y rechazar ~5% de las veces."""
    print("\n[1] Error tipo I bajo H0 (sin efecto de grupo)")
    nulo = {g: 0.0 for g in N_POR_GRUPO}
    p_param, p_perm = [], []
    for i in range(n_sim):
        d = muestra_sintetica(nulo, rng=np.random.default_rng(1000 + i))
        r = modelos.ancova(d, "y", COVARIABLES, n_perm=500, n_boot=200, seed=1000 + i)
        p_param.append(r.p_param)
        p_perm.append(r.p_perm)
    p_param, p_perm = np.array(p_param), np.array(p_perm)

    tasa_par = np.mean(p_param < 0.05)
    tasa_perm = np.mean(p_perm < 0.05)
    ks = stats.kstest(p_param, "uniform").pvalue
    print(f"     tasa de rechazo paramétrica  = {tasa_par:.3f}  (esperado ≈0.05)")
    print(f"     tasa de rechazo permutación  = {tasa_perm:.3f}  (esperado ≈0.05)")
    print(f"     KS de uniformidad de p       = {ks:.3f}  (debe ser > 0.05)")
    return all([
        ok(0.02 < tasa_par < 0.09, "el test paramétrico controla el error tipo I"),
        ok(0.02 < tasa_perm < 0.09, "la permutación controla el error tipo I"),
        ok(ks > 0.05, "los p son uniformes bajo H0"),
    ])


def test_recupera_efecto() -> bool:
    """Con un efecto grande y conocido, debe detectarlo y estimar bien la d."""
    print("\n[2] Recuperación de un efecto conocido")
    # MPPP 1.0 DE por debajo de Sano; Vestibular intermedio (0.5).
    efecto = {"MPPP": -1.0, "Vestibular": -0.5, "Voluntario Sano": 0.0}
    d = muestra_sintetica(efecto, sigma=1.0, n_extra=30, rng=np.random.default_rng(7))
    r = modelos.ancova(d, "y", COVARIABLES, n_perm=2000, n_boot=2000, seed=7)

    ph = r.posthoc["MPPP_vs_VoluntarioSano"]
    print(f"     p_param={r.p_param:.2e}  p_perm={r.p_perm:.4f}  η²ₚ={r.eta2p:.3f}")
    print(f"     d(MPPP−Sano) = {ph['d']:.3f}  IC95% [{ph['d_ic'][0]:.3f}, {ph['d_ic'][1]:.3f}]"
          f"   (verdadero = −1.0)")
    ph2 = r.posthoc["MPPP_vs_Vestibular"]
    print(f"     d(MPPP−Vest) = {ph2['d']:.3f}   (verdadero = −0.5)")
    return all([
        ok(r.p_param < 0.001, "detecta el efecto (paramétrico)"),
        ok(r.p_perm < 0.01, "detecta el efecto (permutación)"),
        ok(abs(ph["d"] - (-1.0)) < 0.25, "estima bien d(MPPP−Sano)"),
        ok(abs(ph2["d"] - (-0.5)) < 0.25, "estima bien d(MPPP−Vestibular)"),
        ok(ph["d_ic"][0] < -1.0 < ph["d_ic"][1], "el IC BCa cubre el valor verdadero"),
    ])


def test_signo_contrastes() -> bool:
    """El signo del contraste debe ser el correcto: a − b, no b − a."""
    print("\n[3] Orientación de los contrastes")
    efecto = {"MPPP": 5.0, "Vestibular": 0.0, "Voluntario Sano": 0.0}
    d = muestra_sintetica(efecto, rng=np.random.default_rng(3))
    r = modelos.ancova(d, "y", COVARIABLES, n_perm=500, n_boot=500, seed=3)
    dif_sano = r.posthoc["MPPP_vs_VoluntarioSano"]["diferencia"]
    dif_vest = r.posthoc["MPPP_vs_Vestibular"]["diferencia"]
    print(f"     MPPP−Sano = {dif_sano:+.2f}   MPPP−Vest = {dif_vest:+.2f}  (verdadero +5)")
    return all([
        ok(3.5 < dif_sano < 6.5, "MPPP−Sano tiene el signo y la magnitud correctos"),
        ok(3.5 < dif_vest < 6.5, "MPPP−Vestibular tiene el signo y la magnitud correctos"),
    ])


def test_ancova_ajusta_covariable(n_sim: int = 300) -> bool:
    """Un efecto de grupo FALSO, inducido solo por confusión con la edad, debe desaparecer
    al ajustar. Es la prueba de que la ANCOVA está haciendo su trabajo.

    Se evalúa sobre RÉPLICAS, no sobre una simulación única: en cualquier muestra
    concreta el p ajustado puede caer bajo 0,05 por azar (y debe hacerlo ~5% de las
    veces). Lo que prueba que el ajuste funciona es que la **tasa de rechazo** vuelva
    al nominal, no que un p suelto sea alto.

    Se prueban dos escenarios de separación en edad, incluido uno con solapamiento
    casi nulo entre grupos — el caso en que la ANCOVA extrapola y es más frágil
    (Miller & Chapman, 2001).
    """
    print("\n[4] La ANCOVA elimina la confusión por edad (tasa sobre réplicas)")
    # `confusion_fuerte` dice si el escenario debe producir un efecto espurio
    # casi siempre. En el escenario realista la diferencia de edad entre grupos
    # (3-5 años) es pequeña frente a la DE (12), así que la confusión es leve y
    # exigir que aparezca "casi siempre" sería un umbral mal puesto, no un fallo.
    escenarios = {
        "grupos muy separados (58/45/32, DE=5)": ({"MPPP": 58, "Vestibular": 45,
                                                   "Voluntario Sano": 32}, 5, True),
        "como los datos reales (48/45/43, DE=12)": ({"MPPP": 48, "Vestibular": 45,
                                                     "Voluntario Sano": 43}, 12, False),
    }
    checks = []
    for etiqueta, (edad_media, sd, confusion_fuerte) in escenarios.items():
        p_crudo, p_ajustado = [], []
        for i in range(n_sim):
            rng = np.random.default_rng(4000 + i)
            filas = []
            for g, n in N_POR_GRUPO.items():
                for _ in range(n):
                    edad = rng.normal(edad_media[g], sd)
                    # y depende SOLO de la edad; no hay efecto real de grupo.
                    filas.append({"Grupo": g, "Edad": edad,
                                  "y": 0.08 * edad + rng.normal(0, 0.5)})
            d = pd.DataFrame(filas)
            p_crudo.append(stats.kruskal(*[d.loc[d.Grupo == g, "y"]
                                           for g in N_POR_GRUPO]).pvalue)
            p_ajustado.append(modelos.ancova(d, "y", ["Edad"], n_perm=1, n_boot=1,
                                             seed=4000 + i).p_param)
        tasa_cruda = np.mean(np.array(p_crudo) < 0.05)
        tasa_aj = np.mean(np.array(p_ajustado) < 0.05)
        ks = stats.kstest(p_ajustado, "uniform").pvalue
        print(f"     {etiqueta}")
        print(f"       sin ajustar → rechaza {tasa_cruda:.1%} de las veces (efecto espurio)")
        print(f"       ajustando   → rechaza {tasa_aj:.1%}  (esperado ≈5%), KS={ks:.3f}")
        e = etiqueta[:22]
        checks += [
            ok(tasa_cruda > 0.90 if confusion_fuerte else tasa_cruda > tasa_aj,
               f"[{e}…] sin ajustar aparece el efecto espurio"
               + ("" if confusion_fuerte else " (confusión leve: basta que supere al ajustado)")),
            ok(0.02 < tasa_aj < 0.09, f"[{e}…] al ajustar, la tasa vuelve al nominal"),
            ok(ks > 0.05, f"[{e}…] los p ajustados son uniformes"),
        ]
    return all(checks)


def test_permutacion_vs_parametrico() -> bool:
    """Con supuestos cumplidos, permutación y paramétrico deben coincidir de cerca."""
    print("\n[5] Concordancia permutación ↔ paramétrico (supuestos cumplidos)")
    difs = []
    for i in range(30):
        efecto = {"MPPP": 0.4, "Vestibular": 0.0, "Voluntario Sano": 0.0}
        d = muestra_sintetica(efecto, rng=np.random.default_rng(500 + i))
        r = modelos.ancova(d, "y", COVARIABLES, n_perm=2000, n_boot=200, seed=500 + i)
        difs.append(abs(r.p_param - r.p_perm))
    difs = np.array(difs)
    print(f"     |p_param − p_perm|: mediana={np.median(difs):.4f}  máx={difs.max():.4f}")
    return ok(np.median(difs) < 0.05, "ambos p concuerdan cuando los supuestos se cumplen")


def test_eta2_conocido() -> bool:
    """η²ₚ debe crecer monótonamente con el tamaño del efecto y quedar en [0,1]."""
    print("\n[6] Monotonía y rango de η²ₚ")
    etas = []
    for mag in [0.0, 0.5, 1.0, 2.0]:
        d = muestra_sintetica({"MPPP": -mag, "Vestibular": -mag / 2, "Voluntario Sano": 0.0},
                              n_extra=20, rng=np.random.default_rng(900))
        r = modelos.ancova(d, "y", COVARIABLES, n_perm=200, n_boot=200, seed=900)
        etas.append(r.eta2p)
        print(f"     efecto={mag:>3.1f} DE → η²ₚ={r.eta2p:.4f}")
    return all([
        ok(all(0 <= e <= 1 for e in etas), "η²ₚ está en [0,1]"),
        ok(all(etas[i] < etas[i + 1] for i in range(len(etas) - 1)), "η²ₚ crece con el efecto"),
    ])


def test_listwise_y_n() -> bool:
    """El N reportado debe ser el de las filas completas, sin imputar."""
    print("\n[7] Eliminación listwise y N reportado")
    d = muestra_sintetica({g: 0.0 for g in N_POR_GRUPO}, rng=np.random.default_rng(11))
    d.loc[d.index[:6], "y"] = np.nan  # 6 faltantes en el outcome
    r = modelos.ancova(d, "y", COVARIABLES, n_perm=200, n_boot=200, seed=11)
    print(f"     N total={len(d)}  con NaN=6  →  N del modelo={r.n}  ({r.n_por_grupo})")
    return all([
        ok(r.n == len(d) - 6, "el N excluye las filas incompletas"),
        ok(sum(r.n_por_grupo.values()) == r.n, "el N por grupo suma el N total"),
    ])


if __name__ == "__main__":
    print("=" * 74)
    print("TESTS DEL MOTOR ESTADÍSTICO — datos sintéticos con efectos conocidos")
    print("=" * 74)
    resultados = {
        "error tipo I": test_error_tipo_I(),
        "recupera efecto": test_recupera_efecto(),
        "signo de contrastes": test_signo_contrastes(),
        "ajuste por covariable": test_ancova_ajusta_covariable(),
        "permutación ↔ paramétrico": test_permutacion_vs_parametrico(),
        "η²ₚ": test_eta2_conocido(),
        "listwise": test_listwise_y_n(),
    }
    print("\n" + "=" * 74)
    for k, v in resultados.items():
        print(f"  {'PASA' if v else 'FALLA':>5}  {k}")
    print("=" * 74)
    print("TODOS LOS TESTS PASAN" if all(resultados.values()) else "⚠️  HAY TESTS QUE FALLAN")
    raise SystemExit(0 if all(resultados.values()) else 1)
