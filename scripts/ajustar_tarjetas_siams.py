"""SIAMS | Ajuste seguro de tarjetas de sede y créditos fotográficos.

Se aplica SOBRE los archivos actuales, sin sustituir módulos por versiones antiguas.
Uso: python scripts/ajustar_tarjetas_siams.py [--verificar]
"""
from __future__ import annotations

import argparse
import ast
import csv
import shutil
from datetime import datetime
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
INICIO = RAIZ / "siams" / "inicio.py"
ESTILOS = RAIZ / "siams" / "estilos.py"
CREDITOS = RAIZ / "docs" / "CREDITOS_FOTOS_SEDES.csv"

FUNCION_CREDITOS = '''\n\ndef credito_foto_sede(nombre_sede: str, ruta_foto: Path) -> tuple[str, str]:
    """Crédito visible y texto ampliado a partir del inventario de fotos.

    No confundir la copia recibida por SIAMS con el autor o fuente original.
    """
    import csv

    inventario = Path(__file__).resolve().parents[1] / "docs" / "CREDITOS_FOTOS_SEDES.csv"
    sin_confirmar = {"", "por confirmar", "por verificar", "pendiente", "desconocido", "—", "-"}
    etiqueta = "Foto: crédito pendiente"
    detalle = (f"{nombre_sede}: autor y fuente original sin verificar. "
               "Consultar docs/CREDITOS_FOTOS_SEDES.csv antes de atribuir autoría.")
    if not inventario.is_file():
        return etiqueta, detalle

    try:
        with inventario.open("r", encoding="utf-8-sig", newline="") as archivo:
            for fila in csv.DictReader(archivo):
                if (normalizar_etiqueta(str(fila.get("Sede", ""))) != normalizar_etiqueta(nombre_sede)
                        or str(fila.get("Archivo", "")).casefold() != ruta_foto.name.casefold()):
                    continue
                autor = str(fila.get("Autor/a de la foto", "")).strip()
                fuente = str(fila.get("Fuente original", "")).strip()
                enlace = str(fila.get("Enlace fuente original", "")).strip()
                autoria_confirmada = autor.casefold() not in sin_confirmar
                fuente_confirmada = fuente.casefold() not in sin_confirmar
                enlace_confirmado = enlace.casefold() not in sin_confirmar
                if autoria_confirmada:
                    etiqueta = f"Foto: {autor}"
                elif fuente_confirmada:
                    etiqueta = f"Foto: {fuente}"
                elif enlace_confirmado:
                    etiqueta = "Foto: fuente registrada"
                detalle = " · ".join([
                    f"Sede: {nombre_sede}",
                    f"Autor/a: {autor if autoria_confirmada else 'sin verificar'}",
                    f"Fuente original: {fuente if fuente_confirmada else 'sin verificar'}",
                    *([f"Enlace: {enlace}"] if enlace_confirmado else []),
                ])
                return etiqueta, detalle
    except (OSError, UnicodeError, csv.Error) as error:
        import logging
        logging.getLogger(__name__).warning("No se pudieron leer créditos fotográficos: %s", error)
    return etiqueta, detalle
'''


START = '''            if ruta_foto is not None:
                imagen = foto_sede_data_uri(str(ruta_foto), ruta_foto.stat().st_mtime_ns)
                visual = (
                    '<div class="siams-sede-media">'
                    f'<img src="{imagen}" alt="Fotografía de {escape(nombre)}" loading="lazy">'
                    f'<span class="siams-sede-photo-label">{escape(nombre)}</span>'
                    '</div>'
                )'''
REPLACEMENT = '''            if ruta_foto is not None:
                imagen = foto_sede_data_uri(str(ruta_foto), ruta_foto.stat().st_mtime_ns)
                credito, titulo_credito = credito_foto_sede(nombre, ruta_foto)
                visual = (
                    '<div class="siams-sede-media">'
                    f'<img src="{imagen}" alt="Fotografía de {escape(nombre)}" loading="lazy">'
                    f'<span class="siams-sede-photo-label">{escape(nombre)}</span>'
                    f'<span class="siams-sede-photo-credit" title="{escape(titulo_credito, quote=True)}">'
                    f'{escape(credito)}</span>'
                    '</div>'
                )'''

CSS_CREDITOS = '''\n        /* SIAMS_A6_FOTOS_PORTADA_CREDITOS | crédito fotográfico junto a cada imagen */
        .siams-sede-photo-credit {
            position: absolute;
            top: 7px;
            right: 7px;
            z-index: 2;
            max-width: calc(100% - 14px);
            padding: .19rem .42rem;
            border-radius: 7px;
            background: rgba(8, 28, 25, .80);
            color: #fff !important;
            font-size: .65rem;
            font-weight: 650;
            line-height: 1.35;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            cursor: help;
        }
'''


def reemplazar_unico(texto: str, viejo: str, nuevo: str, etiqueta: str) -> str:
    cantidad = texto.count(viejo)
    if cantidad != 1:
        raise ValueError(f"{etiqueta}: se esperaba 1 coincidencia, encontradas {cantidad}. No se modificó ningún archivo.")
    return texto.replace(viejo, nuevo, 1)


