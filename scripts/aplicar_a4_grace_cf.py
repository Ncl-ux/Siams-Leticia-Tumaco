#!/usr/bin/env python3
"""A4 · Completa metadatos CF del NetCDF GRACE en uso y la referencia en app.py.

No altera datos ni cálculos. Se niega a cambiar un NetCDF distinto al original
entregado para SIAMS; verifica las matrices antes y después de aplicar metadatos.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import shutil
import tempfile

import numpy as np
from netCDF4 import Dataset, num2date

RAIZ = Path(__file__).resolve().parents[1]
RUTA_NC = RAIZ / 'data' / 'processed' / 'grace' / 'COL_GWS_estimations.nc'
RUTA_APP = RAIZ / 'app.py'
SHA_ORIGEN = 'adc65487253eba92e4323238dca72b1349a32e640bf89d37ada8cc89ef23782a'
SHA_VALORES = 'a5562da4444f40b1c5c49de489a5cbc97c103edac8a3b63ce3cfea79f936359e'
SHA_EJES = {
    'lat': 'e47f4b55315f58f76642d2d8072540b6519eb3bfe23f3f45b8c246b9a48595b1',
    'lon': 'fa50a6ae06ae5b5dee57aac3f500f0bfa48dceed5ae12352decf3fbed8598337',
    'time': 'd31c240246aee5396de595c062d074fc2638fcc5530d6ac38ea424e0c827a6b3',
}
DOI_ARTICULO = 'https://doi.org/10.1016/j.ejrh.2025.102756'
DOI_DATOS_RELACIONADOS = 'https://doi.org/10.5281/zenodo.14707819'
MARCADOR = 'SIAMS_A4_REFERENCIA_CF'


def sha_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open('rb') as f:
        for parte in iter(lambda: f.read(1024 * 1024), b''):
            h.update(parte)
    return h.hexdigest()


def sha_variable(var) -> str:
    # Este producto es float64 de 244 x 135 x 99: lectura de 26 MB.
    datos = np.asarray(var[:], dtype=np.float64)
    return hashlib.sha256(np.ascontiguousarray(datos).tobytes()).hexdigest()


def inspect_netcdf(ruta: Path, exige_cf: bool = False) -> None:
    with Dataset(str(ruta), 'r') as ds:
        assert 'GWS_anom' in ds.variables, 'Falta GWS_anom'
        assert tuple(ds.variables['GWS_anom'].dimensions) == ('time', 'lat', 'lon')
        assert ds.variables['GWS_anom'].shape == (244, 135, 99)
        assert sha_variable(ds.variables['GWS_anom']) == SHA_VALORES, 'Los valores GWSa no coinciden con el original'
        for eje, checksum in SHA_EJES.items():
            assert sha_variable(ds.variables[eje]) == checksum, f'Las coordenadas {eje} cambiaron'
        if exige_cf:
            assert ds.getncattr('Conventions') == 'CF-1.8'
            assert DOI_ARTICULO in ds.getncattr('references')
            assert 'no documentado' in ds.getncattr('anomaly_reference_period').lower()
            assert ds.variables['GWS_anom'].getncattr('units') == 'cm'
            assert ds.variables['lon'].getncattr('units') == 'degrees_east'
            assert ds.variables['lat'].getncattr('units') == 'degrees_north'
            assert 'crs' in ds.variables
            assert ds.variables['GWS_anom'].getncattr('grid_mapping') == 'crs'
            for nombre in ('time', 'lat', 'lon'):
                var = ds.variables[nombre]
                if 'bounds' in var.ncattrs():
                    assert var.getncattr('bounds') in ds.variables, f'bounds inexistentes en {nombre}'


def preparar_app(texto: str) -> str:
    inicio = texto.find('elif seccion == "Agua subterránea (GRACE)":')
    if inicio < 0:
        raise RuntimeError('No se encontró sección GRACE; no se modificó el proyecto')
    fin = texto.find('elif seccion == "Hidrogeoquímica":', inicio)
    if fin < 0:
        raise RuntimeError('No se encontró límite de sección GRACE; no se modificó el proyecto')
    bloque = texto[inicio:fin]
    if MARCADOR in bloque:
        return texto  # idempotente
    subtitulo = '    st.caption("GWSa + índice de sequía de agua subterránea (GGDI) · GRACE/GRACE-FO + GLDAS")'
    if subtitulo not in bloque:
        raise RuntimeError('Cambió el encabezado GRACE; revisar app.py manualmente sin sobrescribirlo')
    adicional = (
        '\n    # ' + MARCADOR + '\n'
        '    st.caption(\n'
        '        "Referencia metodológica: Romero, P. y Piña, A. (2025), "\n'
        '        "GRACE-based analysis of groundwater sustainability in the tropics. "\n'
        '        "Journal of Hydrology: Regional Studies, 62, 102756. "\n'
        '        "https://doi.org/10.1016/j.ejrh.2025.102756"\n'
        '    )\n'
        '    st.caption(\n'
        '        "Producto regional: el archivo de SIAMS cubre 2002–2025. "\n'
        '        "La versión exacta de los insumos y el periodo base de la anomalía "\n'
        '        "no están documentados en el NetCDF original; se requiere confirmación de los autores. "\n'
        '        "Los resultados no representan niveles de pozos y pueden incluir efectos de agua superficial."\n'
        '    )'
    )
    bloque = bloque.replace(subtitulo, subtitulo + adicional, 1)
    # No eliminar ni reescribir el resto de la sección para preservar las modificaciones posteriores.
    return texto[:inicio] + bloque + texto[fin:]


def completar_cf(ruta: Path) -> None:
    with Dataset(str(ruta), 'a') as ds:
        v = ds.variables['GWS_anom']
        ds.setncatts({
            'Conventions': 'CF-1.8',
            'title': 'Colombia - groundwater storage anomaly (GWSa) - SIAMS',
            'summary': 'Estimaciones regionales de anomalia del almacenamiento subterraneo (GWSa), en centimetros equivalentes de agua; no son niveles piezometricos. Es posible contribucion de aguas superficiales en zonas inundables.',
            'institution': 'Semillero de Investigacion de Aguas y Modelacion Subterranea (SIAMS) - Universidad Nacional de Colombia',
            'source': 'Archivo GWSa suministrado al proyecto SIAMS. Metodo de referencia: residuo de almacenamiento de agua total GRACE/GRACE-FO menos componentes terrestres GLDAS, segun Romero y Pina (2025). No se ha verificado la trazabilidad de procesamiento especifica de este archivo.',
            'references': ('Romero, P., & Pina, A. (2025). GRACE-based analysis of groundwater sustainability in the tropics. Journal of Hydrology: Regional Studies, 62, 102756. ' + DOI_ARTICULO),
            'related_dataset': DOI_DATOS_RELACIONADOS,
            'related_dataset_note': 'Zenodo registra una version de dimensiones y cobertura temporal diferentes; no se afirma que sea identica a COL_GWS_estimations.nc de SIAMS.',
            'methodology_satellite_product': 'El ARTICULO describe JPL GRACE/GRACE-FO mascons RL06.3Mv04-CRI; la version utilizada para ESTE NetCDF no esta verificada.',
            'methodology_gldas_models': 'El ARTICULO describe CLSM_F2.5, Noah_v3.6 y VIC_v4.1.2; la configuracion exacta de ESTE NetCDF no esta verificada.',
            'anomaly_reference_period': 'No documentado en el NetCDF original; requiere confirmacion de los autores.',
            'anomaly_reference_status': 'unverified',
            'source_product_version_status': 'unverified for this specific NetCDF',
            'spatial_reference': 'Latitude and longitude in decimal degrees. The original file does not explicitly document the geodetic datum/ellipsoid; no EPSG code has been asserted.',
            'spatial_resolution_note': 'Paso nominal de malla ~0.12 grados; resolucion efectiva GRACE regional, cientos de kilometros. No confundir malla con resolucion fisica.',
            'history': (datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') + ' | SIAMS A4: atributos CF y cita metodologica incorporados; datos GWS_anom, tiempos y coordenadas sin cambio.'),
        })
        v.setncatts({
            'long_name': 'Groundwater storage anomaly (equivalent water thickness)',
            'units': 'cm',
            'comment': 'Anomalia regional obtenida como estimacion residual; no equivale a nivel de un pozo ni a profundidad de acuifero.',
            'grid_mapping': 'crs',
        })
        ds.variables['lat'].setncatts({'standard_name': 'latitude', 'long_name': 'latitude', 'units': 'degrees_north', 'axis': 'Y'})
        ds.variables['lon'].setncatts({'standard_name': 'longitude', 'long_name': 'longitude', 'units': 'degrees_east', 'axis': 'X'})
        ds.variables['time'].setncatts({'standard_name': 'time', 'long_name': 'time', 'axis': 'T'})
        for nombre in ('lat', 'lon', 'time'):
            var = ds.variables[nombre]
            if 'bounds' in var.ncattrs() and var.getncattr('bounds') not in ds.variables:
                var.delncattr('bounds')
        if 'crs' not in ds.variables:
            crs = ds.createVariable('crs', 'i4', ())
            crs.assignValue(0)
        else:
            crs = ds.variables['crs']
        crs.setncattr('grid_mapping_name', 'latitude_longitude')
        fecha = ds.variables['time']
        tiempos = num2date([float(fecha[0]), float(fecha[-1])], units=fecha.units, calendar=getattr(fecha, 'calendar', 'standard'))
        ds.setncatts({
            'time_coverage_start': tiempos[0].strftime('%Y-%m-%dT%H:%M:%S'),
            'time_coverage_end': tiempos[1].strftime('%Y-%m-%dT%H:%M:%S'),
            'geospatial_lat_min': float(np.min(ds.variables['lat'][:])),
            'geospatial_lat_max': float(np.max(ds.variables['lat'][:])),
            'geospatial_lon_min': float(np.min(ds.variables['lon'][:])),
            'geospatial_lon_max': float(np.max(ds.variables['lon'][:])),
        })


def main() -> None:
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--verificar', action='store_true', help='Solo valida NetCDF y app.py')
    opciones = args.parse_args()
    if not RUTA_NC.is_file() or not RUTA_APP.is_file():
        raise SystemExit('Falta data/processed/grace/COL_GWS_estimations.nc o app.py; no se modifico nada.')
    texto_app = RUTA_APP.read_text(encoding='utf-8-sig')
    if opciones.verificar:
        inspect_netcdf(RUTA_NC, exige_cf=True)
        assert DOI_ARTICULO in texto_app and MARCADOR in texto_app, 'No se encontro la referencia A4 en app.py'
        print('A4 OK: atributos CF, integridad GWSa y cita en app.py comprobados')
        return

    inspect_netcdf(RUTA_NC)
    if MARCADOR in texto_app:
        print('A4 ya esta aplicado en app.py. Validando NetCDF existente...')
        inspect_netcdf(RUTA_NC, exige_cf=True)
        print('A4 ya esta completo: sin cambios.')
        return
    if sha_archivo(RUTA_NC) != SHA_ORIGEN:
        raise SystemExit('SEGURIDAD: el NetCDF local es diferente al original recibido. No se sobrescribe: revisa si alguien ya modifico A4.')
    nuevo_app = preparar_app(texto_app)
    compile(nuevo_app, str(RUTA_APP), 'exec')

    respaldos = Path.home() / 'Documents'
    if not respaldos.is_dir():
        respaldos = Path.home()
    respaldo_nc = respaldos / 'SIAMS_A4_GRACE_original_respaldo.nc'
    respaldo_app = respaldos / 'SIAMS_A4_app_original_respaldo.py'
    if respaldo_nc.exists() or respaldo_app.exists():
        raise SystemExit('Ya existe un respaldo A4 en Documentos; para protegerlo no se sobreescribe.')

    temporal_nc = None
    temporal_app = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.siams_a4_', suffix='.nc', dir=RUTA_NC.parent, delete=False) as fh:
            temporal_nc = Path(fh.name)
        shutil.copy2(RUTA_NC, temporal_nc)
        completar_cf(temporal_nc)
        inspect_netcdf(temporal_nc, exige_cf=True)
        with tempfile.NamedTemporaryFile(prefix='.siams_a4_', suffix='.py', mode='w', encoding='utf-8', dir=RUTA_APP.parent, delete=False) as fh:
            temporal_app = Path(fh.name)
            fh.write(nuevo_app)
        shutil.copy2(RUTA_NC, respaldo_nc)
        shutil.copy2(RUTA_APP, respaldo_app)
        os.replace(temporal_nc, RUTA_NC)
        os.replace(temporal_app, RUTA_APP)
        print('A4 APLICADO: metadatos CF + referencia cientifica en app.py')
        print('Respaldos externos:', respaldo_nc, 'y', respaldo_app)
        print('La matriz GWS_anom permanece IDENTICA al archivo original.')
    finally:
        for ruta in (temporal_nc, temporal_app):
            if ruta is not None and ruta.exists():
                ruta.unlink()


if __name__ == '__main__':
    main()
