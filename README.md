# SIAMS | Semillero de Investigación en Agua y Modelación Subterránea

**Plataforma hidroambiental de consulta, exploración y visualización territorial** desarrollada en el marco del Semillero SIAMS de la **Universidad Nacional de Colombia**.

SIAMS reúne información sobre clima, agua superficial, aguas subterráneas, coberturas de la tierra y cartografía para facilitar la lectura ambiental de distintos territorios vinculados con las sedes de la Universidad Nacional de Colombia. Su propósito es acercar datos técnicos a estudiantes, investigadores y comunidades mediante mapas, indicadores, series temporales y recursos visuales interactivos.

> [!IMPORTANT]
> **Estado: prototipo académico en revisión.** La plataforma integra productos de distintas fuentes, escalas y periodos. No reemplaza los datos oficiales, estudios de detalle, instrumentos de gestión del riesgo ni decisiones técnicas de las autoridades competentes. Las salidas exploratorias deben verificarse antes de utilizarse en publicaciones, diseño o toma de decisiones.

## 1. Territorios incluidos

Actualmente la interfaz contempla **siete territorios**:

| Territorio en SIAMS | Referencia institucional | Enfoque disponible en el prototipo |
|---|---|---|
| **Bogotá** | Sede Bogotá | Ubicación multiescala y cartografía piloto. |
| **Leticia** | Sede Amazonia | Climatología, mapas ambientales, productos SWOT y análisis regional de agua subterránea, según disponibilidad. |
| **Tumaco** | Sede Tumaco | Comparación IDEAM–NASA POWER, coberturas, cartografía, ríos Mira y Rosario mediante SWOT. |
| **Medellín** | Sede Medellín | Clima, geología, coberturas, cartografía e información SWOT. |
| **San Andrés** | Sede Caribe | Clima, hidrogeología insular, cartografía y coberturas diferenciadas por zona. |
| **Arauca** | Sede Orinoquía | Clima IDEAM–NASA POWER, cartografía, coberturas, Landsat y productos SWOT. |
| **La Paz** | Sede de La Paz | Climatología, cartografía de ubicación y productos disponibles para exploración territorial. |

**Nota de clasificación:** cuando los archivos de MapBiomas lo permiten, la aplicación mantiene separados **SA (San Andrés)** y **SAC (San Andrés Costa)**. Estos códigos no son equivalentes ni deben fusionarse automáticamente.

La cantidad de información y su nivel de validación **no son iguales** en todos los territorios. Dentro de la aplicación se identifican componentes *Completos*, *En proceso*, *Pendientes* o *Sin datos*; esta clasificación indica avance de integración y no constituye una certificación de calidad científica.

## 2. ¿Qué permite consultar SIAMS?

| Componente | Fuente o producto principal | Cobertura temporal de referencia* | Nivel de análisis | Estado de uso |
|---|---|---|---|---|
| **Clima y estaciones** | IDEAM / DHIME y NASA POWER | Depende del Excel y de la estación consultados | Estación o celda climática | Integrado; validación pendiente según variable y sede |
| **Tendencias** | Series climáticas disponibles; Mann–Kendall y pendiente de Sen | Según longitud de la serie útil | Temporal | Exploratorio; requiere controles de homogeneidad y autocorrelación |
| **Agua subterránea** | Anomalías GWSa derivadas de GRACE/GRACE-FO y GLDAS | Según NetCDF disponible, aproximadamente desde 2002 | Regional | Exploratorio; no equivale al nivel de un pozo |
| **Ríos** | SWOT, mediante datos procesados de HydroWeb | Desde la misión SWOT, según observaciones disponibles | Tramos fluviales (*reaches*) | Exploratorio; sujeto a filtros de calidad |
| **Coberturas de la tierra** | MapBiomas Colombia | Series CSV disponibles de 1985–2024 | Clases y subclases territoriales | Exploratorio; depende de la colección y zona |
| **Evolución satelital** | Landsat y Sentinel-2 | Fechas efectivamente procesadas (se incluyen productos de 2024–2025) | Escenas e índices | Visualización de productos procesados |
| **Cartografía** | Mapas temáticos y composiciones elaboradas en QGIS | Según fecha de cada fuente o mapa | Local, municipal, regional y nacional | Consulta de referencia; verificar escala, SRC y autoría |
| **Calidad y monitoreo** | IRCA, datos de estaciones, sondeos y registros que se integren | Según disponibilidad y autorización | Punto, estación o territorio | Desarrollo progresivo; no se inventan mediciones ausentes |

\* **Los intervalos de esta tabla no garantizan cobertura continua ni completitud.** La fecha efectiva, la resolución, las unidades, el sistema de referencia y la procedencia deben revisarse para cada producto individual.

