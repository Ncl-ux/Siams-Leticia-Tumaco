# Cambios de esta versión corregida (octubre de 2026)

Versión preparada por Pedro León a partir de la revisión técnica del 10 de octubre de 2026
(«Revisión del repositorio SIAMS Leticia–Tumaco»), sobre el commit `24634851` de
<https://github.com/Ncl-ux/Siams-Leticia-Tumaco>. Cada cambio indica la observación de la revisión
(sección 3.x o ID de la lista de chequeo A/M/B) a la que responde.

**Criterio general:** no se cambió ningún valor de los datos. Se corrigieron rótulos, unidades, metadatos y
la forma de presentarlos; los problemas de calidad se **marcan y documentan**, no se «arreglan» en silencio.

## 1. Datos y estadística

| Obs. | Cambio |
|---|---|
| 3.2.a · A1 | **Lluvia IDEAM de Tumaco (COCO EL 51030020).** Se agregaron las pruebas de Pettitt y SNHT (`siams/estadistica.py`) y se documentó el cambio de registro de 1995 (`docs/homogeneidad_tumaco.md`, `data/README.md`). La serie queda marcada en `siams/calidad.py`; la app muestra una advertencia en «Clima» y en «Análisis de tendencias», marca 1995 en la gráfica y agrega la fila del tramo homogéneo 1995–2024 (+34,4 mm/año, p = 0,11, **no significativa**). La tendencia 1985–2024 se rotula **no concluyente**. Los datos crudos no se tocaron. |
| 3.3.e · M5 | Mann-Kendall modificado de **Hamed y Rao (1998)** junto al Mann-Kendall clásico, en la app y en `docs/tendencias_homogeneidad.csv`. Implementación verificada contra `pymannkendall` 1.4.3 y `pyhomogeneity`. |
| 3.2.c · A2 | **Radiación en MJ/m²/día**, no kWh/m²/día. Se confirmó con la API de NASA POWER (comunidad AG declara `MJ/m^2/day`; los valores del 1–3 de enero de 1992 en Tumaco coinciden con el Excel). Columna renombrada a `radiacion_solar_MJ_m2_dia` en los seis Excel NASA; todos los rótulos de la app y la tabla de tendencias corregidos. `siams/unidades.py` trae la conversión (1 kWh = 3,6 MJ) y una prueba de rango físico. |
| 3.2.c · A3 | **Precipitación con su unidad real:** `P_mensual` y `Regimen_P` → `precipitacion_mm_mes`; `P_anual` → `precipitacion_mm_anio` (NASA e IDEAM). `Datos_diarios` y `Climatologia_mensual` siguen en `precipitacion_mm_dia`, que sí es correcto. Hoja `Diccionario` nueva en cada Excel. El código lee los nombres nuevos (y los viejos, por compatibilidad). Script: `scripts/00_corregir_rotulos_excel.py`. |
| 3.2.c | Arauca, `Control_faltantes`: la columna «Fechas ausentes» tenía formato de fecha (322 aparecía como 1900-11-17). Corregido a número. |
| 3.2.e · A4 | **NetCDF GWSa con metadatos CF-1.8:** unidades, nombre largo, fuente, referencia completa con DOI, periodo, variable `crs` (EPSG:4326), cobertura espacial y temporal. Lo que no se pudo establecer está escrito como «por confirmar» o «inferido» (versión GRACE/GLDAS, periodo de referencia, unidad cm). Valores idénticos; compresión sin pérdida 25 MB → 4,6 MB. Script: `scripts/04_netcdf_metadatos_cf.py`. |
| 3.2.d · M10 | La gráfica de GWSa se remuestrea por mes y **corta la línea en los vacíos** (`connectgaps=False`): el vacío GRACE/GRACE-FO 2017–2018 ya no aparece como una recta. |
| 3.2.d | Convenciones de tiempo por fuente (día pluviométrico IDEAM, hora solar local NASA, punto medio GRACE, UTC SWOT) en `data/README.md`. |
| 3.2.f · M8 | Landsat: la vista por defecto es el **porcentaje del área clasificada**, con una nota de por qué las hectáreas no son comparables entre fechas. |
| 3.2.e | Referencia de Romero y Piña (2025) completa, con DOI, en la página de GRACE. |

