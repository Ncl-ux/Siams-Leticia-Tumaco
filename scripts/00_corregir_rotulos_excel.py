"""Corrige rótulos de unidades en los Excel procesados SIN tocar los valores.

Aplicado una sola vez en la versión corregida (ver CAMBIOS.md). Es idempotente:
si se corre de nuevo no cambia nada.

* NASA POWER: ``radiacion_solar_kWh_m2_dia`` → ``radiacion_solar_MJ_m2_dia``
  (la API declara MJ/m^2/day para ALLSKY_SFC_SW_DWN en la comunidad AG;
  se verificó descargando de nuevo los mismos días).
* NASA POWER: ``precipitacion_mm_dia`` → ``precipitacion_mm_mes`` en
  ``P_mensual`` y ``Regimen_P``, y → ``precipitacion_mm_anio`` en ``P_anual``.
* IDEAM (Tumaco y Arauca): ``precipitacion`` → nombre con unidad por hoja.
* Se agrega la hoja ``Diccionario`` (columna, descripción, unidad, fuente).
* Arauca, hoja ``Control_faltantes``: la columna «Fechas ausentes» tenía
  formato de fecha y un conteo de 322 días se veía como «1900-11-17»; se
  cambia el formato de celda a número entero.

Uso:
    python scripts/00_corregir_rotulos_excel.py "Analisis Hidro"
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from openpyxl import load_workbook

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from siams.unidades import (  # noqa: E402
    DICCIONARIO_IDEAM, DICCIONARIO_NASA, RENOMBRES_FILAS_RESUMEN,
    RENOMBRES_IDEAM_POR_HOJA, RENOMBRES_NASA_POR_HOJA,
)


def _renombrar_encabezados(ws, mapa: dict) -> int:
    cambios = 0
    for celda in ws[1]:
        if celda.value in mapa:
            celda.value = mapa[celda.value]
            cambios += 1
    return cambios


def _escribir_diccionario(wb, filas) -> None:
    if "Diccionario" in wb.sheetnames:
        del wb["Diccionario"]
    ws = wb.create_sheet("Diccionario")
    ws.append(["columna", "descripcion", "unidad", "fuente"])
    for fila in filas:
        ws.append(list(fila))
    for col, ancho in zip("ABCD", (34, 90, 14, 40)):
        ws.column_dimensions[col].width = ancho


def _valores_en_cache(ruta: Path) -> dict:
    """Valores calculados de las celdas con fórmula (openpyxl los descarta al guardar)."""
    con_formula = load_workbook(ruta)
    calculados = load_workbook(ruta, data_only=True)
    cache = {}
    for ws in con_formula:
        for fila in ws.iter_rows():
            for c in fila:
                if c.data_type == "f":
                    cache[(ws.title, c.coordinate)] = calculados[ws.title][c.coordinate].value
    return cache


def _restaurar_cache(ruta: Path, cache: dict) -> None:
    """Vuelve a escribir el valor en caché (<v>) de cada fórmula en el XML."""
    if not cache:
        return
    with zipfile.ZipFile(ruta) as z:
        libro = z.read("xl/workbook.xml").decode("utf-8")
        rels = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
        hojas = {}
        for nombre, rid in re.findall(r'<sheet[^>]*name="([^"]+)"[^>]*r:id="([^"]+)"', libro):
            destino = re.search(rf'Id="{rid}"[^>]*Target="([^"]+)"|Target="([^"]+)"[^>]*Id="{rid}"', rels)
            objetivo = (destino.group(1) or destino.group(2)).lstrip("/")
            hojas[nombre] = objetivo if objetivo.startswith("xl/") else "xl/" + objetivo
        contenido = {n: z.read(n) for n in z.namelist()}
    for (hoja, coord), valor in cache.items():
        if valor is None or hoja not in hojas:
            continue
        xml = contenido[hojas[hoja]].decode("utf-8")
        xml = re.sub(rf'(<c r="{coord}"[^>]*>)(<f>[^<]*</f>)<v\s*/?>(</v>)?',
                     lambda m: f"{m.group(1)}{m.group(2)}<v>{valor!r}</v>", xml, count=1)
        contenido[hojas[hoja]] = xml.encode("utf-8")
    tmp = Path(tempfile.mkstemp(suffix=".xlsx")[1])
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre, datos in contenido.items():
            z.writestr(nombre, datos)
    shutil.move(tmp, ruta)


def corregir(ruta: Path) -> list[str]:
    cache = _valores_en_cache(ruta)
    wb = load_workbook(ruta)
    es_nasa = ruta.name.upper().startswith("NASA_POWER")
    mapas = RENOMBRES_NASA_POR_HOJA if es_nasa else RENOMBRES_IDEAM_POR_HOJA
    log = []
    for hoja, mapa in mapas.items():
        if hoja in wb.sheetnames:
            n = _renombrar_encabezados(wb[hoja], mapa)
            if n:
                log.append(f"{hoja}: {n} encabezado(s)")
    if es_nasa and "Resumen_estadistico" in wb.sheetnames:
        ws = wb["Resumen_estadistico"]
        for fila in ws.iter_rows(min_col=1, max_col=1):
            for c in fila:
                if c.value in RENOMBRES_FILAS_RESUMEN:
                    c.value = RENOMBRES_FILAS_RESUMEN[c.value]
                    log.append("Resumen_estadistico: fila de radiación")
    if "Control_faltantes" in wb.sheetnames:
        ws = wb["Control_faltantes"]
        encabezados = [c.value for c in ws[1]]
        if "Fechas ausentes" in encabezados:
            col = encabezados.index("Fechas ausentes") + 1
            for (c,) in ws.iter_rows(min_row=2, min_col=col, max_col=col):
                if c.number_format != "0":
                    c.number_format = "0"
                    log.append("Control_faltantes: formato numérico en «Fechas ausentes»")
    _escribir_diccionario(wb, DICCIONARIO_NASA if es_nasa else DICCIONARIO_IDEAM)
    wb.save(ruta)
    _restaurar_cache(ruta, cache)
    return log


def main(carpeta: str) -> None:
    for ruta in sorted(Path(carpeta).glob("*.xlsx")):
        print(ruta.name, "→", "; ".join(sorted(set(corregir(ruta)))) or "sin cambios de rótulo")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(RAIZ / "Analisis Hidro"))
