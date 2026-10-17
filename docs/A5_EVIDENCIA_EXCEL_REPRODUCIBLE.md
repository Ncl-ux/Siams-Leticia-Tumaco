# SIAMS · Evidencia de reproducción A5

## Qué pide literalmente Pedro

**A5 (alta):** Subir los scripts de descarga y procesamiento; separar `data/raw/` y `data/processed/`.
**Criterio de cierre:** "Otra persona regenera un Excel desde cero".

## Prueba de extremo a extremo ya disponible

Los **80 archivos originales `plot_*.csv` de HydroWeb** están separados de los procesados bajo `data/raw/swot/`. Los módulos `scripts/procesar_swot.py` y `scripts/reproducir_excel_swot_a5.py` reconstruyen un Excel completo sin depender de los CSV previamente publicados ni de `app.py`.

Desde PowerShell, en la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe scripts\reproducir_excel_swot_a5.py
.\.venv\Scripts\python.exe -m pytest tests\test_a5_excel_swot.py -q
```

**Salida:** `data/processed/swot/SWOT_A5_reproducido_desde_plot.xlsx`.

**Contenido:** `Resumen`, `Observaciones`, `Fuentes_raw` (con SHA-256, bytes y ruta original), `Diccionario`, `Metodologia`.

**Comprobaciones del ejemplo existente:** 80 CSV originales → 20 tramos → 1.957 registros → 76 alertas **exploratorias**. El libro incluye el procedimiento y sus limitaciones; no interpreta esos 76 casos como mediciones erróneas ni como banderas oficiales RiverSP.

**Reproducir de forma independiente:** otra persona clona el repositorio o descarga la rama publicada, instala `requirements.txt`, ejecuta el comando anterior en un entorno limpio y comprueba las hojas. No necesita los CSV ya procesados ni los Excel originales de NASA POWER para generar este Excel SWOT.

## Qué se puede afirmar, y qué no

✅ **Demostración del criterio operativo de A5:** un Excel reproducible desde originales con script y separación `raw/processed`.

⚠️ **No equivale a reproducibilidad integral de todo SIAMS:** seguimos sin los datos crudos originales y scripts históricos de IDEAM, GRACE/GLDAS, MapBiomas, Landsat, Sentinel e hidrogeoquímica; NASA POWER tiene un descargador nuevo pero la reproducción idéntica de los Excel históricos requiere las coordenadas, rango de fechas y parámetros empleados en cada sede.

⚠️ **A4 es independiente:** completar atributos CF del NetCDF GRACE (unidades, referencia, coordenadas, fuente, línea base, metadatos). No se puede inventar producto/versión o periodo base.

⚠️ **SWOT M7 es independiente:** los `plot` exportados no incluyen las banderas de calidad oficiales de RiverSP. Las alertas por salto de WSE son un control estadístico exploratorio.

**Estado recomendado para la auditoría:** A5 con su criterio *demostrable*; solicitar a Pedro confirmación de si exige además la reproducción desde originales de todas las fuentes, lo que requiere recuperar insumos faltantes. No etiquetar el resto de las fuentes como reproducidas.

## Compatibilidad con el SIAMS existente

- Esta mejora **solo añade** `scripts/reproducir_excel_swot_a5.py`, `tests/test_a5_excel_swot.py` y este documento.
- No sobrescribe `app.py`, `siams/`, `data/`, `requirements.txt`, GRACE, clima, hidrología ni las animaciones.
- El Excel se genera al ejecutar el comando; no se versiona por duplicado salvo decisión expresa del equipo.
- Antes de publicar a GitHub, ejecutar `git status` y revisar permisos de publicación de datos.
