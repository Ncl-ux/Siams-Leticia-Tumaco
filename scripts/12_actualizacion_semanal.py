"""Actualización semanal (GitHub Actions) de series abiertas por sede.

Fuentes activas:
  * NASA POWER diario (API v2, comunidad AG)           -> nasa_power_<sede>.csv
  * CHIRPS v3.0 mensual (UCSB-CHC, lectura puntual)     -> chirps_<sede>.csv
  * IDEAM en datos.gov.co (Socrata), verificados 2026-11-01:
      s54a-sgyg Precipitación, sbwg-7ju4 Temperatura Ambiente del Aire,
      bdmn-sqnh Nivel Instantáneo del Río               -> ideam_<sede>.csv
Fuentes desactivadas (documentadas, requieren credenciales o procesamiento pesado):
  * GRACE/GRACE-FO + GLDAS (scripts/06_gwsa_grace_gldas_extendido.py; Earthdata login)
  * ERA5-Land (Copernicus CDS; requiere clave CDSAPI)

Cada archivo es incremental: se descargan solo las fechas posteriores al último registro
(con una ventana de reproceso de 60 días para capturar correcciones de la fuente).
Escribe data/processed/actualizacion/metadatos.json con la fecha de 'última actualización'.

Uso:  python scripts/12_actualizacion_semanal.py [--fuentes nasa_power,chirps,ideam] [--sedes leticia,tumaco]
"""
from __future__ import annotations

import argparse
import datetime as dt
import functools
import importlib.util
import json
import math
import os
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "data" / "processed" / "actualizacion"
REPROCESO_DIAS = 60

# Reutilizar el descargador científico original, sin cambiar su metodología.
_spec_nasa = importlib.util.spec_from_file_location(
    "siams_descarga_nasa_original", RAIZ / "scripts" / "01_descarga_nasa_power.py"
)
_nasa_original = importlib.util.module_from_spec(_spec_nasa)
_spec_nasa.loader.exec_module(_nasa_original)

SEDES = {**_nasa_original.SEDES, "bogota": (4.638193, -74.084046)}
# Bogotá conserva las coordenadas utilizadas en su actualización previa.
INICIO = {"nasa_power": "1981-01-01", "chirps": "1981-01-01", "ideam": "2026-01-01"}  # carga inicial corta: Socrata corta consultas agregadas largas

# Estaciones automáticas IDEAM con datos en datos.gov.co (consultado 2026-11-01).
ESTACIONES_IDEAM = {
    "leticia": {"precipitacion": "0048015050", "temperatura": "0048015050"},
    "tumaco": {"precipitacion": "0051039010", "temperatura": "0051039010", "nivel_rio": "0051027060"},
    "arauca": {"precipitacion": "3706500109", "temperatura": "3706500109"},
}
SOCRATA = {"precipitacion": "s54a-sgyg", "temperatura": "sbwg-7ju4", "nivel_rio": "bdmn-sqnh"}
AGREGADO = {"precipitacion": "sum(valorobservado)", "temperatura": "avg(valorobservado)", "nivel_rio": "avg(valorobservado)"}

NASA_PARAM = dict(_nasa_original.PARAMETROS)
CHIRPS_URL = "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/global/tifs/chirps-v3.0.{a:04d}.{m:02d}.tif"


