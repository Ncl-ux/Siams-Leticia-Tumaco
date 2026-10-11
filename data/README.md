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
| GRACE/GRACE-FO (NetCDF) | La fecha (`2002-05-10T12:00`) es el **punto medio** de la ventana de solución mensual; el NetCDF extendido trae además `mes_nominal` (dos ventanas tienen el punto medio en otro mes: 2012-01-01 → 2011-12 y 2015-04-27 → 2015-05). Hay 33 meses sin solución en 2002-04..2026-06, incluido el vacío GRACE → GRACE-FO (julio 2017 – mayo 2018), que no se interpolan |
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

## 4. Agua subterránea — GWSa GRACE/GLDAS

Hay **dos versiones extendidas hasta 2026-06** y la elección entre ellas está **pendiente de decidir con el semillero**
(ver `CAMBIOS.md`, sección 9). La app usa por defecto el método estándar (4.1) y en la página «Agua subterránea
(GRACE)» tiene un selector para ver la serie original extendida (4.2); en «Análisis de tendencias» se usa la versión
elegida en ese selector. El original del semillero (4.3) se conserva como respaldo: la app lo lee solo si faltan los
extendidos (o si `SIAMS_ARCHIVO_GWS` apunta a él, lo que además oculta el selector).

| | 4.1 Método estándar (B) | 4.2 Serie original extendida (diferencias) |
|---|---|---|
| Fórmula | TWSA − anomalías (respecto a 2004–2009) de humedad del suelo, dosel y nieve | TWSA − cambio mensual (ΔSM + ΔSWE) |
| Cómo se construye | Recalculado de forma homogénea 2002-04 a 2026-06 | Valores del original hasta 2025-04 + 14 meses nuevos (2025-05 a 2026-06) |
| Frente al producto publicado (Zenodo) | r mediano por píxel 0,963, amplitud ×0,98 | Original: r mediano 0,89, amplitud ×1,28 |
| Continuidad con lo que ya mostraba la app | Cambia los valores históricos (Arauca y La Paz: −35–40 % de desviación estándar) | Idéntico hasta 2025-04 |
| Tumaco | Hasta 2026-06 | Termina en 2025-04 (ver 4.2) |

### 4.1 `data/processed/gwsa/COL_GWS_estimations_2002-2026.nc` (en uso)

| Campo | Valor |
|---|---|
| Variable | `GWS_anom(time, lat, lon)`, float32, **cm** de lámina de agua equivalente. Además: `mes_nominal(time)` (AAAA-MM), `time_bnds`, `factor_escala_negativo(lat, lon)` y `crs` |
| Malla y máscara | Idénticas al original (~0,12°, 135 × 99, 6.153 píxeles válidos). La señal viene de una malla de 0,5° remuestreada por vecino más cercano |
| Tiempo | **2002-04 a 2026-06**, 258 meses con solución; fecha = punto medio de la ventana JPL; agrupar por `mes_nominal` |
| Meses sin dato | 33 meses sin solución JPL **no se interpolan** (no tienen paso temporal): 2002-06, 2002-07, 2003-06, 2011-01, 2011-06, 2012-05, 2012-10, 2013-03, 2013-08, 2013-09, 2014-02, 2014-07, 2014-12, 2015-06, 2015-10, 2015-11, 2016-04, 2016-09, 2016-10, 2017-02, **2017-07 a 2018-05 (brecha GRACE → GRACE-FO)**, 2018-08 y 2018-09. Desde 2018-10 hasta 2026-06 no falta ningún mes |
| TWSA | NASA JPL GRACE/GRACE-FO Mascon CRI **RL06.3Mv04** (`TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4`, PO.DAAC, doi:10.5067/TEMSC-3JC634), archivo `GRCTellus.JPL.200204_202607.GLO.RL06.3M.MSCNv04CRI.nc` (creado 2026-09-08, md5 `431986da0c7be4c7c5b22bffd99d059f`). `lwe_thickness × scale_factor` |
| Componentes | **GLDAS-2.1 Noah 0,25° mensual** (`GLDAS_NOAH025_M` v2.1, GES DISC, doi:10.5067/SXAVCZFAQLNO), 2002-01 a 2026-06, recorte OPeNDAP de Colombia: `SoilMoi0_10cm_inst + SoilMoi10_40cm_inst + SoilMoi40_100cm_inst + SoilMoi100_200cm_inst`, `CanopInt_inst`, `SWE_inst` (kg m⁻² × 0,1 = cm) |
| Método («B», anomalías) | `GWSA = TWSA·scale_factor − (SMSA + CWSA + SWEA)`; cada componente GLDAS como anomalía respecto a la media de los 72 meses nominales GRACE de **2004–2009** (la línea base de JPL). GLDAS 0,25° → 0,5° por media ponderada por cos(lat) de las 4 subceldas válidas; mes GLDAS = mes nominal JPL; celdas oceánicas JPL = NaN |
| Script | `python scripts/06_gwsa_grace_gldas_extendido.py descargar` (cuenta NASA Earthdata) y `... procesar`. Los insumos crudos van a `data/raw/grace/` y `data/raw/gldas/` (no se versionan) |
| Otras salidas | `data/processed/gwsa/GWSa_sedes_2002-2026.csv` (serie del píxel que usa la app en cada sede) y `docs/gwsa_validacion_extension.csv` |
| Licencia | Datos NASA de uso libre con atribución (ver `CREDITOS.md`); producto derivado CC BY 4.0 (propuesta) |

