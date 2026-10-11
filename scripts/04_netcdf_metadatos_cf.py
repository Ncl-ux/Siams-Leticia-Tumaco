"""Agrega metadatos CF al NetCDF de anomalías de agua subterránea (GWSa).

Observación 3.2.e de la revisión: ``COL_GWS_estimations.nc`` no traía ningún
atributo. Este script NO cambia los valores (float64, compresión sin pérdida);
solo agrega atributos, quita referencias a variables de límites inexistentes
(``bounds`` sin ``time_bounds``/``lat_bounds``) y comprime.

Lo que se sabe y lo que se infiere (ver data/README.md):
* Unidades: cm de lámina de agua equivalente (inferido: rango -71 a 84 cm,
  coherente con mascones JPL que se entregan en cm; la app ya lo trataba en cm).
* Producto GRACE: los atributos huérfanos del archivo (lat.valid_min = -89.75,
  time.bounds) coinciden con la malla de 0,5° de los mascones JPL RL06.x
  (INFERIDO, por confirmar con los autores).
* Periodo de referencia de la anomalía: la media 2004–2009 de cada píxel es
  ≈ 0 (media espacial 0,09 cm), como en los mascones JPL (2004.0–2009.999).
  INFERIDO, por confirmar.
* GLDAS: modelo y versión POR CONFIRMAR (probablemente Noah 2.1).
* Malla de ~0,12°: es una malla de distribución, no la resolución efectiva
  de GRACE (cientos de km).

Uso:
    python scripts/04_netcdf_metadatos_cf.py ENTRADA.nc SALIDA.nc
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

import numpy as np
import xarray as xr

POR_CONFIRMAR = "por confirmar"


def agregar_metadatos(ds: xr.Dataset, archivo_origen: str) -> xr.Dataset:
    ds = ds.copy()
    for nombre in ("time", "lat", "lon"):
        ds[nombre].attrs.pop("bounds", None)
    ds["lat"].attrs.update(units="degrees_north", long_name="latitud", standard_name="latitude", axis="Y")
    ds["lat"].attrs.pop("valid_min", None)
    ds["lat"].attrs.pop("valid_max", None)
    ds["lon"].attrs.update(units="degrees_east", long_name="longitud", standard_name="longitude", axis="X")
    ds["time"].attrs.update(
        long_name="fecha central de la ventana de solución mensual GRACE/GRACE-FO",
        standard_name="time", axis="T",
        comment="Las fechas son puntos medios de ventanas de solución (no días de medición). "
                "Hay meses sin solución, entre ellos el vacío GRACE/GRACE-FO de julio de 2017 a mayo de 2018.",
    )
    ds["GWS_anom"].attrs.update(
        units="cm",
        long_name="Anomalía de almacenamiento de agua subterránea (GWSa), lámina de agua equivalente",
        comment="GWSa = TWSa (GRACE/GRACE-FO) - [humedad del suelo + nieve + agua en el dosel] (GLDAS). "
                "Señal regional: la resolución efectiva de GRACE es de cientos de km. "
                "En llanuras de inundación (p. ej. Amazonas) puede incluir almacenamiento superficial "
                "(río y várzea) que GLDAS no resta. Unidad cm inferida del rango de valores (por confirmar).",
        anomaly_baseline="2004-01-01/2009-12-31 (inferido: la media 2004-2009 por píxel es ~0; por confirmar)",
        grid_mapping="crs",
    )
    ds["crs"] = xr.DataArray(np.int32(0), attrs={
        "grid_mapping_name": "latitude_longitude",
        "epsg_code": "EPSG:4326",
        "semi_major_axis": 6378137.0,
        "inverse_flattening": 298.257223563,
    })
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    ds.attrs.update({
        "Conventions": "CF-1.8",
        "title": "Anomalías de almacenamiento de agua subterránea (GWSa) para Colombia",
        "summary": "Producto GWSa derivado de GRACE/GRACE-FO menos componentes de GLDAS, usado por la "
                   "plataforma SIAMS para extraer la serie del píxel válido más cercano a cada sede.",
        "institution": "Semillero SIAMS, Universidad Nacional de Colombia (redistribución); "
                       "autoría del producto: Romero y Piña (2025), " + POR_CONFIRMAR,
        "source": "GRACE/GRACE-FO (probablemente mascones JPL RL06.x, malla 0,5°; inferido, " + POR_CONFIRMAR +
                  ") menos GLDAS (modelo y versión " + POR_CONFIRMAR + ")",
        "references": "Romero, P. & Piña, A. (2025). GRACE-based analysis of groundwater sustainability in the "
                      "tropics. Journal of Hydrology: Regional Studies, 62, 102756. "
                      "https://doi.org/10.1016/j.ejrh.2025.102756 ; Rodell et al. (2004) GLDAS, "
                      "https://doi.org/10.1175/BAMS-85-3-381 ; Watkins et al. (2015) JPL mascons, "
                      "https://doi.org/10.1002/2014JB011547",
        "history": f"{ahora}: metadatos CF agregados con scripts/04_netcdf_metadatos_cf.py a partir de "
                   f"{archivo_origen} (valores sin modificar; compresión zlib sin pérdida). "
                   "Procesamiento previo: " + POR_CONFIRMAR + ".",
        "geospatial_lat_min": float(ds["lat"].min()),
        "geospatial_lat_max": float(ds["lat"].max()),
        "geospatial_lon_min": float(ds["lon"].min()),
        "geospatial_lon_max": float(ds["lon"].max()),
        "time_coverage_start": str(np.datetime_as_string(ds["time"].values.min(), unit="D")),
        "time_coverage_end": str(np.datetime_as_string(ds["time"].values.max(), unit="D")),
        "license": "Por confirmar con los autores del producto (Romero y Piña, 2025) antes de redistribuir.",
        "comment": "Malla de ~0,12°; no representa la resolución efectiva de GRACE. Los campos marcados "
                   "'por confirmar' deben completarse con los autores del producto.",
    })
    return ds


def main(entrada: str, salida: str) -> None:
    with xr.open_dataset(entrada) as ds:
        ds = ds.load()
    nuevo = agregar_metadatos(ds, entrada.rsplit("/", 1)[-1])
    codif = {"GWS_anom": {"zlib": True, "complevel": 5, "shuffle": True, "_FillValue": np.nan, "dtype": "float64"},
             "time": {"units": "days since 2002-01-01 00:00:00", "calendar": "standard", "dtype": "float64", "_FillValue": None},
             "lat": {"_FillValue": None}, "lon": {"_FillValue": None}}
    nuevo.to_netcdf(salida, encoding=codif, format="NETCDF4")
    with xr.open_dataset(salida) as chk:
        assert np.array_equal(chk["GWS_anom"].values, ds["GWS_anom"].values, equal_nan=True)
        assert np.array_equal(chk["time"].values, ds["time"].values)
    print(f"Escrito {salida}: valores idénticos al original.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
