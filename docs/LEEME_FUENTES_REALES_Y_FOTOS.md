# SIAMS – A6 y A8, sin carpetas auxiliares

Este paquete **no contiene** `plantillas/` ni `insumos_fotos_sedes/`. Usa solamente carpetas que ya existen en SIAMS:
- `Fotos_Sedes/`: fotografía actualizada de Tumaco (las otras seis ya coinciden con las del proyecto original).
- `docs/`: procedencia de las fuentes oficiales y crédito fotográfico. Si falta `docs/AUTORES_SIAMS.csv`, el verificador lo crea con los encabezados, sin inventar autores ni sobrescribir una lista existente.
- `siams/`: módulo existente para visualización de fuentes.
- `scripts/` y `tests/`: instaladores y verificaciones.

## Instalación en la raíz del repositorio de SIAMS

1. Si quieres conservar la fotografía anterior de Tumaco por fuera de Git, guarda primero una copia. El ZIP incluye la nueva `Fotos_Sedes/Tumaco.jpeg` y al extraer con `-Force` sobrescribe ese archivo. Git también permite recuperar la foto previamente versionada.
2. Extrae el ZIP en la **raíz del proyecto**, manteniendo las rutas. **No utilices simultáneamente el ZIP anterior con carpetas temporales.**
3. Ejecuta: `python scripts/instalar_fuentes_creditos_siams.py` (integra en `app.py` de forma idempotente, sin reemplazar su contenido completo).
4. Ejecuta: `python scripts/instalar_fotos_y_fuentes_siams.py` (crea `docs/AUTORES_SIAMS.csv` solo si falta y verifica fotos; no las mueve).
5. Verifica: `python scripts/instalar_fuentes_creditos_siams.py --verificar`; `python scripts/instalar_fotos_y_fuentes_siams.py --verificar`; `python -m pytest -q`.
6. Revisa la vista de Streamlit antes de commit y push.

## Fuentes

Incluye enlaces oficiales de IDEAM DHIME, NASA POWER, Hydroweb.next (SWOT), MapBiomas Colombia, Copernicus Data Space (Sentinel-2), USGS Landsat Collection 2, y referencia bibliográfica del producto derivado GRACE. IDEAM y NASA POWER aparecen por separado; los portales son **referencias de institución**, no enlaces certificados de cada descarga.

La identidad institucional es "Semillero de Investigación de Aguas y Modelación Subterránea (SIAMS)". Los nombres de autores, la autoría de las fotos, licencias y permisos requieren validación y no se inventan.
