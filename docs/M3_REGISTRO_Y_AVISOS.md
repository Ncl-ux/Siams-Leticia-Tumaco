# M3 — Registro de excepciones y avisos visibles

## Alcance de esta entrega

Se revisaron **los cinco archivos suministrados en `SIAMS_M3_CODIGO_ACTUAL.zip`**. Los 14 manejadores `except` que contenían `pass` ahora registran el error e informan la degradación de la funcionalidad afectada. No se afirma que el resto del repositorio esté libre de `except: pass` hasta auditarlo.

- `app.py` (4): fallos en comparación NASA POWER/IDEAM; se advierte qué sede/fuente no pudo procesarse y se corrige la atribución de fuentes **solo en la ruta de fallo** para no atribuir datos NASA ausentes.
- `siams/clima.py` (3): fallos en la obtención de series históricas NASA POWER, IDEAM y GRACE; se registra traza y se avisa que la fuente no está disponible.
- `siams/inicio.py` (4): fallos en hallazgos, inventario y lectura de años IDEAM/NASA y MapBiomas; se muestra una advertencia solo al capturar un error.
- `siams/hidrogeoquimica_datos.py` (2): carbonatos/balance iónico inválidos mantienen resultados `NaN` y agregan la causa en la columna `banderas`; los errores se registran en la consola. No se inventan valores.
- `siams/cartografia.py` (1): fallo del visor PDF nativo; registra la excepción y sigue intentando las alternativas ya implementadas. Si logra mostrar el mapa, presenta una nota discreta.

Se usa `logging.getLogger(__name__)`; no hace falta introducir una dependencia nueva. Los detalles técnicos y las trazas se dejan en los registros del servidor; los mensajes visibles evitan mostrar rutas internas completas.

## Validación

En la raíz de SIAMS:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app.py siams
```

Verificar manualmente las secciones **Comparar territorios**, **Inicio**, **Tendencias** y **Mapas QGIS**. En las condiciones normales no deben aparecer advertencias nuevas. Ante fallos reproducibles de lectura, debe mostrarse el aviso correspondiente y registrarse el motivo en la terminal.

**No se tocaron** los datos científicos, los scripts de A5, el historial Git de M1 ni los algoritmos de cálculo de GRACE/IRCA. La ejecución de la batería completa de SIAMS debe realizarse sobre el repositorio del usuario, donde están los demás módulos, datos y pruebas.
