"""Comprobación básica independiente de Streamlit para la entrega SIAMS modular."""
from pathlib import Path
import ast
import sys

BASE = Path(__file__).resolve().parent
MODULOS = [
    "estilos", "catalogo", "utilidades", "grace", "tendencias",
    "componentes", "mapas_datos", "swot", "clima", "cartografia",
    "mapbiomas", "landsat", "sentinel", "estados", "inicio",
]

faltantes = []
archivos = [BASE / "app.py", BASE / "siams" / "__init__.py"]
archivos += [BASE / "siams" / f"{nombre}.py" for nombre in MODULOS]
for archivo in archivos:
    if not archivo.is_file():
        faltantes.append(str(archivo.relative_to(BASE)))
        print(f"FALTA: {archivo.relative_to(BASE)}")
        continue
    try:
        ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
        print(f"OK: {archivo.relative_to(BASE)}")
    except SyntaxError as exc:
        faltantes.append(str(archivo.relative_to(BASE)))
        print(f"ERROR DE SINTAXIS: {archivo.relative_to(BASE)}: {exc}")

if faltantes:
    print("\nCorrige los archivos faltantes o con errores antes de iniciar SIAMS.")
    sys.exit(1)

print("\nMódulos y sintaxis correctos. Falta comprobar el funcionamiento con Streamlit y tus datos reales.")