### Funcionalidades de la interfaz

La aplicación, construida con **Python + Streamlit**, organiza la consulta en los grupos **Inicio**, **Territorio**, **Clima y datos**, **Subsuelo y calidad del agua**, **Monitoreo** y **Proyecto**. Según la sección y los archivos disponibles, presenta:

- Fichas de las sedes, indicadores, mapas e información contextual.
- Series, regímenes climáticos y comparaciones entre fuentes, sin fusionarlas indiscriminadamente.
- Exploración de tendencias mediante Mann–Kendall y pendiente de Sen.
- Coberturas de MapBiomas, animaciones Landsat/Sentinel-2 y productos fluviales SWOT.
- Mapas QGIS en PDF, cartografía temática y fichas de procedencia.
- Anomalías regionales de almacenamiento subterráneo (GWSa) y análisis exploratorio GGDI.
- Indicadores de disponibilidad de datos y advertencias cuando faltan fuentes.

## 3. Instalación local

### Requisitos previos

- **Python 3.12** recomendado para reproducir el entorno de desarrollo.
- **Git** para clonar y actualizar el repositorio.
- Navegador web moderno.
- Espacio de almacenamiento suficiente para los mapas, archivos de datos y animaciones que se incluyan en la instalación.

### Obtener el código

```bash
git clone https://github.com/Ncl-ux/Siams-Leticia-Tumaco.git
cd Siams-Leticia-Tumaco
```

> Si ya tienes el proyecto abierto en Visual Studio Code, **no necesitas clonarlo otra vez**: usa la terminal dentro de esa carpeta.

### Crear y activar un entorno virtual

**Windows (PowerShell):**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si Python 3.12 no está registrado en `py`, utiliza `python -m venv .venv` con la versión instalada. Si PowerShell restringe la activación, se puede ejecutar directamente `.\.venv\Scripts\python.exe` sin activar el entorno.

**Linux, macOS o Codespaces:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Instalar dependencias

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Para visualizar mapas PDF, `requirements.txt` debe incluir estas dependencias si la versión instalada de Streamlit las requiere:

```text
streamlit[pdf]
pymupdf
```

Si aparecen avisos por falta de un motor de PDF, comprueba que instalaste las dependencias **en el mismo entorno virtual** que ejecuta Streamlit.

### Iniciar la aplicación

```bash
python -m streamlit run app.py
```

Streamlit indicará en la terminal la dirección local de acceso, habitualmente `http://localhost:8501`.

Para detener la aplicación, presiona **Ctrl + C** en la terminal.

### Comprobar la instalación

```bash
python -m py_compile app.py
python -c "import streamlit, pandas, plotly; print('Dependencias principales disponibles')"
```

La compilación comprueba **sintaxis**, pero no garantiza que todas las hojas de Excel, gráficos y mapas estén disponibles. Es necesario recorrer las siete sedes y las secciones que correspondan.

## 4. Estructura del repositorio

La estructura A5 separa datos, scripts reproducibles y recursos visuales; los módulos de SIAMS leen los datos desde `data/processed/`.

```text
Siams-Leticia-Tumaco/
├── app.py                     # Interfaz principal de Streamlit
├── siams/                     # Módulos de la aplicación
├── scripts/                   # Descarga, procesamiento y verificación A5
├── data/
│   ├── raw/swot/              # plot_*.csv originales de HydroWeb
│   ├── processed/clima/       # Excel IDEAM y NASA POWER
│   ├── processed/swot/        # Tablas por reach_id
│   ├── processed/grace/       # NetCDF y tablas derivadas
│   ├── processed/hidrogeoquimica/
│   ├── processed/mapbiomas/
│   └── processed/landsat/
├── Animaciones_SWOT/          # GIF (sin modificar)
├── Tarjetas_SWOT/             # PNG técnicos (sin modificar)
├── Coberturas_MapBiomas/      # Recursos visuales
├── Landsat/ y Sentinel/       # Recursos visuales
├── Mapas_Qgis/ y Mapas_Tematicos/
├── Fotos_Sedes/ y Recursos_Hidrogeoquimica/
├── tests/ y docs/
├── README.md y .gitignore
└── requirements.txt
```

Las descargas originales aún no disponibles se incorporarán progresivamente a `data/raw/`. No crear copias adicionales de Excel o CSV procesados en las carpetas visuales. Consulta `data/README.md` para la trazabilidad y las limitaciones de A5.

### Convención de nombres

