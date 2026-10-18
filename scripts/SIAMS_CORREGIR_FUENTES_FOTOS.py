"""SIAMS | Créditos de fotografías: registrar pistas verificables sin atribuciones falsas.

Ejecutar desde la raíz del repositorio con el Python de SIAMS.
- No crea carpetas en el proyecto.
- Preserva nombres y créditos que el equipo haya confirmado.
- Oculta ÚNICAMENTE la etiqueta de crédito NO confirmado en las fotos del inicio.
- Añade fuentes contextuales a las observaciones del CSV, NUNCA como autor o licencia.
- Es idempotente; si un código inesperado aparece, falla sin tocar archivos.
"""
from __future__ import annotations

import ast
import csv
import io
import shutil
from datetime import datetime
from pathlib import Path

RAIZ = Path.cwd()
INICIO = RAIZ / 'siams' / 'inicio.py'
CREDITOS = RAIZ / 'docs' / 'CREDITOS_FOTOS_SEDES.csv'

BASE = ('Sede','Archivo','Procedencia de la copia','Autor/a de la foto','Permiso de publicación','Observaciones')
EXTRAS = ('Fuente original','Enlace fuente original')

# Referencias de CONTEXTO o archivos visualmente comparables.
# No demuestran que el JPEG local se extrajera de esas publicaciones.
REFERENCIAS = {
    'Bogotá': (
        'Candidato a contrastar visualmente: Wikimedia Commons, "Plaza Che - UN Bogotá.jpg" (Chilangoco; CC BY-SA 2.5); NO se ha confirmado que sea el mismo archivo. '
        'https://commons.wikimedia.org/wiki/File:Plaza_Che_-_UN_Bogot%C3%A1.jpg'
    ),
    'Medellín': (
        'Candidato a contrastar visualmente: Wikimedia Commons, "Un sede medellin aerea - Bloque 41.jpg" (Medios Digitales; CC BY-SA 4.0); NO se ha confirmado identidad de imagen. '
        'https://commons.wikimedia.org/wiki/File:Un_sede_medellin_aerea_-_Bloque_41.jpg'
    ),
    'Tumaco': (
        'Contexto comprobado: la exposición "Presencia negra en Bogotá" estuvo en Tumaco en 2014; aparece anunciada en la foto. '
        'Eso NO acredita el autor de esta imagen ni confirma su localización exacta como sede universitaria. '
        'https://imaginacionmuseografica.blogspot.com/2019/02/presencia-negra-en-tumaco.html'
    ),
}

MARCA = 'SIAMS_FOTOS_CREDITOS_VERIFICADOS_V2'


def preparar_inicio(contenido: str) -> tuple[str, bool]:
    # No reemplazamos la función de búsqueda de créditos; solamente el elemento visual.
    if 'credito_html = ""' in contenido and "f'{credito_html}'" in contenido:
        ast.parse(contenido)
        return contenido, False

    asignacion = '                credito, titulo_credito = credito_foto_sede(nombre, ruta_foto)'
    etiqueta = '''                    f'<span class="siams-sede-photo-credit" title="{escape(titulo_credito, quote=True)}">'
                    f'{escape(credito)}</span>' '''.rstrip()
    if contenido.count(asignacion) != 1 or contenido.count(etiqueta) != 1:
        raise RuntimeError(
            'No se reconoció el bloque de créditos en siams/inicio.py. '
            'No se modificó ningún archivo. Envíame ese módulo actualizado para adaptarlo.'
        )
    reemplazo = '''                credito, titulo_credito = credito_foto_sede(nombre, ruta_foto)
                # SIAMS_FOTOS_CREDITOS_VERIFICADOS_V2: no exhibir créditos sin fuente demostrada.
                credito_html = ""
                if credito and credito != "Foto: crédito pendiente":
                    credito_html = (
                        f'<span class="siams-sede-photo-credit" title="{escape(titulo_credito, quote=True)}">'
                        f'{escape(credito)}</span>'
                    )'''
    texto = contenido.replace(asignacion, reemplazo, 1).replace(etiqueta, "                    f'{credito_html}'", 1)
    ast.parse(texto, filename=str(INICIO))
    return texto, True


