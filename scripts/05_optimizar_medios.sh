#!/usr/bin/env bash
# Comandos usados para aligerar el repositorio (revisión 3.4 y 3.5; prioridad M1/M9).
# Requiere: ghostscript, poppler-utils (pdftoppm), ffmpeg y Python con Pillow.
# Se documentan para que el semillero pueda repetirlos con archivos nuevos.
set -euo pipefail

# 1) PDF de QGIS: primero ghostscript /ebook (imágenes a 150 ppp, vectores intactos).
#    gs -q -dNOPAUSE -dBATCH -dSAFER -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 \
#       -dPDFSETTINGS=/ebook -dDetectDuplicateImages=true -sOutputFile=salida.pdf entrada.pdf
#    Los mapas 1:10.000.000 y 1:1.500.000-1:8.250.000 tienen límites municipales vectoriales
#    de todo el país (48-54 MB) y gs casi no los reduce; esos se rasterizaron a 250 ppp:
#    pdftoppm -r 250 -jpeg -jpegopt quality=88 -singlefile entrada.pdf pagina
#    python -c "from PIL import Image; Image.open('pagina.jpg').save('salida.pdf','PDF',resolution=250,quality=88)"
#    Conserven el PDF vectorial original fuera del repositorio (Zenodo / Releases / Drive).

# 2) Animaciones SWOT (GIF 1280x720, 330-805 cuadros, 10-20 MB) → MP4 H.264:
for gif in "$@"; do
  ffmpeg -loglevel error -y -i "$gif" \
    -vf "fps=12.5,scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=lanczos" \
    -c:v libx264 -crf 23 -preset slow -pix_fmt yuv420p -movflags +faststart -an \
    "${gif%.gif}.mp4"
done
#    Sentinel-2 (26 cuadros a 250 ms): igual pero con fps=4 y -crf 20.
#    MapBiomas y Landsat se dejaron en GIF: son mapas de clases con pocos colores y el GIF
#    resultó más liviano que el MP4 (y la app ralentiza los GIF Landsat con Pillow).

# 3) Quitar EXIF/XMP/GPS de fotos (y reducir a 1600 px de ancho):
#    python -c "from PIL import Image; im=Image.open('foto.jpeg').convert('RGB'); \
#      im.thumbnail((1600,1600)); im.save('foto.jpeg', quality=85, optimize=True)"
