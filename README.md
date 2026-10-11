# SIAMS · Plataforma hidroambiental del Semillero SIAMS

> **Sigla por desarrollar:** el semillero debe escribir aquí qué significa SIAMS.

SIAMS es una aplicación web hecha en [Streamlit](https://streamlit.io) por el **Semillero SIAMS de la
Universidad Nacional de Colombia**. Permite consultar, por sede, información de clima, agua superficial,
agua subterránea y coberturas de la tierra, con la procedencia y las limitaciones de cada dato a la vista.

> **Prototipo académico.** No reemplaza la información oficial del IDEAM, Corpoamazonia, CORPONARIÑO,
> CORALINA, el SGC ni las autoridades de gestión del riesgo.

## Sedes

Bogotá · Leticia (Sede Amazonia) · Tumaco (Sede Tumaco) · Medellín · San Andrés (Sede Caribe) · Arauca
(Sede Orinoquia) · La Paz (Sede La Paz). El nombre del repositorio menciona solo Leticia y Tumaco porque
así empezó el proyecto.

## Qué muestra

| Componente | Fuente | Periodo | Escala | Estado |
|---|---|---|---|---|
| Clima diario | [NASA POWER](https://power.larc.nasa.gov/) (API v2, comunidad AG) | 1992/2000–2026 | celda de ~0,5° | Reanálisis sin validar localmente |
| Clima de estación | [IDEAM – DHIME](http://dhime.ideam.gov.co/atencionciudadano/) (Tumaco, Arauca) | 1985–2025 | estación | En validación; **lluvia de Tumaco inhomogénea** |
| Agua subterránea (GWSa, GGDI) | [JPL GRACE/GRACE-FO mascon RL06.3Mv04](https://doi.org/10.5067/TEMSC-3JC634) menos [GLDAS-2.1 Noah](https://doi.org/10.5067/SXAVCZFAQLNO), según [Romero y Piña (2025)](https://doi.org/10.1016/j.ejrh.2025.102756) | 2002-04 – 2026-06 | regional (cientos de km) | Exploratorio |
| Río (nivel y ancho) | [SWOT](https://swot.jpl.nasa.gov/) vía [HydroWeb](https://hydroweb.next.theia-land.fr/) | 2023–2026 | tramo de río | Exploratorio |
| Coberturas | [MapBiomas Colombia](https://colombia.mapbiomas.org/) (colección por confirmar), Landsat 8/9 C2 L2 | 1985–2025 | 30 m | Exploratorio |
| Agua en superficie y vegetación | [Copernicus Sentinel-2](https://dataspace.copernicus.eu/) (NDVI, MNDWI, SCL) | 2025 | 10–20 m | Solo Arauca |
| Cartografía | Mapas QGIS del semillero y mapas oficiales (SINCHI, Corpoamazonia, CORPONARIÑO, CORALINA, SGC, IDEAM, Alcaldía de Medellín) | — | — | Ver `CREDITOS.md` |

## Cómo ejecutarlo

Requiere **Python 3.13** (probado con 3.13.5) y unos 150 MB de espacio.

```bash
git clone https://github.com/Ncl-ux/Siams-Leticia-Tumaco.git
cd Siams-Leticia-Tumaco
python -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

La app abre en <http://localhost:8501>. Con conda: `conda env create -f environment.yml`.

- **Modo desarrollo:** `SIAMS_MODO=dev streamlit run app.py` (PowerShell: `$env:SIAMS_MODO="dev"; streamlit run app.py`)
  muestra el panel «Diagnóstico de archivos», que en producción queda oculto porque expone rutas del servidor.
- **Pruebas:** `pip install -r requirements-dev.txt` y luego `python -m pytest`. También corren en GitHub
  Actions (`.github/workflows/pruebas.yml`).

## Reproducir los productos

```bash
python scripts/01_descarga_nasa_power.py --sede tumaco --inicio 1992-01-01 --fin 2025-12-31
python scripts/02_agregados_anuales.py          # series anuales en data/processed/anuales/
python scripts/03_tendencias_homogeneidad.py    # docs/tendencias_homogeneidad.csv
python scripts/06_gwsa_grace_gldas_extendido.py procesar   # GWSa 2002-04..2026-06 (insumos: ver data/README.md, 4.1)
```

Ver `scripts/README.md`: ahí se explica qué se reconstruyó y qué falta (procesamiento IDEAM, Landsat, SWOT,
Sentinel, MapBiomas y el NetCDF de GWSa).

## Estructura

```text
app.py                     aplicación Streamlit (navegación y presentación)
siams/                     funciones reutilizables y probadas
  estadistica.py           Mann-Kendall, Hamed-Rao, Sen, Pettitt, SNHT, agregación anual
  unidades.py              unidades, conversiones y nombres de columnas
  calidad.py               series con problemas de calidad documentados
scripts/                   descarga y procesamiento reproducibles
tests/                     pruebas con pytest
data/README.md             diccionario de datos (fuente, unidad, zona horaria, licencia)
data/processed/            productos generados por los scripts
docs/                      notas técnicas (homogeneidad de Tumaco, tabla de tendencias)
Analisis Hidro/            Excel de clima NASA POWER e IDEAM
COL_GWS_estimations.nc     GWSa original del semillero, 2002–2025 (respaldo)
data/processed/gwsa/       GWSa extendido 2002-04 – 2026-06 (lo usa la app) y series por sede
Coberturas MapBio/  Landsat/  Sentinel/  Gif/  Tarjeta Tecnica Swot/
SIAMS MAPAS/  Mapas Qgis/  Presentacion/
```

## Limitaciones conocidas

- **Lluvia IDEAM de Tumaco (COCO EL, 51030020):** la forma de registro cambió hacia 1995 y el total anual se
  duplicó. La tendencia 1985–2024 (+56 mm/año) **no es concluyente**; en 1995–2024 no hay tendencia significativa.
  Ver `docs/homogeneidad_tumaco.md`.
- **NASA POWER** es un reanálisis de baja resolución: en Tumaco subestima la lluvia ~60 % frente a IDEAM y llueve
  casi todos los días; en San Andrés la celda está dominada por el mar. No se ha validado contra estaciones.
- **GWSa** es una señal regional de cientos de kilómetros, no el nivel de un pozo. El NetCDF que usa la app
  (2002-04 – 2026-06) está documentado y es reproducible (`scripts/06_gwsa_grace_gldas_extendido.py`); San Andrés
  no tiene serie (celda oceánica) y los meses sin solución GRACE, como el vacío 2017-07 – 2018-05, no se interpolan.
  Ver `data/README.md`, sección 4.
- **Landsat:** el área clasificada cambia con las nubes; compare en porcentaje, no en hectáreas.
- **SWOT:** las tarjetas no traen las tablas de origen ni los indicadores de calidad oficiales.
- **Años parciales:** 2026 (NASA POWER) y 2025 (IDEAM Tumaco) están en las hojas `P_anual`, pero no entran en las
  tendencias.

## Ética y datos comunitarios

SIAMS sigue los principios [FAIR](https://doi.org/10.1038/sdata.2016.18) y
[CARE](https://doi.org/10.5334/dsj-2020-043): cuando los datos vienen de territorios indígenas o de consejos
comunitarios, la comunidad decide qué se publica.

- **No se publican ubicaciones de pozos familiares ni de viviendas** sin consentimiento informado. Por eso se retiró
  el mapa de pozos de Leticia, ubicado junto al Resguardo La Playa (ver `CAMBIOS.md`).
- Si se recogen nombres, teléfonos o ubicaciones, aplica la Ley 1581 de 2012. Los formularios de consentimiento se
  guardan **fuera** del repositorio (carpeta `privado/`, ignorada por Git).

## Contribuir

Ver `CONTRIBUTING.md` (ramas, pull requests, mensajes de commit y convención de nombres de archivo).

## Repositorio liviano y Git LFS

El historial original pesaba 467 MB porque se subió un `.venv`. Esta versión parte de un historial limpio, con PDF
comprimidos y GIF de SWOT/Sentinel convertidos a MP4 (de 455 MB a unos 125 MB). Si vuelven a crecer los
binarios, activen **Git LFS** (`git lfs install` y las líneas comentadas en `.gitattributes`) o publiquen los
productos pesados en *Releases* de GitHub o en Zenodo. GitHub rechaza archivos de más de 100 MB.

## Créditos

Ver `CREDITOS.md` y la página «Fuentes y descargas» de la app. Varias fotografías y capas base tienen
**fuente por confirmar**.

## Licencia

- Código: **MIT** (`LICENSE`).
- Textos, mapas y productos propios: **CC BY 4.0** (propuesta, por confirmar por el semillero).
- Datos de terceros: según cada fuente (`CREDITOS.md`, `data/README.md`).

## Cómo citar

Ver `CITATION.cff` (GitHub muestra el botón «Cite this repository»). Lista de autores por completar.

## Equipo

Semillero SIAMS, Universidad Nacional de Colombia. Integrantes, docente coordinador y contacto institucional:
**por completar**, con autorización de cada persona.

---

### Resumo em português

O SIAMS é uma plataforma web (Streamlit) do Semillero SIAMS da Universidade Nacional da Colômbia que reúne,
para sete sedes (incluindo Letícia, na fronteira com Tabatinga, Brasil), dados de clima (IDEAM e NASA POWER),
águas subterrâneas (GRACE/GLDAS), rios (SWOT), cobertura do solo (MapBiomas, Landsat) e mapas QGIS. É um
protótipo acadêmico e não substitui informações oficiais. Para executar: `pip install -r requirements.txt` e
`streamlit run app.py`. A série de chuva IDEAM de Tumaco apresenta inomogeneidade (mudança de registro por volta
de 1995), e a sua tendência não é conclusiva. Código sob licença MIT; dados de terceiros conforme cada fonte.
