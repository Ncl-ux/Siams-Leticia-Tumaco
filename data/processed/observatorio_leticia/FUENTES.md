# Procedencia de series de lluvia del observatorio Leticia

Los tres CSV de este directorio provienen del paquete entregado `Explorador_Leticia_para_SIAMS(1).zip`:

* `ideam_precip_mensual_qc.csv`: `03_proyecto_GRACE_Leticia/data_procesados/processed/local/ideam/ideam_precip_mensual.csv` (se seleccionaron únicamente columnas necesarias para validación y su calidad).
* `chirps_v2_leticia_mensual.csv`: `03_proyecto_GRACE_Leticia/data_procesados/processed/chirps/CHIRPS_v2.0_monthly_mm_sites.csv` (columna Leticia).
* `imerg_final_leticia_mensual.csv`: `03_proyecto_GRACE_Leticia/data_procesados/processed/imerg/IMERG_Final_V07_monthly_mm_sites.csv` (columna Leticia).

Para CHIRPS v3 se conserva **sin duplicar** la serie de la profesora `data/processed/actualizacion/chirps_leticia.csv`. Se usan exclusivamente meses IDEAM identificados como `completo=True`, sin reconstruir periodos parciales. Los datos satelitales son estimaciones por píxel, no mediciones de la estación.

No se incluyen ubicaciones de pozos ni series horarias privadas.
