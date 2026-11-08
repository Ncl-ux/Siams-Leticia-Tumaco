"""Integra las series de nivel de agua subterránea de las sedes y calcula la cota del nivel.

Entradas crudas (NO se versionan): carpeta SIAMS_CRUDOS (por defecto data/raw/sedes/) con la
misma estructura que D:\\APF\\Sedes_Niveles\\Monitoreo:
    Arauca/SONDA05_*.xlsx                     Keller DCX (columna de agua mH2O)
    LaPaz/SONDA04_*.csv                       Keller DCX exportado a CSV (; y coma decimal)
    Leticia/SONDA_01*.xlsx, SONDA_02*.xlsx, ticunasas_*.xlsx, Niveles.xlsx
    Tumaco/csv/CSV/PZ-UN-TU_*_BW249.CSV       Diver TD (presión absoluta)  + VEI_EP979_*.CSV (barómetro)
    Bogota/Bogota/UNAL/2026-19-05_OGA.xlsm    red de piezómetros del campus (OGA)
    Bogota/Bogota/UNAL/Pozo SGC_*.xlsx, Pz - 02_*.xlsx  Keller con 'Water Depth' (B − columna)

Salidas (versionadas): data/processed/niveles/pozos.csv y niveles_<sede>.csv

Método de cota (decisión del semillero, nov-2026):
    cota_terreno = GLO-30 − 1,5 m (salvo cota levantada en config/pozos_monitoreo.csv)
    profundidad_nivel = prof_sensor − columna_agua   (transductores)
    cota_nivel = cota_terreno − profundidad_nivel
Si la profundidad del sensor no se conoce, se publica la columna de agua y el cambio relativo,
y la cota queda vacía con el supuesto anotado.

Uso:  python scripts/10_niveles_sedes.py [--crudos RUTA] [--sin-dem]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from siams.dem import (SESGO_DEM_M, FUENTE_DEM, elevacion_glo30, cota_terreno,  # noqa: E402
                       profundidad_desde_presion)

SALIDA = RAIZ / "data" / "processed" / "niveles"
CONFIG = RAIZ / "config" / "pozos_monitoreo.csv"
UMBRAL_FUERA_AGUA_M = 0.05


def _ultimo(patron: str) -> list[str]:
    return sorted(glob.glob(patron))


# ---------------------------------------------------------------- lectores
def leer_keller_xlsx(ruta: str) -> pd.DataFrame:
    """Hoja 'Data' de KOLIBRI Desktop: encabezado en la fila 10."""
    d = pd.read_excel(ruta, sheet_name="Data", header=9)
    d.columns = [" ".join(str(c).replace("_x000d_", "").split()) for c in d.columns]
    t = next(c for c in d.columns if "local time" in c)
    h = next(c for c in d.columns if c.startswith("mH20"))
    temp = next((c for c in d.columns if c.startswith("TOB1")), None)
    out = pd.DataFrame({"fecha": pd.to_datetime(d[t], errors="coerce"), "valor_m": pd.to_numeric(d[h], errors="coerce")})
    if temp:
        out["temp_c"] = pd.to_numeric(d[temp], errors="coerce")
    calc = pd.read_excel(ruta, sheet_name="Calculation Settings", header=None)
    formula = str(calc.iloc[4, 0])
    b = calc[calc[1].astype(str).str.strip() == "B"]
    out.attrs["modo"] = "water_depth" if "Water Depth" in formula else "columna_agua"
    out.attrs["B"] = float(b.iloc[0, 2]) if len(b) else None
    return out.dropna(subset=["fecha", "valor_m"])


def leer_keller_csv(ruta: str) -> pd.DataFrame:
    d = pd.read_csv(ruta, sep=";", decimal=",")
    d.columns = [" ".join(str(c).split()) for c in d.columns]
    t = next(c for c in d.columns if "local time" in c)
    h = next(c for c in d.columns if c.startswith("mH20"))
    temp = next((c for c in d.columns if c.startswith("TOB1")), None)
    f = pd.to_datetime(d[t].astype(str).str.split(",").str[0], errors="coerce")
    out = pd.DataFrame({"fecha": f, "valor_m": pd.to_numeric(d[h], errors="coerce")})
    if temp:
        out["temp_c"] = pd.to_numeric(d[temp], errors="coerce")
    out.attrs["modo"] = "columna_agua"
    return out.dropna(subset=["fecha", "valor_m"])


def leer_diver_csv(ruta: str) -> pd.DataFrame:
    """Archivo CSV de Diver-Office: datos tras la línea 'Date/time;...'."""
    with open(ruta, encoding="latin-1") as fh:
        lineas = fh.read().splitlines()
    i = next(k for k, l in enumerate(lineas) if l.startswith("Date/time"))
    filas = [l.split(";") for l in lineas[i + 1:] if l and l[0].isdigit()]
    d = pd.DataFrame(filas).iloc[:, :3]
    d.columns = ["fecha", "p_cm", "temp_c"]
    d["fecha"] = pd.to_datetime(d.fecha, format="%Y/%m/%d %H:%M:%S", errors="coerce")
    for c in ("p_cm", "temp_c"):
        d[c] = pd.to_numeric(d[c].str.replace(",", "."), errors="coerce")
    ident = next((l for l in lineas if "Identification" in l), "")
    d.attrs["identificacion"] = ident.split("=")[-1].strip()
    return d.dropna(subset=["fecha", "p_cm"])


# ---------------------------------------------------------------- utilidades
def marcar_calidad(df: pd.DataFrame, col_carga: str = "carga_sobre_sensor_m") -> pd.Series:
    q = pd.Series("ok", index=df.index)
    q[df[col_carga] < UMBRAL_FUERA_AGUA_M] = "sensor_fuera_del_agua"
    med = df.set_index("fecha")[col_carga].rolling("7D", min_periods=12).median().to_numpy()
    q[(q == "ok") & (df[col_carga].to_numpy() < med - 2.0)] = "descenso_brusco_posible_bombeo"
    return q


def serie_transductor(df, pozo, prof_sensor, cota_ter, supuesto, horario=True):
    df = df.sort_values("fecha").drop_duplicates("fecha")
    if horario:
        df = df.set_index("fecha").resample("1h").mean(numeric_only=True).dropna(how="all").reset_index()
    out = pd.DataFrame({"fecha": df.fecha, "pozo_id": pozo, "metodo": "transductor",
                        "carga_sobre_sensor_m": df.carga_sobre_sensor_m.round(3)})
    out["calidad"] = marcar_calidad(out)
    if prof_sensor is not None and not pd.isna(prof_sensor):
        out["profundidad_nivel_m"] = profundidad_desde_presion(prof_sensor, out.carga_sobre_sensor_m).round(3)
    else:
        out["profundidad_nivel_m"] = np.nan
    out["cota_nivel_msnm"] = (cota_ter - out.profundidad_nivel_m).round(3)
    out.loc[out.calidad == "sensor_fuera_del_agua", ["profundidad_nivel_m", "cota_nivel_msnm"]] = np.nan
    out["supuesto"] = supuesto
    return out


# ---------------------------------------------------------------- pozos y DEM
def tabla_pozos(crudos: Path, usar_dem: bool) -> pd.DataFrame:
    from pyproj import Transformer

    pozos = pd.read_csv(CONFIG, dtype={"serial": str})
    tr = Transformer.from_crs("EPSG:3116", "EPSG:4326", always_xy=True)
    oga = crudos / "Bogota" / "Bogota" / "UNAL" / "2026-19-05_OGA.xlsm"
    extra = []
    if oga.exists():
        nom = pd.read_excel(oga, sheet_name="nomenclatura").dropna(subset=["ID", "X"])
        nom = nom[nom.ID.astype(str).str.match(r"^PA\d+")]
        for r in nom.itertuples():
            lon, lat = tr.transform(r.X, r.Y)
            pid = f"BOG-{r.ID}"
            if pid in set(pozos.pozo_id):
                m = pozos.pozo_id == pid
                if pd.isna(pozos.loc[m, "lat"]).all():
                    pozos.loc[m, ["lat", "lon"]] = [round(lat, 6), round(lon, 6)]
                continue
            extra.append(dict(pozo_id=pid, sede="Bogotá", nombre=r.Nombre_cap, equipo="sonda manual / OGA",
                              tipo_registro=f"{r.TIPO} · {r.Estado}", lat=round(lat, 6), lon=round(lon, 6),
                              fuente_coordenada="OGA 2026-19-05 (MAGNA-SIRGAS origen Bogotá → WGS84)",
                              prof_pozo_m=r.Profundida if r.Profundida else np.nan,
                              notas=f"Unidad captada: {r.Unidad_cap}"))
    pozos = pd.concat([pozos, pd.DataFrame(extra)], ignore_index=True)
    cache = SALIDA / "pozos.csv"
    previo = pd.read_csv(cache).set_index("pozo_id") if cache.exists() else pd.DataFrame()
    dem = []
    for r in pozos.itertuples():
        v = np.nan
        if usar_dem:
            try:
                v = round(elevacion_glo30(r.lat, r.lon), 2)
            except Exception as e:  # sin red: se conserva el valor anterior
                print("DEM no disponible para", r.pozo_id, e)
        if pd.isna(v) and r.pozo_id in previo.index:
            v = previo.loc[r.pozo_id, "dem_glo30_m"]
        dem.append(v)
    pozos["dem_glo30_m"] = dem
    pozos["cota_terreno_msnm"] = np.where(pozos.cota_levantada_msnm.notna() if "cota_levantada_msnm" in pozos else False,
                                          pozos.get("cota_levantada_msnm"), pozos.dem_glo30_m - SESGO_DEM_M).round(2)
    pozos["metodo_cota_terreno"] = np.where(pozos.cota_levantada_msnm.notna(), "cota levantada",
                                            f"GLO-30 − {SESGO_DEM_M} m (sesgo estimado en Leticia)")
    # SIAMS_LA_PAZ_COTA_ESTIMADA: valor estimado de Google Earth, NO levantado.
    if "cota_estimada_msnm" in pozos.columns:
        estimada = pd.to_numeric(pozos["cota_estimada_msnm"], errors="coerce")
        sin_levantamiento = pozos["cota_levantada_msnm"].isna()
        m_estimada = estimada.notna() & sin_levantamiento
        pozos.loc[m_estimada, "cota_terreno_msnm"] = estimada[m_estimada].round(2)
        if "fuente_cota_estimada" in pozos.columns:
            pozos.loc[m_estimada, "metodo_cota_terreno"] = pozos.loc[m_estimada, "fuente_cota_estimada"].fillna("Cota estimada")
        else:
            pozos.loc[m_estimada, "metodo_cota_terreno"] = "Cota estimada (sin levantamiento)"
    return pozos


# ---------------------------------------------------------------- por sede
def procesar(crudos: Path, pozos: pd.DataFrame) -> dict[str, pd.DataFrame]:
    P = pozos.set_index("pozo_id")
    S = {}

    def cota(pid):
        return float(P.loc[pid, "cota_terreno_msnm"])

    # Arauca
    f = _ultimo(str(crudos / "Arauca" / "SONDA05_*.xlsx"))
    if f:
        d = pd.concat([leer_keller_xlsx(x) for x in f]).rename(columns={"valor_m": "carga_sobre_sensor_m"})
        S["Arauca"] = serie_transductor(d, "ARA-PTAP", P.loc["ARA-PTAP", "prof_sensor_m"], cota("ARA-PTAP"),
                                        "Keller con compensación barométrica interna (sensor relativo). Profundidad del sensor DESCONOCIDA: sin cota; se publica la columna de agua.")
    # La Paz
    f = _ultimo(str(crudos / "LaPaz" / "SONDA04_*.csv"))
    if f:
        d = pd.concat([leer_keller_csv(x) for x in f]).rename(columns={"valor_m": "carga_sobre_sensor_m"})
        S["La Paz"] = serie_transductor(d, "LPZ-UNAL", P.loc["LPZ-UNAL", "prof_sensor_m"], cota("LPZ-UNAL"),
                                        "Keller con compensación barométrica interna (sensor relativo). Sensor instalado a 42,81 m (dato profesora Pina, nov-2026). Cota del terreno estimada, pendiente verificacion topografica.")
    # Leticia
    partes = []
    for patron, pid, sup in [
        ("SONDA_01*.xlsx", "LET-ARTURO", "Keller compensado internamente. Profundidad del sensor DESCONOCIDA: sin cota."),
        ("SONDA_02*.xlsx", "LET-PACHOVELA", "Keller compensado internamente; lectura en vivo (16 datos). Profundidad del sensor DESCONOCIDA: sin cota."),
        ("ticunasas_*.xlsx", "LET-NUMAE", "Keller compensado internamente. Sensor a 17 m bajo la referencia (dato del semillero); profundidad = 17 − columna de agua."),
    ]:
        f = _ultimo(str(crudos / "Leticia" / patron))
        if f:
            d = pd.concat([leer_keller_xlsx(x) for x in f]).rename(columns={"valor_m": "carga_sobre_sensor_m"})
            d = d[d.fecha <= "2026-10-15 23:59"]
            partes.append(serie_transductor(d, pid, P.loc[pid, "prof_sensor_m"], cota(pid), sup, horario=pid != "LET-PACHOVELA"))
    man = crudos / "Leticia" / "Niveles.xlsx"
    if man.exists():
        m = pd.read_excel(man)
        m.columns = ["fecha", "hora", "nivel"]
        m["profundidad_nivel_m"] = pd.to_numeric(m.nivel.astype(str).str.replace(",", ".").str.strip(), errors="coerce")
        m = m.dropna(subset=["profundidad_nivel_m"])
        m = m[m.profundidad_nivel_m < 30]
        partes.append(pd.DataFrame({"fecha": pd.to_datetime(m.fecha), "pozo_id": "LET-UNAL", "metodo": "manual",
                                    "carga_sobre_sensor_m": np.nan, "calidad": "ok",
                                    "profundidad_nivel_m": m.profundidad_nivel_m.round(3),
                                    "cota_nivel_msnm": (cota("LET-UNAL") - m.profundidad_nivel_m).round(3),
                                    "supuesto": "Profundidad al agua medida con sonda manual desde la boca del pozo; hora de lectura no estandarizada (se usa la fecha)."}))
    if partes:
        S["Leticia"] = pd.concat(partes, ignore_index=True)
    # Tumaco
    fw = [x for x in _ultimo(str(crudos / "Tumaco" / "**" / "PZ-UN-TU_*_BW249.CSV")) if True]
    fb = _ultimo(str(crudos / "Tumaco" / "**" / "VEI_EP979_*.CSV"))
    if not fw:
        fw = _ultimo(str(crudos / "Tumaco" / "*" / "*" / "PZ-UN-TU_*_BW249.CSV"))
        fb = _ultimo(str(crudos / "Tumaco" / "*" / "*" / "VEI_EP979_*.CSV"))
    if fw and fb:
        brutos = [leer_diver_csv(x) for x in fw]
        w = next((x for x in brutos if x.attrs.get("identificacion") == "PRESSURE"), brutos[0])
        b = max((leer_diver_csv(x) for x in fb), key=len)
        b = b.set_index("fecha").p_cm.resample("10min").interpolate("time")
        w = w.set_index("fecha")
        w["baro_cm"] = b.reindex(w.index, method="nearest", tolerance=pd.Timedelta("2h"))
        w["carga_sobre_sensor_m"] = (w.p_cm - w.baro_cm) / 100.0
        d = w.reset_index().dropna(subset=["carga_sobre_sensor_m"])
        t = serie_transductor(d, "TUM-PZ-UN-TU", P.loc["TUM-PZ-UN-TU", "prof_sensor_m"], cota("TUM-PZ-UN-TU"),
                              "Diver de presión absoluta compensado con el barómetro EP979 (interpolado). Profundidad del sensor = longitud de cable 13,00 m configurada en Diver-Office (otro export usa 1,30 m: error de digitación). Antes de fines de julio de 2026 el Diver registra la misma presión que el barómetro (fuera del agua).")
        t.loc[t.carga_sobre_sensor_m < 0.3, "calidad"] = "sensor_fuera_del_agua"
        t.loc[t.calidad == "sensor_fuera_del_agua", ["profundidad_nivel_m", "cota_nivel_msnm"]] = np.nan
        S["Tumaco"] = t
    # Bogotá
    partes = []
    ubase = crudos / "Bogota" / "Bogota" / "UNAL"
    for patron, pid in [("Pozo SGC_*.xlsx", "BOG-PA01"), ("Pz - 02_*.xlsx", "BOG-PA06")]:
        f = _ultimo(str(ubase / patron))
        if f:
            d = leer_keller_xlsx(f[0])
            B = d.attrs.get("B") or P.loc[pid, "prof_sensor_m"]
            d["carga_sobre_sensor_m"] = B - d.valor_m if d.attrs.get("modo") == "water_depth" else d.valor_m
            partes.append(serie_transductor(d, pid, B, cota(pid),
                                            f"Keller con 'Water Depth' = B − columna; B = {B:g} m (Calculation Settings). Profundidad medida desde la referencia de instalación (boca del tubo); no se descuenta la altura del brocal."))
    oga = ubase / "2026-19-05_OGA.xlsm"
    if oga.exists():
        v = pd.read_excel(oga, sheet_name="Niveles")
        v = v.rename(columns={"ID *": "id", "Nivel piezometrico corregido": "corr", "Metodo de medicion": "met"})
        v = v.dropna(subset=["id", "corr", "Fecha"])
        v = v[v.id.astype(str).str.match(r"^PA\d+")]
        v["pozo_id"] = "BOG-" + v.id.astype(str)
        v = v[v.pozo_id.isin(P.index)]
        v["profundidad_nivel_m"] = -pd.to_numeric(v["corr"], errors="coerce")
        v = v.dropna(subset=["profundidad_nivel_m"])
        ct = v.pozo_id.map(P.cota_terreno_msnm)
        partes.append(pd.DataFrame({"fecha": pd.to_datetime(v.Fecha), "pozo_id": v.pozo_id,
                                    "metodo": np.where(v.met.astype(str).str.upper().str.startswith("AUTO"), "automatico_oga", "manual"),
                                    "carga_sobre_sensor_m": np.nan, "calidad": "ok",
                                    "profundidad_nivel_m": v.profundidad_nivel_m.round(3),
                                    "cota_nivel_msnm": (ct - v.profundidad_nivel_m).round(3),
                                    "supuesto": "Base OGA: 'Nivel piezométrico corregido' (lectura − altura del brocal) se toma como profundidad bajo el terreno."}))
    if partes:
        S["Bogotá"] = pd.concat(partes, ignore_index=True)
    for s, d in S.items():
        d.insert(1, "sede", s)
        d["fecha"] = pd.to_datetime(d.fecha).dt.strftime("%Y-%m-%d %H:%M")
    return S


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--crudos", default=os.environ.get("SIAMS_CRUDOS", str(RAIZ / "data" / "raw" / "sedes")))
    ap.add_argument("--sin-dem", action="store_true", help="no consulta GLO-30 (usa pozos.csv previo)")
    a = ap.parse_args(argv)
    crudos = Path(a.crudos)
    SALIDA.mkdir(parents=True, exist_ok=True)
    pozos = tabla_pozos(crudos, not a.sin_dem)
    series = procesar(crudos, pozos)
    pozos["n_registros"] = pozos.pozo_id.map(pd.concat(series.values()).groupby("pozo_id").size()).fillna(0).astype(int)
    pozos = pozos[(pozos.n_registros > 0) | pozos.pozo_id.isin(pd.read_csv(CONFIG).pozo_id)]
    pozos.to_csv(SALIDA / "pozos.csv", index=False)
    meta = {"generado": pd.Timestamp.now(tz="America/Bogota").isoformat(timespec="seconds"),
            "fuente_dem": FUENTE_DEM, "sesgo_dem_m": SESGO_DEM_M, "series": {}}
    for s, d in series.items():
        nombre = "niveles_" + s.lower().replace(" ", "_").replace("á", "a").replace("ó", "o") + ".csv"
        d.to_csv(SALIDA / nombre, index=False)
        meta["series"][s] = {"archivo": nombre, "registros": len(d), "inicio": d.fecha.min(), "fin": d.fecha.max()}
        print(f"{s}: {len(d)} registros {d.fecha.min()} → {d.fecha.max()}")
    (SALIDA / "metadatos.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
