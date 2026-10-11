# Diccionario de datos de SIAMS

Responde a las observaciones **3.2.c, 3.2.d, 3.2.e, 3.2.h y A2–A5** de la revisión. Para cada archivo
se indica fuente, variables, unidades, convención de tiempo, periodo, procesamiento y licencia.
Lo que no se pudo establecer queda marcado **«por confirmar»**.

> Por compatibilidad con la app, los archivos siguen en sus carpetas originales (`Analisis Hidro/`,
> `Landsat/`, etc.). La meta es moverlos a `data/raw/` (crudos o la consulta exacta para obtenerlos) y
> `data/processed/` (productos), con nombres sin espacios ni tildes (ver `CONTRIBUTING.md`).

## 1. Convenciones generales

| Tema | Convención |
|---|---|
| Separador decimal | Punto en archivos; coma solo en textos de la app |
| Coordenadas | WGS84 geográficas (EPSG:4326). Mapas QGIS de ubicación: MAGNA-SIRGAS 2018 / Origen Nacional (EPSG:9377), **por verificar en cada PDF** |
| Faltantes | Celda vacía (NaN). Un cero de lluvia es un dato válido, no un faltante |
| Año completo | Para agregados anuales se exige al menos el 75 % de la mediana de días por año (función `agregar_serie_anual`). Los años parciales (p. ej. 2026 en NASA POWER y 2025 en IDEAM Tumaco) **no** entran en tendencias |

### Zona horaria y «día» de cada fuente

| Fuente | Qué significa una fecha |
|---|---|
| IDEAM (DHIME), lluvia | **Día pluviométrico**: total acumulado en las 24 horas que terminan a las 07:00 hora local del día indicado (convención IDEAM; confirmar en los metadatos de DHIME de cada estación). No coincide con el día calendario |
| IDEAM, temperatura y HR | Valor diario de la estación (hora local de Colombia, UTC−5) |
| NASA POWER | Día calendario en **hora solar local** (`time_standard = LST` en la respuesta de la API) |
| GRACE/GRACE-FO (NetCDF) | La fecha (`2002-05-10T12:00`) es el **punto medio** de la ventana de solución mensual. Hay 35 meses sin dato, incluido el vacío GRACE → GRACE-FO (julio 2017 – mayo 2018) |
| SWOT (tarjetas y animaciones) | Fecha y hora de paso en **UTC**. Hora de Colombia = UTC − 5 h |
| Sentinel-2 / Landsat | Fecha de adquisición de la escena (UTC) |

## 2. Clima NASA POWER — `Analisis Hidro/NASA_POWER_<SEDE>_FINAL*.xlsx`

- **Fuente:** NASA POWER, API v2 diaria por punto, comunidad **AG** (agroclimatología): <https://power.larc.nasa.gov/>.
  Parámetros: `PRECTOTCORR, T2M, T2M_MAX, T2M_MIN, RH2M, WS2M, PS, ALLSKY_SFC_SW_DWN`.
- **Resolución:** malla de 0,5° × 0,625° (MERRA-2) y 1° (radiación CERES/GEWEX). Es un **reanálisis/estimación
  satelital**, no una medición de estación.
- **Coordenadas de consulta** (las de la sede en `scripts/01_descarga_nasa_power.py`): Leticia −4,1937 / −69,9410;
  Tumaco 1,6102 / −78,7205; Medellín 6,2607 / −75,5796; San Andrés 12,5366 / −81,7079; Arauca 7,0122 / −70,7434;
  La Paz 10,3902 / −73,2004.
- **Periodo:** Tumaco 1992-01-01 a 2026; demás sedes 2000-01-01 a 2026. **2026 es parcial** y NASA lo reemplaza
  cuando consolida los datos casi en tiempo real.
- **Reproducción:** `python scripts/01_descarga_nasa_power.py --sede tumaco --inicio 1992-01-01 --fin 2025-12-31` reproduce
  exactamente los valores diarios del Excel (verificado el 11/10/2026).
- **Licencia:** uso libre con reconocimiento al proyecto NASA LaRC POWER.