## 2. Reproducibilidad y código

| Obs. | Cambio |
|---|---|
| 3.3.a · A5 | Carpeta `scripts/` con `00`–`05`. **`01_descarga_nasa_power.py` es real y está verificado:** reproduce exactamente los valores diarios de Tumaco 1992–2025 y del primer año de las otras cinco sedes. `02` genera las series anuales (`data/processed/anuales/`) y `03` la tabla de tendencias y homogeneidad. |
| 3.3.b · M2 | `requirements.txt` con versiones fijas y probado en un entorno limpio (Python 3.13.5), con `pymupdf` para el visor de PDF. `requirements-dev.txt` (pytest), `.python-version` y `environment.yml`. |
| 3.3.d · M4 | Pruebas con pytest en `tests/` (**33 pruebas**): conversiones de unidades, Mann-Kendall, Sen, Hamed-Rao, Pettitt, SNHT, agregación anual, carga de los Excel, coherencia entre `P_mensual` y la suma diaria, atributos del NetCDF, ausencia de EXIF y del mapa de pozos. GitHub Actions en `.github/workflows/pruebas.yml`. |
| 3.1.b · M4 | Paquete `siams/` (`estadistica.py`, `unidades.py`, `calidad.py`). La estadística salió de `app.py`. **La modularización completa queda pendiente.** |
| 3.3.c · M3 | Los 9 `except Exception: pass` (y los demás silenciosos) ahora registran el error con `logging`; los de la tabla de tendencias además muestran un aviso en la app. |
| 3.3.f · B2 | Eliminadas las listas climáticas mensuales sin fuente de Leticia y Tumaco. **Corrección a la revisión:** `clima_prototipo` sí se llamaba (como respaldo cuando faltaba el Excel), así que esos valores sí podían publicarse. Ahora devuelve una tabla vacía. |
| 3.3.g · B3 | El panel «Diagnóstico de archivos» solo aparece con `SIAMS_MODO=dev`. |
| B4 | Los 69 usos de `use_container_width` pasaron a `width="stretch"`/`"content"`: sin avisos de obsolescencia. |
| 3.1.b | Eliminado el `from pathlib import Path` duplicado. |
| — | `VERSION_APP = "PROTOTIPO-SIAMS-V38-REVISADO-2026-10-11"`. |

## 3. Licencias, créditos y ética

| Obs. | Cambio |
|---|---|
| 3.5 · A6 | `LICENSE` (MIT para el código) con la **propuesta** de CC BY 4.0 para textos y productos propios. `CITATION.cff` con los autores que aparecen en los metadatos de los PDF (Jean Carlot Hernández Hernández, Diana Ruiz) y el resto «por completar». |
| 3.6 · A6 | `CREDITOS.md`: créditos por fuente, mapa y fotografía; «fuente por confirmar» donde no se sabe. Créditos también en la app (Inicio, Fuentes y descargas, SWOT, Sentinel). |
| 3.4 · 3.6 · A7 | **Retirado el mapa de pozos de Leticia** (`SIAMS MAPAS/mapa_pozos_irca_leticia.png`) de la app y del repositorio. Mostraba cientos de pozos, en su mayoría domésticos, junto al Resguardo La Playa; su leyenda no mostraba el IRCA sino el uso del pozo, e incluía la capa Google Satellite. En su lugar, la app muestra una nota sobre consentimiento, principios CARE y Ley 1581 de 2012, con crédito al trabajo del Semillero Amazonas Verde (SENA Amazonas). Como el historial es nuevo, **el archivo nunca entra al historial de Git**. Cuando haya acuerdo con el resguardo, las fuentes y los usuarios, se puede publicar un resultado agregado (celdas de 500 m o por sector). |
| 3.5 · B5 | **EXIF eliminado de todas las imágenes.** `Presentacion/Tumaco.jpeg` (cámara Nikon D300S, 2014; su bloque GPS solo tenía la versión, sin coordenadas) quedó sin EXIF/XMP/ICC y reducida a 1.600 px. Las PNG de SWOT se guardaron sin el bloque de texto «Software». Hay una prueba automática que lo verifica. |
| 3.5 | `.gitignore` con `.venv`, `.env`, `secrets.toml`, `*.netrc`, cachés y una carpeta `privado/` para consentimientos. |

