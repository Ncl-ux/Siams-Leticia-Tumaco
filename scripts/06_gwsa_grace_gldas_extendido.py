#!/usr/bin/env python
"""Extiende la GWSa de SIAMS (GRACE/GRACE-FO menos GLDAS) hasta el último mes disponible (2026-06).

Método B «estándar» (anomalías con línea base común), el que mejor reproduce el producto de
Romero y Piña (2025) en el período común:

    GWSA = TWSA · scale_factor − (SMSA + CWSA + SWEA)

* TWSA: JPL GRACE/GRACE-FO Mascon CRI RL06.3Mv04 (``lwe_thickness``, cm, anomalía respecto a
  2004.000–2009.999), multiplicada por el ``scale_factor`` de JPL. Malla de muestreo 0,5°.
* SMSA, CWSA, SWEA: GLDAS-2.1 Noah 0,25° mensual (GLDAS_NOAH025_M v2.1). Humedad del suelo
  (suma de las 4 capas 0–200 cm), agua en el dosel y equivalente de agua en nieve, en kg m⁻²
  (= mm) × 0,1 → cm. Anomalía respecto a la media de los 72 meses nominales GRACE de 2004–2009.
* GLDAS 0,25° → 0,5°: media ponderada por cos(lat) de las 4 celdas de 0,25° contenidas en cada
  celda JPL (solo celdas válidas). Mes GLDAS = mes nominal JPL (sin interpolación temporal).
* Celdas oceánicas JPL (``land_mask = 0``) = NaN. Los meses sin solución JPL (33 en 2002-04..2026-06,
  entre ellos la brecha GRACE → GRACE-FO 2017-07..2018-05) **no se interpolan**: no tienen paso temporal.
* La malla de 0,5° se lleva a la malla de ~0,12° del NetCDF original de la app por vecino más
  cercano y se aplica la máscara de píxeles válidos del original (contorno de Colombia).

Uso (desde la raíz del repositorio; todas las rutas son relativas a ella):

    python scripts/06_gwsa_grace_gldas_extendido.py descargar   # requiere cuenta NASA Earthdata
    python scripts/06_gwsa_grace_gldas_extendido.py procesar

``descargar`` baja el archivo global JPL (≈46 MB) a ``data/raw/grace/`` y el recorte OPeNDAP de
GLDAS para Colombia (≈0,17 MB/mes) a ``data/raw/gldas/GLDAS_NOAH025_M.2.1/``. La autenticación se
toma de ``~/.netrc`` (machine urs.earthdata.nasa.gov) o de la variable ``EARTHDATA_TOKEN``; nunca se
imprime ni se guarda en el repositorio. Los insumos crudos no se versionan (ver ``.gitignore``).

``procesar`` escribe:
    data/processed/gwsa/COL_GWS_estimations_2002-2026.nc   (lo lee la app)
    data/processed/gwsa/GWSa_sedes_2002-2026.csv            (serie del píxel de cada sede)
    docs/gwsa_validacion_extension.csv                      (comparación con el NetCDF original)
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

RAIZ = Path(__file__).resolve().parents[1]
RAW_GRACE = RAIZ / "data" / "raw" / "grace"
RAW_GLDAS = RAIZ / "data" / "raw" / "gldas" / "GLDAS_NOAH025_M.2.1"
REFERENCIA = RAIZ / "COL_GWS_estimations.nc"
SALIDA_NC = RAIZ / "data" / "processed" / "gwsa" / "COL_GWS_estimations_2002-2026.nc"
SALIDA_SEDES = RAIZ / "data" / "processed" / "gwsa" / "GWSa_sedes_2002-2026.csv"
SALIDA_VALIDACION = RAIZ / "docs" / "gwsa_validacion_extension.csv"

# Recorte de trabajo (bordes de celda), con margen alrededor de Colombia continental e insular.
BBOX = dict(lat_min=-4.5, lat_max=13.0, lon_min=-82.0, lon_max=-66.5)
LINEA_BASE = ("2004-01", "2009-12")

# Mismas coordenadas que TERRITORIOS en app.py.
SEDES = {
    "Bogotá": (4.6386, -74.0841),
    "Leticia": (-4.193717, -69.941001),
    "Tumaco": (1.610206, -78.720520),
    "Medellín": (6.262190, -75.576968),
    "San Andrés": (12.536552, -81.707935),
    "Arauca": (7.012222763876252, -70.74338825990411),
    "La Paz": (10.390218033322455, -73.20038917337925),
}
RADIO_MAX_KM = 120.0  # igual que extraer_gws_territorio() en app.py

GRACE_COLECCION = "TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4"
GLDAS_CONCEPTO = "C1342986036-GES_DISC"  # GLDAS_NOAH025_M v2.1
GLDAS_VARS = ["SoilMoi0_10cm_inst", "SoilMoi10_40cm_inst", "SoilMoi40_100cm_inst",
              "SoilMoi100_200cm_inst", "CanopInt_inst", "SWE_inst"]
CMR = "https://cmr.earthdata.nasa.gov/search"


def rel(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(RAIZ))
    except ValueError:
        return Path(p).name


# --------------------------------------------------------------------------- descarga
def sesion_earthdata():
    import requests

    s = requests.Session()
    token = os.environ.get("EARTHDATA_TOKEN")
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    # Sin token, requests usa ~/.netrc (machine urs.earthdata.nasa.gov) en las redirecciones.
    return s


def descargar(inicio: str, fin: str) -> None:
    import requests

    s = sesion_earthdata()
    # 1) GRACE/GRACE-FO: colección de un solo gránulo que JPL reemplaza en cada actualización.
    r = requests.get(f"{CMR}/granules.umm_json", params={"short_name": GRACE_COLECCION, "provider": "POCLOUD",
                                                         "page_size": 10, "sort_key": "-start_date"}, timeout=60)
    r.raise_for_status()
    urls = [u["URL"] for it in r.json()["items"] for u in it["umm"].get("RelatedUrls", [])
            if u.get("Type") == "GET DATA" and u["URL"].startswith("https") and u["URL"].endswith(".nc")]
    if not urls:
        sys.exit("CMR no devolvió el archivo JPL mascon.")
    destino = RAW_GRACE / urls[0].rsplit("/", 1)[1]
    RAW_GRACE.mkdir(parents=True, exist_ok=True)
    if not destino.exists():
        print("GRACE:", urls[0])
        _bajar(s, urls[0], destino)
    print("GRACE listo:", rel(destino))

    # 2) GLDAS: recorte server-side OPeNDAP (DAP4) de la malla global 0,25° (1440 × 600).
    lat = -59.875 + 0.25 * np.arange(600)
    lon = -179.875 + 0.25 * np.arange(1440)
    ii = np.where((lat >= BBOX["lat_min"]) & (lat <= BBOX["lat_max"]))[0]
    jj = np.where((lon >= BBOX["lon_min"]) & (lon <= BBOX["lon_max"]))[0]
    la, lo = f"[{ii[0]}:1:{ii[-1]}]", f"[{jj[0]}:1:{jj[-1]}]"
    ce = ";".join([f"/{v}[0:1:0]{la}{lo}" for v in GLDAS_VARS] + [f"/lat{la}", f"/lon{lo}", "/time"])
    RAW_GLDAS.mkdir(parents=True, exist_ok=True)
    for mes in pd.period_range(inicio, fin, freq="M"):
        nombre = f"GLDAS_NOAH025_M.A{mes.year}{mes.month:02d}.021"
        destino = RAW_GLDAS / f"{nombre}.COLsubset.nc4"
        if destino.exists():
            continue
        url = (f"https://opendap.earthdata.nasa.gov/collections/{GLDAS_CONCEPTO}/granules/"
               f"GLDAS_NOAH025_M.2.1%3A{nombre}.nc4.dap.nc4")
        resp = s.get(url, params={"dap4.ce": ce}, timeout=600)
        if resp.status_code == 404:
            print("GLDAS aún no publicado:", mes)
            continue
        resp.raise_for_status()
        destino.write_bytes(resp.content)
        print("GLDAS", mes, destino.stat().st_size, "bytes")


def _bajar(s, url, destino: Path) -> None:
    tmp = destino.with_suffix(destino.suffix + ".part")
    with s.get(url, stream=True, timeout=900) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for c in r.iter_content(1 << 20):
                f.write(c)
    tmp.rename(destino)


# --------------------------------------------------------------------------- procesamiento
def cargar_grace(ruta: Path, fin: str):
    ds = xr.open_dataset(ruta)
    ds = ds.assign_coords(lon=((ds.lon + 180) % 360) - 180).sortby("lon")
    ds = ds.sel(lat=slice(BBOX["lat_min"], BBOX["lat_max"]), lon=slice(BBOX["lon_min"], BBOX["lon_max"]))
    t = pd.DatetimeIndex(ds.time.values)
    meses = pd.period_range(t[0].to_period("M"), t[-1].to_period("M"), freq="M")
    # RL06.1Mv03 traía la cadena mal formada «2018-08-2018-09»; se corrige por si acaso.
    faltan = set(re.sub(r"(\d{4}-\d{2})-(\d{4}-\d{2})", r"\1;\2", ds.attrs["months_missing"]).split(";"))
    nominal = [str(p) for p in meses if str(p) not in faltan]
    assert len(nominal) == len(t), (len(nominal), len(t))
    ds = ds.assign_coords(mes_nominal=("time", nominal))
    ds = ds.isel(time=np.where(ds.mes_nominal.values <= fin)[0])
    faltantes = sorted(m for m in faltan if m <= fin)
    return ds, faltantes


def cargar_gldas(carpeta: Path):
    archivos = sorted(carpeta.glob("GLDAS_NOAH025_M.A*.nc4"))
    if not archivos:
        sys.exit(f"No hay archivos GLDAS en {rel(carpeta)}. Ejecute primero «descargar».")
    partes = []
    for a in archivos:
        with xr.open_dataset(a, engine="netcdf4") as d:
            d = d[GLDAS_VARS].sortby("lat")
            d = d.sel(lat=slice(BBOX["lat_min"], BBOX["lat_max"]), lon=slice(BBOX["lon_min"], BBOX["lon_max"]))
            partes.append(d.load())
    g = xr.concat(partes, dim="time")
    meses = pd.DatetimeIndex(g.time.values).to_period("M").astype(str)
    assert not pd.Index(meses).duplicated().any(), "meses GLDAS duplicados"
    sm = 0.1 * sum(g[v] for v in GLDAS_VARS if v.startswith("SoilMoi"))  # kg m-2 -> cm
    cw = 0.1 * g["CanopInt_inst"]
    swe = 0.1 * g["SWE_inst"]
    return {"SMSA": sm, "CWSA": cw, "SWEA": swe}, list(meses), archivos


def a_medio_grado(da: xr.DataArray) -> xr.DataArray:
    """Media ponderada por área (cos lat) de las 4 celdas de 0,25° dentro de cada celda de 0,5°."""
    assert np.isclose((float(da.lat[0]) - 0.125) % 0.5, 0.0) or np.isclose((float(da.lat[0]) - 0.125) % 0.5, 0.5)
    w = np.cos(np.deg2rad(da.lat)).broadcast_like(da.isel(time=0, drop=True))
    valido = da.notnull()
    num = (da.fillna(0) * w).coarsen(lat=2, lon=2, boundary="trim").sum()
    den = (valido * w).coarsen(lat=2, lon=2, boundary="trim").sum()
    out = (num / den).where(den > 0)
    return out.assign_coords(lat=out.lat.round(3), lon=out.lon.round(3))


def metodo_b(gr: xr.Dataset, comp: dict, meses_gldas: list[str]):
    nominal = list(gr.mes_nominal.values)
    falta = sorted(set(nominal) - set(meses_gldas))
    if falta:
        sys.exit(f"Faltan meses GLDAS para: {falta}")
    base = [m for m in nominal if LINEA_BASE[0] <= m <= LINEA_BASE[1]]
    assert len(base) == 72, len(base)
    total = 0
    for nombre, da in comp.items():
        h = a_medio_grado(da).assign_coords(time=meses_gldas)
        h = h.reindex(lat=gr.lat, lon=gr.lon, method="nearest", tolerance=1e-3)
        anom = h.sel(time=nominal) - h.sel(time=base).mean("time")
        total = total + anom.assign_coords(time=gr.time)
    tws = gr["lwe_thickness"] * gr["scale_factor"]
    gwsa = (tws - total).where(gr["land_mask"] > 0)
    return gwsa.transpose("time", "lat", "lon")


def pixel_sede(da: xr.DataArray, lat0: float, lon0: float):
    """Misma regla que la app: píxel válido (algún mes) más cercano, a menos de 120 km."""
    la, lo = np.meshgrid(da.lat.values, da.lon.values, indexing="ij")
    p1, p2 = np.radians(lat0), np.radians(la)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lo - lon0) / 2) ** 2
    d = 2 * 6371.0088 * np.arcsin(np.sqrt(a))
    d = np.where(da.notnull().any("time").values, d, np.inf)
    i, j = np.unravel_index(np.argmin(d), d.shape)
    return (int(i), int(j), float(d[i, j])) if d[i, j] <= RADIO_MAX_KM else (None, None, float(d[i, j]))


def estadisticas(nuevo: np.ndarray, viejo: np.ndarray) -> dict:
    ok = np.isfinite(nuevo) & np.isfinite(viejo)
    a, b = nuevo[ok], viejo[ok]
    if ok.sum() < 3:
        return dict(n_meses=int(ok.sum()))
    return dict(n_meses=int(ok.sum()), r=float(np.corrcoef(a, b)[0, 1]), sesgo_cm=float(np.mean(a - b)),
                rmse_cm=float(np.sqrt(np.mean((a - b) ** 2))), razon_amplitud=float(np.std(a) / np.std(b)))


def procesar(args) -> None:
    grace = Path(args.grace) if args.grace else sorted(RAW_GRACE.glob("GRCTellus.JPL.*RL06.3M.MSCNv04CRI.nc"))[-1]
    gr, faltantes = cargar_grace(grace, args.fin)
    comp, meses_gldas, archivos_gldas = cargar_gldas(Path(args.gldas))
    g05 = metodo_b(gr, comp, meses_gldas)

    ref = xr.open_dataset(args.referencia).load()
    mascara = ref["GWS_anom"].notnull().any("time")
    fino = g05.sel(lat=ref.lat, lon=ref.lon, method="nearest")
    fino = fino.assign_coords(lat=ref.lat, lon=ref.lon).where(mascara)
    neg = (gr["scale_factor"] < 0) & (gr["land_mask"] > 0)
    neg_fino = neg.sel(lat=ref.lat, lon=ref.lon, method="nearest").assign_coords(lat=ref.lat, lon=ref.lon) & mascara

    tb = gr["time_bounds"].values if "time_bounds" in gr else None
    ahora = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    t_ini, t_fin = str(gr.mes_nominal.values[0]), str(gr.mes_nominal.values[-1])
    out = xr.Dataset(coords=dict(time=gr.time.values, lat=ref.lat.values, lon=ref.lon.values))
    out = out.assign_coords(mes_nominal=("time", gr.mes_nominal.values.astype(str)))
    out["GWS_anom"] = fino.astype("float32")
    out["GWS_anom"].attrs = dict(
        units="cm", long_name="Anomalía de almacenamiento de agua subterránea (GWSa), lámina de agua equivalente",
        anomaly_baseline="2004-01-01/2009-12-31 (72 meses nominales GRACE; misma línea base que JPL para TWSA)",
        comment=("GWSa = TWSA·scale_factor (JPL mascon CRI RL06.3Mv04) − (SMSA + CWSA + SWEA) (GLDAS-2.1 Noah 0,25°). "
                 "Señal regional: la resolución efectiva de GRACE es de cientos de km (mascones de ~3°). "
                 "En llanuras de inundación (p. ej. Amazonas) puede incluir agua superficial que GLDAS no resta."),
        grid_mapping="crs", ancillary_variables="factor_escala_negativo")
    out["factor_escala_negativo"] = neg_fino.astype("int8")
    out["factor_escala_negativo"].attrs = dict(
        long_name="1 = la celda JPL de 0,5° tiene scale_factor < 0 (GWSa poco fiable: señal invertida o suprimida)",
        flag_values=np.array([0, 1], dtype="int8"), flag_meanings="normal factor_de_escala_negativo", grid_mapping="crs")
    if tb is not None:
        out["time_bnds"] = (("time", "nv"), tb)
        out["time_bnds"].attrs = dict(long_name="ventana de la solución mensual GRACE/GRACE-FO")
    out["crs"] = ref["crs"] if "crs" in ref else xr.DataArray(np.int32(0))
    out.time.attrs = dict(standard_name="time", long_name="fecha central de la ventana de solución mensual GRACE/GRACE-FO",
                          axis="T", **({"bounds": "time_bnds"} if tb is not None else {}),
                          comment="Punto medio de la ventana de solución (no día de medición). Use mes_nominal para agrupar por mes: "
                                  "dos soluciones (2012-01-01 → 2011-12 y 2015-04-27 → 2015-05) caen en otro mes calendario.")
    out.mes_nominal.attrs = dict(long_name="mes nominal de la solución JPL (AAAA-MM)")
    out.lat.attrs = dict(ref.lat.attrs); out.lon.attrs = dict(ref.lon.attrs)
    out.attrs = dict(
        Conventions="CF-1.8",
        title="Anomalías de almacenamiento de agua subterránea (GWSa) para Colombia, 2002-04 a " + t_fin,
        summary=("Extensión del producto GWSa de SIAMS hasta " + t_fin + " recalculado de forma homogénea para todo el "
                 "período con el método B (anomalías con línea base 2004–2009). Misma malla (~0,12°), variable y máscara "
                 "que COL_GWS_estimations.nc, de modo que la app lo usa sin cambios de formato."),
        institution="Semillero SIAMS, Universidad Nacional de Colombia",
        source=("GRACE/GRACE-FO: JPL Mascon CRI RL06.3Mv04 (" + grace.name + ", date_created " + str(gr.attrs.get("date_created", "?")) +
                "; doi:10.5067/TEMSC-3JC634). GLDAS: GLDAS_NOAH025_M v2.1 (GLDAS-2.1 Noah 0,25° mensual; doi:10.5067/SXAVCZFAQLNO), "
                f"{len(archivos_gldas)} archivos {meses_gldas[0]}..{meses_gldas[-1]}, recorte OPeNDAP."),
        method=("GWSA = lwe_thickness·scale_factor − (SMSA + CWSA + SWEA). SM = suma de SoilMoi 0–10, 10–40, 40–100 y 100–200 cm; "
                "CW = CanopInt_inst; SWE = SWE_inst; kg m-2 × 0,1 = cm; anomalías respecto a la media de los meses nominales "
                "GRACE 2004-01..2009-12. GLDAS 0,25° → 0,5° por media ponderada por cos(lat) de las 4 subceldas válidas; "
                "mes GLDAS = mes nominal JPL; celdas oceánicas JPL = NaN. Remuestreo 0,5° → malla de la app por vecino más "
                "cercano y máscara de píxeles válidos del NetCDF original."),
        time_coverage_start=t_ini, time_coverage_end=t_fin,
        period=(f"{t_ini}..{t_fin}: {out.sizes['time']} meses con solución. Meses sin solución JPL (sin paso temporal, NO "
                "interpolados): " + ";".join(faltantes) + ". Incluye la brecha GRACE → GRACE-FO 2017-07..2018-05."),
        references=("Watkins et al. (2015) doi:10.1002/2014JB011547; Wiese et al. (2016) doi:10.1002/2016WR019344; "
                    "Rodell et al. (2004) doi:10.1175/BAMS-85-3-381; Beaudoing & Rodell (2020) doi:10.5067/SXAVCZFAQLNO; "
                    "Romero, P. & Piña, A. (2025) J. Hydrol. Reg. Stud. 62, 102756, doi:10.1016/j.ejrh.2025.102756"),
        acknowledgment=("GRACE/GRACE-FO mascon data: NASA JPL/Caltech, distribuidos por PO.DAAC. GLDAS: NASA GSFC Hydrological "
                        "Sciences Laboratory, distribuidos por GES DISC."),
        license="Datos de origen NASA de uso libre con atribución. Producto derivado: CC BY 4.0 (propuesta, ver LICENSE).",
        history=f"{ahora}: generado con scripts/06_gwsa_grace_gldas_extendido.py a partir de {grace.name}, GLDAS_NOAH025_M v2.1 y {Path(args.referencia).name} (malla y máscara).",
        geospatial_lat_min=float(ref.lat.min()), geospatial_lat_max=float(ref.lat.max()),
        geospatial_lon_min=float(ref.lon.min()), geospatial_lon_max=float(ref.lon.max()),
        comment=("Malla de ~0,12° heredada del producto original; la resolución efectiva es la de GRACE. Ver "
                 "factor_escala_negativo. San Andrés queda fuera de la malla y su celda GRACE es oceánica: sin GWSa."),
    )
    enc = {"GWS_anom": dict(zlib=True, complevel=6, _FillValue=np.float32(np.nan), least_significant_digit=3),
           "factor_escala_negativo": dict(zlib=True), "time": dict(units="days since 2002-01-01", calendar="standard", dtype="float64")}
    if tb is not None:
        enc["time_bnds"] = dict(units="days since 2002-01-01", calendar="standard", dtype="float64")
    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    out.to_netcdf(salida, encoding=enc)
    print("NetCDF:", rel(salida), f"{salida.stat().st_size / 1e6:.1f} MB", t_ini, "→", t_fin, out.sizes)

    # ---------------- series por sede y validación contra el original (período común)
    nuevo = xr.open_dataset(salida).load()
    comunes = np.intersect1d(nuevo.time.values, ref.time.values)
    filas, series = [], []
    for sede, (la, lo) in SEDES.items():
        i, j, d = pixel_sede(nuevo["GWS_anom"], la, lo)
        io, jo, do = pixel_sede(ref["GWS_anom"], la, lo)
        fila = dict(ambito=sede, lat_pixel=None if i is None else float(nuevo.lat[i]),
                    lon_pixel=None if j is None else float(nuevo.lon[j]), distancia_km=round(d, 1),
                    mismo_pixel_que_original=(i, j) == (io, jo))
        if i is not None:
            s = nuevo["GWS_anom"].isel(lat=i, lon=j)
            series.append(pd.DataFrame({"sede": sede, "mes_nominal": nuevo.mes_nominal.values,
                                        "fecha": pd.DatetimeIndex(nuevo.time.values).strftime("%Y-%m-%d"),
                                        "GWSa_cm": np.round(s.values.astype(float), 3),
                                        "lat_pixel": float(nuevo.lat[i]), "lon_pixel": float(nuevo.lon[j])}))
            fila["ultimo_mes_valido"] = str(nuevo.mes_nominal.values[np.where(np.isfinite(s.values))[0][-1]])
            if io is not None:
                fila.update(estadisticas(s.sel(time=comunes).values, ref["GWS_anom"].isel(lat=io, lon=jo).sel(time=comunes).values))
        filas.append(fila)
    a = nuevo["GWS_anom"].sel(time=comunes).values.astype(float)
    b = ref["GWS_anom"].sel(time=comunes).values.astype(float)
    ok = np.isfinite(a) & np.isfinite(b)
    n = ok.sum(0)
    A, B = np.where(ok, a, np.nan), np.where(ok, b, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # píxeles fuera de la máscara (todo NaN)
        r = np.nanmean((A - np.nanmean(A, 0)) * (B - np.nanmean(B, 0)), 0) / (np.nanstd(A, 0) * np.nanstd(B, 0))
        rm = np.sqrt(np.nanmean((A - B) ** 2, 0))
        sg = np.nanmean(A - B, 0)
        ma, mb = np.nanmean(A, (1, 2)), np.nanmean(B, (1, 2))
    m = n >= 24
    filas.append(dict(ambito="Malla: mediana por píxel", n_pixeles=int(m.sum()), n_meses=int(np.median(n[m])),
                      r=float(np.median(r[m])), r_p10=float(np.percentile(r[m], 10)), sesgo_cm=float(np.median(sg[m])),
                      rmse_cm=float(np.median(rm[m]))))
    filas.append(dict(ambito="Malla: serie media nacional", n_pixeles=int(m.sum()), **estadisticas(ma, mb)))
    val = pd.DataFrame(filas)
    for c in ("n_meses", "n_pixeles"):
        val[c] = val[c].astype("Int64")
    val.insert(1, "periodo_comun", f"{pd.Timestamp(comunes[0]):%Y-%m}..{pd.Timestamp(comunes[-1]):%Y-%m}")
    Path(args.validacion).parent.mkdir(parents=True, exist_ok=True)
    val.to_csv(args.validacion, index=False, float_format="%.4f")
    pd.concat(series).to_csv(args.sedes, index=False)
    print(val.round(3).to_string())
    print("Validación:", rel(Path(args.validacion)), "| series:", rel(Path(args.sedes)))


# --------------------------------------------------------------------------- versión alternativa
SALIDA_NC_ALT = RAIZ / "data" / "processed" / "gwsa" / "COL_GWS_estimations_2002-2026_diferencias.nc"
SALIDA_SEDES_ALT = RAIZ / "data" / "processed" / "gwsa" / "GWSa_sedes_2002-2026_diferencias.csv"
SALIDA_VALIDACION_ALT = RAIZ / "docs" / "gwsa_validacion_diferencias.csv"


def metodo_diferencias(gr: xr.Dataset, comp: dict, meses_gldas: list[str]) -> xr.DataArray:
    """Fórmula de diferencias mensuales (UNgroundwater, ComputeGwe.py), variante A3.

    GWe = lwe_thickness·scale_factor − (ΔSM + ΔSWE), con ΔX = X(mes) − X(mes anterior) de GLDAS,
    sin canopia. GLDAS 0,25° → 0,5° por interpolación lineal en los centros JPL, que caen justo
    entre 4 celdas GLDAS: equivale a su promedio simple, y es NaN si falta alguna (como xarray.interp).
    La diferencia del mes calendario se asigna al mes nominal JPL (sin interpolación temporal).
    """
    d = (comp["SMSA"] + comp["SWEA"]).assign_coords(time=meses_gldas)
    d = d.diff("time")  # etiqueta = mes final de la diferencia
    d = d.coarsen(lat=2, lon=2, boundary="trim").reduce(np.mean)  # NaN si falta alguna
    d = d.assign_coords(lat=d.lat.round(3), lon=d.lon.round(3)).reindex(lat=gr.lat, lon=gr.lon, method="nearest", tolerance=1e-3)
    nominal = list(gr.mes_nominal.values)
    falta = sorted(set(nominal) - set(d.time.values.astype(str)))
    if falta:
        sys.exit(f"Faltan diferencias GLDAS para: {falta}")
    d = d.sel(time=nominal).assign_coords(time=gr.time)
    return (gr["lwe_thickness"] * gr["scale_factor"] - d).transpose("time", "lat", "lon")


def procesar_alternativa(args) -> None:
    """Serie original del semillero + meses nuevos con su misma fórmula (diferencias mensuales)."""
    grace = Path(args.grace) if args.grace else sorted(RAW_GRACE.glob("GRCTellus.JPL.*RL06.3M.MSCNv04CRI.nc"))[-1]
    gr, faltantes = cargar_grace(grace, args.fin)
    comp, meses_gldas, archivos_gldas = cargar_gldas(Path(args.gldas))
    a05 = metodo_diferencias(gr, comp, meses_gldas)
    ref = xr.open_dataset(args.referencia).load()
    mascara = ref["GWS_anom"].notnull().any("time")
    a_fino = a05.sel(lat=ref.lat, lon=ref.lon, method="nearest").assign_coords(lat=ref.lat, lon=ref.lon).where(mascara)

    # Último mes del original con datos (el paso 2025-05 del archivo original está vacío).
    con_dato = ref["GWS_anom"].notnull().any(("lat", "lon")).values
    t_ult = ref.time.values[np.where(con_dato)[0][-1]]
    t_orig = ref.time.values[con_dato]
    assert np.isin(t_orig, gr.time.values).all(), "fechas del original que no están en el archivo JPL"
    nuevos = gr.time.values[gr.time.values > t_ult]
    tiempos = np.concatenate([t_orig, nuevos])
    gr_t = gr.sel(time=tiempos)
    valores = xr.concat([ref["GWS_anom"].sel(time=t_orig).astype("float32"),
                         a_fino.sel(time=nuevos).drop_vars("mes_nominal").astype("float32")], dim="time")
    origen = np.r_[np.zeros(len(t_orig), "int8"), np.ones(len(nuevos), "int8")]

    # Empalme: la fórmula recalculada frente al original en los 24 meses previos al corte.
    solape = t_orig[-24:]
    filas = []
    nuevo_sol, viejo_sol = a_fino.sel(time=solape), ref["GWS_anom"].sel(time=solape)
    for sede, (la, lo) in SEDES.items():
        i, j, d = pixel_sede(ref["GWS_anom"], la, lo)
        fila = dict(ambito=sede, distancia_km=round(d, 1))
        if i is not None:
            s_new = a_fino.isel(lat=i, lon=j)
            fila["meses_nuevos_con_dato"] = int(np.isfinite(s_new.sel(time=nuevos).values).sum())
            fila.update(estadisticas(nuevo_sol.isel(lat=i, lon=j).values, viejo_sol.isel(lat=i, lon=j).values))
            # Todo el período común (2002-05..2025-04): qué tanto reproduce la fórmula al original.
            todo = estadisticas(a_fino.isel(lat=i, lon=j).sel(time=t_orig).values, ref["GWS_anom"].isel(lat=i, lon=j).sel(time=t_orig).values)
            fila.update({f"{k}_2002_2025": v for k, v in todo.items() if k != "n_meses"})
        filas.append(fila)
    ma = np.nanmean(nuevo_sol.values, (1, 2)); mb = np.nanmean(viejo_sol.values, (1, 2))
    filas.append(dict(ambito="Malla: serie media nacional", **estadisticas(ma, mb)))
    val = pd.DataFrame(filas)
    val.insert(1, "periodo_empalme", f"{pd.Timestamp(solape[0]):%Y-%m}..{pd.Timestamp(solape[-1]):%Y-%m}")

    ahora = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    t_fin = str(gr_t.mes_nominal.values[-1]); t_ini = str(gr_t.mes_nominal.values[0])
    corte = str(gr_t.mes_nominal.values[len(t_orig) - 1])
    out = xr.Dataset(coords=dict(time=tiempos, lat=ref.lat.values, lon=ref.lon.values))
    out = out.assign_coords(mes_nominal=("time", gr_t.mes_nominal.values.astype(str)))
    out["GWS_anom"] = valores.assign_coords(time=tiempos)
    out["GWS_anom"].attrs = dict(
        units="cm", long_name="Anomalía de almacenamiento de agua subterránea (GWSa), lámina de agua equivalente",
        anomaly_baseline=("TWSA respecto a 2004-01-01/2009-12-31 (línea base JPL); a TWSA se le restan diferencias mensuales "
                          "de humedad del suelo y nieve, no anomalías, así que la serie no tiene una línea base común"),
        comment=(f"Hasta {corte}: valores del NetCDF original del semillero sin cambios (COL_GWS_estimations.nc). Desde el mes "
                 "siguiente: GWe = TWSA·scale_factor (JPL RL06.3Mv04) − (ΔSM + ΔSWE) (GLDAS-2.1 Noah), la fórmula de diferencias "
                 "mensuales con la que se reproduce el original (r mediano 0,975). Ver origen_valor."),
        grid_mapping="crs", ancillary_variables="origen_valor")
    out["origen_valor"] = ("time", origen)
    out["origen_valor"].attrs = dict(long_name="procedencia del valor de cada mes", flag_values=np.array([0, 1], dtype="int8"),
                                     flag_meanings="original_del_semillero extension_formula_diferencias_mensuales")
    if "time_bounds" in gr_t:
        out["time_bnds"] = (("time", "nv"), gr_t["time_bounds"].values)
    out["crs"] = ref["crs"]
    out.time.attrs = dict(standard_name="time", long_name="fecha central de la ventana de solución mensual GRACE/GRACE-FO",
                          axis="T", **({"bounds": "time_bnds"} if "time_bnds" in out else {}))
    out.mes_nominal.attrs = dict(long_name="mes nominal de la solución JPL (AAAA-MM)")
    out.lat.attrs = dict(ref.lat.attrs); out.lon.attrs = dict(ref.lon.attrs)
    sol = val.iloc[-1]
    out.attrs = dict(
        Conventions="CF-1.8",
        title=f"GWSa para Colombia, serie original del semillero extendida hasta {t_fin} (diferencias mensuales)",
        summary=(f"Versión ALTERNATIVA (pendiente de decisión con el semillero). Conserva sin cambios los valores del NetCDF "
                 f"original ({t_ini}..{corte}) y agrega {len(nuevos)} meses ({pd.Timestamp(nuevos[0]):%Y-%m}..{t_fin}) "
                 "calculados con la fórmula de diferencias mensuales de UNgroundwater, que es la que reproduce al original. "
                 "La versión estándar es COL_GWS_estimations_2002-2026.nc (método B)."),
        institution="Semillero SIAMS, Universidad Nacional de Colombia",
        source=("Hasta el corte: COL_GWS_estimations.nc (procesamiento original por confirmar). Extensión: JPL GRACE/GRACE-FO Mascon "
                f"CRI RL06.3Mv04 ({grace.name}, doi:10.5067/TEMSC-3JC634) y GLDAS_NOAH025_M v2.1 (doi:10.5067/SXAVCZFAQLNO)."),
        method=("Extensión: GWe = lwe_thickness·scale_factor − (ΔSM + ΔSWE); SM = 0,1·(SoilMoi 0–10 + 10–40 + 40–100 + 100–200 cm), "
                "SWE = 0,1·SWE_inst (cm); Δ = mes calendario menos mes anterior, asignado al mes nominal JPL (variante A3); "
                "GLDAS llevado a 0,5° por interpolación lineal (promedio de las 4 celdas, NaN si falta alguna). Resta un flujo "
                "(cambio mensual) a un estado (anomalía), por eso su amplitud es mayor que la del producto publicado."),
        validation=(f"Fórmula recalculada frente al original en {val.periodo_empalme.iloc[0]}: serie media nacional r = {sol.get('r', float('nan')):.3f}, "
                    f"sesgo = {sol.get('sesgo_cm', float('nan')):+.2f} cm, RMSE = {sol.get('rmse_cm', float('nan')):.2f} cm "
                    "(docs/gwsa_validacion_diferencias.csv). Frente al producto Zenodo de Romero y Piña (2002-04..2023-04) el original "
                    "tiene r mediano por píxel 0,89 y amplitud ×1,28; el método B, r 0,963 y amplitud ×0,98."),
        time_coverage_start=t_ini, time_coverage_end=t_fin,
        period=(f"{t_ini}..{t_fin}, {len(tiempos)} meses con solución. Meses sin solución JPL no interpolados: " + ";".join(m for m in faltantes if m >= t_ini)
                + ". Incluye la brecha GRACE → GRACE-FO 2017-07..2018-05."),
        references=("Romero, P. & Piña, A. (2025) doi:10.1016/j.ejrh.2025.102756; Watkins et al. (2015) doi:10.1002/2014JB011547; "
                    "Rodell et al. (2004) doi:10.1175/BAMS-85-3-381"),
        license="Por confirmar con los autores del producto original; datos NASA de uso libre con atribución.",
        history=f"{ahora}: generado con scripts/06_gwsa_grace_gldas_extendido.py alternativa.",
        geospatial_lat_min=float(ref.lat.min()), geospatial_lat_max=float(ref.lat.max()),
        geospatial_lon_min=float(ref.lon.min()), geospatial_lon_max=float(ref.lon.max()),
        comment="Las celdas costeras donde GLDAS no tiene las 4 subceldas quedan sin dato en los meses nuevos (p. ej. Tumaco).",
    )
    enc = {"GWS_anom": dict(zlib=True, complevel=6, _FillValue=np.float32(np.nan), least_significant_digit=3),
           "time": dict(units="days since 2002-01-01", calendar="standard", dtype="float64")}
    if "time_bnds" in out:
        enc["time_bnds"] = dict(units="days since 2002-01-01", calendar="standard", dtype="float64")
    salida = Path(args.salida)
    out.to_netcdf(salida, encoding=enc)
    print("NetCDF:", rel(salida), f"{salida.stat().st_size / 1e6:.1f} MB", t_ini, "→", t_fin, f"(corte {corte})")

    series = []
    for sede, (la, lo) in SEDES.items():
        i, j, _ = pixel_sede(out["GWS_anom"], la, lo)
        if i is None:
            continue
        s = out["GWS_anom"].isel(lat=i, lon=j).values.astype(float)
        series.append(pd.DataFrame({"sede": sede, "mes_nominal": out.mes_nominal.values,
                                    "fecha": pd.DatetimeIndex(out.time.values).strftime("%Y-%m-%d"),
                                    "GWSa_cm": np.round(s, 3), "origen": np.where(origen == 0, "original", "extension"),
                                    "lat_pixel": float(out.lat[i]), "lon_pixel": float(out.lon[j])}))
    pd.concat(series).to_csv(args.sedes, index=False)
    for c in ("n_meses", "meses_nuevos_con_dato"):
        if c in val:
            val[c] = val[c].astype("Int64")
    val.to_csv(args.validacion, index=False, float_format="%.4f")
    print(val.round(3).to_string())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="accion", required=True)
    d = sub.add_parser("descargar", help="baja GRACE (JPL) y GLDAS (recorte Colombia) desde NASA Earthdata")
    d.add_argument("--inicio", default="2002-01")
    d.add_argument("--fin", default="2026-06")
    p = sub.add_parser("procesar", help="calcula GWSa (método B) y escribe el NetCDF extendido")
    p.add_argument("--grace", default=None, help="archivo JPL mascon (por defecto data/raw/grace/GRCTellus.JPL.*RL06.3M.MSCNv04CRI.nc)")
    p.add_argument("--gldas", default=str(RAW_GLDAS), help="carpeta con GLDAS_NOAH025_M.A*.nc4")
    p.add_argument("--referencia", default=str(REFERENCIA), help="NetCDF original: malla, máscara y validación")
    p.add_argument("--fin", default="2026-06", help="último mes nominal (AAAA-MM)")
    p.add_argument("--salida", default=str(SALIDA_NC))
    p.add_argument("--sedes", default=str(SALIDA_SEDES))
    p.add_argument("--validacion", default=str(SALIDA_VALIDACION))
    q = sub.add_parser("alternativa", help="serie original del semillero + meses nuevos con la fórmula de diferencias")
    q.add_argument("--grace", default=None)
    q.add_argument("--gldas", default=str(RAW_GLDAS))
    q.add_argument("--referencia", default=str(REFERENCIA))
    q.add_argument("--fin", default="2026-06")
    q.add_argument("--salida", default=str(SALIDA_NC_ALT))
    q.add_argument("--sedes", default=str(SALIDA_SEDES_ALT))
    q.add_argument("--validacion", default=str(SALIDA_VALIDACION_ALT))
    a = ap.parse_args(argv)
    if a.accion == "descargar":
        descargar(a.inicio, a.fin)
    elif a.accion == "alternativa":
        procesar_alternativa(a)
    else:
        procesar(a)


if __name__ == "__main__":
    main()