| Hoja | Columna | Unidad | Descripción |
|---|---|---|---|
| `Datos_diarios` | `fecha` | — | Día (hora solar local) |
| | `precipitacion_mm_dia` | mm/día | `PRECTOTCORR`, lluvia corregida |
| | `temperatura_media_C`, `temperatura_maxima_C`, `temperatura_minima_C` | °C | `T2M`, `T2M_MAX`, `T2M_MIN` a 2 m |
| | `humedad_relativa_pct` | % | `RH2M` |
| | `viento_2m_m_s` | m/s | `WS2M` |
| | `presion_superficie_kPa` | kPa | `PS` |
| | `radiacion_solar_MJ_m2_dia` | **MJ/m²/día** | `ALLSKY_SFC_SW_DWN`. **Antes se rotulaba kWh/m²/día por error**; 1 kWh = 3,6 MJ |
| `P_mensual`, `Regimen_P` | `precipitacion_mm_mes` | mm/mes | Suma mensual / promedio multianual por mes. **Antes `precipitacion_mm_dia`** |
| `P_anual` | `precipitacion_mm_anio` | mm/año | Suma anual. **Incluye el año parcial 2026**: no usarlo para promedios |
| `Climatologia_mensual` | `precipitacion_mm_dia` | mm/día | Promedio diario por mes del año |
| `Radiacion_mensual` | `radiacion_solar_MJ_m2_dia` | MJ/m²/día | Promedio mensual |
| `Diccionario` | — | — | Hoja nueva con esta misma información |

Los nombres de columna exactos por hoja están en `siams/unidades.py` (`DICCIONARIO_NASA`).

**Advertencias de calidad (ver `docs/tendencias_homogeneidad.csv`):**
- En Tumaco NASA POWER suma ~1.130 mm/año frente a ~2.835 mm/año de IDEAM, llueve en el 98,5 % de los días
  («llovizna» típica de baja resolución) y su serie anual tiene un punto de cambio hacia 2005 (Pettitt p < 0,001).
  La tendencia decreciente (−11 mm/año, p de Mann-Kendall 0,015) **no es significativa** con la corrección de
  Hamed-Rao (p = 0,10).
- La radiación de Leticia muestra un punto de cambio hacia 2010.
- En San Andrés la celda está dominada por el mar (Tmáx y Tmín difieren ~0,5 °C).
- Falta validar NASA POWER contra IDEAM, ANA (Tabatinga) y CHIRPS/IMERG (revisión 3.2.b / M6).

## 3. Clima IDEAM — `Analisis Hidro/ANALISIS_HIDROMETEOROLOGICO_<Sede>.xlsx`

**Fuente:** IDEAM – DHIME <http://dhime.ideam.gov.co/atencionciudadano/>. Unidades: precipitación en mm,
temperatura en °C, humedad relativa en %. La hoja `Fuentes` lista estación, código, periodo y archivo crudo.

### Tumaco

| Variable | Estación | Periodo | Observación |
|---|---|---|---|
| Precipitación | COCO EL [51030020] | 1985-01-01 a 2025-07-30 | **Serie inhomogénea, ver abajo** |
| Temperatura media, máxima y mínima | CCCP DEL PACÍFICO [51035020] | 1992 a 2020-10 | Tmín con posible punto de cambio (~2005) |
| Humedad relativa | GRANJA EL MIRA [51025090] | 2016-09 a 2022-06 | 848 registros (~40 % de completitud); distancia a la sede por confirmar |

Faltan en la hoja `Fuentes` de Tumaco la latitud, longitud y distancia de cada estación a la sede (sí están en Arauca).
Columnas renombradas: `P_mensual` y `Regimen_P` → `precipitacion_mm_mes`; `P_anual` → `precipitacion_mm_anio`.

#### ⚠️ Inhomogeneidad de la lluvia de COCO EL [51030020]

**Los valores crudos no se modificaron.** La serie se marca como inhomogénea en `siams/calidad.py` y la app:
1. muestra una advertencia en «Clima» y en «Análisis de tendencias»;
2. calcula la tendencia también para el **tramo homogéneo 1995–2024**;
3. marca con una línea vertical el año del cambio en la gráfica.

| Evidencia | 1985–1994 | 1995–2024 |
|---|---|---|
| Días con lluvia registrados con decimales | 51–96 % (1985–1993), 21 % en 1994 | 0 % |
| Lámina media por día lluvioso | ~11 mm | ~19 mm |
| Total anual medio | ~1.570 mm (1985–1991) | ~3.740 mm (2015–2024); 5.976 mm en 2023 |