## 4. Peso del repositorio

| Obs. | Cambio | Antes | Después |
|---|---|---|---|
| 3.4 · M9 | GIF de SWOT (`Gif/`) → MP4 H.264 | 69 MB | 4,1 MB |
| 3.4 | GIF Sentinel-2 Arauca → MP4 | 16,9 MB | 4,1 MB |
| 3.1.c | Carpeta `Sentinel/Leticia /`: eran **copias idénticas** de las animaciones de Arauca (un fotograma muestra el río Arauca y la sabana). Eliminada, junto con su entrada en la app. | 16,9 MB | 0 |
| 3.4 | PDF de `Mapas Qgis/`: ghostscript `/ebook`; los seis PDF con límites municipales vectoriales muy pesados se rasterizaron a 250 ppp (calidad revisada visualmente; se conserva el autor en los metadatos) | 226 MB | 15,7 MB |
| 3.2.e | NetCDF GWSa (compresión sin pérdida) | 26,1 MB | 4,9 MB |
| 3.5 · M1 | `.venv` y su historial fuera del repositorio (historial nuevo) | `.git` de 467 MB | ver abajo |

Los GIF de MapBiomas y Landsat se dejaron como GIF: en MP4 o GIF optimizado quedaban más pesados, y la app
ralentiza los fotogramas de Landsat con Pillow. **Total de la carpeta de trabajo: de 455 MB (sin `.git` ni `.venv`;
902 MB con el historial) a unos 125 MB.** `.gitattributes` trae la sugerencia de Git LFS comentada.

## 5. Interfaz

| Obs. | Cambio |
|---|---|
| 3.4 · M9 | `initial_sidebar_state="auto"`: en celular la barra lateral arranca cerrada. CSS para que las tarjetas de inicio pasen a una columna por debajo de 640 px. |
| 3.2.c | Unidades en todos los ejes y tablas de tendencias (mm/año, °C/año, MJ/m²/día/año…). |
| 3.1.a · A8 | `README.md` completo en español (qué es, sedes, cómo correrlo, fuentes con enlaces, limitaciones, estructura, ética, contribuir, créditos, licencia, cita) con resumen en portugués. `CONTRIBUTING.md` con flujo de trabajo y convención de nombres (B1). `data/README.md` como diccionario de datos. |

## 6. Otros errores encontrados en esta revisión

1. **Mapa de ubicación de Medellín (nivel 2) no se mostraba:** la configuración pedía `Medellín 1-250000.pdf`, pero el
   archivo es `Medellín  1-2500000.pdf` (1:2.500.000, todo Antioquia). Corregidos el nombre, la escala y la descripción.
2. **Animaciones Sentinel de Leticia** eran las de Arauca (ver arriba).
3. **`clima_prototipo` sí se usaba** como respaldo, con valores de origen desconocido (ver 3.3.f).
4. **Formato de «Fechas ausentes»** en el Excel de Arauca (ver arriba).
5. **ID duplicado de `st.video`** en la comparación Sentinel (mismo archivo dos veces): Streamlit lanzaba una excepción.
   Ahora cada video tiene texto alternativo distinto.
6. **Atributos `bounds` colgantes** en el NetCDF (apuntaban a variables inexistentes): eliminados.
7. **NASA POWER Tumaco, lluvia:** la tendencia decreciente (−11,2 mm/año, p de MK = 0,015) **no es significativa con
   Hamed-Rao** (p = 0,10) y la serie tiene punto de cambio hacia 2005. Igual para varias variables NASA de Tumaco y para
   la radiación de Leticia (cambio hacia 2010). Ver `docs/tendencias_homogeneidad.csv`.
8. **`P_anual` de NASA incluye 2026 parcial**, y el indicador «Precipitación anual media» de la hoja `Indicadores` de
   IDEAM Tumaco (2.799 mm) mezcla años completos e incompletos. Las tendencias de la app ya excluían los años
   incompletos; los Excel no se modificaron (ver pendientes).
9. **Visor de PDF:** `st.pdf` necesita el componente opcional `streamlit[pdf]`; si falta, la app usa PyMuPDF. Antes el
   fallo se tragaba en silencio; ahora queda en el registro.

