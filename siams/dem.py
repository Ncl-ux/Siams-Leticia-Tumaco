"""Elevación de terreno con Copernicus GLO-30 (DSM, 30 m) y su corrección de sesgo.

Las teselas son públicas en el bucket ``copernicus-dem-30m`` de AWS (sin credenciales).
GLO-30 es un modelo de superficie: en zona urbana o con dosel puede quedar por encima del
terreno. En Leticia se estimó un sesgo de ~1,5 m frente a puntos de control, por lo que se
resta ``SESGO_DEM_M`` a todas las sedes mientras no exista una cota levantada.
"""
from __future__ import annotations

import math

SESGO_DEM_M = 1.5
URL_TESELA = (
    "https://copernicus-dem-30m.s3.amazonaws.com/"
    "Copernicus_DSM_COG_10_{lat}_00_{lon}_00_DEM/Copernicus_DSM_COG_10_{lat}_00_{lon}_00_DEM.tif"
)
FUENTE_DEM = "Copernicus DEM GLO-30 (ESA/Airbus, © DLR e.V. 2010-2014 y © Airbus Defence and Space GmbH 2014-2018, licencia Copernicus)"


def nombre_tesela(lat: float, lon: float) -> tuple[str, str]:
    """Rótulos de la tesela 1°×1° que contiene el punto (esquina suroeste)."""
    la, lo = math.floor(lat), math.floor(lon)
    return (f"{'N' if la >= 0 else 'S'}{abs(la):02d}", f"{'E' if lo >= 0 else 'W'}{abs(lo):03d}")


def url_tesela(lat: float, lon: float) -> str:
    la, lo = nombre_tesela(lat, lon)
    return URL_TESELA.format(lat=la, lon=lo)


def elevacion_glo30(lat: float, lon: float) -> float:
    """Valor del píxel GLO-30 que contiene el punto (m, EGM2008). Requiere rasterio."""
    import rasterio  # dependencia solo de los scripts de procesamiento

    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", AWS_NO_SIGN_REQUEST="YES"):
        with rasterio.open(url_tesela(lat, lon)) as src:
            valor = next(src.sample([(lon, lat)]))[0]
    return float(valor)


def cota_terreno(dem_m: float, sesgo_m: float = SESGO_DEM_M) -> float:
    return round(dem_m - sesgo_m, 2)


def cota_nivel(cota_terreno_msnm, profundidad_nivel_m):
    """Cota del nivel de agua = cota del terreno − profundidad al agua."""
    return cota_terreno_msnm - profundidad_nivel_m


def profundidad_desde_presion(prof_sensor_m, carga_m):
    """Para transductores: profundidad al agua = profundidad del sensor − columna de agua sobre él."""
    return prof_sensor_m - carga_m