- Preferir nombres descriptivos y estables, **sin espacios iniciales o finales**, tildes ni caracteres especiales en las rutas de datos.
- Para nombres de archivos procesados, preferir minúsculas y guion bajo: `nasa_power_tumaco.xlsx`, `mapbiomas_arauca_nivel_1.gif`.
- Conservar los códigos que diferencian zonas o productos, como `SA` y `SAC`, y los identificadores de tramos SWOT cuando correspondan.
- Registrar el año o periodo cuando sea necesario para evitar confundir versiones.
- Al renombrar archivos o carpetas, actualizar también sus referencias en el código y probar la aplicación **antes** de confirmar los cambios con Git.

## 5. Datos, procedencia y reproducibilidad

Los archivos incluidos en SIAMS proceden de entidades externas y de procesamientos académicos. **Su presencia en el repositorio no implica que el equipo sea propietario de los datos originales o que exista permiso para redistribuirlos.**

Para cada conjunto de datos se debe mantener una ficha con, como mínimo:

| Campo requerido | Qué documentar |
|---|---|
| Fuente responsable | Entidad, equipo o publicación original. |
| Producto y versión | Nombre técnico, colección, nivel de procesamiento y fecha de consulta. |
| Periodo | Fechas inicial y final efectivas y faltantes relevantes. |
| Unidades y zona horaria | Unidad real de cada campo; UTC o hora local cuando corresponda. |
| Cobertura espacial | Coordenadas, estación, celda, *reach*, área de estudio y SRC. |
| Control de calidad | Filtros, criterios de exclusión y registros descartados. |
| Procesamiento | Script, parámetros, transformaciones y versión de dependencias. |
| Licencia y crédito | Condiciones de uso, enlace original y atribución exigida. |

**Pendiente de implementación:** centralizar estos metadatos en un inventario versionado y publicar los scripts/cuadernos que generan los Excel, NetCDF, CSV derivados y animaciones. El repositorio actual no permite asegurar una reproducción completa de todos esos productos desde los datos crudos.

## 6. Limitaciones científicas conocidas

1. **Precipitación de Tumaco:** la serie IDEAM presenta indicios de cambios de resolución o consistencia entre periodos. Las tendencias no deben interpretarse como evidencia concluyente de cambio climático antes de verificar homogeneidad, metadatos y estaciones cercanas.
2. **Radiación solar:** está pendiente verificar y normalizar las unidades de los archivos derivados de NASA POWER. Las etiquetas de visualización deben corresponder a la unidad efectivamente almacenada (por ejemplo, MJ/m²/día o kWh/m²/día, según el procesamiento).
3. **Precipitación agregada:** las columnas que representan totales mensuales o anuales no deben seguir rotuladas como si contuvieran precipitación diaria.
4. **NASA POWER frente a IDEAM:** sus diferencias responden, entre otros factores, a escalas y metodologías de estimación distintas. No deben sustituirse automáticamente las mediciones locales con celdas de reanálisis.
5. **GRACE/GLDAS:** GWSa representa una **anomalía regional de almacenamiento**. No es profundidad del nivel freático, nivel de un pozo ni recarga puntual. También está pendiente completar metadatos del NetCDF y la cita de la metodología original.
6. **SWOT:** las observaciones dependen del tramo, fechas de paso y calidad del producto. Las fichas e imágenes no reemplazan la consulta del dato original con sus indicadores de calidad.
7. **Mapas y coberturas:** las escalas, fuentes, proyecciones, fechas y permisos pueden variar. Los PDF de QGIS requieren verificación individual de sus metadatos de exportación.
8. **Móvil y conectividad:** las visualizaciones, PDF y GIF pesados pueden tardar en cargar en celulares o redes de baja velocidad; la optimización multimedia sigue en progreso.

Estas limitaciones se mantienen documentadas incluso cuando la aplicación se ejecuta sin errores.

## 7. Ética, privacidad y datos comunitarios

El trabajo debe considerar los principios **FAIR** (encontrabilidad, accesibilidad, interoperabilidad y reutilización) y **CARE** (beneficio colectivo, autoridad para controlar, responsabilidad y ética), especialmente en datos procedentes de comunidades y territorios indígenas.

**No se deben divulgar coordenadas de pozos domésticos, puntos de abastecimiento familiar u otra información sensible sin revisar su origen, sus condiciones de uso y las autorizaciones correspondientes.** El mapa de pozos de Leticia fue señalado para revisión prioritaria; debe retirarse de la publicación pública o mantenerse restringido hasta contar con una decisión documentada con las fuentes y la comunidad pertinente. Incluir esta advertencia en el README **no sustituye retirar o restringir el archivo ni sus versiones públicas**.

Las fotografías y mapas de terceros deben contar con crédito de autor, procedencia y permiso o base jurídica de utilización. Antes de publicar fotografías se deben revisar metadatos EXIF que puedan contener información de ubicación no prevista.

