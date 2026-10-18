"""Integra MP4 H.264 optimizados en las carpetas existentes de SIAMS.

Ejecutar desde la raiz del repositorio:
    python scripts/instalar_mp4_siams.py
    python scripts/instalar_mp4_siams.py --verificar

No borra GIF/PDF, no modifica app.py, no crea carpetas dentro de SIAMS.
"""
from __future__ import annotations

import argparse
import ast
import shutil
from pathlib import Path

MARCA = "SIAMS_M1_MP4_PRECEDENCIA"
RAIZ = Path(__file__).resolve().parents[1]
VIDEOS_SWOT = (
    "swot_arauca_arauca_ancho.mp4",
    "swot_leticia_amazonas_ancho.mp4",
    "swot_medellin_medellin_ancho.mp4",
    "swot_tumaco_mira_ancho.mp4",
    "swot_tumaco_rosario_ancho.mp4",
)
TERRITORIOS = {
    "Arauca": "arauca",
    "La_Paz": "la_paz",
    "Leticia": "leticia",
    "Medellín": "medellin",
    "San_Andres": "san_andres",
    "Tumaco": "tumaco",
}
VIDEOS_MAPBIOMAS = tuple(
    f"Coberturas_MapBiomas/{carpeta}/mapbiomas_{prefijo}_{tipo}.mp4"
    for carpeta, prefijo in TERRITORIOS.items()
    for tipo in ("ant_nat", "nivel_1", "nivel_2")
)
VIDEOS = tuple(f"Animaciones_SWOT/{nombre}" for nombre in VIDEOS_SWOT) + VIDEOS_MAPBIOMAS


def _funcion(fuente: str, nombre: str) -> tuple[str, int, int]:
    arbol = ast.parse(fuente)
    objetivo = next((n for n in arbol.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nombre), None)
    if objetivo is None:
        raise ValueError(f"Falta la funcion esperada {nombre} en el modulo; no se modifica el archivo.")
    lineas = fuente.splitlines(keepends=True)
    return "".join(lineas[objetivo.lineno - 1:objetivo.end_lineno]), objetivo.lineno - 1, objetivo.end_lineno


def _reemplazar_funcion(fuente: str, nombre: str, convertir) -> str:
    cuerpo, inicio, final = _funcion(fuente, nombre)
    nuevo = convertir(cuerpo)
    if nuevo == cuerpo:
        return fuente
    lineas = fuente.splitlines(keepends=True)
    return "".join(lineas[:inicio]) + nuevo + "".join(lineas[final:])


def actualizar_swot(fuente: str) -> str:
    def busqueda(cuerpo):
        if MARCA in cuerpo:
            return cuerpo
        objetivo = "    return buscar_archivo_exacto(CARPETA_GIFS, nombre_archivo,"
        if cuerpo.count(objetivo) != 1:
            raise ValueError("No se reconoce la busqueda de SWOT. No se modifico.")
        insercion = (
            f"    # {MARCA}: MP4 primero; GIF de respaldo.\n"
            "    video = buscar_archivo_exacto(CARPETA_GIFS, Path(nombre_archivo).with_suffix('.mp4').name)\n"
            "    if video is not None:\n"
            "        return video\n"
        )
        return cuerpo.replace(objetivo, insercion + objetivo, 1)

    fuente = _reemplazar_funcion(fuente, "buscar_gif_swot", busqueda)

    def visualizacion(cuerpo):
        if MARCA in cuerpo:
            return cuerpo
        antes = (
            "            st.image(\n"
            "                str(ruta),\n"
            "                caption=f\"{item['descripcion']} · Fuente: HydroWeb / SWOT\",\n"
            "                use_container_width=True,\n"
            "            )\n"
        )
        if cuerpo.count(antes) != 1:
            raise ValueError("No se reconoce el visor SWOT; no se modifico.")
        despues = (
            f"            # {MARCA}: reproducir video en bucle, conservando imagen alternativa.\n"
            "            if ruta.suffix.casefold() == '.mp4':\n"
            "                st.video(str(ruta), autoplay=True, loop=True, muted=True)\n"
            "                st.caption(f\"{item['descripcion']} · Fuente: HydroWeb / SWOT\")\n"
            "            else:\n"
            "                st.image(\n"
            "                    str(ruta),\n"
            "                    caption=f\"{item['descripcion']} · Fuente: HydroWeb / SWOT\",\n"
            "                    use_container_width=True,\n"
            "                )\n"
        )
        return cuerpo.replace(antes, despues, 1)

    return _reemplazar_funcion(fuente, "mostrar_gifs_swot", visualizacion)