| Prueba (serie anual) | 1985–2024 | 1995–2024 |
|---|---|---|
| Mann-Kendall, p | 0,00002 | 0,108 |
| Hamed-Rao, p | 0,00047 | 0,190 |
| Pendiente de Sen | +56,1 mm/año | +34,4 mm/año |
| Pettitt, p (año de cambio) | 0,0006 (1998) | 0,25 |
| SNHT, p | 0,0005 | 0,0005 (por los años extremos 2023–2024) |
| Conclusión | **No concluyente** (salto de registro) | Sin tendencia significativa; tramo «dudoso» por SNHT |

Detalle y pasos pendientes: `docs/homogeneidad_tumaco.md`.

### Arauca

Precipitación MATEZAMURO [37050040] (principal) con VILLANUEVA [37050050] y AEROPUERTO SANTIAGO PÉREZ
[37055010] como contraste; temperatura del aeropuerto. Descarga de julio de 2026. La hoja `Metodologia`
documenta umbrales (75 % de días por mes, 90 % por año) y que la HR mínima es inferida. Se corrigió el formato
de la columna «Fechas ausentes» de `Control_faltantes` (mostraba 1900-11-17 en lugar de 322 días).

## 4. Agua subterránea — `COL_GWS_estimations.nc`

| Campo | Valor |
|---|---|
| Variable | `GWS_anom(time, lat, lon)`, anomalía de almacenamiento de agua subterránea |
| Unidad | cm de lámina de agua equivalente (**inferida** por la magnitud; por confirmar) |
| Malla | ~0,12°, lat −4,14 a 12,27, lon −78,90 a −66,98 (EPSG:4326, variable `crs`) |
| Tiempo | 244 meses, 2002-05 a 2025-05, fecha = punto medio de la ventana GRACE |
| Producto | GRACE/GRACE-FO (mascones JPL RL06.x, **inferido**) menos humedad del suelo, nieve y dosel de GLDAS (**modelo y versión por confirmar**) |
| Periodo de referencia de la anomalía | 2004–2009 (**inferido**; por confirmar) |
| Metodología | Romero, P. y Piña, A. (2025). *Journal of Hydrology: Regional Studies*, 62, 102756. <https://doi.org/10.1016/j.ejrh.2025.102756> |
| Licencia | Por confirmar con los autores |

La resolución efectiva de GRACE es de cientos de kilómetros: la serie es **regional** (el píxel de Leticia tiene
r = 0,997 con uno ubicado 1° al norte) y no representa el nivel de un pozo. En la llanura del Amazonas puede incluir
almacenamiento superficial. Los atributos CF se agregaron con `scripts/04_netcdf_metadatos_cf.py` sin cambiar
valores (compresión sin pérdida: 25 MB → 4,6 MB).

## 5. Coberturas

| Archivo | Fuente | Unidad | Notas |
|---|---|---|---|
| `Coberturas MapBio/<SEDE>/*.csv` | MapBiomas Colombia | ha (**asumida** por el código; el CSV no la declara) | Colección **por confirmar**. Hay nombres con «Copia de» y «Probidencia» |
| `Landsat/<Sede>/Areas_coberturas_por_fecha.csv` | Landsat 8/9 C2 L2, clasificación propia (Colab) | ha | El área clasificada cambia con la nubosidad: compare en % del área clasificada (vista por defecto en la app) |
| `Landsat/<Sede>/Control_escenas.csv` | Ídem | — | ID de escena LC08/LC09 L2SP, nubosidad, fracción útil, motivo de descarte |

## 6. Sensores remotos (solo animaciones e imágenes)

| Archivo | Fuente | Notas |
|---|---|---|
| `Gif/*_SWOT_*.mp4` | SWOT vía HydroWeb | Convertidos de GIF a MP4 (69 MB → 4 MB). Faltan las tablas por tramo (`reach_id`, WSE, ancho, banderas de calidad) |
| `Tarjeta Tecnica Swot/*.png` | SWOT vía HydroWeb | Fechas en UTC |
| `Sentinel/Arauca/*.mp4` | Copernicus Sentinel-2 | NDVI, MNDWI, SCL 2025. La carpeta `Sentinel/Leticia /` se eliminó: eran copias idénticas de las de Arauca |

## 7. Productos generados por los scripts

| Archivo | Script | Contenido |
|---|---|---|
| `data/processed/anuales/*_anual.csv` | `02_agregados_anuales.py` | Serie anual por variable (suma de lluvia en mm/año; promedios en su unidad), solo años completos |
| `docs/tendencias_homogeneidad.csv` | `03_tendencias_homogeneidad.py` | MK, Hamed-Rao, Sen, Pettitt y SNHT por sede, fuente y variable |
