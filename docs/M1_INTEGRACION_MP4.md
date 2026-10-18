# SIAMS · Integración MP4 (M1, fase de animaciones)

Se incorporan **23 videos H.264/yuv420p** provenientes de `COMPRIMIR_Optimizados.zip`:
- 5 MP4 en `Animaciones_SWOT/`, de los ríos Amazonas, Arauca, Medellín, Mira y Rosario.
- 18 MP4 en `Coberturas_MapBiomas/{sede}/`, correspondientes a nivel 1, nivel 2 y natural/antrópico de seis sedes.

Las funciones existentes de `siams/swot.py` y `siams/mapbiomas.py` priorizan MP4 y conservan GIF como alternativa. `app.py`, GRACE, IDEAM, NASA POWER, M2, M3 y A6/A8 no se modifican por esta instalación.

## Instalación

1. Extraer el ZIP de integración directamente en la raíz del proyecto SIAMS (sin crear una carpeta contenedora adicional).
2. Ejecutar `python scripts/instalar_mp4_siams.py` usando el Python del `.venv`.
3. Ejecutar `python scripts/instalar_mp4_siams.py --verificar`.
4. Ejecutar `python -m pytest -q` y comprobar visualmente las pestañas SWOT y MapBiomas antes de borrar los GIF.

## Precauciones

No se eliminan los GIF ni se sobrescriben los PDF en la instalación. Tras validar los MP4 en la página, se pueden retirar del HEAD los **23 GIF equivalentes** y conservar las copias del respaldo Git pre-M1. Los GIF de Landsat y Sentinel siguen siendo necesarios porque no hay MP4 de esas secciones en el ZIP recibido.

Los 20 PDF recibidos solo difieren en unos cientos de bytes frente a los mapas del paquete anterior, por lo que no suponen una reducción sustancial y no se instalan en esta fase. Las modificaciones de repositorio de trabajo no eliminan automáticamente los archivos grandes de **historial Git**: M1 requiere reescritura y validación separadas, sobre la copia experimental y el respaldo ya creado.