def _json(url: str, timeout=300):
    req = urllib.request.Request(url, headers={"User-Agent": "SIAMS-UNAL/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def desde(archivo: Path, fuente: str) -> pd.Timestamp:
    if archivo.exists():
        f = pd.read_csv(archivo, usecols=["fecha"], parse_dates=["fecha"]).fecha.max()
        return max(pd.Timestamp(INICIO[fuente]), f - pd.Timedelta(days=REPROCESO_DIAS))
    return pd.Timestamp(INICIO[fuente])


def combinar(archivo: Path, nuevo: pd.DataFrame, claves=("fecha",)) -> int:
    if archivo.exists():
        viejo = pd.read_csv(archivo, parse_dates=["fecha"])
        nuevo = pd.concat([viejo, nuevo]).drop_duplicates(list(claves), keep="last")
    nuevo = nuevo.sort_values(list(claves))
    nuevo.to_csv(archivo, index=False, date_format="%Y-%m-%d")
    return len(nuevo)


def _nasa_diario(tabla):
    """Valida fechas y nombres; conserva NaN, no interpola ni convierte unidades."""
    tabla = tabla.copy()
    tabla["fecha"] = pd.to_datetime(tabla["fecha"], errors="raise").dt.normalize()
    if tabla["fecha"].isna().any() or tabla["fecha"].duplicated().any():
        raise ValueError("NASA POWER: fechas ausentes o duplicadas")
    for col in NASA_PARAM.values():
        if col in tabla:
            tabla[col] = pd.to_numeric(tabla[col], errors="raise").replace(-999.0, float("nan"))
    return tabla.sort_values("fecha").set_index("fecha")


def nasa_power(sede, lat, lon, hoy):
    arch = SALIDA / f"nasa_power_{sede}.csv"
    columnas = list(NASA_PARAM.values())
    viejo = _nasa_diario(pd.read_csv(arch)) if arch.exists() else pd.DataFrame()
    # Una migración de 5 a 8 variables exige recuperar el histórico, no solo 60 días.
    ampliar = viejo.empty or any(c not in viejo or not viejo[c].notna().any() for c in columnas)
    ini = pd.Timestamp(INICIO["nasa_power"]) if ampliar else desde(arch, "nasa_power")
    nuevo, consulta = _nasa_original.descargar(lat, lon, ini.strftime("%Y-%m-%d"), hoy.strftime("%Y-%m-%d"))
    nuevo = _nasa_diario(nuevo)
    if not set(columnas).issubset(nuevo.columns):
        raise ValueError("NASA POWER: respuesta sin las ocho variables originales")
    nuevo = nuevo[columnas].dropna(how="all")
    if nuevo.empty or any(not nuevo[c].notna().any() for c in columnas):
        raise ValueError("NASA POWER: respuesta vacía o variable sin datos; se conserva el archivo anterior")
    if nuevo.index.min() < ini or nuevo.index.max() > hoy:
        raise ValueError("NASA POWER: respuesta fuera del periodo solicitado")
    if ampliar:
        # Impide marcar una migración parcial como completa. Los vacíos de radiación
        # anteriores a su disponibilidad no se rellenan.
        if nuevo.index.min() > ini + pd.Timedelta(days=31):
            raise ValueError("NASA POWER: la descarga inicial no cubre el inicio histórico")
        if nuevo.index.max() < hoy - pd.Timedelta(days=90):
            raise ValueError("NASA POWER: la descarga inicial no alcanza el periodo reciente")
    # Valores nuevos válidos tienen prioridad; una respuesta nula no elimina datos
    # previos. El original de los Excel permanece intacto para comparar la metodología.
    combinado = nuevo.combine_first(viejo).sort_index().reindex(columns=columnas)
    combinado.index.name = "fecha"
    temporal = arch.with_suffix(".csv.tmp")
    combinado.reset_index().to_csv(temporal, index=False, date_format="%Y-%m-%d")
    os.replace(temporal, arch)
    meta = {"sede": sede, "lat": lat, "lon": lon, "comunidad": _nasa_original.COMUNIDAD,
            "inicio_solicitado": str(ini.date()), "fin_solicitado": str(hoy.date()),
            "modo": "historico" if ampliar else "incremental",
            "consulta": consulta,
            "cobertura": {c: {"validos": int(combinado[c].count()),
                              "inicio": str(combinado[c].first_valid_index().date()) if combinado[c].count() else None,
                              "fin": str(combinado[c].last_valid_index().date()) if combinado[c].count() else None}
                          for c in columnas}}
    arch.with_suffix(".consulta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(combinado)


@functools.lru_cache(maxsize=None)
def _chirps_mes(a: int, m: int):
    """Lee el mes una sola vez para todas las sedes (lectura por rangos HTTP).

    Los GeoTIFF de CHIRPS v3.0 no traen geotransformación (GDAL ve la identidad):
    la malla es 0,05° de -180 a 180 E y de 60 N a -60 S (7200 × 2400), así que la
    celda se calcula a mano.
    """
    import time
    import warnings
    import rasterio
    import numpy as np
    from rasterio.windows import Window
    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    os.environ.setdefault("GDAL_HTTP_TIMEOUT", "60")
    for intento in range(3):
        try:
            with warnings.catch_warnings(), rasterio.open("/vsicurl/" + CHIRPS_URL.format(a=a, m=m)) as r:
                warnings.simplefilter("ignore")
                assert (r.width, r.height) == (7200, 2400), "malla CHIRPS inesperada"
                out = {}
                for sede, (lat, lon) in SEDES.items():
                    col, fila = int((lon + 180) / 0.05), int((60 - lat) / 0.05)
                    if not r.transform.is_identity:
                        if r.crs and not r.crs.is_geographic:
                            raise ValueError('CRS CHIRPS no geográfico')
                        if not np.allclose(tuple(r.bounds), (-180, -60, 180, 60), atol=.01):
                            raise ValueError('Extensión geográfica CHIRPS inesperada')
                        fila, col = r.index(lon, lat)
                    if not (0 <= col < r.width and 0 <= fila < r.height):
                        raise ValueError(f'Coordenadas fuera de malla CHIRPS: {sede}')
                    pixel = r.read(1, window=Window(col, fila, 1, 1), masked=True)[0, 0]
                    out[sede] = float(pixel) if not np.ma.is_masked(pixel) else float('nan')
                return out
        except rasterio.errors.RasterioIOError:
            time.sleep(3 * (intento + 1))
    return None  # mes no publicado o no disponible (se cachea para no reintentar por cada sede)


def chirps_sedes(sedes, hoy):
    """Una lectura por mes, con guardado incremental para todas las sedes solicitadas."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    SALIDA.mkdir(parents=True, exist_ok=True)
    ultimo = pd.Timestamp(hoy).replace(day=1) - pd.offsets.MonthBegin(1)
    todos = pd.date_range(INICIO["chirps"], ultimo, freq="MS")
    estados, solicitudes = {}, {}
    for sede in sedes:
        arch = SALIDA / f"chirps_{sede}.csv"
        viejo = pd.DataFrame({"fecha": pd.Series(dtype="datetime64[ns]"), "precipitacion_mm_mes": pd.Series(dtype=float)})
        if arch.exists():
            viejo = pd.read_csv(arch, parse_dates=["fecha"])
            if viejo.fecha.isna().any() or viejo.fecha.duplicated().any() or not viejo.fecha.dt.day.eq(1).all():
                raise ValueError(f"CHIRPS {sede}: fechas inválidas o duplicadas")
            viejo["precipitacion_mm_mes"] = pd.to_numeric(viejo.precipitacion_mm_mes, errors="coerce")
        validos = viejo.precipitacion_mm_mes.map(lambda v: pd.notna(v) and math.isfinite(v) and v >= 0)
        viejo = viejo.loc[validos & viejo.fecha.le(ultimo)].set_index("fecha").sort_index()
        control = arch.with_suffix('.nodata.json')
        nodata = set(pd.to_datetime(json.loads(control.read_text(encoding='utf-8')))) if control.exists() else set()
        meses = (set(todos) - set(viejo.index) - nodata) | set(todos[-3:])
        estados[sede] = (arch, control, viejo, nodata)
        for f in meses:
            solicitudes.setdefault(f, []).append(sede)
    meses = sorted(solicitudes)
    exitos = dict.fromkeys(sedes, 0)
    print(f"CHIRPS: {len(meses)} meses por consultar para {', '.join(sedes)}; guardado por mes.", flush=True)
    def procesar(f, mes):
        for sede in solicitudes[f]:
            arch, control, viejo, nodata = estados[sede]
            if sede not in mes:
                continue
            v = mes[sede]
            cambio = False
            if math.isfinite(v) and v >= 0:
                cambio = f in nodata
                nodata.discard(f)
                viejo.loc[f, "precipitacion_mm_mes"] = round(v, 2)
                temporal = arch.with_suffix(".csv.tmp")
                viejo.sort_index().to_csv(temporal, date_format="%Y-%m-%d", index_label="fecha")
                os.replace(temporal, arch)
                exitos[sede] += 1
            elif f not in viejo.index and f not in nodata:
                nodata.add(f)
                cambio = True
            if cambio:
                temporal_control = control.with_suffix('.json.tmp')
                temporal_control.write_text(json.dumps([str(x.date()) for x in sorted(nodata)], indent=2), encoding='utf-8')
                os.replace(temporal_control, control)

    # Un lote acotado evita encolar el histórico entero y permite reanudar.
    ex = ThreadPoolExecutor(max_workers=4)
    hechos = 0
    try:
        for i in range(0, len(meses), 12):
            pendientes = {ex.submit(_chirps_mes, f.year, f.month): f for f in meses[i:i+12]}
            for futuro in as_completed(pendientes):
                f = pendientes[futuro]
                try:
                    mes = futuro.result()
                except Exception as e:
                    print(f"CHIRPS {f:%Y-%m}: {type(e).__name__}: {e}", flush=True)
                    mes = None
                if mes is not None:
                    procesar(f, mes)
                hechos += 1
                if hechos == 1 or hechos % 12 == 0 or hechos == len(meses) or mes is None:
                    cuentas = ", ".join(f"{s}: {len(estados[s][2])} guardados" for s in sedes)
                    aviso = " (sin respuesta válida; se reintentará)" if mes is None else ""
                    print(f"CHIRPS {hechos}/{len(meses)} | {f:%Y-%m}{aviso} | {cuentas}", flush=True)
    finally:
        ex.shutdown(wait=False, cancel_futures=True)
    return {s: len(estados[s][2]) if exitos[s] else 0 for s in sedes}


def chirps(sede, lat, lon, hoy):
    return chirps_sedes([sede], hoy)[sede]


def ideam(sede, hoy):
    if sede not in ESTACIONES_IDEAM:
        return 0
    arch = SALIDA / f"ideam_{sede}.csv"
    ini = desde(arch, "ideam")
    partes = []
    for var, est in ESTACIONES_IDEAM[sede].items():
        q = urllib.parse.urlencode({
            "$select": f"date_trunc_ymd(fechaobservacion) as fecha, {AGREGADO[var]} as valor, count(*) as n_obs, min(nombreestacion) as estacion",
            "$where": f"codigoestacion='{est}' and fechaobservacion >= '{ini:%Y-%m-%d}T00:00:00'",
            "$group": "fecha", "$order": "fecha", "$limit": 50000})
        d = pd.DataFrame(_json(f"https://www.datos.gov.co/resource/{SOCRATA[var]}.json?{q}"))
        if d.empty:
            continue
        d["variable"], d["codigoestacion"], d["dataset"] = var, est, SOCRATA[var]
        partes.append(d)
    if not partes:
        return 0
    df = pd.concat(partes)
    df["fecha"] = pd.to_datetime(df.fecha).dt.normalize()
    df["valor"] = pd.to_numeric(df.valor).round(3)
    return combinar(arch, df[["fecha", "variable", "valor", "n_obs", "codigoestacion", "estacion", "dataset"]],
                    claves=("fecha", "variable"))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuentes", default="nasa_power,chirps,ideam")
    ap.add_argument("--sedes", default=",".join(SEDES))
    a = ap.parse_args(argv)
    SALIDA.mkdir(parents=True, exist_ok=True)
    hoy = pd.Timestamp(dt.date.today())
    metaf = SALIDA / "metadatos.json"
    meta = json.loads(metaf.read_text(encoding="utf-8")) if metaf.exists() else {"fuentes": {}}
    meta["desactivadas"] = {"grace_gldas": "Requiere Earthdata (scripts/06_*.py); se actualiza manualmente.",
                            "era5_land": "Requiere clave Copernicus CDS; no configurada."}
    errores = 0
    for fuente in a.fuentes.split(","):
        seleccion = a.sedes.split(",")
        resultado_chirps, error_chirps = {}, None
        if fuente == "chirps":
            try:
                resultado_chirps = chirps_sedes(seleccion, hoy)
            except Exception as e:
                error_chirps = e
        for sede in seleccion:
            lat, lon = SEDES[sede]
            try:
                if fuente == "chirps":
                    if error_chirps is not None:
                        raise error_chirps
                    n = resultado_chirps[sede]
                else:
                    n = {"nasa_power": lambda: nasa_power(sede, lat, lon, hoy),
                         "ideam": lambda: ideam(sede, hoy)}[fuente]()
                estado = "sin datos válidos nuevos" if fuente == "chirps" and n == 0 else "ok"
            except Exception as e:  # una fuente caída no detiene las demás
                n, estado, errores = None, f"error: {e}"[:300], errores + 1
            meta["fuentes"].setdefault(fuente, {})[sede] = {"filas": n, "estado": estado,
                                                           "actualizado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
            print(fuente, sede, n, estado, flush=True)
    meta["ultima_actualizacion"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    metaf.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if errores and errores == len(a.fuentes.split(",")) * len(a.sedes.split(",")) else 0


if __name__ == "__main__":
    raise SystemExit(main())
