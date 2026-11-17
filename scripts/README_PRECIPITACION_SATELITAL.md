# SIAMS — CHIRPS e IMERG, fase 5

No se sustituyen los módulos GRACE, precipitación IDEAM, homogeneidad A1 ni tendencias. El panel nuevo está al final de **Clima** para las siete sedes; utiliza los CSV realmente disponibles. Las series históricas que ya utiliza GRACE Leticia se conservan y se distinguen de las series nuevas. No se modifica ni se automatiza aquí IMERG Late ni CHIRPS v2.

## En Windows, desde la raíz del repositorio

```powershell
python scripts/17_auditar_precipitacion_satelital.py
python -m pytest tests/test_precipitacion_satelital.py -q
python scripts/12_actualizacion_semanal.py --fuentes chirps
python scripts/17_auditar_precipitacion_satelital.py
```

CHIRPS usa la cuadrícula puntual original de 0.05° del producto Final v3. Excluye el mes en curso; conserva observaciones previas válidas si falla el servidor; los píxeles marcados NoData se guardan en `chirps_<sede>.nodata.json` y no como cero. Se prueban de nuevo los últimos tres meses cerrados. Para reintentar el NoData histórico de una sede, eliminar **solo** su `.nodata.json` (no su CSV) y volver a ejecutar. No se desplaza automáticamente un punto costero tierra adentro.

## IMERG Final: autenticación y primera descarga

1. Crear o usar la cuenta gratuita en https://urs.earthdata.nasa.gov/ (autorizar acceso al archivo GES DISC cuando NASA lo solicite). No publicar las credenciales.
2. `python -m pip install earthaccess h5py`
3. Probar un intervalo pequeño de meses publicados, con autenticación interactiva si no existe una sesión. Ejemplo:

```powershell
python scripts/16_actualizar_imerg.py --desde 2025-01-01 --hasta 2025-03-01
python scripts/17_auditar_precipitacion_satelital.py
```

4. Cuando esa prueba sea satisfactoria, completar de 1998 hasta el último mes efectivamente publicado en CMR:

```powershell
python scripts/16_actualizar_imerg.py
```

La descarga histórica completa puede ser pesada. Puede hacerse en bloques con `--max-meses 24`, reanudables. Los resultados se conservan tras cada mes. Solo se admiten granules mensuales V07B de GPM_3IMERGM, identificados por el nombre de archivo; se validan unidad y malla. Se descargan los HDF5 oficiales completos uno por mes, se extraen las siete celdas puntuales en una sola lectura y se eliminan los temporales. Tasa mm/h × 24 × días del mes (incluido febrero bisiesto). CSV nuevos `imerg_final_<sede>.csv`, con coordenadas del píxel y nombre del granule. No mezcla con las series históricas Leticia. Si CMR o NASA devuelven un archivo inesperado, se conserva lo anterior y se reporta error. `imerg_consulta.json` informa meses publicados, procesados y errores. Verificar que los nombres/rutas reales devueltos por NASA coincidan en la primera corrida autenticada.

Para GitHub Actions, agregar los secretos `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD` en Settings > Secrets and variables > Actions. La tarea semanal existente incluye un paso IMERG limitado a 24 meses por corrida para no monopolizar el workflow; sin secretos muestra advertencia y omite IMERG. Ninguna contraseña debe ir en Git. El cron despliega solo cuando la rama predeterminada contenga la actualización y Actions esté habilitado. Validar ejecución manual antes de confiar en su automatización.

## Fuentes y límites

- UCSB Climate Hazards Center, CHIRPS v3 Final: https://chc.ucsb.edu/data/chirps3 ; descarga original del repositorio https://data.chc.ucsb.edu/products/CHIRPS/v3.0/ . Datos mensuales estimados por celda terrestre; publicación final usualmente durante el mes siguiente.
- NASA GPM IMERG Final mensual V07: https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07 ; https://gpm.nasa.gov/data/directory . El retraso de publicación es de varios meses. Extracción de la celda más cercana, no promedio de cuenca. IMERG Late no se usa para rellenar Final.
- NASA POWER diario: lector de CSV existente; solo se suma si todos los días del mes tienen precipitación válida. IDEAM Bogotá usa `mensual.csv` y solo meses completos; Leticia usa la estación 48015050 con control mensual previo. Las comparaciones se hacen únicamente con fechas comunes; no se certifica homogeneidad ni precisión por comparación de fuentes de rejilla. No se modifican las fórmulas estadísticas existentes.

**Verificación pendiente**: descarga real con acceso Earthdata, cobertura de CSV locales (no estaban en el ZIP de código suministrado), interfaz Streamlit, ejecución del cron en GitHub. Pruebas unitarias offline usan datos sintéticos y los insumos IDEAM ya suministrados; no prueban disponibilidad remota.
