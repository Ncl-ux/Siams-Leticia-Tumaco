"""Inventario local sin red, sin cambiar ningún dato. Imprime las siete sedes."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from siams.precipitacion_satelital_datos import SEDES,cargar,inventario

if __name__=='__main__':
    for nombre,sede in SEDES.items():
        t,avisos=cargar(sede)
        print(f'\n=== {nombre} ===')
        if not t.empty: print(inventario(t).to_string(index=False))
        for fuente,detalle in avisos.items():print(f'PENDIENTE {fuente}: {detalle}')
