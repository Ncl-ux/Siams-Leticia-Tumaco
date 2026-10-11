# Créditos y licencias por fuente

Este archivo responde a la observación **3.5 / 3.6 y A6** de la revisión: cada producto de terceros
debe tener crédito o retirarse. Donde no se pudo establecer la fuente, se escribe **«fuente por
confirmar»**: el semillero debe completarlo antes de publicar.

> **Regla práctica:** si no saben de dónde salió una imagen o un mapa, o si su licencia no permite
> redistribuirlo, no lo suban al repositorio público. Pongan el enlace a la fuente original.

## 1. Equipo

| Rol | Nombre | Estado |
|---|---|---|
| Elaboración de mapas QGIS (Arauca, Bogotá, Medellín, San Andrés, Tumaco) | Jean Carlot Hernández Hernández | Tomado del campo *Author* de los PDF. **Confirmar** autorización para publicar el nombre. |
| Elaboración de mapas QGIS (La Paz, Leticia) | Diana Ruiz | Tomado del campo *Author* de los PDF. **Confirmar**. |
| Desarrollo de la aplicación | Cuenta de GitHub `Ncl-ux` | **Por completar** con los nombres de los integrantes que autoricen aparecer. |
| Docente coordinador / contacto institucional | — | **Por completar** (sección «Sobre SIAMS» de la app). |
| Revisión técnica (octubre de 2026) | Pedro León, Universidad Nacional de Colombia | — |

## 2. Datos

