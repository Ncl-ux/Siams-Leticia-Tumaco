"""Esquema y validación de los datos de campo que llegarán desde la app offline de XUE Hub.

SIAMS no captura datos: solo publica el esquema (config/esquema_datos_campo.csv) y valida los
CSV antes de integrarlos (scripts/validar_datos_campo.py).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ESQUEMA = RAIZ / "config" / "esquema_datos_campo.csv"
POZOS = RAIZ / "config" / "pozos_monitoreo.csv"
SEDES = {"Arauca", "La Paz", "Leticia", "Tumaco", "Bogotá"}
TIPOS = {"nivel_manual", "descarga_sensor", "fq_campo"}
RANGOS = {"profundidad_nivel_m": (0, 300), "altura_brocal_m": (-1, 3), "ph": (0, 14),
          "ce_us_cm": (0, 100000), "temperatura_c": (0, 50), "od_mg_l": (0, 20)}
URL_APP_XUE = "https://observatorio-siams.vercel.app/campo/"  # App offline de XUE Hub (Observatorio SIAMS)


def cargar_esquema() -> pd.DataFrame:
    return pd.read_csv(ESQUEMA)


def pozos_validos() -> set[str]:
    ids = set(pd.read_csv(POZOS).pozo_id) if POZOS.exists() else set()
    p = RAIZ / "data" / "processed" / "niveles" / "pozos.csv"
    if p.exists():
        ids |= set(pd.read_csv(p).pozo_id)
    return ids


def validar(df: pd.DataFrame, pozos: set[str] | None = None, ahora: pd.Timestamp | None = None) -> list[str]:
    """Devuelve la lista de errores (vacía si el archivo es válido). Filas numeradas desde 2 (como en Excel)."""
    esq = cargar_esquema()
    errores = []
    faltan = [c for c in esq.columna if c not in df.columns]
    if faltan:
        return [f"Faltan columnas: {', '.join(faltan)}"]
    extra = [c for c in df.columns if c not in set(esq.columna)]
    if extra:
        errores.append(f"Columnas no reconocidas: {', '.join(extra)}")
    pozos = pozos_validos() if pozos is None else pozos
    ahora = ahora or pd.Timestamp.now(tz="America/Bogota").tz_localize(None)
    fechas = pd.to_datetime(df.fecha_hora, format="%Y-%m-%d %H:%M", errors="coerce")
    for col in RANGOS:
        df[col] = pd.to_numeric(df[col], errors="coerce").where(df[col].notna() & (df[col].astype(str).str.strip() != ""))
    for i, f in df.iterrows():
        n = i + 2
        if pd.isna(fechas[i]):
            errores.append(f"Fila {n}: fecha_hora inválida ({f.fecha_hora!r}); use AAAA-MM-DD HH:MM")
        elif fechas[i] > ahora + pd.Timedelta(hours=1):
            errores.append(f"Fila {n}: fecha_hora en el futuro")
        if f.sede not in SEDES:
            errores.append(f"Fila {n}: sede desconocida ({f.sede!r})")
        if pozos and f.pozo_id not in pozos:
            errores.append(f"Fila {n}: pozo_id no registrado ({f.pozo_id!r})")
        if f.tipo_medicion not in TIPOS:
            errores.append(f"Fila {n}: tipo_medicion inválido ({f.tipo_medicion!r})")
        if f.tipo_medicion == "nivel_manual" and pd.isna(f.profundidad_nivel_m):
            errores.append(f"Fila {n}: falta profundidad_nivel_m para nivel_manual")
        if pd.notna(f.profundidad_nivel_m) and f.referencia not in ("brocal", "terreno"):
            errores.append(f"Fila {n}: referencia debe ser 'brocal' o 'terreno'")
        for col, (lo, hi) in RANGOS.items():
            v = f[col]
            if pd.notna(v) and not lo <= v <= hi:
                errores.append(f"Fila {n}: {col}={v} fuera de rango [{lo}, {hi}]")
        if pd.isna(f.operador) or not str(f.operador).strip():
            errores.append(f"Fila {n}: falta operador")
    return errores
