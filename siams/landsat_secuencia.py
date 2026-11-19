"""Secuencias de compuestos anuales aprobados; no son escenas individuales."""
from pathlib import Path
import json
import hashlib
import math


def fotogramas_aprobados(carpeta: Path, max_sin_dato: float, sede="Bogotá", meses=(12, 1, 2)) -> list[dict]:
    """Solo compuestos de una temporada, con ficha e imagen local válida."""
    registros = {}
    for ficha in sorted(carpeta.glob('*_compuesto.json')):
        try:
            d = json.loads(ficha.read_text(encoding='utf-8-sig'))
            temporadas = d['temporadas']
            falta = float(d['aoi_sin_observacion_pct'])
            if (d.get('sede') != sede or d.get('publicable') is not True
                    or not math.isfinite(falta) or not 0 <= falta <= max_sin_dato
                    or len(temporadas) != 1 or type(temporadas[0]) is not int
                    or d.get('ventana_meses') != list(meses)):
                continue
            nombre = d['imagenes']['color_natural']
            if not isinstance(nombre, str) or Path(nombre).name != nombre:
                continue
            imagen = carpeta / nombre
            if not imagen.is_file() or imagen.suffix.lower() not in {'.jpg', '.jpeg', '.png'}:
                continue
            if temporadas[0] in registros:
                raise RuntimeError(f'Más de un compuesto aprobado para {temporadas[0]}; revisar fichas.')
            registros[temporadas[0]] = dict(temporada=temporadas[0], ficha=ficha.name, imagen=nombre,
                                            sha256_ficha=hashlib.sha256(ficha.read_bytes()).hexdigest(),
                                            sha256_imagen=hashlib.sha256(imagen.read_bytes()).hexdigest())
        except (ValueError, TypeError, KeyError, OSError):
            continue
    return [registros[t] for t in sorted(registros)]