def preparar_csv(texto: str) -> tuple[str, bool, int]:
    lector = csv.DictReader(io.StringIO(texto))
    campos = tuple(lector.fieldnames or ())
    if campos not in (BASE, BASE + EXTRAS):
        raise RuntimeError(f'Columnas inesperadas en {CREDITOS.name}: {campos}. No se modificó nada.')
    filas = list(lector)
    if any(None in fila for fila in filas):
        raise RuntimeError('CSV con columnas sobrantes. No se modificó nada.')
    if len(filas) != 7 or len({f['Sede'] for f in filas}) != 7:
        raise RuntimeError('No hay exactamente siete sedes únicas en los créditos. No se modificó nada.')

    columnas = list(BASE + EXTRAS)
    cambios = 0
    for fila in filas:
        # No alterar las atribuciones verificadas que alguien haya completado.
        for columna in EXTRAS:
            fila.setdefault(columna, '')
        sede = fila.get('Sede', '')
        nota = REFERENCIAS.get(sede)
        if nota and nota not in fila['Observaciones']:
            # Se añade como pista, NO como 'Fuente original' ni como autor.
            fila['Observaciones'] = (fila['Observaciones'].rstrip(' .') + '. ' + nota).strip()
            cambios += 1
    salida = io.StringIO(newline='')
    escritor = csv.DictWriter(salida, fieldnames=columnas, lineterminator='\n')
    escritor.writeheader()
    escritor.writerows({c: fila.get(c, '') for c in columnas} for fila in filas)
    resultado = salida.getvalue()
    # Idempotencia: se compara el contenido semántico sin forzar reescritura si coincide.
    actual_semantica = texto.replace('\r\n','\n').lstrip('\ufeff')
    return resultado, resultado != actual_semantica, cambios


def main() -> None:
    if not INICIO.is_file() or not CREDITOS.is_file() or not (RAIZ / 'app.py').is_file():
        raise SystemExit('ERROR: ejecutar desde la raíz de SIAMS (donde está app.py).')

    actual_inicio = INICIO.read_text(encoding='utf-8-sig')
    actual_csv = CREDITOS.read_text(encoding='utf-8-sig')
    try:
        nuevo_inicio, cambia_inicio = preparar_inicio(actual_inicio)
        nuevo_csv, cambia_csv, nuevas_referencias = preparar_csv(actual_csv)
    except (RuntimeError, SyntaxError) as e:
        raise SystemExit(f'ERROR: {e}') from e

    if not (cambia_inicio or cambia_csv):
        print('OK: los créditos ya están corregidos. Sin cambios adicionales.')
        return

    # Respaldo fuera del repositorio para no añadir carpetas ni archivos temporales a Git.
    respaldo_dir = Path.home() / 'Documents'
    if not respaldo_dir.is_dir():
        respaldo_dir = Path.home()
    sello = datetime.now().strftime('%Y%m%d_%H%M%S')
    for ruta, cambia in ((INICIO,cambia_inicio),(CREDITOS,cambia_csv)):
        if cambia:
            shutil.copy2(ruta, respaldo_dir / f'SIAMS_antes_fotos_{sello}_{ruta.name}')
    if cambia_inicio:
        INICIO.write_text(nuevo_inicio, encoding='utf-8')
    if cambia_csv:
        CREDITOS.write_text(nuevo_csv, encoding='utf-8-sig', newline='')
    print('OK: Inicio solo muestra créditos fotográficos CONFIRMADOS, no "fuente pendiente".')
    print(f'OK: inventario actualizado en docs/CREDITOS_FOTOS_SEDES.csv ({nuevas_referencias} referencias contextuales agregadas).')
    print('No se inventaron fotógrafos, permisos o publicaciones de origen.')
    print('No se modificó app.py, las fotos, los cálculos ni las animaciones.')
    print('Ejecuta: .\\.venv\\Scripts\\python.exe -m pytest -q')


if __name__ == '__main__':
    main()
