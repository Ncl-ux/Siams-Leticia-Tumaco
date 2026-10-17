# M2 — Versiones reproducibles de dependencias (SIAMS)

**Objetivo:** sustituir las dependencias sin versión o con intervalos por versiones exactas, tomadas del entorno virtual **que ya ejecuta SIAMS con 76 pruebas aprobadas**. No modificar los cálculos ni instalar versiones nuevas sin revisar.

## Instalación segura (Windows / PowerShell)

1. Extraer `SIAMS_M2_PREPARAR.zip` **sobre la carpeta principal de SIAMS**, conservando sus rutas `scripts/`, `tests/` y `docs/`. Este ZIP todavía **no reemplaza** los archivos `requirements*.txt`.
2. Desde `C:\Users\NITRO\Documents\Siams-Leticia-Tumaco`, ejecutar:

   ```powershell
   .\.venv\Scripts\python.exe -m pip check
   .\.venv\Scripts\python.exe scripts\m2_fijar_dependencias.py
   .\.venv\Scripts\python.exe -m pytest -q
   .\.venv\Scripts\python.exe scripts\m2_fijar_dependencias.py --verificar
   git diff -- requirements.txt requirements_hidrogeoquimica.txt requirements-dev.txt
   ```

3. **Antes de confirmar M2**, comprobar que CI de GitHub Actions pasa y la aplicación abre con `streamlit run app.py`. El equipo debe validar de nuevo el visor PDF y los cálculos climáticos/GRACE cuando actualice las dependencias.
4. Solo si pasa todo, crear el commit y hacer push:

   ```powershell
   git add requirements.txt requirements_hidrogeoquimica.txt requirements-dev.txt requirements-lock.txt scripts/m2_fijar_dependencias.py tests/test_m2_dependencias.py docs/M2_DEPENDENCIAS.md
   git diff --cached --check
   git commit -m "M2: fijar dependencias y documentar entorno reproducible"
   git push origin mejoras-revision-siams
   ```

## Archivos generados

- `requirements.txt`: versiones **directas** exactas para la aplicación/Streamlit Cloud, conservando el extra `streamlit[pdf]`, eliminando la declaración duplicada de Streamlit y declarando `Pillow` y `pypdfium2` usados por el código.
- `requirements_hidrogeoquimica.txt`: versiones exactas para el subsistema de datos fisicoquímicos.
- `requirements-dev.txt`: versión exacta de `pytest` (y las demás dependencias de desarrollo declaradas, si existen).
- `requirements-lock.txt`: cierre recursivo de dependencias directas y transitivas **del entorno local** que pasó las pruebas. No se debe asumir que este lock generado en Windows funciona sin cambios en Linux/Streamlit Cloud; para despliegue multiplataforma se mantiene `requirements.txt`.

**Limitaciones:** fijar números de versión no garantiza identidad binaria (para ello se necesitarían hashes y wheels por plataforma). El lock documenta la resolución del entorno; las dependencias directas sí quedan fijas para las instalaciones normales. Las pruebas unitarias no reemplazan la validación de la interfaz.

**En caso de error:** el script se detiene si falta algún paquete o `pip check` detecta incompatibilidades. No repara ni instala nada automáticamente. Muestra el error concreto para poder corregirlo antes de sobrescribir los `requirements`.

**Nota:** se usa como referencia el Python realmente ejecutado en el `.venv`; para CI se recomienda mantener Python **3.12**, coherente con la configuración existente de GitHub Actions.
