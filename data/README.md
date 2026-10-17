# SIAMS · Registro de procedencia y reproducibilidad (A5)

## Ubicaciones

- `data/raw/swot/{Leticia,Arauca,Medellin,Tumaco}/`: 80 exportaciones `plot_*.csv` originales recibidas de HydroWeb. No se editan.
- `data/raw/nasa_power/`: destino previsto para respuestas JSON originales de NASA POWER; **no había respuestas originales** en el ZIP proporcionado. El descargador permite obtener nuevas respuestas, sujetas a parámetros y disponibilidad de la API.
- `data/raw/ideam/`, `grace/`, `mapbiomas/`, `landsat/`, `sentinel/`: ubicaciones previstas, que se crearán cuando se consigan los originales. **No se proporcionaron las descargas originales ni el procesamiento histórico íntegro de estas fuentes.** No son fuentes reconstruidas.
- `data/processed/clima/`: seis Excel NASA POWER y dos IDEAM que consumía SIAMS, conservados sin alterar sus valores durante la migración.
- `data/processed/swot/`: 20 CSV consolidados por `reach_id` y resumen M7. El resumen recibido se conserva. `scripts/procesar_swot.py` puede regenerar nuevas versiones desde los 80 plot; el conteo de 76 alertas exploratorias coincide con los archivos conservados; revisar diferencias de precisión y metadatos antes de reemplazar resultados.
- `data/processed/grace/`: NetCDF GWSa derivado y cinco tablas de Leticia; se desconocen las entradas primarias exactas y sus permisos deben revisarse antes de publicar.
- `data/processed/hidrogeoquimica/`: tabla fisicoquímica y envolvente, sin alterar los registros.
- `data/processed/mapbiomas/` y `landsat/`: CSV derivados tal como se recibieron; los GIF permanecen en sus carpetas visuales.

## Procedencia y advertencias

| Conjunto | Fuente declarada | Raw original | Reproducible desde raw disponible | Pendiente |
|---|---|---|---|---|
| SWOT | HydroWeb (productos SWOT) | Sí, 80 `plot_*.csv` | Sí, consolidación exploratoria | Banderas oficiales RiverSP, confirmación Mira/Rosario y regla temporal exacta de anomalías |
| NASA POWER | API NASA POWER Daily | No en ZIP; descargable en nuevas consultas | Se genera un Excel nuevo documentado, **no se garantiza equivalencia con el Excel histórico** | Coordenadas/periodos exactos de las consultas originales y contraste hoja a hoja |
| IDEAM | IDEAM (DHIME) | No | No | Descargas originales, estaciones, procesamiento histórico, licencias |
| GRACE/GLDAS | NetCDF GWSa recibido | No (producto derivado) | No | Productos y versiones, línea base, scripts científicos, metadatos CF |
| MapBiomas | Exportaciones de MapBiomas | No, solo tablas ya exportadas | No | Colección, consulta y procesamiento original |
| Landsat / Sentinel | Productos procesados | No | No | Scripts/escenas/mascaras originales |
| Hidrogeoquímica | Informes internos | Dataset analítico recibido | No con raw primario | Permisos y procedencia por informe |

Para datos de comunidades, pozos y mediciones de campo, revisar consentimiento **antes de `git push` a un repositorio público**. Un ZIP completo no constituye autorización de publicación.

El archivo `docs/migracion_a5.csv` registra las 150 rutas de archivo migradas o incorporadas y el SHA-256 **tomado al momento de migración**. Es un inventario de integridad, no una licencia, garantía de calidad ni trazabilidad original completa.

## Ejecución

Desde la raíz del proyecto con el entorno Python del repositorio:

```powershell
.\.venv\Scripts\python.exe scripts\verificar_a5.py
.\.venv\Scripts\python.exe scripts\procesar_swot.py --out data\processed\swot_regenerado_revision
.\.venv\Scripts\python.exe scripts\nasa_power.py descargar --sede leticia --lat -4.215 --lon -69.94 --inicio 20250101 --fin 20251231
.\.venv\Scripts\python.exe scripts\nasa_power.py procesar --raw data\raw\nasa_power\nasa_power_leticia_20250101_20251231.json --out data\processed\clima\nasa_power_leticia_reconstruido_2025.xlsx
```

Las coordenadas anteriores son **ejemplo de ejecución**, no una certificación de las coordenadas usadas en los archivos históricos. No sobrescribas los Excel operativos sin comparar resultados.

Los campos negativos de radiación o códigos de faltantes se controlan en el procesamiento; las unidades solares se obtienen de los **metadatos de la respuesta** y se convierten a MJ/m²/día cuando corresponde. Las marcas de tiempo de NASA Daily no deben desplazarse automáticamente como si fueran UTC local de una sonda.

Si faltan originales, añadirlos en `raw` con fuente, fecha, licencia, resolución, unidad, sistema de referencia y script usado. Los datos grandes o sujetos a autorización pueden almacenarse fuera de Git con ruta recuperable y controles de acceso.
