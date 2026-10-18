r"""Valida fotos existentes y crea, si falta, el registro de autores en docs/.

Fotos_Sedes/ es la única carpeta para fotografías; no crea insumos ni plantillas.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
FOTOS_SEDES = RAIZ / "Fotos_Sedes"
AUTORES = RAIZ / "docs" / "AUTORES_SIAMS.csv"
FOTOS = ("Arauca.jpg", "Bogota.jpg", "La Paz.jpg", "Leticia.jpg", "Medellin.jpg", "San Andres.jpg", "Tumaco.jpeg")
HUELLAS = {'Tumaco.jpeg': 'd50e2563785170ead24249e6ddb06205f76cadcc5eceab5500910822936bc39f', 'San Andres.jpg': 'ebaa8e19331f3e59d0e9c1f697fae73325665b4c0bd1f429cf721ee682386d41', 'Leticia.jpg': '1d64bebe7bf03270bc24c4a76c83da52b94ad32b1dd383de55d24989e23456a8', 'Arauca.jpg': 'e9e937530e41ff5b468e9ef6ab0419322505c5c724abcf68660038a3fb757260', 'Bogota.jpg': '781eeb210b4fcdbb4405f4d137069b64d72f2ae97b631f63fada807bdd4e645e', 'Medellin.jpg': '4608e0f6c0e90ca179dde096d923c60d1347153869b7a1b7ff3020b271499246', 'La Paz.jpg': '18e7bdd3fcd8b2b0719d2d47001d439b22a48f17a2ca954a8a13559c9e47e80a'}

def validar(verificar=False):
    if not AUTORES.is_file():
        if verificar:
            raise FileNotFoundError(f"Falta {AUTORES}; ejecuta sin --verificar una vez")
        if not AUTORES.parent.is_dir():
            raise FileNotFoundError("Falta la carpeta existente docs/; comprueba la raíz de SIAMS")
        AUTORES.write_text("Nombre,Rol,Afiliación\n", encoding="utf-8-sig")
        print("Creado docs/AUTORES_SIAMS.csv (solo encabezados; agrega autores autorizados)")
    else:
        print("Conservado docs/AUTORES_SIAMS.csv sin modificar autores existentes")

    faltantes=[]
    distintos=[]
    for nombre in FOTOS:
        foto=FOTOS_SEDES/nombre
        if not foto.is_file():
            faltantes.append(nombre)
        elif sha256(foto.read_bytes()).hexdigest()!=HUELLAS[nombre]:
            distintos.append(nombre)
    if faltantes:
        raise FileNotFoundError("Faltan imágenes en Fotos_Sedes/: " + ", ".join(faltantes))
    if distintos:
        raise RuntimeError("Estas imágenes son distintas de las fotos enviadas: " + ", ".join(distintos) + ". Revisa la copia antes de reemplazarla.")
    print("7 fotografías verificadas en Fotos_Sedes/. No se crean carpetas auxiliares.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verificar", action="store_true")
    validar(parser.parse_args().verificar)
