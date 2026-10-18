r"""Agrega procedencia y créditos a app.py sin reemplazar avances posteriores.

PowerShell, desde la raíz de SIAMS:
    .\.venv\Scripts\python.exe scripts\instalar_fuentes_creditos_siams.py
    .\.venv\Scripts\python.exe scripts\instalar_fuentes_creditos_siams.py --verificar
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ARCHIVO = RAIZ / "app.py"
MARCA = "# SIAMS_A6_A8_FUENTES_CREDITOS"
IMPORTACION = "from siams.fuentes_creditos import mostrar_fuentes_y_creditos, mostrar_creditos_institucionales"

TABS_ANTES = '''    tab_archivos, tab_mapas, tab_fuentes = st.tabs([
        "Archivos de datos", "Estado de mapas", "Inventario de fuentes"
    ])'''
TABS_DESPUES = '''    tab_archivos, tab_mapas, tab_fuentes, tab_creditos = st.tabs([
        "Archivos de datos", "Estado de mapas", "Inventario de fuentes",
        "Procedencia y créditos",
    ])'''
ANTES_ACERCA = '''    st.subheader("Información institucional pendiente")

    st.markdown(
        """
        - Reseña oficial del semillero.
        - Docente coordinador.
        - Integrantes autorizados.
        - Líneas de trabajo.
        - Logos.
        - Contacto institucional.
        """
    )'''
DESPUES_ACERCA = '''    st.subheader("Identidad y créditos")
    mostrar_creditos_institucionales()
    st.caption("Coordinación, líneas de investigación y contacto: pendientes de confirmación institucional.")'''


def integrar(texto: str) -> str:
    """Transformación estricta e idempotente; falla sin escribir si cambió app.py."""
    if MARCA in texto:
        if not (IMPORTACION in texto and "with tab_creditos:" in texto and
                "mostrar_creditos_institucionales()" in texto):
            raise RuntimeError("Se encontró instalación A6/A8 incompleta; no se cambió app.py")
        return texto

    for anterior in (TABS_ANTES, ANTES_ACERCA):
        if texto.count(anterior) != 1:
            raise RuntimeError(
                "No coincide la estructura actual de app.py; no se aplicará un parche parcial. "
                "Envíame el app.py actual para adaptar la integración."
            )

    import_inicio = re.search(r"^from siams\.inicio import .+$", texto, flags=re.M)
    if not import_inicio:
        raise RuntimeError("No se encontró la importación siams.inicio; app.py permanece intacto")
    if IMPORTACION in texto:
        raise RuntimeError("Existe una importación de créditos pero falta parte de la integración")
    separador = "# =========================================================\n# SOBRE SIAMS"
    if texto.count(separador) != 1:
        raise RuntimeError("No se encontró la sección Sobre SIAMS; app.py permanece intacto")

    texto = texto[:import_inicio.end()] + "\n" + IMPORTACION + texto[import_inicio.end():]
    texto = texto.replace(TABS_ANTES, TABS_DESPUES, 1)
    texto = texto.replace(ANTES_ACERCA, DESPUES_ACERCA, 1)
    texto = texto.replace(
        separador,
        "    " + MARCA + "\n"
        "    with tab_creditos:\n"
        "        mostrar_fuentes_y_creditos()\n\n" + separador,
        1,
    )
    leyenda_sidebar = 'st.sidebar.caption("Prototipo académico. Información sujeta a revisión.")'
    if leyenda_sidebar in texto:
        texto = texto.replace(
            leyenda_sidebar,
            'st.sidebar.caption("Semillero de Investigación de Aguas y Modelación Subterránea")\n'
            + leyenda_sidebar,
            1,
        )
    ast.parse(texto)
    return texto


def comprobacion(texto: str) -> None:
    assert MARCA in texto and IMPORTACION in texto, "La integración no está instalada"
    assert "with tab_creditos:" in texto
    assert "mostrar_fuentes_y_creditos()" in texto
    assert "mostrar_creditos_institucionales()" in texto
    for ruta in (
        RAIZ / "siams/fuentes_creditos.py",
        RAIZ / "docs/FUENTES_POR_SECCION_SIAMS.csv",
        RAIZ / "docs/AUTORES_SIAMS.csv",
    ):
        assert ruta.is_file(), f"Falta archivo: {ruta}"
    ast.parse(texto)
    print("A6/A8: integración verificada correctamente")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verificar", action="store_true")
    args = parser.parse_args()
    ruta_autores = RAIZ / "docs" / "AUTORES_SIAMS.csv"
    if not ruta_autores.is_file() and not args.verificar:
        if not ruta_autores.parent.is_dir():
            raise FileNotFoundError("Falta docs/; extrae el paquete en la raíz del proyecto")
        ruta_autores.write_text("Nombre,Rol,Afiliación\n", encoding="utf-8-sig")
        print("Se creó docs/AUTORES_SIAMS.csv sin sobrescribir datos existentes")
    bruto = ARCHIVO.read_bytes()
    con_bom = bruto.startswith(b"\xef\xbb\xbf")
    salto = "\r\n" if b"\r\n" in bruto else "\n"
    texto = bruto.decode("utf-8-sig").replace("\r\n", "\n")
    if args.verificar:
        comprobacion(texto)
        return
    editado = integrar(texto)
    if editado != texto:
        destino_respaldo = RAIZ.parent / f"SIAMS_app_respaldo_A6_A8_{datetime.now():%Y%m%d_%H%M%S_%f}.py"
        destino_respaldo.write_bytes(bruto)
        salida = (b"\xef\xbb\xbf" if con_bom else b"") + editado.replace("\n", salto).encode("utf-8")
        ARCHIVO.write_bytes(salida)
        print(f"A6/A8: sección instalada en app.py; respaldo: {destino_respaldo}")
    else:
        print("A6/A8: ya estaba integrado, sin cambios")
    comprobacion(editado)


if __name__ == "__main__":
    main()
