"""SIAMS: actualiza SOLO la sonda LPZ-UNAL (La Paz).

Uso desde la raiz del proyecto:
    python scripts/ajustar_la_paz_siams.py
    python scripts/ajustar_la_paz_siams.py --cota-google-earth <VALOR_REAL>

Sin --cota-google-earth: reutiliza la cota provisional YA registrada en
pozos.csv, sin atribuirla a Google Earth. Con el argumento: adopta la
estimacion introducida, la documenta y conserva el valor en la configuracion
para futuros procesamientos (sin confundirla con un levantamiento topografico).

Los registros con 'sensor_fuera_del_agua' siguen sin nivel/cota calculado.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import math
from pathlib import Path
import shutil

POZO = "LPZ-UNAL"
PROFUNDIDAD_M = 42.81
UMBRAL_M = 0.05
FUENTE_PROFUNDIDAD = "Dato comunicado por la profesora Piña (noviembre de 2026); pendiente verificacion en campo"
FUENTE_ELEVACION_GOOGLE_EARTH = "Google Earth, elevacion del terreno estimada; pendiente verificacion topografica"
CAMPO_COTA_ESTIMADA = "cota_estimada_msnm"
CAMPO_FUENTE_COTA_ESTIMADA = "fuente_cota_estimada"


def cargar_csv(ruta: Path):
    contenido = ruta.read_text(encoding="utf-8-sig")
    rdr = csv.DictReader(io.StringIO(contenido))
    if not rdr.fieldnames:
        raise ValueError(f"CSV sin encabezados: {ruta}")
    return list(rdr.fieldnames), list(rdr)


def csv_texto(campos, filas):
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=campos, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(filas)
    return buf.getvalue()


def fila_unica(filas, pozo):
    encontrados = [f for f in filas if f.get("pozo_id", "").strip() == pozo]
    if len(encontrados) != 1:
        raise ValueError(f"Se esperaba un solo pozo {pozo}; encontrados: {len(encontrados)}")
    return encontrados[0]


def numero(cadena):
    try:
        v = float(str(cadena).strip().replace(",", "."))
        return v if math.isfinite(v) else None
    except (ValueError, TypeError):
        return None


def preparar_pipeline(original: str):
    """Conserva la cota estimada de Google Earth al regenerar los CSV."""
    marca = "# SIAMS_LA_PAZ_COTA_ESTIMADA"
    if marca not in original:
        comienzo = original.find("def tabla_pozos(")
        fin = original.find("\ndef procesar(", comienzo)
        if comienzo < 0:
            raise ValueError("No se encontro tabla_pozos en scripts/10_niveles_sedes.py")
        if fin < 0:
            fin = original.find("\n# ---------------------------------------------------------------- por sede", comienzo)
        if fin < 0:
            raise ValueError("No se pudo delimitar la funcion tabla_pozos")
        fragmento = original[comienzo:fin]
        needle = "    return pozos"
        if fragmento.count(needle) != 1:
            raise ValueError("No se pudo ubicar return pozos de forma segura")
        anexo = '''    # SIAMS_LA_PAZ_COTA_ESTIMADA: valor estimado de Google Earth, NO levantado.\n    if "cota_estimada_msnm" in pozos.columns:\n        estimada = pd.to_numeric(pozos["cota_estimada_msnm"], errors="coerce")\n        sin_levantamiento = pozos["cota_levantada_msnm"].isna()\n        m_estimada = estimada.notna() & sin_levantamiento\n        pozos.loc[m_estimada, "cota_terreno_msnm"] = estimada[m_estimada].round(2)\n        if "fuente_cota_estimada" in pozos.columns:\n            pozos.loc[m_estimada, "metodo_cota_terreno"] = pozos.loc[m_estimada, "fuente_cota_estimada"].fillna("Cota estimada")\n        else:\n            pozos.loc[m_estimada, "metodo_cota_terreno"] = "Cota estimada (sin levantamiento)"\n'''
        original = original[:comienzo] + fragmento.replace(needle, anexo + needle) + original[fin:]
    # Corregir solo la descripcion de La Paz, dejando intacta la de Arauca.
    start = original.find('S["La Paz"] = serie_transductor(')
    if start >= 0:
        end = original.find('\n    # Leticia', start)
        if end >= 0:
            bloque = original[start:end]
            bloque = bloque.replace(
                "Profundidad del sensor DESCONOCIDA: sin cota; se publica la columna de agua.",
                "Sensor instalado a 42,81 m (dato profesora Pina, nov-2026). "
                "Cota del terreno estimada, pendiente verificacion topografica."
            )
            original = original[:start] + bloque + original[end:]
    return original


def ejecutar(raiz: Path, cota_ge: float | None) -> None:
    conf = raiz / "config/pozos_monitoreo.csv"
    invent = raiz / "data/processed/niveles/pozos.csv"
    serie = raiz / "data/processed/niveles/niveles_la_paz.csv"
    pipeline = raiz / "scripts/10_niveles_sedes.py"
    for ruta in [conf, invent, serie, pipeline]:
        if not ruta.is_file():
            raise FileNotFoundError(f"No se encuentra {ruta}. Ejecutar desde la raiz de SIAMS.")

    cp_campos, cp_filas = cargar_csv(conf)
    ip_campos, ip_filas = cargar_csv(invent)
    sp_campos, sp_filas = cargar_csv(serie)
    c = fila_unica(cp_filas, POZO)
    p = fila_unica(ip_filas, POZO)
    requiere = {"pozo_id", "prof_sensor_m", "fuente_prof_sensor"}
    if not requiere.issubset(cp_campos) or not requiere.issubset(ip_campos):
        raise ValueError("Estructura de configuracion/inventario distinta; no se modifica nada")
    if not {"pozo_id", "carga_sobre_sensor_m", "calidad", "profundidad_nivel_m", "cota_nivel_msnm", "supuesto"}.issubset(sp_campos):
        raise ValueError("Estructura de niveles_la_paz.csv distinta; no se modifica nada")
    nlpz = sum(f.get("pozo_id") == POZO for f in sp_filas)
    if nlpz == 0 or nlpz != len(sp_filas):
        raise ValueError("Se esperaba que niveles_la_paz.csv contuviera solo LPZ-UNAL")

    if cota_ge is not None:
        if not math.isfinite(cota_ge) or not (-100 < cota_ge < 6000):
            raise ValueError("Cota de Google Earth fuera de rango; confirma m s.n.m.")
        for col in (CAMPO_COTA_ESTIMADA, CAMPO_FUENTE_COTA_ESTIMADA):
            if col not in cp_campos:
                cp_campos.append(col)
        z = cota_ge
        p["cota_terreno_msnm"] = f"{z:.2f}"
        p["metodo_cota_terreno"] = FUENTE_ELEVACION_GOOGLE_EARTH
        c[CAMPO_COTA_ESTIMADA] = f"{z:.2f}"
        c[CAMPO_FUENTE_COTA_ESTIMADA] = FUENTE_ELEVACION_GOOGLE_EARTH
        fuente_z = "Google Earth (estimada, NO topografica)"
    else:
        z = numero(p.get("cota_terreno_msnm", ""))
        if z is None:
            raise ValueError("No hay cota del terreno registrada: usa --cota-google-earth VALOR")
        fuente_z = "Cota provisional ya registrada: " + (p.get("metodo_cota_terreno") or "origen no documentado")

    c["prof_sensor_m"] = f"{PROFUNDIDAD_M:.2f}"
    c["fuente_prof_sensor"] = FUENTE_PROFUNDIDAD
    p["prof_sensor_m"] = f"{PROFUNDIDAD_M:.2f}"
    p["fuente_prof_sensor"] = FUENTE_PROFUNDIDAD

    correctas, excluidas, marcadas = 0, 0, 0
    for f in sp_filas:
        h = numero(f.get("carga_sobre_sensor_m"))
        estado = (f.get("calidad") or "").strip()
        if h is None or estado == "sensor_fuera_del_agua" or h < UMBRAL_M or h > PROFUNDIDAD_M:
            f["profundidad_nivel_m"] = ""
            f["cota_nivel_msnm"] = ""
            excluidas += 1
        else:
            prof_agua = PROFUNDIDAD_M - h
            nivel = z - prof_agua
            f["profundidad_nivel_m"] = f"{prof_agua:.3f}"
            f["cota_nivel_msnm"] = f"{nivel:.3f}"
            correctas += 1
            if estado != "ok":
                marcadas += 1
        f["supuesto"] = (
            f"Sensor a {PROFUNDIDAD_M:.2f} m (profe Pina nov-2026); "
            f"profundidad agua = profundidad sensor - carga. {fuente_z}. "
            "Lecturas marcadas requieren revision."
        )

    nuevos = {
        conf: csv_texto(cp_campos, cp_filas),
        invent: csv_texto(ip_campos, ip_filas),
        serie: csv_texto(sp_campos, sp_filas),
        pipeline: preparar_pipeline(pipeline.read_text(encoding="utf-8-sig")),
    }
    respaldo = raiz / ".siams_backups" / "la_paz" / dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    respaldo.mkdir(parents=True, exist_ok=False)
    modificados = []
    for ruta, txt in nuevos.items():
        antes = ruta.read_text(encoding="utf-8-sig")
        if antes == txt:
            continue
        (respaldo / ruta.relative_to(raiz)).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ruta, respaldo / ruta.relative_to(raiz))
        ruta.write_text(txt, encoding="utf-8", newline="")
        modificados.append(str(ruta.relative_to(raiz)))

    print(f"Pozo: {POZO}  | Profundidad sonda: {PROFUNDIDAD_M:.2f} m")
    print(f"Cota del terreno aplicada: {z:.2f} m s.n.m. | {fuente_z}")
    print(f"Registros: {len(sp_filas)} | con nivel: {correctas} | sin nivel: {excluidas} | marcados con nivel: {marcadas}")
    print("Archivos modificados:\n  " + "\n  ".join(modificados) if modificados else "Sin cambios nuevos")
    print(f"Respaldo local de los archivos alterados: {respaldo}")
    if cota_ge is None:
        print("ADVERTENCIA: la cota usada NO se ha comprobado en Google Earth ni con topografia.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cota-google-earth", type=float, metavar="MSNM", help="Elevacion estimada manualmente en Google Earth (m s.n.m.)")
    args = ap.parse_args()
    ejecutar(Path(__file__).resolve().parents[1], args.cota_google_earth)
