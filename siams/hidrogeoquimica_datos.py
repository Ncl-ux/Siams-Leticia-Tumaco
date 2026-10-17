"""Validación y análisis de informes FQ de SIAMS, basado en el núcleo Python del taller.

Admite formato largo, CSV y Excel con hoja datos_largo. No infiere ni corrige
unidades desconocidas; los parámetros deben utilizar las unidades documentadas.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import math
import re
import pandas as pd
from . import hidrogeoquimica_nucleo as hq

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/processed/hidrogeoquimica" / "siams_fq_largo.csv"
if not BASE.is_file():
    BASE = ROOT / "Datos_Hidrogeoquimica" / "siams_fq_largo.csv"
RECURSOS = ROOT / "Recursos_Hidrogeoquimica"
REQUERIDAS = ("informe", "parametro", "valor")
IONICOS_REQUERIDOS = (
    "ph", "alcalinidad", "dureza_calcica", "dureza_magnesica", "cloruros",
    "sulfatos", "nitratos_n", "fluoruros",
)
NOMBRES = {row[0]: row[1] for row in hq.IRCA}
NOMBRES.update({
    "conductividad": "Conductividad (µS/cm)", "dureza_calcica": "Dureza cálcica",
    "dureza_magnesica": "Dureza magnésica", "acidez": "Acidez",
    "solidos_totales": "Sólidos totales", "sst": "Sólidos suspendidos",
    "sodio": "Sodio", "potasio": "Potasio",
})
UNIDADES = {
    "ph": "Unidades", "conductividad": "µS/cm 25 °C", "turbiedad": "UNT",
    "color_aparente": "UPC", "alcalinidad": "mg/L CaCO3", "acidez": "mg/L CaCO3",
    "dureza_total": "mg/L CaCO3", "dureza_calcica": "mg/L CaCO3",
    "dureza_magnesica": "mg/L CaCO3", "nitratos_n": "mg/L N-NO3-",
    "nitritos_n": "mg/L N-NO2-", "coliformes_totales": "NMP/100 mL",
    "e_coli": "NMP/100 mL", "sodio": "mg/L Na", "potasio": "mg/L K",
    "calcio": "mg/L Ca", "magnesio": "mg/L Mg", "hierro": "mg/L Fe +3",
    "manganeso": "mg/L Mn +7", "zinc": "mg/L Zn", "fluoruros": "mg/L F-",
    "cloruros": "mg/L Cl-", "sulfatos": "mg/L SO4=", "ortofosfatos": "mg/L PO4-3",
    "cot": "mg/L C", "solidos_totales": "mg/L", "sst": "mg/L",
}
for k, nombre in NOMBRES.items():
    UNIDADES.setdefault(k, "mg/L")


def leer_carga(nombre: str, contenido: bytes) -> pd.DataFrame:
    """Carga archivos sin ejecutar macros ni aceptar otras extensiones."""
    sufijo = Path(nombre).suffix.casefold()
    if sufijo == ".csv":
        errores = []
        for codificacion in ("utf-8-sig", "cp1252"):
            try:
                return pd.read_csv(BytesIO(contenido), sep=None, engine="python", encoding=codificacion, dtype={"informe": str})
            except (UnicodeError, pd.errors.ParserError) as error:
                errores.append(str(error))
        raise ValueError("No se pudo leer el CSV (codificación o delimitador). " + "; ".join(errores))
    if sufijo == ".xlsx":
        hojas = pd.read_excel(BytesIO(contenido), sheet_name=None, dtype={"informe": str})
        for prioridad in ("datos_largo", "Datos", "datos", "Sheet1"):
            if prioridad in hojas and set(REQUERIDAS).issubset(hojas[prioridad].columns):
                return hojas[prioridad]
        for tabla in hojas.values():
            if set(REQUERIDAS).issubset(tabla.columns):
                return tabla
        raise ValueError("El Excel no contiene una hoja en formato largo con columnas: informe, parametro, valor. Usa 'datos_largo' de la plantilla.")
    raise ValueError("Solo se admiten archivos CSV o Excel (.xlsx).")


def _numero(value):
    if pd.isna(value):
        return float("nan")
    text = str(value).strip()
    if text.startswith("<"):
        text = text[1:].strip()
    return pd.to_numeric(text.replace(",", "."), errors="coerce")


def normalizar_base(entrada: pd.DataFrame, *, nombre_fuente: str = "carga") -> pd.DataFrame:
    """Falla explícitamente si hay duplicados, unidades no previstas o entradas inválidas."""
    df = entrada.copy()
    df.columns = [str(x).strip().lower() for x in df.columns]
    faltan = set(REQUERIDAS).difference(df.columns)
    if faltan:
        raise ValueError("Faltan columnas: " + ", ".join(sorted(faltan)))
    df = df.dropna(how="all")
    if df.empty:
        raise ValueError("La tabla está vacía")
    for col, pred in {
        "sede": "Sin especificar", "punto": "SIN-CODIGO", "grupo_punto": "SIN-GRUPO",
        "tipo_agua": "No especificada", "fecha": "", "fecha_uso": "",
        "signo": "", "unidad": "", "bandera": "", "fuente": nombre_fuente,
        "nombre_punto": "", "laboratorio": "", "metodo": "", "LD": float("nan"),
    }.items():
        if col not in df.columns:
            df[col] = pred
    for col in ("informe", "parametro", "sede", "punto", "grupo_punto", "signo", "unidad", "fecha_uso", "bandera"):
        df[col] = df[col].fillna("").astype(str).str.strip()
    df["parametro"] = df["parametro"].str.lower()
    invalidos = sorted(set(df["parametro"]) - set(NOMBRES))
    if invalidos:
        raise ValueError("Códigos de parámetros sin equivalencia documentada: " + ", ".join(invalidos[:12]))
    df["signo"] = df["signo"].str.replace("≤", "<", regex=False)
    indicados = df["valor"].astype(str).str.strip().str.startswith("<")
    df.loc[indicados, "signo"] = "<"
    if not df["signo"].isin(["", "<"]).all():
        raise ValueError("Solo se admite signo vacío o '<' para resultados bajo límite de detección")
    df["valor"] = df["valor"].map(_numero)
    if df["valor"].isna().any() or (~df["valor"].map(math.isfinite)).any():
        raise ValueError("Hay valores vacíos o no numéricos. Revisa la columna 'valor'.")
    if (df["valor"] < 0).any():
        raise ValueError("Se detectaron valores negativos; verifica los datos originales.")
    if (df.loc[df["parametro"] == "ph", "valor"] > 14).any():
        raise ValueError("Hay pH superiores a 14; revisa los datos.")
    sin_informe = df["informe"].eq("")
    if sin_informe.any():
        raise ValueError("Todas las filas deben tener un identificador de informe o muestra.")
    df["id_muestra"] = df["sede"].astype(str) + " · " + df["informe"].astype(str)
    duplicadas = df.duplicated(subset=["id_muestra", "parametro"])
    if duplicadas.any():
        ejemplo = df.loc[duplicadas, ["id_muestra", "parametro"]].head(3).to_dict("records")
        raise ValueError(f"Hay resultados duplicados para una muestra y parámetro: {ejemplo}")
    # Comprobación por código: la unidad del archivo debe corresponder con la guía,
    # o dejarse vacía para ingresar datos que explícitamente siguen la guía.
    # Aceptamos textos específicos del Excel original, no conversiones automáticas.
    for codigo, sub in df.groupby("parametro"):
        esperada = UNIDADES[codigo]
        # La codificación de parámetro identifica especie y forma analítica.
        # Se acepta mg/L genérico para mayoritarios si la clave es explícita;
        # no se aceptan valores de N-NO3/NO3 sin escenario de interpretación.
        permitidas = {esperada}
        if codigo == "ph": permitidas |= {"unidades", "Unidad", "pH"}
        if codigo in {"calcio", "magnesio", "hierro", "manganeso", "zinc", "fluoruros", "cloruros", "sulfatos", "ortofosfatos", "sodio", "potasio"}:
            permitidas |= {"mg/L"}
        unidades = set(sub["unidad"].replace("", esperada))
        if not unidades <= permitidas:
            raise ValueError(f"Unidad incompatible para {codigo}: {sorted(unidades - permitidas)}. Se espera {esperada}.")
    return df.reset_index(drop=True)


def parametros_de(muestra: pd.DataFrame, *, nitratos_en_no3: bool = False) -> dict[str, tuple[str, float]]:
    p = {r.parametro: (r.signo, float(r.valor)) for r in muestra.itertuples()}
    if nitratos_en_no3 and "nitratos_n" in p:
        signo, valor = p["nitratos_n"]
        p["nitratos_n"] = (signo, valor / hq.F_N_NO3)
    return p


def analizar(df: pd.DataFrame, *, nitratos_en_no3: bool = False, regla_ld: str = "LD/2") -> pd.DataFrame:
    filas = []
    for id_muestra, muestra in df.groupby("id_muestra", sort=False):
        meta = muestra.iloc[0]
        p = parametros_de(muestra, nitratos_en_no3=nitratos_en_no3)
        resumen = dict(id_muestra=id_muestra, informe=meta.informe, sede=meta.sede,
                       punto=meta.punto, grupo_punto=meta.grupo_punto,
                       fecha_uso=meta.fecha_uso, tipo_agua=meta.tipo_agua,
                       parametros=len(p), banderas="; ".join(sorted(set(str(x) for x in muestra.bandera if str(x).strip()))))
        if any(k in p for k, *_ in hq.IRCA):
            _, ir = hq.irca_muestra(p)
            resumen.update(irca=ir["irca"], irca_max=ir["irca_max"], nivel=ir["nivel"],
                           puntos_analizados=ir["suma_analizadas"])
        else:
            resumen.update(irca=float("nan"), irca_max=float("nan"), nivel="Sin información", puntos_analizados=0.)
        resumen.update(hco3_mg=float("nan"), co3_mg=float("nan"),
                       error_balance_pct=float("nan"), nak_inferido_meq=float("nan"),
                       CE_estimada=float("nan"), CE_medida=float("nan"))
        if "ph" in p and "alcalinidad" in p:
            try:
                car = hq.carbonatos(hq.valor_calculo(*p["ph"], regla_ld),
                                    hq.valor_calculo(*p["alcalinidad"], regla_ld))
                resumen["hco3_mg"] = car["hco3_mg"]
                resumen["co3_mg"] = car["co3_mg"]
            except (ValueError, OverflowError, ZeroDivisionError):
                pass
        if set(IONICOS_REQUERIDOS).issubset(p):
            try:
                b = hq.balance(p, regla_ld)
                resumen.update(error_balance_pct=b["error_pct"],
                               nak_inferido_meq=b["nak_dif_meq"], CE_estimada=b["ce_estimada"])
            except (ValueError, OverflowError, ZeroDivisionError):
                pass
        if "conductividad" in p:
            resumen["CE_medida"] = p["conductividad"][1]
        filas.append(resumen)
    return pd.DataFrame(filas)


def detalle_irca(muestra: pd.DataFrame, *, nitratos_en_no3: bool = False) -> tuple[pd.DataFrame, dict]:
    return hq.irca_muestra(parametros_de(muestra, nitratos_en_no3=nitratos_en_no3))


def preparar_manual(sede: str, punto: str, informe: str, fecha: str, edicion: pd.DataFrame) -> pd.DataFrame:
    trabajo = edicion.copy().dropna(subset=["valor"])
    if trabajo.empty:
        raise ValueError("Ingresa al menos un resultado para analizar")
    trabajo["sede"] = sede.strip() or "Sin especificar"
    trabajo["punto"] = punto.strip() or "SIN-CODIGO"
    trabajo["grupo_punto"] = trabajo["punto"]
    trabajo["informe"] = informe.strip() or "MANUAL-001"
    trabajo["fecha_uso"] = fecha
    trabajo["fecha"] = fecha
    trabajo["tipo_agua"] = "No especificada"
    trabajo["fuente"] = "Entrada manual SIAMS"
    return normalizar_base(trabajo, nombre_fuente="Entrada manual SIAMS")