def verificar_contenido(inicio: str, estilos: str) -> None:
    ast.parse(inicio, filename=str(INICIO))
    ast.parse(estilos, filename=str(ESTILOS))
    for condicion, descripcion in [
        ("def credito_foto_sede(" in inicio, "función de créditos"),
        ('credito, titulo_credito = credito_foto_sede(nombre, ruta_foto)' in inicio, "llamada en tarjeta"),
        ('siams-sede-photo-credit' in inicio and '.siams-sede-photo-credit {' in estilos, "crédito visible con estilo"),
        ('-webkit-line-clamp:3;' in estilos, "texto de 3 líneas"),
    ]:
        if not condicion:
            raise ValueError(f"Falta comprobar {descripcion}")


def ampliar_inventario_creditos(respaldo: Path, sello: str) -> bool:
    """Añade columnas editables a la tabla existente sin borrar créditos anteriores."""
    if not CREDITOS.is_file():
        return False
    with CREDITOS.open("r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        columnas = list(lector.fieldnames or [])
        filas = list(lector)
    if not columnas:
        raise ValueError("La tabla de créditos está vacía o carece de cabeceras.")
    nuevas = ["Fuente original", "Enlace fuente original"]
    adicionales = [col for col in nuevas if col not in columnas]
    if not adicionales:
        return False
    shutil.copy2(CREDITOS, respaldo / f"SIAMS_creditos_antes_tarjetas_{sello}.csv")
    with CREDITOS.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas + adicionales)
        escritor.writeheader()
        escritor.writerows(filas)
    return True


def aplicar() -> None:
    if not (INICIO.is_file() and ESTILOS.is_file()):
        raise SystemExit("No se encontró siams/inicio.py o siams/estilos.py. Ejecuta dentro de SIAMS.")

    t_inicio = INICIO.read_text(encoding="utf-8-sig")
    t_estilos = ESTILOS.read_text(encoding="utf-8-sig")
    if 'siams-sede-photo-credit' in t_inicio:
        verificar_contenido(t_inicio, t_estilos)
        print("YA INSTALADO: los ajustes están presentes; no se duplicó nada.")
        return

    t_inicio_nuevo = reemplazar_unico(t_inicio, START, REPLACEMENT, "Tarjeta de imagen")
    ancla = 'def foto_sede_data_uri('
    if ancla not in t_inicio_nuevo:
        raise ValueError("No se encontró la función de imagen. No se realizaron cambios.")
    # Inserta ANTES del decorador para no mover el cache del generador de miniaturas.
    decorador = '@st.cache_data(show_spinner=False, max_entries=20)\ndef foto_sede_data_uri('
    t_inicio_nuevo = reemplazar_unico(
        t_inicio_nuevo, decorador, FUNCION_CREDITOS + '\n' + decorador,
        "Inserción del lector de crédito",
    )
    t_inicio_nuevo = reemplazar_unico(
        t_inicio_nuevo,
        '''f'<p class="siams-sede-description">{escape(datos["descripcion"])}</p>' '''.rstrip(),
        '''f'<p class="siams-sede-description" title="{escape(datos["descripcion"], quote=True)}">{escape(datos["descripcion"])}</p>' '''.rstrip(),
        "Descripción completa al pasar el cursor",
    )

    t_estilos_nuevo = reemplazar_unico(
        t_estilos,
        'height: 385px; min-width: 0; display: flex;',
        'height: 375px; min-width: 0; display: flex;',
        "Altura principal tarjetas",
    )
    t_estilos_nuevo = reemplazar_unico(
        t_estilos_nuevo,
        'margin:0 0 .50rem; min-height:2.85em;',
        'margin:0 0 .35rem; min-height:4.26em;',
        "Espacio descriptivo",
    )
    t_estilos_nuevo = reemplazar_unico(
        t_estilos_nuevo, '-webkit-line-clamp:2; overflow:hidden;',
        '-webkit-line-clamp:3; overflow:hidden;', "Límite de líneas",
    )
    t_estilos_nuevo = reemplazar_unico(
        t_estilos_nuevo,
        '        .siams-sede-body {',
        CSS_CREDITOS + '        .siams-sede-body {',
        "CSS para crédito",
    )
    # No sobrescribas ninguna línea fuera de los estilos exclusivos de portada.
    verificar_contenido(t_inicio_nuevo, t_estilos_nuevo)

    respaldo = Path.home() / 'Documents'
    if not respaldo.is_dir():
        respaldo = Path.home()
    sello = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(INICIO, respaldo / f'SIAMS_inicio_antes_tarjetas_{sello}.py')
    shutil.copy2(ESTILOS, respaldo / f'SIAMS_estilos_antes_tarjetas_{sello}.py')
    INICIO.write_text(t_inicio_nuevo, encoding='utf-8')
    ESTILOS.write_text(t_estilos_nuevo, encoding='utf-8')
    if ampliar_inventario_creditos(respaldo, sello):
        print('OK: se añadieron Fuente original y Enlace fuente original al CSV, preservando los créditos existentes.')
    print('OK: tarjetas corregidas, 3 líneas visibles, crédito dinámico en fotos.')
    print(f'Copias de seguridad en {respaldo}')


if __name__ == '__main__':
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--verificar', action='store_true')
    opt = args.parse_args()
    if opt.verificar:
        verificar_contenido(INICIO.read_text(encoding='utf-8-sig'), ESTILOS.read_text(encoding='utf-8-sig'))
        print('OK: modificaciones presentes y sintaxis válida.')
    else:
        aplicar()
