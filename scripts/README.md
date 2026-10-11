# Scripts de procesamiento

Todos se corren desde la raíz del repositorio con el entorno activado.

| Script | Qué hace | Estado |
|---|---|---|
| `00_corregir_rotulos_excel.py` | Corrige rótulos de unidades en los Excel (radiación en MJ/m²/día, precipitación mm/día · mm/mes · mm/año), agrega la hoja `Diccionario` y arregla el formato de «Fechas ausentes» en Arauca. No cambia valores. | Aplicado en esta versión (idempotente). |
| `01_descarga_nasa_power.py` | Descarga NASA POWER diario (API v2, comunidad AG) para una sede y arma el Excel con la misma estructura de `NASA_POWER_*_FINAL.xlsx`. | **Reconstruido y verificado**: con las coordenadas de la sede reproduce exactamente los valores diarios de 1992–2025 de Tumaco y del primer año de las otras cinco sedes. 2026 difiere porque NASA reemplaza los datos casi en tiempo real. |
| `02_agregados_anuales.py` | Series anuales (suma de lluvia, promedios del resto) desde `Datos_diarios`. | Real. Salida en `data/processed/anuales/`. |
| `03_tendencias_homogeneidad.py` | Mann-Kendall, Hamed-Rao, Sen, Pettitt y SNHT por sede y variable. | Real. Salida en `docs/tendencias_homogeneidad.csv`. |
| `04_netcdf_metadatos_cf.py` | Agrega metadatos CF al NetCDF de GWSa sin cambiar valores. | Aplicado. Faltan datos que solo conocen los autores del producto (marcados «por confirmar»). |
| `05_optimizar_medios.sh` | Comandos usados para comprimir PDF, convertir GIF a MP4 y quitar EXIF. | Documentación de lo aplicado. |

## Lo que todavía falta (para el semillero)

- `02_procesa_ideam.py`: cómo se unificaron los CSV de DHIME (`TUMACO_COCO_EL_UNIFICADO (2).csv`, etc.)
  y cómo se armaron `ANALISIS_HIDROMETEOROLOGICO_*.xlsx`. Los CSV crudos no están en el repositorio:
  súbanlos a `data/raw/` o documenten la consulta exacta en DHIME.
- Clasificación Landsat (Colab), animaciones Sentinel-2, tarjetas y animaciones SWOT (HydroWeb) y
  exportaciones de MapBiomas: suban los cuadernos de Colab/GEE y las tablas por tramo (`reach_id`).
- Cómo se calculó el NetCDF de GWSa (o la referencia exacta del producto descargado).
