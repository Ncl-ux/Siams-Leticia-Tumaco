# Chingaza · fase 1

Territorio de estudio (no sede UNAL). Datos de observación mensuales únicamente. No copiar las fuentes originales diarias al repositorio, ni a las carpetas de descargas de Streamlit.

## Fuentes y criterios
- EAAB E.S.P., SIH, informe 2024/02/02: `INFORMACIÓN CHINGAZA_Acueducto.xlsx`, proyecto Chingaza. Se identifica cada variable por el parámetro del encabezado, no por el nombre de la hoja. Precipitación: suma mensual. Caudal: promedio mensual. Solo meses con todos los días numéricos no negativos, sin marcas sin interpretar. Controles de completitud incluidos. No se imputan faltantes. Las marcas requieren su diccionario antes de relajar este criterio. No se han auditado valores extremos ni homogeneidad; resultados exploratorios. No se incluyen coordenadas de estaciones hasta contrastarlas.
- SIG/Geodatabase del proyecto Chingaza: nueve capas convertidas a EPSG:4326; reparación de geometrías inválidas y simplificación 0,0001 grados, conservando topología. Solo para exploración, no para calcular áreas. Fuente primaria/fecha por capa pendientes. Sin atributos originales ni coordenadas de muestreo. Punto interior PNN 4.567931, -73.744330, elegido como referencia puntual inicial; no representa promedio areal ni el punto de Sentinel-2.
- Sentinel-2: conserva el módulo y los videos previamente instalados.
- NASA POWER AG: script original 01, a partir de 1981, agrega en memoria a escala mensual. Mantiene unidades del proyecto y excluye meses incompletos por variable.
- CHIRPS v3 Final UCSB-CHC: reutiliza lectura puntual incremental del script 12.
- GPM IMERG Final V07B (NASA GES DISC): reutiliza script 16, Earthdata; DOI 10.5067/GPM/IMERG/3B-MONTH/07. Se guardan solo los meses de Chingaza; no modifica datos ni metadatos generales de otras sedes.

## Descargas (ejecutar desde repositorio)
```
python scripts/21_chingaza_satelital.py --fuente nasa_power
python scripts/21_chingaza_satelital.py --fuente chirps
python scripts/21_chingaza_satelital.py --fuente imerg --max-meses 24
```
Repetir IMERG por bloques o quitar el límite. Requiere conexión, rasterio para CHIRPS y earthaccess/h5py y autorización Earthdata para IMERG. No se habilita todavía la actualización automática de Chingaza. El comparador climático incorpora el régimen NASA mensual si existe; los periodos pueden diferir entre sedes. No publicar hasta completar pruebas en el repositorio y verificar fuentes.

## Pendientes
IDEAM (selección espacial, unidad, flags, completitud), geología, DEM, cobertura MapBiomas, Landsat, SWOT, GRACE/GGDI, isotopía, origen de humedad y validación por cuencas. Las descargas satelitales puntuales no equivalen a promedios de cuenca. Verificar datos extremos y ubicaciones de EAAB. Mantener fuentes mensuales separadas. Las capas y código no reemplazan las investigaciones originales.

## Actualización posterior a fase 1 (noviembre 2026)
Se incorporaron módulos de IDEAM mensual, relieve, MapBiomas, Landsat, SWOT, GRACE/GGDI, geología, hidrogeología, isotopía mensual y análisis estadísticos. Los estados de fase 1 anteriores son históricos. Sigue pendiente verificar la clasificación original de coberturas Landsat, las fuentes y permisos específicos, y las pruebas completas en producción. El workflow semanal invoca el script 21 para NASA POWER, CHIRPS e IMERG de Chingaza, con una lista cerrada de productos abiertos para publicar: NASA POWER diario y mensual, CHIRPS e IMERG mensuales. IMERG requiere secretos Earthdata. El workflow programado solo se activa desde la rama predeterminada de GitHub; verificar dicha rama y el despliegue antes de publicar. No se incorporan datos diarios institucionales.
