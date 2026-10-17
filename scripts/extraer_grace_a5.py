"""SIAMS A5: extracción reproducible de GWSa de un NetCDF recibido.

No reproduce el NetCDF desde GRACE/GLDAS, no edita datos de origen,
no modifica los metadatos CF (A4) y no calcula recarga de acuíferos.

Ejemplo (raíz SIAMS):
    .venv\\Scripts\\python.exe scripts\\extraer_grace_a5.py --lat 8.295 --lon -73.652 --etiqueta Aguachica

Dependencias: numpy, h5py. Instalación si hace falta:
    .venv\\Scripts\\python.exe -m pip install h5py numpy
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import h5py
import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
DEFAULT_NC = RAIZ / 'data' / 'processed' / 'grace' / 'COL_GWS_estimations.nc'
DEFAULT_SALIDA = RAIZ / 'data' / 'processed' / 'grace'
DOI_ARTICULO = 'https://doi.org/10.1016/j.ejrh.2025.102756'
ZENODO_REFERENCIA = 'https://doi.org/10.5281/zenodo.14707819'


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open('rb') as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloque)
    return h.hexdigest()


def _texto_attr(valor):
    if isinstance(valor, bytes):
        return valor.decode('utf-8')
    if isinstance(valor, np.ndarray):
        if valor.size == 1:
            return _texto_attr(valor.item())
        return str(valor.tolist())
    return str(valor)


def fechas_desde_netcdf(valores, unidades: str, calendario: str):
    if calendario.lower() not in ('gregorian', 'standard', 'proleptic_gregorian'):
        raise ValueError('Calendario no compatible sin conversión adicional: ' + calendario)
    patron = re.fullmatch(r'days since (\d{4}-\d\d-\d\d)(?:[T ](\d\d:\d\d:\d\d))?(?:\+00:00|Z)?', unidades.strip())
    if patron is None:
        raise ValueError('Unidad temporal no reconocida: ' + unidades)
    inicio = datetime.fromisoformat(patron.group(1) + 'T' + (patron.group(2) or '00:00:00')).replace(tzinfo=timezone.utc)
    return [inicio + timedelta(days=float(d)) for d in valores]


def _nombre_seguro(etiqueta: str) -> str:
    base = unicodedata.normalize('NFKD', etiqueta).encode('ascii', 'ignore').decode('ascii')
    base = re.sub('[^A-Za-z0-9_-]+', '_', base).strip('_')
    if not base:
        raise ValueError('Etiqueta vacía o sin caracteres utilizables.')
    return base[:70]


def extraer_serie(archivo: Path, latitud: float, longitud: float):
    """Lee directamente el contenedor HDF5-NetCDF sin alterar su contenido.

    No interpola entre celdas ni rellena los meses ausentes.
    """
    archivo = Path(archivo)
    if not archivo.is_file():
        raise FileNotFoundError(f'No se encontró NetCDF: {archivo}')
    with h5py.File(archivo, 'r') as ds:
        obligatorios = ('time', 'lat', 'lon', 'GWS_anom')
        faltan = [v for v in obligatorios if v not in ds]
        if faltan:
            raise ValueError('Faltan variables del NetCDF: ' + ', '.join(faltan))
        lat = np.asarray(ds['lat'][:], dtype=float)
        lon = np.asarray(ds['lon'][:], dtype=float)
        tiempo = ds['time']
        unidades = _texto_attr(tiempo.attrs.get('units', ''))
        calendario = _texto_attr(tiempo.attrs.get('calendar', 'gregorian'))
        fechas = fechas_desde_netcdf(tiempo[:], unidades, calendario)
        lon_busqueda = longitud % 360 if np.nanmin(lon) >= 0 else ((longitud + 180) % 360) - 180
        iy = int(np.argmin(np.abs(lat - latitud)))
        ix = int(np.argmin(np.abs(lon - lon_busqueda)))
        datos = ds['GWS_anom']
        if datos.shape != (len(fechas), len(lat), len(lon)):
            raise ValueError(f'Dimensiones inesperadas de GWS_anom: {datos.shape}. Se espera (time, lat, lon)')
        serie = np.asarray(datos[:, iy, ix], dtype=float)
        attr_unidades_variable = datos.attrs.get('units')

    filas = []
    ultima = None
    for fecha, valor in sorted(zip(fechas, serie), key=lambda r: r[0]):
        salto_dias = (fecha - ultima).total_seconds() / 86400 if ultima is not None else None
        filas.append({
            'fecha_utc': fecha.isoformat(),
            'anio_mes': fecha.strftime('%Y-%m'),
            'latitud_celda': float(lat[iy]),
            'longitud_celda': float(lon[ix]),
            'gws_anom_valor_original': float(valor) if np.isfinite(valor) else '',
            'dato_faltante': int(not np.isfinite(valor)),
            'dias_desde_observacion_anterior': round(salto_dias, 6) if salto_dias is not None else '',
            'intervalo_mayor_45_dias': int(salto_dias > 45) if salto_dias is not None else 0,
        })
        ultima = fecha
    metadatos = {
        'tipo_proceso': 'Extracción espacial por vecino más cercano de un NetCDF ya procesado',
        'archivo_entrada': archivo.name,
        'sha256_entrada': sha256_archivo(archivo),
        'variable': 'GWS_anom',
        'unidades_en_variable_netcdf': _texto_attr(attr_unidades_variable) if attr_unidades_variable is not None else None,
        'unidades_desde_articulo_y_notebook': 'cm de espesor de agua equivalente; no certificado en la variable del NetCDF',
        'latitud_solicitada': float(latitud),
        'longitud_solicitada': float(longitud),
        'latitud_celda': float(lat[iy]),
        'longitud_celda': float(lon[ix]),
        'indice_lat': iy,
        'indice_lon': ix,
        'observaciones_totales': len(filas),
        'observaciones_validas': sum(1 for f in filas if not f['dato_faltante']),
        'periodo_inicio': filas[0]['fecha_utc'] if filas else None,
        'periodo_fin': filas[-1]['fecha_utc'] if filas else None,
        'saltos_temporales_mayores_45_dias': sum(f['intervalo_mayor_45_dias'] for f in filas),
        'metodo': 'Celda más cercana; sin interpolación ni imputación; unidades no agregadas al NetCDF',
        'referencia_articulo': DOI_ARTICULO,
        'referencia_zenodo_version_diferente': ZENODO_REFERENCIA,
        'nota_zenodo': 'No se presume identidad entre esta versión y los archivos del registro citado.',
        'advertencia': 'No es medición de un pozo ni estimación validada de recarga.',
    }
    return filas, metadatos


def exportar(archivo: Path, latitud: float, longitud: float, etiqueta: str, carpeta: Path, sobrescribir: bool = False):
    filas, meta = extraer_serie(archivo, latitud, longitud)
    carpeta = Path(carpeta)
    if not carpeta.is_dir():
        raise FileNotFoundError(f'Carpeta de salida no existe: {carpeta}')
    base = 'GRACE_' + _nombre_seguro(etiqueta) + '_GWSa'
    ruta_csv = carpeta / (base + '.csv')
    ruta_json = carpeta / (base + '_procedencia.json')
    if not sobrescribir and (ruta_csv.exists() or ruta_json.exists()):
        raise FileExistsError(f'La salida ya existe. Revisa primero los archivos, o usa --sobrescribir: {base}')
    campos = list(filas[0].keys()) if filas else []
    with ruta_csv.open('w', encoding='utf-8-sig', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(filas)
    meta.update({'etiqueta': etiqueta, 'archivo_salida_csv': ruta_csv.name, 'sha256_csv': sha256_archivo(ruta_csv)})
    ruta_json.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return ruta_csv, ruta_json, meta


def main():
    p = argparse.ArgumentParser(description='Extrae GWSa de un NetCDF existente de forma reproducible (A5, no A4).')
    p.add_argument('--archivo', type=Path, default=DEFAULT_NC)
    p.add_argument('--lat', type=float, default=8.295, help='Latitud de interés en grados decimales')
    p.add_argument('--lon', type=float, default=-73.652, help='Longitud de interés en grados decimales')
    p.add_argument('--etiqueta', default='Aguachica')
    p.add_argument('--salida', type=Path, default=DEFAULT_SALIDA)
    p.add_argument('--sobrescribir', action='store_true')
    a = p.parse_args()
    csv_salida, json_salida, meta = exportar(a.archivo,a.lat,a.lon,a.etiqueta,a.salida,a.sobrescribir)
    print(f"GRACE A5: {meta['observaciones_validas']}/{meta['observaciones_totales']} observaciones válidas")
    print(f"Celda utilizada: ({meta['latitud_celda']:.6f}, {meta['longitud_celda']:.6f})")
    print('CSV:', csv_salida)
    print('Procedencia:', json_salida)
    print('Nota: esto reproduce la extracción del NetCDF, NO la generación del NetCDF desde GRACE/GLDAS.')


if __name__ == '__main__':
    main()