**Validación.** Sobre el período común con el NetCDF original (2002-05 a 2025-05, 243 meses; `docs/gwsa_validacion_extension.csv`;
sesgo = extendido − original):

| Ámbito | r | Sesgo (cm) | RMSE (cm) | Razón de amplitud |
|---|---|---|---|---|
| Bogotá | 0,94 | +0,94 | 3,3 | 0,82 |
| Leticia | 0,97 | +1,29 | 4,9 | 0,85 |
| Tumaco | 0,52 | +0,40 | 3,7 | 1,10 |
| Medellín | 0,72 | +2,03 | 4,7 | 0,82 |
| Arauca | 0,93 | +3,32 | 10,2 | 0,59 |
| La Paz | 0,89 | +1,62 | 8,1 | 0,64 |
| San Andrés | — | — | — | — (fuera de la malla; celda GRACE oceánica) |
| Malla, mediana por píxel (6.153) | 0,89 (p10 0,53) | +1,03 | 5,1 | — |
| Malla, serie media nacional | 0,92 | +1,16 | 4,2 | 0,57 |

La coincidencia con el original es solo moderada porque **el NetCDF original no es el producto publicado de Romero
y Piña (Zenodo, doi:10.5281/zenodo.14707819)**: frente a ese producto tiene r mediano 0,89 y amplitud ×1,28 (×1,67
en la serie media nacional), y se parece mucho más (r mediano 0,975, amplitud ×1,03) a la fórmula de diferencias del
código UNgroundwater (`GWSA = TWSA − (ΔSM + ΔSWE)` mes a mes), que mezcla un estado con un flujo y exagera la
amplitud. En cambio, el extendido reproduce el producto Zenodo (2002-04 a 2023-04) con r mediano por píxel 0,963,
RMSE 2,1 cm y amplitud ×0,98; por sede: Leticia r 0,99, Arauca 0,97, La Paz 0,97, Bogotá 0,95, Tumaco 0,93 y Medellín 0,77.
Esa comparación con Zenodo se hizo fuera del repositorio (el archivo Zenodo no se redistribuye aquí).

**Advertencias.** 161 píxeles (`factor_escala_negativo = 1`) caen en celdas JPL con `scale_factor < 0` (franja de
lon −72,75 y costa pacífica, incluida la vecindad de Tumaco): ahí la señal escalada es poco fiable. La serie es
**regional** (mascones de ~3°), no el nivel de un pozo, y en la llanura amazónica puede incluir agua superficial.
GRACE-FO se publica con 2–3 meses de retraso y JPL reprocesa los meses recientes: al actualizar, los últimos
valores pueden cambiar un poco. La reconstrucción es cercana pero no exacta al producto Zenodo (residuo de ~2 cm).

### 4.2 `data/processed/gwsa/COL_GWS_estimations_2002-2026_diferencias.nc` (alternativa, pendiente de decisión)

| Campo | Valor |
|---|---|
| Variable | `GWS_anom(time, lat, lon)`, float32, **cm**; `origen_valor(time)` (0 = valor del NetCDF original, 1 = mes nuevo calculado), `mes_nominal(time)`, `crs` |
| Malla y máscara | Idénticas al original (135 × 99) |
| Tiempo | 2002-05 a 2026-06. Hasta **2025-04** son exactamente los valores de `COL_GWS_estimations.nc` (salvo cuantización de 0,001 cm); **2025-05 a 2026-06** (14 meses) son nuevos. El paso vacío 2025-05 del original se reemplaza por el calculado |
| Fórmula de los meses nuevos | `GWSA = lwe_thickness·scale_factor − (ΔSM + ΔSWE)`, con SM = suma de las cuatro capas de `SoilMoi` y SWE de GLDAS-2.1 Noah 0,25° (kg m⁻² × 0,1 = cm); Δ = mes calendario menos mes anterior, asignado al mes nominal JPL; GLDAS llevado a 0,5° con el promedio simple de las 4 subceldas (NaN si falta alguna), que equivale a la interpolación lineal en el centro de la celda. Es la fórmula del código UNgroundwater que reproduce el original (r mediano 0,975 por píxel) |
| Mismos insumos que 4.1 | JPL Mascon CRI RL06.3Mv04 y GLDAS-2.1 Noah 0,25° mensual |
| Script | `python scripts/06_gwsa_grace_gldas_extendido.py alternativa` |
| Otras salidas | `data/processed/gwsa/GWSa_sedes_2002-2026_diferencias.csv` (columna `origen`: `original` / `extension`) y `docs/gwsa_validacion_diferencias.csv` |

