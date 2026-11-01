"""Niveles de Bogotá desde el paquete ordenado preparado el 2026-11-01 (bogota/niveles/*.csv),
en lugar de reprocesar los crudos (OGA 2026-19-05_OGA.xlsm, loggers 'Pozo SGC' y 'Pz-02').

Entrada (NO versionada): --paquete <carpeta bogota> con niveles/niveles_bogota_tidy.csv y niveles/pozos.csv
Reemplaza data/processed/niveles/niveles_bogota.csv y las filas de Bogotá en pozos.csv.

* Profundidad bajo el terreno = −nivel_corregido (OGA; manual y logger OGA).
* Logger crudo (columna_agua_mH2O) se publica solo como carga sobre el sensor: la profundidad del sensor
  y la asignación del equipo 'Pz-02' no están confirmadas.
* nivel_msnm 'logger_procesado' NO se usa: su referencia no está documentada.
* Cota del nivel = (GLO-30 − 1,5 m) − profundidad.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from siams import dem  # noqa: E402

SAL = RAIZ / "data" / "processed" / "niveles"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--paquete", required=True)
    ap.add_argument("--sin-dem", action="store_true")
    a = ap.parse_args(argv)
    paq = Path(a.paquete) / "niveles"
    t = pd.read_csv(paq / "niveles_bogota_tidy.csv", parse_dates=["datetime"])
    pz = pd.read_csv(paq / "pozos.csv")
    t["pozo_id"] = "BOG-" + t.well.str.split().str[0]
    pz["pozo_id"] = "BOG-" + pz.well.str.split().str[0]

    cotas = {}
    for r in pz.dropna(subset=["lat", "lon"]).itertuples():
        cotas[r.pozo_id] = None if a.sin_dem else round(float(dem.elevacion_glo30(r.lat, r.lon)), 2)

    prof = t[t.variable == "nivel_corregido"].copy()
    prof["profundidad_nivel_m"] = -prof.value
    prof["metodo"] = prof.flag.map({"manual": "manual", "logger": "automatico_oga"})
    prof["supuesto"] = "Profundidad = −'nivel corregido' de la OGA (bajo superficie)."
    prof.loc[prof.profundidad_nivel_m < 0, "supuesto"] += " Valor sobre el terreno (artesiano o error)."
    log = prof[prof.metodo == "automatico_oga"]
    log = (log.set_index("datetime").groupby("pozo_id").profundidad_nivel_m.resample("1h").mean().dropna().reset_index()
           .assign(metodo="automatico_oga", supuesto=log.supuesto.iloc[0] if len(log) else ""))
    man = prof[prof.metodo == "manual"][["pozo_id", "datetime", "profundidad_nivel_m", "metodo", "supuesto"]]
    cr = t[t.variable == "columna_agua_mH2O"].set_index("datetime").groupby("pozo_id").value.resample("1h").mean().dropna().reset_index()
    cr = cr.rename(columns={"value": "carga_sobre_sensor_m"}).assign(
        metodo="transductor", supuesto="Logger Keller crudo (B = 32 m): profundidad del sensor y equipo por confirmar; sin cota.")
    d = pd.concat([man, log, cr], ignore_index=True).rename(columns={"datetime": "fecha"})
    d["sede"] = "Bogotá"
    d["calidad"] = "ok"
    cot = d.pozo_id.map(cotas)
    d["cota_terreno"] = cot - dem.SESGO_DEM_M
    d["cota_nivel_msnm"] = (d.cota_terreno - d.profundidad_nivel_m).round(3)
    d["profundidad_nivel_m"] = d.profundidad_nivel_m.round(3)
    d["carga_sobre_sensor_m"] = d.carga_sobre_sensor_m.round(3)
    cols = ["fecha", "sede", "pozo_id", "metodo", "carga_sobre_sensor_m", "calidad", "profundidad_nivel_m", "cota_nivel_msnm", "supuesto"]
    d = d.sort_values(["pozo_id", "fecha"])[cols]
    d.to_csv(SAL / "niveles_bogota.csv", index=False, date_format="%Y-%m-%d %H:%M")

    pozos = pd.read_csv(SAL / "pozos.csv")
    pozos = pozos[pozos.sede != "Bogotá"]
    b = pd.DataFrame({"pozo_id": pz.pozo_id, "sede": "Bogotá", "nombre": pz.well, "tipo_registro": "OGA manual/automático",
                      "lat": pz.lat, "lon": pz.lon, "fuente_coordenada": "Nomenclatura OGA (EPSG:3116 → WGS84)",
                      "dem_glo30_m": pz.pozo_id.map(cotas)})
    b["cota_terreno_msnm"] = (b.dem_glo30_m - dem.SESGO_DEM_M).round(2)
    b["metodo_cota_terreno"] = "GLO-30 − 1.5 m"
    b["notas"] = ""
    b.loc[b.lat.isna(), "notas"] = "Sin coordenadas en la nomenclatura OGA."
    b.loc[b.pozo_id == "BOG-PA36", "notas"] = "Posición distinta entre nomenclatura y Campus.xlsx (≈1,2 km)."
    b.loc[b.pozo_id.isin(["BOG-PA05", "BOG-PA25"]), "notas"] = ("Muestra FQ 2023 con turbiedad/SST extremos (sin purga): "
                                                              "no representa el acuífero.")
    b["n_registros"] = b.pozo_id.map(d.pozo_id.value_counts()).fillna(0).astype(int)
    pd.concat([pozos, b], ignore_index=True).to_csv(SAL / "pozos.csv", index=False)

    mf = SAL / "metadatos.json"
    m = json.loads(mf.read_text(encoding="utf-8"))
    m["series"]["Bogotá"] = {"archivo": "niveles_bogota.csv", "registros": len(d), "inicio": str(d.fecha.min()),
                             "fin": str(d.fecha.max()), "fuente": "Paquete Bogotá 2026-11-01 (OGA UNAL + loggers)"}
    mf.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(d), "registros;", len(b), "pozos;", d.groupby("metodo").size().to_dict())


if __name__ == "__main__":
    main()
