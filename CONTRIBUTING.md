# Cómo contribuir a SIAMS

## Flujo de trabajo

1. Cada integrante trabaja con **su propia cuenta** de GitHub.
2. Nada se edita directo en `main`: creen una rama (`git switch -c corrige-unidades-radiacion`).
3. Abran un *pull request*; un compañero lo revisa y las pruebas de GitHub Actions deben pasar.
4. Mensajes de commit que digan **qué y por qué**: «Corrige unidad de radiación a MJ/m²/día», no «cambios» ni «d».
   Si el trabajo es conjunto, agreguen al final `Co-authored-by: Nombre <correo>`.
5. Marquen versiones con etiquetas: `git tag v0.38.1 && git push --tags`.
6. No editen `app.py` copiando y pegando el archivo completo: usen Git, que para eso guarda el historial.

## Antes de subir

```bash
python -m pytest            # todas las pruebas en verde
streamlit run app.py        # revisar al menos las páginas que tocaron
```

- Nada de `.venv/`, contraseñas, tokens ni archivos `.env` (ya están en `.gitignore`).
- Nada de datos personales ni ubicaciones de viviendas o pozos familiares.
- Cada archivo de terceros con su crédito en `CREDITOS.md`; si la licencia no lo permite, solo el enlace.
- Quiten el EXIF de las fotos: `python -c "from PIL import Image; im=Image.open('f.jpg'); im.save('f.jpg', quality=85)"`
  o `exiftool -all= f.jpg`.
- Imágenes de más de 2 MB, GIF y PDF pesados: ver `scripts/05_optimizar_medios.sh`.

## Convención de nombres de archivos (revisión B1)

- Minúsculas, sin tildes, sin espacios, sin «•», sin «(3)» ni «Copia de». Separar con guion bajo.
- Fecha o periodo en formato ISO y versión al final: `nasa_power_leticia_2000-2026_v1.xlsx`,
  `swot_rio_amazonas_leticia_ancho_2023-2026_v1.mp4`.
- Las versiones las maneja Git, no el nombre del archivo.
- Columnas con la unidad real: `precipitacion_mm_mes`, `radiacion_solar_MJ_m2_dia`.
- Datos crudos en `data/raw/`, productos en `data/processed/`, cada uno descrito en `data/README.md`.

> Los archivos actuales todavía no siguen esta convención porque `app.py` los busca por su nombre actual.
> El cambio debe hacerse junto con un registro explícito de archivos (`territorios.yaml`) en un pull request aparte.
