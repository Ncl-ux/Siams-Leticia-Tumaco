# SIAMS — A5: reproducibilidad de la extracción GRACE

## Alcance y separación frente a A4

Este complemento **no altera ni sustituye `COL_GWS_estimations.nc`** y no modifica la lógica de la aplicación. A4 (metadatos CF y cita dentro del NetCDF) corresponde a otro responsable.

`extraer_grace_a5.py` reproduce la parte verificable del notebook `ExtraerDatos_Aguachica.ipynb`: identifica la celda espacial más cercana y extrae la serie completa de `GWS_anom`, preservando fechas, valores no disponibles y saltos temporales. Genera un CSV y un JSON de procedencia, con SHA-256 del NetCDF de entrada y del CSV exportado. No reconstruye el NetCDF desde los productos satelitales primarios.

## Entrada

`data/processed/grace/COL_GWS_estimations.nc` (archivo recibido, 26 107 090 bytes). La copia recibida por el semillero coincide byte a byte con el NetCDF que aparecía en el ZIP completo utilizado para la reorganización anterior:

`adc65487253eba92e4323238dca72b1349a32e640bf89d37ada8cc89ef23782a`

Dimensiones inspeccionadas: `time=244`, `lat=135`, `lon=99`; rango temporal registrado: 2002-05-10 a 2025-05-16. La variable `GWS_anom` no tiene atributo `units` explícito; el artículo y el notebook interpretan las anomalías en centímetros de espesor de agua equivalente. Esta incertidumbre documental es materia de A4 y no se cambia aquí.

**Atención:** el dataset citado en el artículo y publicado en https://zenodo.org/records/14707819 describe 220 fechas y una dimensión latitudinal de 136; por tanto no se debe declarar que el NetCDF recibido es la misma versión sin verificación de sus autores. La procedencia exacta y el procedimiento de actualización hasta 2025 siguen pendientes.

## Ejecutar (desde la raíz del repositorio, en Windows)

```powershell
.\.venv\Scripts\python.exe -m pip install h5py numpy
.\.venv\Scripts\python.exe scripts\extraer_grace_a5.py --lat 8.295 --lon -73.652 --etiqueta Aguachica
.\.venv\Scripts\python.exe -m pytest -q tests\test_a5_grace_extraccion.py
```

La instalación con pip es necesaria **solo si esas librerías no están ya disponibles**. Se generan dos archivos en `data/processed/grace/`: `GRACE_Aguachica_GWSa.csv` y `GRACE_Aguachica_GWSa_procedencia.json`. El script no sobrescribe resultados existentes salvo que se use explícitamente `--sobrescribir`. No hace descargas y no añade carpetas nuevas.

## Verificación

- Identificación de celdas por coordenadas geográficas, vecino más cercano **sin interpolación**.
- Fechas UTC tomadas de la variable `time` y sus atributos reales.
- `dato_faltante` para valores no finitos. `intervalo_mayor_45_dias` como señal temporal exploratoria, **no como bandera científica oficial**.
- Metadatos con huellas digitales, índices de celda y referencias.
- Los datos son señales **regionales**, no niveles medidos de pozos.

## Revisión metodológica del notebook entregado

El notebook **lee** un NetCDF ya calculado; no descarga GRACE/GLDAS ni genera GWSa. Además:

1. Usa una ruta local `D:\\Codigos\\...` que no funciona en otros equipos.
2. En una gráfica de Aguachica aparece un título de Bogotá.
3. Utiliza `Sy=0.15` en las expresiones, pero en una gráfica aparece `Sy = 0.01`.
4. La estimación `max(0, ΔGWSa / Sy)` no equivale por sí sola a recarga real. GWSa está expresada como espesor equivalente de agua y puede responder a procesos de extracción, escorrentía subterránea y variación del almacenamiento; dividir por Sy se relaciona con la variación de nivel freático, bajo supuestos restrictivos. Se requiere una revisión hidrogeológica y un balance para interpretar recarga. **Esta estimación se omite intencionalmente.**
5. Diferencias de fechas por vacíos instrumentales deben conservarse, no rellenarse ni unirse en las gráficas.

## Reproducción completa del NetCDF desde satélites: aún pendiente

El artículo (Romero y Piña, 2025) menciona GRACE/GRACE-FO JPL RL06.3Mv04-CRI, los modelos GLDAS CLSM_F2.5, Noah_v3.6 y VIC_v4.1.2, y la herramienta **UNGroundwater** para estimar anomalías:

- Artículo: https://doi.org/10.1016/j.ejrh.2025.102756
- Datos del artículo: https://doi.org/10.5281/zenodo.14707819
- Herramienta original: https://doi.org/10.5281/zenodo.14708277

Para regenerar el **mismo NetCDF** hacen falta los archivos satelitales y de GLDAS utilizados, periodos de referencia de las anomalías, versiones y procedimientos exactos de remuestreo y sincronización. El artículo por sí solo no identifica todos los parámetros del producto específico recibido. No se debe simular esta etapa ni inventar una equivalencia.

## Estado para Pedro

- **Reproducible:** extracción de series SIAMS desde el NetCDF suministrado, con entrada y salidas rastreables.
- **No reproducible aún:** generación del NetCDF recibido a partir de GRACE + GLDAS y cálculos de recarga del notebook.
- **A4:** apartado independiente, a cargo del compañero.