## 7. Lo que queda para el semillero

**Prioridad alta**
- [ ] Revisar en DHIME la historia de la estación COCO EL y compararla con estaciones vecinas y CHIRPS/IMERG; verificar
      2023–2024 (`docs/homogeneidad_tumaco.md`). Decidir con el docente cómo tratar el tramo 1985–1994.
- [ ] Subir el procesamiento IDEAM (`02_procesa_ideam.py`) y los CSV crudos de DHIME (o la consulta exacta) a `data/raw/`.
- [ ] Subir los cuadernos de Landsat, Sentinel-2, SWOT y MapBiomas, y las tablas SWOT por tramo con banderas de
      calidad (`reach_id`, `reach_q`, `xovr_cal_q`, `dark_frac`) (3.2.g · M7).
- [ ] Confirmar con los autores del producto GWSa: versión GRACE y GLDAS, unidades, periodo de referencia y licencia.
- [ ] Completar autores, docente coordinador y contacto en `CITATION.cff`, `CREDITOS.md`, `LICENSE` y «Sobre SIAMS»,
      con autorización de cada persona. Confirmar la licencia CC BY 4.0.
- [ ] Créditos de las fotografías y de la capa base satelital de los mapas QGIS (o reemplazarlas).
- [ ] Verificar que las entidades de `SIAMS MAPAS/` permiten redistribuir sus mapas.
- [ ] Desarrollar la sigla SIAMS en el README y en la app.
- [ ] Acordar con el Resguardo La Playa, el SENA, Corpoamazonia y los usuarios si se publica un mapa agregado de pozos.

**Prioridad media**
- [ ] Validar NASA POWER contra IDEAM, ANA (Tabatinga) y CHIRPS/IMERG con sesgo, KGE y POD/FAR (3.2.b · M6).
- [ ] Ubicación y distancia a la sede de las estaciones de Tumaco en la hoja `Fuentes` (3.2.h).
- [ ] Quitar el año parcial de `P_anual` y recalcular el indicador de precipitación media con años completos.
- [ ] Terminar de modularizar `app.py` (lectura de datos, gráficas, CSS en `assets/`, configuración en `territorios.yaml`).
- [ ] Descargas bajo demanda o enlazadas a Releases/Zenodo en «Fuentes y descargas» (3.3.g).
- [ ] Máscara común entre fechas para Landsat (3.2.f).
- [ ] Probar la app en un celular real de gama media.

**Prioridad baja**
- [ ] Renombrar archivos según `CONTRIBUTING.md` (B1) junto con un registro explícito de archivos.
- [ ] Glosario y frase en lenguaje común por indicador (B7); revisar contraste del rótulo de diagnóstico.
- [ ] Pasar por `html.escape` todo texto que venga de CSV/Excel en los 47 `unsafe_allow_html=True`.
- [ ] Trabajo con ramas, pull requests y etiquetas (`git tag v0.38.1`) (B6).

## 8. Actualización del agua subterránea GRACE/GLDAS hasta junio de 2026

La serie GWSa de la app terminaba en 2025-04 (el último paso del NetCDF original, 2025-05, está vacío). Ahora llega a
**2026-06** en todas las sedes continentales y en toda la malla nacional.

