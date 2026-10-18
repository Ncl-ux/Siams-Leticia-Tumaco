# SIAMS · A4 — Metadatos CF y metodología de GRACE/GRACE-FO

## Evidencia revisada

- Archivo aportado a SIAMS: `data/processed/grace/COL_GWS_estimations.nc`, variable `GWS_anom(time, lat, lon)`, 244 tiempos × 135 latitudes × 99 longitudes, entre 2002-05-10 y 2025-05-16.
- Valores GWSa expresados en **cm de espesor equivalente de agua**, de acuerdo con el cuaderno `ExtraerDatos_Aguachica (1).ipynb` y el método publicado.
- El NetCDF original carecía de atributos globales científicos y de unidades para `GWS_anom` y `lon`; contenía enlaces `bounds` hacia variables inexistentes.

## Metodología científica (referencia de interpretación)

Según Romero y Piña (2025), la anomalía del almacenamiento subterráneo se estima a partir del balance de las anomalías de almacenamiento total de agua observadas por GRACE/GRACE-FO (TWSa) menos componentes de superficie terrestre modelados por GLDAS: humedad del suelo, equivalente de agua en nieve y agua de dosel, con la salvedad de que no se sustrae explícitamente el almacenamiento superficial del agua. El artículo menciona el producto **JPL RL06.3Mv04-CRI** para GRACE/GRACE-FO y los modelos **CLSM_F2.5**, **Noah_v3.6** y **VIC_v4.1.2** para GLDAS.

Estas son las **fuentes utilizadas en la metodología del artículo**. La procedencia específica y la combinación utilizada para construir el NetCDF concreto de SIAMS **no están documentadas en el archivo ni en el cuaderno recibido**, por lo que NO se asigna falsamente esa versión como entrada verificada.

**GGDI implementado en SIAMS:** climatología media por mes calendario de los registros disponibles; `GSD = GWSa - climatología_del_mes`; `GGDI = GSD / desviación_estándar(GSD)` (adimensional). El procesamiento y la visualización de GGDI son secundarios al archivo NetCDF y **no se han modificado**.

## Conformidad CF añadida

- `Conventions=CF-1.8`, unidades `cm` y `long_name` de `GWS_anom`.
- `lat` con `degrees_north`, `lon` con `degrees_east`, ambos con `standard_name` y `axis`; tiempo original preservado.
- Variable escalar `crs` con `grid_mapping_name=latitude_longitude` (sin inventar datum/ellipsoide). Referencia `grid_mapping=crs` en GWSa.
- Se suprimen únicamente atributos `bounds` si las variables a las que apuntan no existen; no se inventan los límites.
- Cita formal, estado de trazabilidad, cobertura real, advertencia de resolución física y documentación del periodo de referencia no conocido.

**Precisión:** declarar `Conventions=CF-1.8` y comprobar los atributos principales no equivale a una certificación de conformidad exhaustiva por `cfchecker`.

## Referencias y diferencias entre archivos

- Romero, P., & Piña, A. (2025). *GRACE-based analysis of groundwater sustainability in the tropics*. **Journal of Hydrology: Regional Studies**, 62, 102756. https://doi.org/10.1016/j.ejrh.2025.102756
- Romero, P. J., & Piña, A. (2025). *Colombia Groundwater Storage Anomalies (2002–2023)*. Zenodo. https://doi.org/10.5281/zenodo.14707819

**No son el mismo archivo:** Zenodo describe `Groundwater_cm`, 220 fechas y malla de 136 × 99; el NetCDF suministrado a SIAMS es `GWS_anom`, 244 fechas y malla de 135 × 99. El enlace Zenodo se ofrece como **producto relacionado**, no como procedencia demostrada del NetCDF actual.

## Limitaciones

La malla de aproximadamente 0,12° es un *remuestreo geográfico*, NO la resolución física de GRACE, cuyo soporte espacial es de centenares de kilómetros. Para Leticia deben tenerse en cuenta los humedales y planicies inundables, ya que una parte de la señal podría reflejar cambios de almacenamiento superficial. GWSa y GGDI **no** representan directamente niveles piezométricos ni tasas de recarga locales.

El **periodo real de referencia usado al generar GWSa permanece sin documentar**; tampoco consta el datum del sistema de coordenadas del producto original. Por rigor metodológico se consignan como no verificados, sin completar campos con estimaciones.

## Verificación y preservación de datos

`python scripts/aplicar_a4_grace_cf.py` modifica solo atributos y añade una variable escalar de CRS en una copia temporal validada. Si el archivo fuente no coincide exactamente con la huella SHA-256 recibida, no modifica nada. Crea respaldos en Documentos, fuera de Git. Preserva sin cambios los **244 × 135 × 99 valores originales**, las fechas y las coordenadas. `python scripts/aplicar_a4_grace_cf.py --verificar` comprueba integridad y cita visible en `app.py`.