| Producto en el repositorio | Fuente | Cómo citar / licencia |
|---|---|---|
| `Analisis Hidro/NASA_POWER_*_FINAL*.xlsx` | NASA Langley Research Center, proyecto POWER (API v2, comunidad AG, diario) — <https://power.larc.nasa.gov/> | «Estos datos se obtuvieron del proyecto POWER del NASA Langley Research Center (LaRC), financiado por el programa NASA Earth Science/Applied Science». Uso libre con reconocimiento. |
| `Analisis Hidro/ANALISIS_HIDROMETEOROLOGICO_Tumaco (2).xlsx` | IDEAM – DHIME, estaciones COCO EL [51030020] (lluvia), CCCP DEL PACÍFICO [51035020] (temperatura) y GRANJA EL MIRA [51025090] (humedad relativa) — <http://dhime.ideam.gov.co/atencionciudadano/> | Citar a IDEAM, código de estación y fecha de consulta (**fecha de descarga por confirmar**). |
| `Analisis Hidro/ANALISIS_HIDROMETEOROLOGICO_Arauca.xlsx` | IDEAM – DHIME (estaciones en la hoja `Fuentes`), descarga de julio de 2026 | Citar a IDEAM y las estaciones. |
| `data/processed/gwsa/COL_GWS_estimations_2002-2026.nc` y `GWSa_sedes_2002-2026.csv` (GWSa que usa la app) | Cálculo propio (`scripts/06_gwsa_grace_gldas_extendido.py`) con: **GRACE/GRACE-FO** JPL Mascon CRI RL06.3Mv04 — Watkins, M. M., Wiese, D. N., Yuan, D.-N., Boening, C. y Landerer, F. W. (2015), *J. Geophys. Res. Solid Earth*, 120, 2648–2671, <https://doi.org/10.1002/2014JB011547>; Wiese, D. N., Landerer, F. W. y Watkins, M. M. (2016), *Water Resour. Res.*, 52, 7490–7502, <https://doi.org/10.1002/2016WR019344>; datos: NASA JPL (2026), JPL GRACE and GRACE-FO Mascon Ocean, Ice, and Hydrology Equivalent Water Height CRI Filtered RL06.3Mv04, PO.DAAC, <https://doi.org/10.5067/TEMSC-3JC634>. **GLDAS**: Beaudoing, H. y Rodell, M. (2020), GLDAS Noah Land Surface Model L4 monthly 0.25 × 0.25 degree V2.1, GES DISC, <https://doi.org/10.5067/SXAVCZFAQLNO>; Rodell, M. et al. (2004), *Bull. Amer. Meteor. Soc.*, 85, 381–394, <https://doi.org/10.1175/BAMS-85-3-381>. Método según Romero y Piña (2025) | Datos NASA de uso libre; citar los DOI de los datos y los artículos. Agradecimiento sugerido: «GRACE/GRACE-FO mascon data are available at <http://grace.jpl.nasa.gov>, supported by the NASA MEaSUREs Program» y «GLDAS data were provided by NASA GES DISC». Producto derivado: CC BY 4.0 (propuesta). |
| `COL_GWS_estimations.nc` (original, respaldo) | GWSa derivado de GRACE/GRACE-FO menos GLDAS, siguiendo a Romero, P. y Piña, A. (2025), *Journal of Hydrology: Regional Studies*, 62, 102756, <https://doi.org/10.1016/j.ejrh.2025.102756> | **Licencia por confirmar** con los autores del producto. Versión de GRACE (mascones JPL RL06.x inferido) y de GLDAS **por confirmar**. |
| `Coberturas MapBio/` (CSV y GIF) | MapBiomas Colombia — <https://colombia.mapbiomas.org/> | **Colección por confirmar** (los CSV llegan a 2024 e incluyen clases de la Colección 3.0, publicada en octubre de 2025). Cita sugerida: «Proyecto MapBiomas Colombia – Colección 3.0 de la serie anual de mapas de cobertura y uso del suelo de Colombia, consultado el [fecha] a través de [enlace]». MapBiomas publica sus datos bajo licencia abierta con atribución (verificar los términos vigentes de la colección usada). |
| `Landsat/` (CSV, `escenas/*.png`, `compuestos/*`) | Landsat 7, 8 y 9, Colección 2 Nivel 2 (USGS/NASA). Escenas: clasificación propia del semillero en Colab. Compuestos: Landsat 8/9 C2 L2 T1 obtenidos del catálogo STAC de Microsoft Planetary Computer (<https://planetarycomputer.microsoft.com/dataset/landsat-c2-l2>) | «Imágenes Landsat cortesía del Servicio Geológico de los Estados Unidos (USGS)». Dominio público. Clasificación: semillero (CC BY 4.0 propuesta). |
| `Sentinel/Arauca/*.mp4` | Copernicus Sentinel-2 (ESA/Unión Europea), NDVI, MNDWI y SCL 2025 | «Contiene datos modificados de Copernicus Sentinel [2025]». |
| `Gif/*.mp4`, `Tarjeta Tecnica Swot/*.png` | SWOT (NASA/CNES), productos de río por tramo vía HydroWeb (Theia/CNES) — <https://hydroweb.next.theia-land.fr/> | Citar SWOT y HydroWeb; **versión del producto y de SWORD por confirmar**. |

## 3. Mapas temáticos (`SIAMS MAPAS/`)

Capturas de mapas oficiales. La entidad sale de `METADATOS_MAPAS` en `app.py`. Antes de publicar,
verifiquen que la licencia de cada entidad permite redistribuir la imagen; si no, dejen solo el enlace.

| Sede | Mapa(s) | Entidad fuente |
|---|---|---|
| Leticia | Hidrografía, geología (Trapecio sur), coberturas, geomorfología y relieve | Instituto SINCHI |
| Leticia | Humedales (Leticia–Puerto Nariño), inundación urbana | Corpoamazonia |
| Tumaco | Hidrografía | Parques Nacionales Naturales de Colombia |
| Tumaco | Manglares | CORPONARIÑO |
| Tumaco | Inundación, geología, coberturas, relieve | CORPONARIÑO – POMCA del río Mira |
| Medellín | Geología (plancha 228) | Servicio Geológico Colombiano (SGC) |
| Medellín | Estructura ecológica, amenaza por inundación | Alcaldía de Medellín – POT |
| San Andrés | Geología, vulnerabilidad del acuífero, nitratos, microcuencas | CORALINA (figuras 3, 4, 9 y 11 del documento fuente) |
| Arauca | Demanda y vertimientos de la industria manufacturera (2021) | IDEAM |
| Arauca | Anomalía de oferta hídrica superficial, puntos de agua subterránea, volumen concesionado | IDEAM – Estudio Nacional del Agua 2014 |
| Arauca | Criterio de demanda hidrogeológica | SGC – PEXAS 2005 |
| Arauca | Mapa geológico de Colombia 2023 | SGC |
| Arauca | Sistema acuífero Arauca–Arauquita | IDEAM – SAP 3.3, anexo 7 |

**Retirado:** `mapa_pozos_irca_leticia.png` (captura de un visor qgis2web elaborado por Oscar Fabián
Cabrera Santacruz y Dora Cecilia Martín Matiz, Semillero Amazonas Verde, SENA Amazonas). Se retiró por
privacidad de los hogares y del Resguardo La Playa y porque incluía la capa Google Satellite, que no se
puede redistribuir así. Ver `CAMBIOS.md` y la sección de ética del `README.md`.

## 4. Mapas de ubicación (`Mapas Qgis/`)

Elaboración propia del semillero en QGIS (autores en la sección 1). Límites administrativos y capa base
satelital: **fuente por confirmar** (si la capa base es Google, Bing o Esri, revisen sus términos de uso:
en general no permiten redistribuir el mapa exportado).

## 5. Fotografías (`Presentacion/`)

| Archivo | Autoría y licencia |
|---|---|
| `Bogota.jpg`, `Leticia.jpg`, `Medellin.jpg`, `San Andres.jpg`, `Arauca.jpg`, `La Paz.jpg` | **Fuente por confirmar** |
| `Tumaco.jpeg` | **Fuente por confirmar.** La foto original traía EXIF de una cámara Nikon D300S fechada el 25/11/2014; el campo de autor estaba vacío. Se le quitaron los metadatos. |

Si una foto no es del semillero y no tiene licencia abierta, reemplácenla por una propia o de
Wikimedia Commons con su crédito.

## 6. Software

Streamlit, pandas, NumPy, Plotly, openpyxl, xarray, netCDF4, Pillow y PyMuPDF (ver
`requirements.txt`). Las pruebas de Mann-Kendall, Hamed-Rao, Pettitt y SNHT se implementaron en
`siams/estadistica.py` y se verificaron contra `pymannkendall` y `pyhomogeneity`.
