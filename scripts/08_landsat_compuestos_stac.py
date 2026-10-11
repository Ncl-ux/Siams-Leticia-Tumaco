#!/usr/bin/env python
"""Compuestos Landsat de mediana con máscara de nubes, por sede y temporada seca.

Cumple los criterios de ``config/landsat_criterios.toml``:

* Landsat 8 y 9, Collection 2 Level-2 (reflectancia superficial, ``landsat-c2-l2``), solo Tier 1.
  Se excluye Landsat 7 (SLC apagado desde 2003). Para períodos anteriores a 2013 habría que
  agregar Landsat 5 y armonizar OLI ↔ TM (p. ej. Roy et al., 2016); no está implementado.
* Solo escenas de la ventana estacional de la sede (misma temporada en todos los años).
* Máscara por píxel con ``QA_PIXEL``: bits 0 relleno, 1 nube dilatada, 2 cirro, 3 nube, 4 sombra y,
  además, confianza de nube media o alta (bits 8–9 ≥ 2); la máscara se amplía 2 píxeles (60 m) para
  quitar bordes de nube que el algoritmo CFMask no marca. Para cada escena se calcula el % del AOI
  (círculo del buffer) despejado y se registra.
* Mediana por píxel de las observaciones despejadas; se informa el % del AOI sin ninguna. Antes de la
  mediana se descartan, píxel por píxel, las observaciones cuyo azul supera en más de 0,04 al azul mínimo
  de ese píxel: son nubes finas o bordes de nube que QA_PIXEL no marcó (en el Pacífico son frecuentes).
  Las superficies brillantes de verdad (arena, techos) conservan sus observaciones porque su mínimo
  también es alto.
* Realce lineal FIJO (mismo rango de reflectancia para todas las sedes y años), color natural
  (B4-B3-B2) y falso color (B6-B5-B4), con norte, barra de escala, fuente y período.

Fuente de datos: catálogo STAC de Microsoft Planetary Computer (copia de USGS Landsat C2 L2),
que no requiere cuenta. También se puede adaptar a Google Earth Engine
(``LANDSAT/LC08/C02/T1_L2`` y ``LANDSAT/LC09/C02/T1_L2``) con la misma lógica.

Dependencias (no las necesita la app): ``pip install pystac-client planetary-computer rasterio pillow``

Uso, desde la raíz del repositorio:

    python scripts/08_landsat_compuestos_stac.py --sede Leticia --temporadas 2023 2024 2025

Salidas en ``Landsat/<Sede>/compuestos/``: ``<sede>_<período>_color_natural.jpg``,
``..._falso_color.jpg``, ``..._escenas.csv`` (todas las escenas consultadas, % del AOI despejado
y si entraron) y ``..._compuesto.json`` (metadatos que lee la app).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from siams.landsat import cargar_criterios, normalizar  # noqa: E402

# Coordenadas de TERRITORIOS (app.py) y carpeta de cada sede dentro de Landsat/.
SEDES = {
    "Arauca": ((7.012222763876252, -70.74338825990411), "Arauca"),
    "La Paz": ((10.390218033322455, -73.20038917337925), "La Paz"),
    "Leticia": ((-4.193717, -69.941001), "Leticia"),
    "Medellín": ((6.262190, -75.576968), "Medellin"),
    "San Andrés": ((12.536552, -81.707935), "San Andres"),
    "Tumaco": ((1.610206, -78.720520), "Tumaco"),
}
PIXEL_M = 30.0
BITS_INVALIDOS = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4)
AMPLIACION_PX = 2
UMBRAL_AZUL_NEBLINA = 0.04
GRIS_SIN_DATO = 190  # píxeles del AOI sin ninguna observación despejada


def mascara_despejado(qa: np.ndarray) -> np.ndarray:
    """True donde el píxel es utilizable según QA_PIXEL (ver docstring del módulo)."""
    invalido = (qa == 0) | ((qa & BITS_INVALIDOS) != 0) | (((qa >> 8) & 3) >= 2)
    nube = ((qa & (BITS_INVALIDOS ^ 1)) != 0) | (((qa >> 8) & 3) >= 2)
    if AMPLIACION_PX:
        r = AMPLIACION_PX
        p = np.pad(nube, r)
        amp = np.zeros_like(nube)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                amp |= p[r + dy:r + dy + nube.shape[0], r + dx:r + dx + nube.shape[1]]
        invalido |= amp
    return ~invalido
BANDAS = ["red", "green", "blue", "nir08", "swir16"]
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "4")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")


def malla_utm(lat, lon, buffer_km):
    zona = int((lon + 180) // 6) + 1
    epsg = (32600 if lat >= 0 else 32700) + zona
    from pyproj import Transformer

    x, y = Transformer.from_crs(4326, epsg, always_xy=True).transform(lon, lat)
    r = buffer_km * 1000.0
    n = int(math.ceil(2 * r / PIXEL_M))
    from rasterio.transform import from_origin

    transform = from_origin(x - r, y + r, PIXEL_M, PIXEL_M)
    yy, xx = np.mgrid[0:n, 0:n]
    cx = (xx + 0.5) * PIXEL_M - r
    cy = r - (yy + 0.5) * PIXEL_M
    circulo = cx ** 2 + cy ** 2 <= r ** 2
    return f"EPSG:{epsg}", transform, n, circulo


def rangos_temporada(meses: list[int], temporada: int) -> tuple[str, str]:
    """Temporada que termina en el año indicado (dic–mar 2024 = dic 2023 a mar 2024)."""
    if meses[0] > meses[-1]:  # cruza el año
        inicio = pd.Timestamp(temporada - 1, meses[0], 1)
    else:
        inicio = pd.Timestamp(temporada, meses[0], 1)
    fin = pd.Timestamp(temporada, meses[-1], 1) + pd.offsets.MonthEnd(0)
    return inicio.strftime("%Y-%m-%d"), fin.strftime("%Y-%m-%d")


def leer(href, crs, transform, n, resampling):
    import rasterio
    from rasterio.vrt import WarpedVRT

    with rasterio.open(href) as src, WarpedVRT(src, crs=crs, transform=transform, width=n, height=n,
                                               resampling=resampling, nodata=0) as vrt:
        return vrt.read(1)


def compuesto_sede(sede, temporadas, criterios, max_escenas, salida_base):
    import planetary_computer
    import pystac_client
    from rasterio.enums import Resampling

    (lat, lon), carpeta = SEDES[sede]
    meses = criterios["ventana_estacional"][normalizar(sede)]
    buffer_km = criterios["buffer_km"][normalizar(sede)]
    cc = criterios["compuestos"]
    crs, transform, n, circulo = malla_utm(lat, lon, buffer_km)
    d = buffer_km / 111.0
    bbox = [lon - d / max(math.cos(math.radians(lat)), 0.2), lat - d, lon + d / max(math.cos(math.radians(lat)), 0.2), lat + d]
    cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1",
                                    modifier=planetary_computer.sign_inplace)
    items = []
    for t in temporadas:
        ini, fin = rangos_temporada(meses, t)
        busq = cat.search(collections=["landsat-c2-l2"], bbox=bbox, datetime=f"{ini}/{fin}",
                          query={"platform": {"in": cc["sensores"]}, "landsat:collection_category": {"eq": "T1"}})
        items += [it for it in busq.items() if pd.Timestamp(it.datetime).month in meses]
    items.sort(key=lambda it: it.properties.get("eo:cloud_cover", 100))
    print(f"{sede}: {len(items)} escenas T1 L8/L9 en la ventana {meses} de {temporadas}", flush=True)

    registros, pilas = [], {b: [] for b in BANDAS}
    for it in items:
        qa = leer(it.assets["qa_pixel"].href, crs, transform, n, Resampling.nearest)
        valido = mascara_despejado(qa)
        cubierto = (qa != 0) & circulo
        desp = 100.0 * (valido & circulo).sum() / circulo.sum()
        usada = desp >= cc["despejado_min_pct_para_compuesto"] and len(pilas["red"]) < max_escenas
        registros.append(dict(id_escena=it.id, fecha=pd.Timestamp(it.datetime).strftime("%Y-%m-%d"),
                              sensor=it.properties.get("platform"), path_row=f"{it.properties.get('landsat:wrs_path')}/{it.properties.get('landsat:wrs_row')}",
                              nubosidad_catalogo_pct=it.properties.get("eo:cloud_cover"),
                              aoi_cubierto_pct=round(100.0 * cubierto.sum() / circulo.sum(), 1),
                              aoi_despejado_pct=round(desp, 1), usada_en_compuesto=usada))
        print(f"  {it.id} {registros[-1]['fecha']} despejado {desp:5.1f}% {'✓' if usada else ''}", flush=True)
        if usada:
            m = valido & circulo
            for b in BANDAS:
                dn = leer(it.assets[b].href, crs, transform, n, Resampling.bilinear)
                pilas[b].append(np.where(m & (dn > 0), dn, 0).astype(np.uint16))

    periodo = f"{rangos_temporada(meses, temporadas[0])[0][:7]}_{rangos_temporada(meses, temporadas[-1])[1][:7]}"
    nombre = f"{normalizar(carpeta).replace(' ', '_')}_{periodo}"
    destino = salida_base / carpeta / "compuestos"
    destino.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(registros).to_csv(destino / f"{nombre}_escenas.csv", index=False)
    if not pilas["red"]:
        print(f"{sede}: ninguna escena con ≥ {cc['despejado_min_pct_para_compuesto']} % del AOI despejado")
        return None

    azul = np.stack(pilas["blue"]).astype(np.float32)
    azul[azul == 0] = np.nan
    azul = azul * 2.75e-5 - 0.2  # escala oficial C2 L2
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        neblina = azul > (np.nanmin(azul, axis=0) + UMBRAL_AZUL_NEBLINA)
    del azul
    refl = {}
    for b in BANDAS:
        pila = np.stack(pilas[b]).astype(np.float32)
        pila[(pila == 0) | neblina] = np.nan
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            refl[b] = np.nanmedian(pila, axis=0) * 2.75e-5 - 0.2  # escala oficial C2 L2
        pilas[b] = None
    n_obs = np.isfinite(refl["red"]).astype(np.uint8)
    sin_dato = 100.0 * ((~np.isfinite(refl["red"])) & circulo).sum() / circulo.sum()
    publicable = sin_dato <= cc["sin_dato_max_pct"]

    fechas = [r["fecha"] for r in registros if r["usada_en_compuesto"]]
    sensores = sorted({r["sensor"] for r in registros if r["usada_en_compuesto"]})
    meta = dict(
        sede=sede, periodo=periodo.replace("_", " a "), temporadas=temporadas,
        ventana_meses=meses, buffer_km=buffer_km, crs=crs, pixel_m=PIXEL_M,
        producto="Landsat Collection 2 Level-2 Tier 1 (reflectancia superficial), vía Microsoft Planetary Computer",
        sensores=sensores, escenas_consultadas=len(registros), escenas_usadas=len(fechas),
        primera_fecha=min(fechas), ultima_fecha=max(fechas),
        mascara="QA_PIXEL bits 0–4 (relleno, nube dilatada, cirro, nube, sombra) y confianza de nube ≥ media, ampliada 60 m",
        metodo=f"mediana por píxel de observaciones despejadas, sin las que superan en {UMBRAL_AZUL_NEBLINA} el azul mínimo del píxel",
        aoi_sin_observacion_pct=round(sin_dato, 2), publicable=bool(publicable),
        criterio_publicacion=f"AOI sin observación ≤ {cc['sin_dato_max_pct']} %",
        realce_color_natural=cc["realce_color_natural"], realce_falso_color=cc["realce_falso_color"],
        imagenes={}, script="scripts/08_landsat_compuestos_stac.py",
    )
    for tipo, bandas, rango, rotulo in (
        ("color_natural", ("red", "green", "blue"), cc["realce_color_natural"], "Color natural B4-B3-B2"),
        ("falso_color", ("swir16", "nir08", "red"), cc["realce_falso_color"], "Falso color B6-B5-B4 (SWIR1-NIR-rojo)"),
    ):
        canales = []
        for b, (lo, hi) in zip(bandas, rango.values()):
            v = np.clip((refl[b] - lo) / (hi - lo), 0, 1)
            canales.append(np.where(np.isfinite(v), v * 255, GRIS_SIN_DATO).astype(np.uint8))
        rgb = np.dstack(canales)
        rgb[~circulo] = 255
        archivo = destino / f"{nombre}_{tipo}.jpg"
        dibujar(rgb, archivo, sede, meta, rotulo, rango, buffer_km)
        meta["imagenes"][tipo] = archivo.name
    with open(destino / f"{nombre}_compuesto.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(f"{sede}: compuesto con {len(fechas)} escenas; AOI sin observación {sin_dato:.2f} % → "
          f"{'publicable' if publicable else 'NO publicable'}")
    return meta


def _fuente(tam):
    from PIL import ImageFont

    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVuSans.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(f, tam)
        except OSError:
            continue
    return ImageFont.load_default(tam)


def dibujar(rgb, archivo, sede, meta, rotulo, rango, buffer_km, ancho=1000):
    """Imagen con norte, barra de escala, leyenda de realce, fuente y período (tildes legibles)."""
    from PIL import Image, ImageDraw

    img = Image.fromarray(rgb).resize((ancho, ancho), Image.Resampling.LANCZOS)
    alto_pie = 150
    lienzo = Image.new("RGB", (ancho, ancho + alto_pie), "white")
    lienzo.paste(img, (0, 0))
    dr = ImageDraw.Draw(lienzo)
    f, fs = _fuente(22), _fuente(17)
    # Norte (la malla UTM está orientada al norte de la cuadrícula).
    x0, y0 = ancho - 70, 30
    dr.polygon([(x0, y0), (x0 - 16, y0 + 44), (x0, y0 + 32), (x0 + 16, y0 + 44)], fill="black")
    dr.text((x0 - 8, y0 + 48), "N", fill="black", font=f)
    # Barra de escala de 10 km.
    m_por_px = 2 * buffer_km * 1000 / ancho
    largo = int(10000 / m_por_px)
    xb, yb = 30, ancho - 40
    dr.rectangle([xb, yb, xb + largo // 2, yb + 10], fill="black")
    dr.rectangle([xb + largo // 2, yb, xb + largo, yb + 10], outline="black", fill="white")
    dr.rectangle([xb - 8, yb - 30, xb + largo + 60, yb + 18], fill="white")
    dr.rectangle([xb, yb, xb + largo // 2, yb + 10], fill="black")
    dr.rectangle([xb + largo // 2, yb, xb + largo, yb + 10], outline="black", fill="white")
    for x, t in ((xb, "0"), (xb + largo // 2, "5"), (xb + largo, "10 km")):
        dr.text((x - 4, yb - 26), t, fill="black", font=fs)
    realce = ", ".join(f"{k} {a:g}–{b:g}" for k, (a, b) in rango.items())
    fs = _fuente(16)
    lineas = [
        f"SIAMS · {sede} · {rotulo} · buffer {buffer_km} km",
        f"Mediana de {meta['escenas_usadas']} escenas despejadas ({meta['primera_fecha']} a {meta['ultima_fecha']}), "
        f"meses {', '.join(str(m) for m in meta['ventana_meses'])}",
        f"Landsat 8/9 C2 L2 Tier 1, máscara QA_PIXEL · realce fijo (reflectancia): {realce}",
        f"AOI sin observación despejada (gris): {meta['aoi_sin_observacion_pct']:.1f} % · {meta['crs']}, 30 m (vista ~{m_por_px:.0f} m/px)",
        "Fuente: USGS/NASA Landsat, vía Microsoft Planetary Computer",
    ]
    for k, t in enumerate(lineas):
        dr.text((20, ancho + 12 + 27 * k), t, fill="black", font=f if k == 0 else fs)
    lienzo.save(archivo, quality=88, optimize=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sede", action="append", choices=list(SEDES), help="se puede repetir; por defecto todas")
    ap.add_argument("--temporadas", nargs="+", type=int, default=[2023, 2024, 2025],
                    help="años en que termina cada temporada (dic–mar 2024 → 2024)")
    ap.add_argument("--max-escenas", type=int, default=24, help="tope de escenas por compuesto (las menos nubladas)")
    a = ap.parse_args(argv)
    criterios = cargar_criterios()
    for sede in a.sede or list(SEDES):
        compuesto_sede(sede, sorted(a.temporadas), criterios, a.max_escenas, RAIZ / "Landsat")


if __name__ == "__main__":
    main()