def actualizar_mapbiomas(fuente: str) -> str:
    def busqueda(cuerpo):
        if MARCA in cuerpo:
            return cuerpo
        objetivo = "    return buscar_archivo_exacto(carpeta, nombre_archivo,"
        if cuerpo.count(objetivo) != 1:
            raise ValueError("No se reconoce la busqueda MapBiomas; no se modifico.")
        insercion = (
            f"    # {MARCA}: MP4 primero; GIF alternativo para versiones previas.\n"
            "    if nombre_archivo:\n"
            "        video = buscar_archivo_exacto(carpeta, Path(nombre_archivo).with_suffix('.mp4').name)\n"
            "        if video is not None:\n"
            "            return video\n"
        )
        return cuerpo.replace(objetivo, insercion + objetivo, 1)

    fuente = _reemplazar_funcion(fuente, "buscar_gif_mapbiomas", busqueda)

    def visualizacion(cuerpo):
        if MARCA in cuerpo:
            return cuerpo
        objetivo = '    gif_b64 = base64.b64encode(ruta.read_bytes()).decode("ascii")'
        if cuerpo.count(objetivo) != 1:
            raise ValueError("No se reconoce el visor MapBiomas; no se modifico.")
        insercion = (
            f"    # {MARCA}: usa el MP4 en lugar de cargar el GIF en base64.\n"
            "    if ruta.suffix.casefold() == '.mp4':\n"
            "        st.video(str(ruta), autoplay=True, loop=True, muted=True)\n"
            "        st.caption(descripcion)\n"
            "        return\n"
        )
        return cuerpo.replace(objetivo, insercion + objetivo, 1)

    return _reemplazar_funcion(fuente, "_mostrar_gif_mapbiomas", visualizacion)


def verificar(raiz: Path) -> list[str]:
    errores = []
    for ruta in VIDEOS:
        archivo = raiz / ruta
        if not archivo.is_file():
            errores.append(f"Falta video: {ruta}")
        elif archivo.stat().st_size < 1024:
            errores.append(f"Archivo MP4 vacio: {ruta}")
    for nombre, funciones in {
        'siams/swot.py': ('buscar_gif_swot', 'mostrar_gifs_swot'),
        'siams/mapbiomas.py': ('buscar_gif_mapbiomas', '_mostrar_gif_mapbiomas'),
    }.items():
        archivo = raiz / nombre
        if not archivo.is_file():
            errores.append(f"Falta modulo: {nombre}")
            continue
        fuente = archivo.read_text(encoding='utf-8-sig')
        try:
            ast.parse(fuente)
            for fun in funciones:
                cuerpo, _, _ = _funcion(fuente, fun)
                if MARCA not in cuerpo:
                    errores.append(f"No esta integrado MP4: {nombre}::{fun}")
        except (SyntaxError, ValueError) as error:
            errores.append(f"Error de codigo: {nombre}: {error}")
    return errores


def instalar(raiz: Path) -> None:
    # Todos los MP4 deben estar YA extraidos en la estructura que se usa en SIAMS.
    faltantes = [r for r in VIDEOS if not (raiz / r).is_file()]
    if faltantes:
        raise RuntimeError(f"Faltan {len(faltantes)} MP4. Extrae primero el ZIP completo en la raiz del proyecto. Ejemplo: {faltantes[0]}")
    modulos = {
        'siams/swot.py': actualizar_swot,
        'siams/mapbiomas.py': actualizar_mapbiomas,
    }
    # Prepara ambos resultados y valida sintaxis antes de tocar archivos.
    cambiados = {}
    for nombre, transformar in modulos.items():
        archivo = raiz / nombre
        original = archivo.read_text(encoding='utf-8-sig')
        resultado = transformar(original)
        ast.parse(resultado, filename=nombre)
        if resultado != original:
            cambiados[archivo] = (original, resultado)

    documentos = Path.home() / 'Documents'
    backup = documentos if documentos.is_dir() else Path.home()
    for archivo, (original, _) in cambiados.items():
        destino = backup / f'SIAMS_{archivo.stem}_antes_MP4.py'
        if not destino.exists():
            destino.write_text(original, encoding='utf-8')
        print(f'Respaldo del codigo: {destino}')
    for archivo, (_, resultado) in cambiados.items():
        archivo.write_text(resultado, encoding='utf-8')
        print(f'Actualizado: {archivo.relative_to(raiz)}')

    errores = verificar(raiz)
    if errores:
        raise RuntimeError('Instalacion incompleta:\n' + '\n'.join(errores))
    print(f'OK: {len(VIDEOS)} videos MP4 disponibles. SWOT y MapBiomas priorizan MP4. GIF y PDF conservados.')


def main() -> None:
    parser = argparse.ArgumentParser(description='Integrar MP4 sin sobrescribir versiones de SIAMS')
    parser.add_argument('--verificar', action='store_true', help='Comprueba los archivos y los visores sin hacer cambios')
    parser.add_argument('--raiz', type=Path, default=RAIZ, help='Carpeta del repositorio SIAMS')
    args = parser.parse_args()
    raiz = args.raiz.resolve()
    try:
        if args.verificar:
            errores = verificar(raiz)
            if errores:
                raise RuntimeError('\n'.join(errores))
            print(f'OK: {len(VIDEOS)} MP4 y dos visores integrados.')
        else:
            instalar(raiz)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(status=1, message=f'ERROR SIAMS MP4: {error}\n')


if __name__ == '__main__':
    main()