**Validación del empalme.** Se recalculó la fórmula sobre los 24 meses anteriores al corte (2023-05 a 2025-04) y se
comparó con el original (sesgo = recalculado − original):

| Ámbito | r | Sesgo (cm) | RMSE (cm) | r 2002–2025 |
|---|---|---|---|---|
| Bogotá | 0,986 | −0,68 | 1,44 | 0,977 |
| Leticia | 0,997 | +0,34 | 1,86 | 0,991 |
| Medellín | 0,960 | −0,49 | 1,51 | 0,963 |
| Arauca | 0,997 | +0,39 | 1,34 | 0,989 |
| La Paz | 0,998 | +0,04 | 1,08 | 0,989 |
| Malla, serie media nacional | 0,995 | −0,14 | 0,83 | — |

El empalme no crea un salto apreciable (sesgos < 0,7 cm frente a oscilaciones de ±20–40 cm). **Tumaco** no tiene
meses nuevos: su celda costera de 0,5° no tiene las cuatro subceldas GLDAS con dato, así que la fórmula original no la
calcula y su serie termina en 2025-04 (el original sí tenía valores ahí; no se sabe con qué tratamiento de borde).
**San Andrés** sigue sin píxel. Advertencia de fondo: la fórmula resta un flujo (cambio mensual) a un estado
(anomalía), por eso su amplitud es mayor que la del producto publicado; las mismas advertencias de 4.1 sobre resolución
(~300 km efectivos) y meses recientes provisionales aplican aquí.

### 4.3 `COL_GWS_estimations.nc` (original del semillero, respaldo)

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
| `Landsat/<Sede>/Areas_coberturas_por_fecha.csv` | Landsat C2 L2, clasificación propia (Colab) | ha | Original, sin cambios. El área clasificada cambia con la nubosidad. La app solo grafica las fechas que cumplen los criterios, en % del área clasificada |
| `Landsat/<Sede>/Control_escenas.csv` | Ídem | — | Original, sin cambios: ID de escena (LC08, LC09, LE07; T1 y T2), nubosidad del catálogo, fracción útil del buffer, estado |
| `Landsat/<Sede>/metadatos_escenas.csv` | `scripts/07_landsat_filtrar_escenas.py` | % | `fecha, id_escena, sensor, path_row, tier, nubosidad_catalogo_pct, nube_aoi_pct` (= 100 × (1 − fracción útil): nubes, sombras y sin dato en el buffer), `estado_original, fotograma_gif, cumple, motivos` |
| `Landsat/<Sede>/escenas/<id_escena>.png` | Ídem | — | Solo los fotogramas de escenas que cumplen `config/landsat_criterios.toml`, extraídos de los GIF originales (que se retiraron) |
| `Landsat/<Sede>/compuestos/*` | `scripts/08_landsat_compuestos_stac.py` | reflectancia | Mediana de temporada seca, Landsat 8/9 C2 L2 T1 con máscara QA_PIXEL: JPG color natural y falso color, `*_escenas.csv` (escenas consultadas, % del AOI despejado, si se usaron) y `*_compuesto.json` (metadatos que lee la app) |
| `config/landsat_criterios.toml` | — | — | Umbrales: nubosidad máxima sobre el AOI, colección, nivel, tier, sensores, ventana seca por sede, buffer y realce fijo de los compuestos |

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
| `data/processed/gwsa/COL_GWS_estimations_2002-2026.nc` | `06_gwsa_grace_gldas_extendido.py` | GWSa 2002-04 a 2026-06 (cm), malla de la app (sección 4.1) |
| `data/processed/gwsa/GWSa_sedes_2002-2026.csv` | `06_gwsa_grace_gldas_extendido.py` | Serie GWSa (cm) del píxel de cada sede: `sede, mes_nominal, fecha, GWSa_cm, lat_pixel, lon_pixel` |
| `docs/gwsa_validacion_extension.csv` | `06_gwsa_grace_gldas_extendido.py` | r, sesgo, RMSE y razón de amplitud frente al NetCDF original, por sede y en la malla |
| `data/processed/gwsa/COL_GWS_estimations_2002-2026_diferencias.nc` y `GWSa_sedes_2002-2026_diferencias.csv` | `06_gwsa_grace_gldas_extendido.py alternativa` | Serie original extendida (sección 4.2) |
| `docs/gwsa_validacion_diferencias.csv` | Ídem | Validación del empalme (2023-05 a 2025-04) por sede y en la serie media nacional |
| `Landsat/<Sede>/metadatos_escenas.csv`, `escenas/` | `07_landsat_filtrar_escenas.py` | Sección 5 |
| `Landsat/<Sede>/compuestos/` | `08_landsat_compuestos_stac.py` | Sección 5 |
