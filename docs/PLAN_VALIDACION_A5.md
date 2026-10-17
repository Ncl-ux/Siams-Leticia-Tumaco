# SIAMS A5 · Informe de migración y verificación

**Alcance:** reorganización de datos *estructurados* sin cambiar la física ni recalcular los indicadores publicados; los GIF, PDF y PNG permanecen donde están, para no romper sus referencias. La aplicación debe consumir los productos desde `data/processed/` mediante adaptaciones en `siams/`.

## Componentes modificados

- `siams/utilidades.py`: Excel climáticos priorizan `data/processed/clima/` con ruta histórica de respaldo.
- `siams/grace.py` y `siams/grace_leticia.py`: NetCDF y tablas GRACE en `data/processed/grace/`.
- `siams/hidrogeoquimica.py` y `siams/hidrogeoquimica_datos.py`: nuevos CSV/JSON de hidrogeoquímica; recursos didácticos no se mueven.
- `siams/landsat.py`, `siams/mapbiomas.py`: tablas CSV en `data/processed/`, GIF en sus carpetas originales.
- `siams/swot.py`: conserva las fichas PNG y GIF; incorpora la interfaz de control exploratorio M7 que ya se había trabajado y la lectura en `data/processed/swot/`.
- `app.py`: únicamente modifica mensaje que indica ubicación del NetCDF. Las visualizaciones y los cálculos de tendencia permanecen.

## Validaciones necesarias antes de cerrar A5

1. Comparar un Excel NASA generado desde JSON real con su Excel histórico para mismos parámetros, punto, periodo, valores, ausentes, unidad y hojas.
2. Ejecutar `scripts/procesar_swot.py --out <directorio temporal>` y comparar con las tablas M7 conservadas; el script ahora reproduce las **76 alertas** y las **1.957 fechas** de las 20 tablas conservadas con tolerancias numéricas; las reglas de vinculación temporal e incertidumbre deben revisarse metodológicamente antes de una validación científica oficial. No eliminar observaciones ni presentar este umbral como bandera oficial.
3. Recuperar descargas originales y scripts históricos IDEAM, GRACE/GLDAS, MapBiomas, Landsat y Sentinel.
4. Confirmar los `reach_id` de Tumaco: asignación Mira vs Rosario con evidencia externa del producto, no por prefijo solamente.
5. Revisar consentimiento/licencias A6/A7 antes de subir pozos, mediciones o cartografía a GitHub.
6. Comprobar arranque local Streamlit, todas las siete sedes, y `pytest` después de fusionar en la rama activa.
7. Controlar PDF grandes (varios exceden 50 MiB) y estrategia de Git LFS/ZENODO antes de hacer `git add -A`.

**Estado:** A5 tiene ya una estructura reproducible y un script real de reconstitución de SWOT; la reproducibilidad *completa de todas las fuentes* sigue en curso. No marcar como formalmente cerrado sin los pasos 1–6.

## GitHub Actions

El ZIP recibido no incluía `.github/`. Se recuperó una configuración de pruebas del paquete de GitHub Actions compartido anteriormente; el instalador NO sobrescribe un workflow local existente. Verifica tus workflows actuales antes de publicarlos.
