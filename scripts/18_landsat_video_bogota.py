#!/usr/bin/env python
"""Genera un MP4 cronológico de compuestos anuales aprobados de Bogotá.
No interpola años faltantes; usa las imágenes y rótulos originales del script 08.
"""
from pathlib import Path
import json
import argparse
import subprocess
import sys
import tempfile

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from siams.landsat_calidad import cargar_criterios, normalizar
from siams.landsat_secuencia import fotogramas_aprobados


def generar(carpeta: Path, umbral: float, sede="Bogotá", meses=(12, 1, 2)):
    from PIL import Image, ImageOps
    import imageio_ffmpeg
    registros = fotogramas_aprobados(carpeta, umbral, sede, meses)
    if len(registros) < 2:
        raise SystemExit('Se necesitan al menos dos temporadas aprobadas para generar el MP4.')
    slug = normalizar(sede).replace(' ', '_')
    video = carpeta / f'landsat_{slug}_temporadas.mp4'
    manifiesto = carpeta / f'landsat_{slug}_temporadas.json'
    with tempfile.TemporaryDirectory(dir=carpeta) as temporal:
        tmp = Path(temporal)
        for i, r in enumerate(registros):
            with Image.open(carpeta / r['imagen']) as img:
                # Mantiene todo el pie de fuente y período, sin recortar.
                img = ImageOps.pad(img.convert('RGB'), (1000, 1150), color='white')
                img.save(tmp / f'{i:05d}.png')
        salida = tmp / 'secuencia.mp4'
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error',
                        '-y', '-framerate', '1/3', '-i', str(tmp / '%05d.png'),
                        '-r', '24', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                        '-movflags', '+faststart', str(salida)], check=True)
        salida.replace(video)
    manifiesto.write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Temporadas incluidas:', ', '.join(str(r['temporada']) for r in registros))
    print(video)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--sede', choices=['Bogotá', 'Chingaza'], default='Bogotá')
    a = p.parse_args()
    c = cargar_criterios()
    carpeta = 'Bogota' if a.sede == 'Bogotá' else 'Chingaza'
    generar(RAIZ / 'Landsat' / carpeta / 'compuestos',
            c['compuestos']['sin_dato_max_pct'], a.sede, c['ventana_estacional'][normalizar(a.sede)])