| Cambio | Detalle |
|---|---|
| NetCDF nuevo | `data/processed/gwsa/COL_GWS_estimations_2002-2026.nc` (0,8 MB): misma variable `GWS_anom` (cm), mismas dimensiones `time, lat, lon`, misma malla (~0,12°, 135 × 99) y misma máscara (6.153 píxeles) que `COL_GWS_estimations.nc`. 258 meses, 2002-04 a 2026-06. Metadatos CF-1.8 con fuentes, versiones, método, período, línea base y lista de meses faltantes. Variables nuevas: `mes_nominal`, `time_bnds` y `factor_escala_negativo`. |
| Datos de origen | NASA JPL GRACE/GRACE-FO Mascon CRI **RL06.3Mv04** (archivo 200204_202607, creado 2026-09-08) y **GLDAS-2.1 Noah 0,25° mensual** (`GLDAS_NOAH025_M` v2.1) 2002-01 a 2026-06. |
| Método | `GWSA = TWSA·scale_factor − (SMSA + CWSA + SWEA)`, componentes GLDAS como anomalías respecto a 2004–2009 (método B). Se recalculó **todo** el período con el mismo método, en lugar de pegar meses nuevos al final del original, para no crear un salto artificial. |
| Meses sin dato | Los 33 meses sin solución JPL, incluida la brecha GRACE → GRACE-FO 2017-07 a 2018-05, **no se interpolan** (igual que el original). Desde 2018-10 no falta ningún mes. |
| Script | `scripts/06_gwsa_grace_gldas_extendido.py` (`descargar` / `procesar`), con rutas relativas a la raíz del repositorio. Los insumos crudos (`data/raw/grace`, `data/raw/gldas`) quedan fuera de Git (`.gitignore`). |
| App | `encontrar_archivo_gws()` prefiere el NetCDF extendido; si falta, usa el original. `SIAMS_ARCHIVO_GWS` permite forzar otro archivo. Las series se fechan por **mes nominal** JPL, así que dos meses ya no se mezclan en la gráfica mensual, la climatología ni el GGDI (antes 2012-01-01 caía en enero en lugar de 2011-12, y 2015-04-27 en abril en lugar de mayo). El selector del mapa usa el mes nominal. Leyendas con el archivo y el período en uso, línea base 2004–2009 y aviso si el píxel de una sede termina antes que el producto. `VERSION_APP = "PROTOTIPO-SIAMS-V38-REVISADO-GRACE-2026-06"`. |
| Documentación | `data/README.md` (sección 4.1, con la tabla de validación), `scripts/README.md`, `README.md`, `CREDITOS.md` y `CITATION.cff` (JPL mascon RL06.3Mv04, Watkins et al. 2015, GLDAS-2.1 Noah, Rodell et al. 2004). |
| Pruebas | `tests/test_gwsa_extendido.py`: el producto llega a 2026-06 y empieza en 2002-04, no tiene la brecha interpolada, está en cm con metadatos CF, conserva malla y máscara del original, y las seis sedes continentales tienen dato hasta 2026-06. **37 pruebas** en total. |

**Validación frente al NetCDF original** (2002-05 a 2025-05, 243 meses; `docs/gwsa_validacion_extension.csv`). r por sede:
Leticia 0,97, Bogotá 0,94, Arauca 0,93, La Paz 0,89, Medellín 0,72 y Tumaco 0,52. En la malla: r mediano por píxel
0,89, sesgo mediano +1,0 cm y RMSE mediano 5,1 cm. La amplitud del nuevo producto es menor (×0,6–0,85 en la mayoría de
sedes).

**Hallazgo: el NetCDF original no es el producto publicado.** Comparado con el GWSa de Romero y Piña en Zenodo
(doi:10.5281/zenodo.14707819, 2002-04 a 2023-04), el original tiene r mediano 0,89 y amplitud ×1,28 por píxel. Se
reproduce casi exactamente (r mediano 0,975, amplitud ×1,03) con la fórmula de diferencias mensuales del código
UNgroundwater (`TWSA − (ΔSM + ΔSWE)`), que resta un flujo a un estado y exagera las oscilaciones. El producto nuevo
reproduce Zenodo con r mediano 0,963, RMSE 2,1 cm y amplitud ×0,98 (Leticia r 0,99). Por eso los valores de la app
cambian un poco, y no solo se alargan: en Arauca y La Paz la variabilidad (desviación estándar) es un 35–40 % menor.

**Advertencias.**
- San Andrés sigue sin serie: está fuera de la malla y su celda GRACE es oceánica.
- 161 píxeles tienen factor de escala JPL negativo (franja lon −72,75 y costa pacífica, incluida la vecindad de Tumaco). Ahí la señal es poco fiable, y eso explica el r bajo de Tumaco frente al original.
- GRACE-FO se publica con unos 2–3 meses de retraso y JPL reprocesa los meses recientes. Al actualizar con `descargar`, los últimos valores pueden cambiar un poco.
- La serie es regional (mascones de ~3°), no el nivel de un pozo.

- [ ] Pendiente para el semillero: confirmar con los autores cómo se generó `COL_GWS_estimations.nc` y decidir si se
      retira del repositorio. La app ya no lo necesita.