## 8. Citación y licencias

**Estado actual: pendiente de formalización.** No se declara una licencia abierta sobre el proyecto mientras no exista un archivo `LICENSE` aprobado por el equipo o la institución correspondiente. La ausencia de ese archivo **no** significa que todos los contenidos puedan reutilizarse libremente.

Antes de publicar una versión de referencia académica, se propone:

- Incorporar `CITATION.cff` con autores autorizados, nombre del proyecto, versión, fecha y enlace del repositorio.
- Definir y aprobar una licencia para **código original**, por separado de la licencia de materiales gráficos o audiovisuales propios.
- Identificar las licencias **de cada fuente externa**, que prevalecen sobre cualquier licencia general del repositorio.
- Completar los créditos de fotografías, figuras, mapas y productos satelitales.
- Documentar la referencia bibliográfica completa del producto regional GWSa de Romero y Piña (2025), tras verificarla en su fuente original.

**Citación provisional del software** (hasta contar con `CITATION.cff`):

> Semillero de Investigación en Agua y Modelación Subterránea (SIAMS). (2026). *SIAMS: plataforma hidroambiental* [Prototipo de software]. Universidad Nacional de Colombia. https://github.com/Ncl-ux/Siams-Leticia-Tumaco

Esta referencia identifica el prototipo, pero **no reemplaza** la citación de los datos, imágenes, algoritmos o publicaciones de terceros.

## 9. Estado del desarrollo y próximas tareas

La plataforma continúa en desarrollo. Las prioridades incluyen:

- Validar la homogeneidad de precipitación IDEAM en Tumaco y revisar otras series con cambios de resolución.
- Corregir y documentar unidades y metadatos climáticos y del NetCDF GWSa.
- Incorporar scripts reproducibles y pruebas automatizadas.
- Mejorar la accesibilidad en celulares y producir animaciones más ligeras.
- Completar licencias, créditos, citas y la revisión ética del mapa de pozos de Leticia.
- Optimizar el repositorio y evitar incluir `.venv`, cachés y archivos temporales en Git.
- Desarrollar fichas comprensibles para usuarios no especialistas y nuevas herramientas de monitoreo cuando existan datos validados.

Las modificaciones se desarrollan en ramas de trabajo y deben comprobarse antes de incorporarse a `main`.

## 10. Contribuciones y equipo

SIAMS es un proyecto académico colaborativo. Las mejoras, correcciones de datos y aportes metodológicos deben registrar su procedencia y ser revisados antes de publicarse.

Flujo recomendado para colaborar:

1. Crear una rama descriptiva a partir de una versión estable.
2. Registrar qué archivos se modificaron y por qué.
3. Probar la aplicación y revisar las siete sedes relacionadas con el cambio.
4. Presentar los cambios mediante una *pull request* para su revisión.
5. No subir datos personales, ubicaciones sensibles, credenciales ni archivos pesados sin autorización.

**Responsable institucional, colaboradores y medio de contacto:** pendientes de confirmar con el equipo antes de su publicación. No se incluyen nombres sin autorización.

---

*Documento de trabajo actualizado para la reorganización técnica de SIAMS (octubre de 2026). Las afirmaciones científicas y los permisos de redistribución siguen sujetos a verificación de las fuentes originales.*

## Reproducibilidad de datos · revisión A5 (octubre de 2026)

El código de la plataforma permanece en `siams/`. Los scripts de obtención, consolidación y verificación se documentan en `scripts/`. Los datos originales se ubican en `data/raw/` y los productos estructurados usados por la plataforma en `data/processed/`. Los PDF, PNG y GIF permanecen en sus carpetas de recursos para mantener la compatibilidad visual.

Para verificar la migración de archivos, ejecutar `python scripts/verificar_a5.py`. Para rehacer las tablas exploratorias SWOT a partir de 80 exportaciones HydroWeb, ejecutar `python scripts/procesar_swot.py --out data/processed/swot_regenerado_revision`; no sustituir las tablas publicadas hasta comparar la versión regenerada. NASA POWER puede descargarse y transformarse con `python scripts/nasa_power.py --help`. Los ejemplos, las advertencias y los datos todavía no reproducibles se encuentran en [`data/README.md`](data/README.md) y [`docs/PLAN_VALIDACION_A5.md`](docs/PLAN_VALIDACION_A5.md).

**Importante:** la migración conserva los datos procesados recibidos, pero no demuestra que los archivos históricos de IDEAM, GRACE/GLDAS, MapBiomas, Landsat o Sentinel puedan reconstruirse sin obtener las fuentes y scripts que faltan. Tampoco autoriza a publicar mediciones personales, pozos ni recursos con licencia no verificada.
