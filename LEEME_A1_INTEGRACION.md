# SIAMS — A1 integrado respetando la estructura actual

Esta versión **corrige el error anterior**: los datos viven bajo `data/`, y los programas auxiliares bajo `scripts/`. No crea carpetas `datos/`, `analisis/` ni `pages/`.

## Destino exacto de los archivos

```text
Siams-Leticia-Tumaco/
├── app.py                                 # modificado solo para incluir A1 en menú
├── siams/
│   └── homogeneidad_a1.py                # módulo nuevo (no reemplaza otros módulos)
├── data/
│   ├── processed/
│   │   ├── clima/                         # intacta: ocho Excel IDEAM/NASA POWER
│   │   ├── a1/
│   │   │   └── tumaco/
│   │   │       ├── SIAMS_A1_COCO_Granja_mensual.csv
│   │   │       ├── SIAMS_A1_Cobertura_Granja_anual.csv
│   │   │       ├── SIAMS_A1_Granja_Analisis_Ampliado.json
│   │   │       ├── SIAMS_A1_Granja_El_Mira_Ampliado.xlsx
│   │   │       └── SIAMS_A1_SNHT_Homogeneidad_Actualizado.xlsx
│   │   ├── grace/                         # intacta
│   │   ├── hidrogeoquimica/               # intacta
│   │   ├── landsat/                       # intacta
│   │   ├── mapbiomas/                     # intacta
│   │   └── swot/                          # intacta
│   └── raw/                               # intacta; insumos crudos si decides guardarlos
├── scripts/
│   └── a1/
│       ├── _siams_a1_base.py
│       └── siams_a1_granja_ampliada.py
└── LEEME_A1_INTEGRACION.md
```

## Instalación segura en VS Code

1. En la raíz del repositorio, guarda copia del `app.py` anterior **fuera del repositorio** o en una ubicación temporal.
2. Abre el ZIP corregido y copia sus carpetas/archivos dentro de `Siams-Leticia-Tumaco` **conservando las rutas**. Reemplaza únicamente `app.py` y añade `siams/homogeneidad_a1.py`. Nunca reemplaces la carpeta `siams` o `data` completa; Windows debe fusionar directorios, no eliminarlos.
3. Comprueba que exista `data/processed/a1/tumaco/SIAMS_A1_COCO_Granja_mensual.csv`. Los ocho Excel actuales siguen en `data/processed/clima` sin cambios.
4. Ejecuta:

```powershell
.\.venv\Scripts\Activate.ps1
python -m py_compile app.py siams\homogeneidad_a1.py
streamlit run app.py
```

5. Dentro de SIAMS: **Tumaco → Clima y datos → Homogeneidad (A1)**.

## Comprobaciones antes de subir al repositorio

```powershell
python -m pytest -q
git status
git diff -- app.py
```

Una vez confirmado localmente:

```powershell
git add app.py siams/homogeneidad_a1.py data/processed/a1/tumaco scripts/a1 LEEME_A1_INTEGRACION.md
git commit -m "Integrar A1 de homogeneidad en SIAMS respetando data/processed"
git push origin mejoras-revision-siams
```

## Qué hace y qué no hace

- `app.py` solo agrega importación, entrada de menú y llamada de la pantalla A1 (el resto permanece intacto).
- El panel muestra SNHT absoluto/relativo y compara precipitación mensual COCO EL–Granja El Mira.
- Los SNHT mostrados fueron **precalculados**; mover el selector de años solo actualiza gráficos.
- Se mantienen las limitaciones metodológicas: la significancia estadística no identifica la causa física ni certifica homogeneidad definitiva.
- Los scripts reproducibles requieren los ZIP de origen de DHIME y `excel.zip`, además de NumPy y SciPy. No se ejecutan automáticamente dentro de SIAMS.
- Si copiaste el ZIP anterior que creó `datos/` o `analisis/`, puedes eliminar esas rutas **solamente después de verificar** que no contienen otros datos tuyos y que los resultados A1 aparecen en `data/processed/a1/tumaco`.
