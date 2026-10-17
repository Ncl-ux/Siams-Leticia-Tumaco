"""Verifica SHA-256, rutas y disponibilidad de los archivos migrados de A5."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
import hashlib

ROOT=Path(__file__).resolve().parents[1]

def verificar(raiz=ROOT):
    raiz=Path(raiz)
    catalogo=raiz/'docs/migracion_a5.csv'
    fallos=[];correctos=0
    with catalogo.open(encoding='utf-8-sig',newline='') as f:
        for fila in csv.DictReader(f):
            ruta=raiz/fila['ruta_actual']
            if not ruta.is_file():
                fallos.append(f'FALTA: {ruta.relative_to(raiz)}');continue
            suma=hashlib.sha256(ruta.read_bytes()).hexdigest()
            if suma!=fila['sha256_actual']:
                fallos.append(f'ALTERADO: {ruta.relative_to(raiz)}');continue
            correctos+=1
    return correctos,fallos

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT)
    a=p.parse_args();n,issues=verificar(a.root)
    print(f'Archivos migrados íntegros: {n}; incidencias: {len(issues)}')
    for i in issues:print(i)
    raise SystemExit(bool(issues))
