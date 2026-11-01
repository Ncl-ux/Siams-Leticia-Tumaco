# Scripts de procesamiento

Todos se corren desde la raíz del repositorio con el entorno activado.

| Script | Qué hace | Estado |
|---|---|---|
| `00_corregir_rotulos_excel.py` | Corrige rótulos de unidades en los Excel (radiación en MJ/m²/día, precipitación mm/día · mm/mes · mm/año), agrega la hoja `Diccionario` y arregla el formato de «Fechas ausentes» en Arauca. No cambia valores. | Aplicado en esta versión (idempotente). |
| `01_descarga_nasa_power.py` | Descarga NASA POWER diario (API v2, comunidad AG) para una sede y arma el Excel con la misma estructura de `NASA_POWER_*_FINAL.xlsx`. | **Reconstruido y verificado**: con las coordenadas de la sede reproduce exactamente los valores diarios de 1992–2025 de Tumaco y del primer año de las otras cinco sedes. 2026 difiere porque NASA reemplaza los datos casi en tiempo real. |
| `02_agregados_anuales.py` | Series anuales (suma de lluvia, promedios del resto) desde `Datos_diarios`. | Real. Salida en `data/processed/anuales/`. |
| `03_tendencias_homogeneidad.py` | Mann-Kendall, Hamed-Rao, Sen, Pettitt y SNHT por sede y variable. | Real. Salida en `docs/tendencias_homogeneidad.csv`. |
| `04_netcdf_metadatos_cf.py` | Agrega metadatos CF al NetCDF de GWSa sin cambiar valores. | Aplicado. Faltan datos que solo conocen los autores del producto (marcados «por confirmar»). |
| `06_gwsa_grace_gldas_extendido.py` | `descargar`: baja el archivo JPL GRACE/GRACE-FO mascon RL06.3Mv04 y el recorte GLDAS-2.1 Noah 0,25° de Colombia (NASA Earthdata; `~/.netrc` o `EARTHDATA_TOKEN`). `procesar`: calcula GWSa con el método de anomalías (línea base 2004–2009) hasta 2026-06 en la malla de la app y valida contra el NetCDF original. | **Real**. `procesar` verificado (reproduce la reconstrucción de 0,5° con diferencias ≤ 0,0005 cm). `descargar` sigue el mismo procedimiento con que se bajaron los insumos, pero no se volvió a ejecutar en esta versión. |
| `06_gwsa_grace_gldas_extendido.py alternativa` | Serie original extendida: copia los valores de `COL_GWS_estimations.nc` hasta 2025-04 y calcula 2025-05 a 2026-06 con la fórmula de diferencias mensuales (`TWSA − (ΔSM + ΔSWE)`); valida el empalme sobre 2023-05 a 2025-04. | **Real**, ejecutado en esta versión. Reproduce la fórmula sobre el original con r = 0,995 en la serie media nacional. |
| `07_landsat_filtrar_escenas.py` | Aplica `config/landsat_criterios.toml` a cada `Landsat/<Sede>/Control_escenas.csv`, escribe `metadatos_escenas.csv` (sensor, path/row, tier, % del buffer no aprovechable, cumple, motivos) y extrae a `escenas/` solo los fotogramas de las escenas que cumplen. Con `--eliminar-gif` borra los GIF originales. | **Real**, ejecutado con `--eliminar-gif`. Los GIF ya no están; volver a correrlo solo actualiza los metadatos. |
| `08_landsat_compuestos_stac.py` | Compuesto de mediana de temporada seca por sede: Landsat 8/9 C2 L2 Tier 1 del catálogo STAC de Microsoft Planetary Computer (sin cuenta), máscara QA_PIXEL, realce fijo, JPG color natural y falso color con norte, escala y fuente, y tabla de escenas usadas. Requiere `pip install pystac-client planetary-computer rasterio pyproj pillow` (no los necesita la app). | **Real**, ejecutado para las seis sedes con temporadas 2023–2025 (Arauca, La Paz y San Andrés con `--max-escenas 10`). |
| `05_optimizar_medios.sh` | Comandos usados para comprimir PDF, convertir GIF a MP4 y quitar EXIF. | Documentación de lo aplicado. |

## Lo que todavía falta (para el semillero)

- `02_procesa_ideam.py`: cómo se unificaron los CSV de DHIME (`TUMACO_COCO_EL_UNIFICADO (2).csv`, etc.)
  y cómo se armaron `ANALISIS_HIDROMETEOROLOGICO_*.xlsx`. Los CSV crudos no están en el repositorio:
  súbanlos a `data/raw/` o documenten la consulta exacta en DHIME.
- Clasificación Landsat (Colab): el cuaderno no está. Si mantienen la clasificación propia, rehagan las áreas
  sobre los compuestos de `08_landsat_compuestos_stac.py` y validen con puntos de referencia; si no, usen MapBiomas.
- Animaciones Sentinel-2, tarjetas y animaciones SWOT (HydroWeb) y
  exportaciones de MapBiomas: suban los cuadernos de Colab/GEE y las tablas por tramo (`reach_id`).
- Cómo se calculó el NetCDF **original** de GWSa (`COL_GWS_estimations.nc`, 2002-05 a 2025-05). Su comportamiento
  coincide con la fórmula de diferencias de UNgroundwater y no con el producto publicado; ver `data/README.md`, 4.1.
  El NetCDF que usa la app ya se reproduce con `06_gwsa_grace_gldas_extendido.py`.
