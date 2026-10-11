"""Estadística de tendencias y homogeneidad para series anuales.

Funciones movidas desde ``app.py`` (``mann_kendall``, ``pendiente_sen`` y
``agregar_serie_anual``) sin cambiar su comportamiento, más pruebas nuevas:

* ``mann_kendall_hamed_rao``: Mann-Kendall con varianza corregida por
  autocorrelación (Hamed y Ramachandra Rao, 1998).
* ``prueba_pettitt``: punto de cambio no paramétrico (Pettitt, 1979).
* ``prueba_snht``: Standard Normal Homogeneity Test (Alexandersson, 1986),
  con valor p por Monte Carlo y semilla fija para que sea reproducible.
* ``evaluar_homogeneidad``: resumen de ambas pruebas.

Solo se usa NumPy y pandas (sin dependencias extra).
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Agregación anual
# ---------------------------------------------------------------------------

def agregar_serie_anual(serie: pd.DataFrame, agregacion: str) -> pd.DataFrame:
    """Agrega una serie a escala anual y elimina años claramente incompletos.

    ``serie`` debe tener columnas ``Fecha`` y ``Valor``. Un año se conserva si
    tiene al menos el 75 % del número típico (mediana) de observaciones por año,
    lo que sirve tanto para datos diarios (~365) como mensuales (~12).
    ``agregacion`` es ``"sum"`` (p. ej. lluvia, mm/año) o cualquier otro valor
    para el promedio (p. ej. temperatura, °C).
    """
    df = serie[["Fecha", "Valor"]].copy().dropna()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df.dropna(subset=["Fecha", "Valor"])
    if df.empty:
        return pd.DataFrame(columns=["Año", "Valor", "N"])

    df["Año"] = df["Fecha"].dt.year
    conteos = df.groupby("Año")["Valor"].count()
    if conteos.empty:
        return pd.DataFrame(columns=["Año", "Valor", "N"])

    positivos = conteos[conteos > 0]
    esperado = float(positivos.median()) if not positivos.empty else 1.0
    umbral = max(1.0, 0.75 * esperado)
    anios_validos = conteos[conteos >= umbral].index
    df = df[df["Año"].isin(anios_validos)]

    if agregacion == "sum":
        valores = df.groupby("Año")["Valor"].sum(min_count=1)
    else:
        valores = df.groupby("Año")["Valor"].mean()
    n = df.groupby("Año")["Valor"].count()

    salida = pd.DataFrame({"Año": valores.index.astype(int), "Valor": valores.values, "N": n.values})
    return salida.dropna(subset=["Valor"]).sort_values("Año").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Mann-Kendall y pendiente de Sen
# ---------------------------------------------------------------------------

def _estadistico_s(y: np.ndarray) -> int:
    s = 0
    for i in range(len(y) - 1):
        s += int(np.sign(y[i + 1:] - y[i]).sum())
    return s


def _varianza_s(y: np.ndarray) -> float:
    n = len(y)
    _, conteos = np.unique(y, return_counts=True)
    empates = conteos[conteos > 1]
    return float(
        n * (n - 1) * (2 * n + 5) - np.sum(empates * (empates - 1) * (2 * empates + 5))
    ) / 18.0


def _z_desde_s(s: float, var_s: float) -> float:
    if var_s <= 0:
        return 0.0
    if s > 0:
        return (s - 1) / math.sqrt(var_s)
    if s < 0:
        return (s + 1) / math.sqrt(var_s)
    return 0.0


def _p_bilateral(z: float) -> float:
    # erfc entrega directamente la probabilidad bilateral de una normal estándar.
    return math.erfc(abs(z) / math.sqrt(2.0))


def _texto_tendencia(significativa: bool, tau: float) -> str:
    if significativa and tau > 0:
        return "Creciente significativa"
    if significativa and tau < 0:
        return "Decreciente significativa"
    return "Sin tendencia significativa"


def mann_kendall(valores, alpha: float = 0.05) -> dict:
    """Prueba Mann-Kendall bilateral con corrección por empates."""
    y = np.asarray(valores, dtype=float)
    y = y[np.isfinite(y)]
    n = len(y)
    if n < 5:
        raise ValueError("Mann-Kendall requiere al menos 5 observaciones válidas.")

    s = _estadistico_s(y)
    var_s = _varianza_s(y)
    z = _z_desde_s(s, var_s)
    p = _p_bilateral(z)
    tau = s / (0.5 * n * (n - 1))
    significativa = p < alpha

    return {
        "n": n,
        "S": float(s),
        "var_S": float(var_s),
        "Z": float(z),
        "p": float(p),
        "tau": float(tau),
        "significativa": bool(significativa),
        "tendencia": _texto_tendencia(significativa, tau),
        "alpha": float(alpha),
    }


def pendiente_sen(anios, valores) -> dict:
    """Pendiente de Sen y ordenada robusta para una serie anual."""
    x = np.asarray(anios, dtype=float)
    y = np.asarray(valores, dtype=float)
    mascara = np.isfinite(x) & np.isfinite(y)
    x, y = x[mascara], y[mascara]
    if len(y) < 2:
        return {"pendiente": float("nan"), "intercepto": float("nan")}

    pendientes = []
    for i in range(len(y) - 1):
        dx = x[i + 1:] - x[i]
        validos = dx != 0
        if validos.any():
            pendientes.extend(((y[i + 1:][validos] - y[i]) / dx[validos]).tolist())

    if not pendientes:
        return {"pendiente": float("nan"), "intercepto": float("nan")}
    pendiente = float(np.median(pendientes))
    intercepto = float(np.median(y - pendiente * x))
    return {"pendiente": pendiente, "intercepto": intercepto}


def _rangos_promedio(y: np.ndarray) -> np.ndarray:
    return pd.Series(y).rank(method="average").to_numpy(dtype=float)


def mann_kendall_hamed_rao(valores, alpha: float = 0.05, alpha_acf: float = 0.05) -> dict:
    """Mann-Kendall modificado de Hamed y Rao (1998) para series autocorrelacionadas.

    1. Se quita la tendencia de Sen a la serie.
    2. Se calcula la autocorrelación de los rangos de la serie sin tendencia.
    3. Solo se usan los rezagos significativos (|r_k| > z_(1-a/2)/sqrt(n)).
    4. Var(S)* = Var(S) · n/n*, con n/n* = 1 + 2/(n(n-1)(n-2)) Σ (n-k)(n-k-1)(n-k-2) r_k.
    """
    y = np.asarray(valores, dtype=float)
    y = y[np.isfinite(y)]
    n = len(y)
    if n < 5:
        raise ValueError("Mann-Kendall requiere al menos 5 observaciones válidas.")

    base = mann_kendall(y, alpha=alpha)
    x = np.arange(1, n + 1, dtype=float)
    sen = pendiente_sen(x, y)["pendiente"]
    residuo = y - sen * x
    rangos = _rangos_promedio(residuo)
    rangos = rangos - rangos.mean()
    denominador = float(np.sum(rangos ** 2))

    z_crit = 1.959963984540054 if abs(alpha_acf - 0.05) < 1e-12 else _z_critico(alpha_acf)
    limite = z_crit / math.sqrt(n)
    suma = 0.0
    if denominador > 0:
        for k in range(1, n - 1):
            r_k = float(np.sum(rangos[:-k] * rangos[k:]) / denominador)
            if abs(r_k) > limite:
                suma += (n - k) * (n - k - 1) * (n - k - 2) * r_k
    factor = 1.0 + 2.0 / (n * (n - 1) * (n - 2)) * suma
    if not np.isfinite(factor) or factor <= 0:
        factor = 1.0

    var_corr = base["var_S"] * factor
    z = _z_desde_s(base["S"], var_corr)
    p = _p_bilateral(z)
    significativa = p < alpha
    return {
        **base,
        "var_S": float(var_corr),
        "Z": float(z),
        "p": float(p),
        "significativa": bool(significativa),
        "tendencia": _texto_tendencia(significativa, base["tau"]),
        "factor_n_n_efectivo": float(factor),
        "metodo": "Hamed y Rao (1998)",
    }


def _z_critico(alpha: float) -> float:
    """Cuantil bilateral de la normal estándar por bisección (sin SciPy)."""
    objetivo = alpha
    bajo, alto = 0.0, 10.0
    for _ in range(100):
        medio = (bajo + alto) / 2
        if _p_bilateral(medio) > objetivo:
            bajo = medio
        else:
            alto = medio
    return (bajo + alto) / 2


# ---------------------------------------------------------------------------
# Homogeneidad
# ---------------------------------------------------------------------------

def prueba_pettitt(valores, alpha: float = 0.05) -> dict:
    """Prueba de Pettitt (1979) para un punto de cambio en la mediana.

    Devuelve ``indice`` = posición (base 0) del último dato ANTES del cambio,
    ``K`` y el valor p aproximado p ≈ 2·exp(-6K²/(n³+n²)).
    """
    y = np.asarray(valores, dtype=float)
    y = y[np.isfinite(y)]
    n = len(y)
    if n < 5:
        raise ValueError("Pettitt requiere al menos 5 observaciones válidas.")
    signos = np.sign(y[:, None] - y[None, :])  # sgn(x_i - x_j)
    # U_t = Σ_{i<=t} Σ_{j>t} sgn(x_i - x_j)
    u = np.array([signos[: t + 1, t + 1:].sum() for t in range(n - 1)], dtype=float)
    indice = int(np.argmax(np.abs(u)))
    k = float(abs(u[indice]))
    p = float(min(1.0, 2.0 * math.exp(-6.0 * k ** 2 / (n ** 3 + n ** 2))))
    return {
        "n": n,
        "K": k,
        "indice": indice,
        "p": p,
        "significativa": bool(p < alpha),
        "media_antes": float(np.mean(y[: indice + 1])),
        "media_despues": float(np.mean(y[indice + 1:])),
    }


def _snht_t(y: np.ndarray) -> tuple[float, int]:
    n = len(y)
    sd = np.std(y, ddof=1)
    if sd == 0 or not np.isfinite(sd):
        return 0.0, 0
    z = (y - y.mean()) / sd
    t = np.empty(n - 1)
    for k in range(1, n):
        z1 = z[:k].mean()
        z2 = z[k:].mean()
        t[k - 1] = k * z1 ** 2 + (n - k) * z2 ** 2
    i = int(np.argmax(t))
    return float(t[i]), i  # i = índice del último dato antes del cambio


def prueba_snht(valores, alpha: float = 0.05, simulaciones: int = 2000, semilla: int = 20261010) -> dict:
    """Standard Normal Homogeneity Test (Alexandersson, 1986), un solo cambio.

    El valor p se estima por Monte Carlo con series normales independientes
    del mismo tamaño (semilla fija: el resultado es reproducible).
    """
    y = np.asarray(valores, dtype=float)
    y = y[np.isfinite(y)]
    n = len(y)
    if n < 5:
        raise ValueError("SNHT requiere al menos 5 observaciones válidas.")
    t0, indice = _snht_t(y)
    rng = np.random.default_rng(semilla)
    mayores = 0
    for _ in range(simulaciones):
        ts, _ = _snht_t(rng.standard_normal(n))
        if ts >= t0:
            mayores += 1
    p = (mayores + 1) / (simulaciones + 1)
    return {
        "n": n,
        "T0": t0,
        "indice": indice,
        "p": float(p),
        "significativa": bool(p < alpha),
        "media_antes": float(np.mean(y[: indice + 1])),
        "media_despues": float(np.mean(y[indice + 1:])),
    }


def evaluar_homogeneidad(anios, valores, alpha: float = 0.05) -> dict:
    """Aplica Pettitt y SNHT a una serie anual y resume el resultado.

    ``anio_cambio`` es el PRIMER año del segundo segmento según Pettitt.
    Una prueba significativa no prueba por sí sola que la serie esté mal: una
    tendencia real también puede producir un punto de cambio. Debe
    contrastarse con la historia de la estación y con estaciones vecinas.
    """
    x = np.asarray(anios, dtype=float)
    y = np.asarray(valores, dtype=float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    pet = prueba_pettitt(y, alpha=alpha)
    snht = prueba_snht(y, alpha=alpha)
    anio_pettitt = int(x[pet["indice"] + 1])
    anio_snht = int(x[snht["indice"] + 1])
    ambas = pet["significativa"] and snht["significativa"]
    alguna = pet["significativa"] or snht["significativa"]
    if ambas:
        dictamen = "Probable inhomogeneidad"
    elif alguna:
        dictamen = "Dudosa"
    else:
        dictamen = "Sin evidencia de cambio"
    return {
        "pettitt_p": pet["p"],
        "pettitt_K": pet["K"],
        "anio_cambio": anio_pettitt,
        "snht_p": snht["p"],
        "snht_T0": snht["T0"],
        "anio_cambio_snht": anio_snht,
        "media_antes": pet["media_antes"],
        "media_despues": pet["media_despues"],
        "dictamen": dictamen,
        "alpha": alpha,
    }


def analizar_serie_tendencia(serie: pd.DataFrame, agregacion: str, alpha: float = 0.05,
                             anio_inicio: int | None = None, anio_fin: int | None = None):
    """Agrega a escala anual y aplica Mann-Kendall + Sen (+ Hamed-Rao).

    Con ``anio_inicio``/``anio_fin`` se restringe el análisis a un subperiodo
    (por ejemplo, el tramo homogéneo de una serie con un cambio documentado).
    """
    anual = agregar_serie_anual(serie, agregacion)
    if anio_inicio is not None:
        anual = anual[anual["Año"] >= anio_inicio]
    if anio_fin is not None:
        anual = anual[anual["Año"] <= anio_fin]
    anual = anual.reset_index(drop=True)
    if len(anual) < 5:
        return anual, None
    mk = mann_kendall(anual["Valor"].values, alpha=alpha)
    sen = pendiente_sen(anual["Año"].values, anual["Valor"].values)
    hr = mann_kendall_hamed_rao(anual["Valor"].values, alpha=alpha)
    resultado = {
        **mk, **sen,
        "p_hamed_rao": hr["p"],
        "tendencia_hamed_rao": hr["tendencia"],
        "significativa_hamed_rao": hr["significativa"],
    }
    return anual, resultado


def fraccion_con_decimales(valores) -> float:
    """Fracción de valores positivos con parte decimal (diagnóstico de resolución)."""
    y = np.asarray(valores, dtype=float)
    y = y[np.isfinite(y) & (y > 0)]
    if len(y) == 0:
        return float("nan")
    return float(np.mean(np.abs(y - np.round(y)) > 1e-9))
