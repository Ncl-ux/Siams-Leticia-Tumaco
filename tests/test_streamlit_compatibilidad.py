"""Evita reintroducir el argumento obsoleto en la interfaz activa."""
import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_interfaz_sin_use_container_width():
    rutas = [RAIZ / 'app.py', *sorted((RAIZ / 'siams').rglob('*.py'))]
    obsoletos = []
    for ruta in rutas:
        arbol = ast.parse(ruta.read_text(encoding='utf-8-sig'))
        for n in ast.walk(arbol):
            if isinstance(n, ast.Call) and any(k.arg == 'use_container_width' for k in n.keywords):
                obsoletos.append(f'{ruta.relative_to(RAIZ)}:{n.lineno}')
    assert not obsoletos, '\n'.join(obsoletos)
