"""Tabla ordenada de resultados fisicoquímicos de Arauca (Orinoquía) y Tumaco, más iones en meq/L
para Piper y Stiff, usando el paquete fqsiams del semillero (no se versiona aquí: uso interno).

Entradas (NO versionadas):
    FQSIAMS_PATH   carpeta que contiene el paquete fqsiams/ (Evaluacion_hidroquimica_v3)
    SIAMS_CRUDOS_FQ carpeta con Arauca/Fisicoquimico.xlsx y los PDF 'Pozo profundo <Mes> 2025.pdf'
La transcripción de Tumaco se toma de fqsiams/datos/transcripcion_pdf_tumaco.csv.
Leticia ya está en data/processed/hidrogeoquimica/siams_fq_largo.csv (rama del semillero).

Salidas: data/processed/hidrogeoquimica/fq_sedes_largo.csv y fq_sedes_iones.csv
Na⁺+K⁺ no se reportan en ningún informe: se estiman por diferencia de carga (ΣA − Ca − Mg)
solo para ubicar la muestra en Piper/Stiff; el balance iónico no es verificable.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "data" / "processed" / "hidrogeoquimica"
DUDOSOS = [("Orinoquía", "2025-10-28", "alc"), ("Orinoquía", "2025-10-28", "dureza"),
           ("Orinoquía", "2025-10-28", "dureza_ca"), ("Tumaco", "2017-11-23", "ca")]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fqsiams", default=os.environ.get("FQSIAMS_PATH", ""))
    ap.add_argument("--crudos", default=os.environ.get("SIAMS_CRUDOS_FQ", str(RAIZ / "data" / "raw" / "fq")))
    a = ap.parse_args(argv)
    sys.path.insert(0, a.fqsiams)
    from fqsiams import lectura as L, quimica as Q

    crudos = Path(a.crudos)
    log: list = []
    cache = str(crudos / "cache_texto")
    ori = pd.DataFrame(L.leer_orinoquia(str(crudos / "Arauca" / "Fisicoquimico.xlsx"), str(crudos / "Arauca"), cache, log))
    tum = pd.DataFrame(L.leer_transcripcion(str(Path(a.fqsiams) / "fqsiams" / "datos" / "transcripcion_pdf_tumaco.csv")))
    d = pd.concat([ori, tum], ignore_index=True)
    # El PDF de septiembre es idéntico al de agosto (misma emisión): un solo registro.
    d = d.drop_duplicates(["sede", "pozo", "fecha", "parametro"])
    d["bandera"] = ""
    for s, f, p in DUDOSOS:
        d.loc[(d.sede == s) & (d.fecha == f) & (d.parametro == p), "bandera"] = "dudoso_excluido_de_calculos"
    d["sede"] = d.sede.replace({"Orinoquía": "Arauca"})
    cols = ["sede", "pozo", "tipo_agua", "fecha", "laboratorio", "informe", "id_muestra", "parametro", "valor",
            "censura", "ld", "unidad", "texto_original", "fuente", "flags", "bandera"]
    largo = d[cols].sort_values(["sede", "pozo", "fecha", "parametro"])
    SALIDA.mkdir(parents=True, exist_ok=True)
    largo.to_csv(SALIDA / "fq_sedes_largo.csv", index=False)

    w = Q.preparar_muestras(Q.tabla_ancha(d[d.bandera == ""].assign(sede=lambda x: x.sede)))
    meq = Q.meq_tabla(w)
    for c in ("na", "k"):
        meq[c] = meq[c] if c in meq else np.nan
    an = meq[["hco3", "co3", "cl", "so4", "no3"]].fillna(0).sum(axis=1)
    completo = meq[["ca", "mg", "hco3", "cl", "so4"]].notna().all(axis=1)
    nak = (an - meq.ca.fillna(0) - meq.mg.fillna(0)).clip(lower=0)
    iones = pd.DataFrame({"sede": w.sede, "pozo": w.pozo, "tipo_agua": w.tipo_agua, "fecha": w.fecha,
                          "informe": w.informe,
                          "ca_meq": meq.ca, "mg_meq": meq.mg, "nak_meq": np.where(completo, nak, np.nan),
                          "hco3_meq": meq.hco3.fillna(0) + meq.co3.fillna(0), "cl_meq": meq.cl, "so4_meq": meq.so4,
                          "no3_meq": meq.no3, "ce_us_cm": w.get("ce_us", w.get("ce")), "ph": w.get("ph")})
    iones["nak_estimado_por_diferencia"] = completo
    cat = iones[["ca_meq", "mg_meq", "nak_meq"]].sum(axis=1)
    ani = iones[["hco3_meq", "cl_meq", "so4_meq"]].sum(axis=1)
    for c, t in (("ca", cat), ("mg", cat), ("nak", cat), ("hco3", ani), ("cl", ani), ("so4", ani)):
        iones[f"pct_{c}"] = np.where(completo, 100 * iones[f"{c}_meq"] / t, np.nan)
    iones.round(4).to_csv(SALIDA / "fq_sedes_iones.csv", index=False)
    print(len(largo), "resultados;", int(completo.sum()), "muestras con iones mayores para Piper de", len(iones))
    for r in log:
        print("bitácora:", r)


if __name__ == "__main__":
    main()
