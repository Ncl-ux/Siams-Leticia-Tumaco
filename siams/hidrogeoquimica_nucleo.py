"""Núcleo de cálculo (Python) para el taller: conversiones, IRCA, carbonatos, balance iónico.
Las mismas reglas están en 03_Herramienta (JavaScript) y en el cuaderno; verificar.py compara las tres."""
import math, re
import pandas as pd

# Masas molares (g/mol), IUPAC 2021 redondeadas a 3 decimales
MM = {'Ca': 40.078, 'Mg': 24.305, 'Na': 22.990, 'K': 39.098, 'Fe': 55.845, 'Mn': 54.938,
      'Cl': 35.453, 'SO4': 96.06, 'NO3': 62.004, 'NO2': 46.005, 'F': 18.998, 'HCO3': 61.016,
      'CO3': 60.008, 'PO4': 94.971, 'N': 14.007, 'CaCO3': 100.086, 'CO2': 44.009, 'C': 12.011}
Z = {'Ca': 2, 'Mg': 2, 'Na': 1, 'K': 1, 'Cl': 1, 'SO4': 2, 'NO3': 1, 'F': 1, 'HCO3': 1, 'CO3': 2}
PEQ_CACO3 = MM['CaCO3'] / 2          # 50,043 mg/meq
F_N_NO3 = MM['NO3'] / MM['N']        # 4,4266
F_N_NO2 = MM['NO2'] / MM['N']        # 3,2845
# Conductividades iónicas límite a 25 °C (S·cm²/eq) — tablas usuales (p. ej. Hem 1985; CRC)
LAMBDA = {'Ca': 59.5, 'Mg': 53.0, 'Na': 50.1, 'K': 73.5, 'H': 349.8, 'HCO3': 44.5, 'CO3': 69.3,
          'Cl': 76.3, 'SO4': 80.0, 'NO3': 71.4, 'F': 55.4}
PK1, PK2, PKW = 6.352, 10.329, 14.0   # 25 °C (Plummer y Busenberg, 1982)

def peq(ion): return MM[ion] / Z[ion]

# Resolución 2115 de 2007: valor máximo aceptable (Cuadros 1, 3, 4, 5; art. 4) y puntaje (Cuadro 6)
# 'conv' pasa del valor del informe a la unidad en que está expresado el límite.
IRCA = [  # codigo, característica, puntaje, mínimo, máximo, unidad del límite, conv
    ('color_aparente', 'Color aparente', 6, None, 15, 'UPC', 1),
    ('turbiedad', 'Turbiedad', 15, None, 2, 'UNT', 1),
    ('ph', 'pH', 1.5, 6.5, 9.0, 'unidades', 1),
    ('cloro_libre', 'Cloro residual libre', 15, 0.3, 2.0, 'mg/L Cl2', 1),
    ('alcalinidad', 'Alcalinidad total', 1, None, 200, 'mg/L CaCO3', 1),
    ('calcio', 'Calcio', 1, None, 60, 'mg/L Ca', 1),
    ('ortofosfatos', 'Fosfatos', 1, None, 0.5, 'mg/L PO4', 1),
    ('manganeso', 'Manganeso', 1, None, 0.1, 'mg/L Mn', 1),
    ('molibdeno', 'Molibdeno', 1, None, 0.07, 'mg/L Mo', 1),
    ('magnesio', 'Magnesio', 1, None, 36, 'mg/L Mg', 1),
    ('zinc', 'Zinc', 1, None, 3, 'mg/L Zn', 1),
    ('dureza_total', 'Dureza total', 1, None, 300, 'mg/L CaCO3', 1),
    ('sulfatos', 'Sulfatos', 1, None, 250, 'mg/L SO4', 1),
    ('hierro', 'Hierro total', 1.5, None, 0.3, 'mg/L Fe', 1),
    ('cloruros', 'Cloruros', 1, None, 250, 'mg/L Cl', 1),
    ('nitratos_n', 'Nitratos', 1, None, 10, 'mg/L NO3', F_N_NO3),
    ('nitritos_n', 'Nitritos', 3, None, 0.1, 'mg/L NO2', F_N_NO2),
    ('aluminio', 'Aluminio (Al3+)', 3, None, 0.2, 'mg/L Al', 1),
    ('fluoruros', 'Fluoruros', 1, None, 1.0, 'mg/L F', 1),
    ('cot', 'COT', 3, None, 5.0, 'mg/L C', 1),
    ('coliformes_totales', 'Coliformes totales', 15, None, 0, 'por 100 mL', 1),
    ('e_coli', 'Escherichia coli', 25, None, 0, 'por 100 mL', 1),
]
assert abs(sum(r[2] for r in IRCA) - 100) < 1e-9
NIVELES = [(5, 'Sin riesgo'), (14, 'Bajo'), (35, 'Medio'), (80, 'Alto'), (100, 'Inviable sanitariamente')]

def nivel(irca):
    # Cuadro 7: 0–5; 5,1–14; 14,1–35; 35,1–80; 80,1–100 (se usa el límite superior inclusivo)
    for tope, n in NIVELES:
        if irca <= tope + 1e-9: return n
    return NIVELES[-1][1]

def parse_valor(txt):
    """'<0,1' -> ('<', 0.1); '5,8 x 10^2' -> ('', 580); '12,4' -> ('', 12.4)."""
    s = str(txt).strip().replace(' ', '')
    signo = ''
    if s[:1] in '<>':
        signo, s = s[0], s[1:]
    s = s.replace(',', '.')
    m = re.match(r'^([0-9.]+)[x×\*]10\^?([0-9]+)$', s)
    if m: return signo, float(m.group(1)) * 10 ** int(m.group(2))
    return signo, float(s)

def evaluar(codigo, signo, valor):
    """Devuelve (estado, valor_en_unidad_del_límite). estado: cumple | no cumple | no concluyente."""
    fila = next(r for r in IRCA if r[0] == codigo)
    _, _, _, vmin, vmax, _, conv = fila
    v = valor * conv
    if signo == '<':           # el valor real está entre 0 y el LD
        if vmin is not None: return 'no concluyente', v
        return ('cumple' if v <= vmax else 'no concluyente'), v
    ok = (vmin is None or v >= vmin) and (vmax is None or v <= vmax)
    return ('cumple' if ok else 'no cumple'), v

def irca_muestra(params):
    """params: dict codigo -> (signo, valor). Devuelve tabla y resumen."""
    filas = []
    for cod, nom, pts, vmin, vmax, und, conv in IRCA:
        if cod not in params:
            filas.append(dict(codigo=cod, caracteristica=nom, puntaje=pts, estado='no analizado')); continue
        sg, val = params[cod]
        est, v = evaluar(cod, sg, val)
        filas.append(dict(codigo=cod, caracteristica=nom, puntaje=pts, signo=sg, valor_limite_und=v,
                          minimo=vmin, maximo=vmax, unidad=und, estado=est))
    t = pd.DataFrame(filas)
    an = t[t.estado != 'no analizado']
    den = an.puntaje.sum()
    nc = an[an.estado == 'no cumple'].puntaje.sum()
    ninc = an[an.estado == 'no concluyente'].puntaje.sum()
    base = 100 * nc / den; maxi = 100 * (nc + ninc) / den
    return t, dict(suma_analizadas=den, suma_no_cumple=nc, suma_no_concluyente=ninc,
                   irca=round(base, 1), nivel=nivel(round(base, 1)),
                   irca_max=round(maxi, 1), nivel_max=nivel(round(maxi, 1)))

def carbonatos(ph, alc_caco3, pk1=PK1, pk2=PK2, pkw=PKW):
    """Especiación con alcalinidad total (mg/L CaCO3) y pH. Devuelve mmol/L y mg/L."""
    H = 10 ** -ph; K1, K2, Kw = 10 ** -pk1, 10 ** -pk2, 10 ** -pkw
    alk = alc_caco3 / PEQ_CACO3 / 1000          # eq/L
    hco3 = (alk - Kw / H + H) / (1 + 2 * K2 / H)  # mol/L
    co3 = hco3 * K2 / H
    co2 = hco3 * H / K1
    return dict(alk_meq=alk * 1000, H_meq=H * 1000, hco3_mmol=hco3 * 1000, co3_mmol=co3 * 1000,
                co2_mmol=co2 * 1000, hco3_mg=hco3 * 1000 * MM['HCO3'], co3_mg=co3 * 1000 * MM['CO3'],
                co2_mg=co2 * 1000 * MM['CO2'], hco3_simple_mg=alc_caco3 * MM['HCO3'] / PEQ_CACO3,
                frac_co3=co3 / (hco3 + co3) if hco3 > 0 else 0)

def valor_calculo(signo, valor, regla='LD/2'):
    if signo == '<':
        return valor / 2 if regla == 'LD/2' else (0.0 if regla == '0' else valor)
    return valor

def balance(p, regla='LD/2'):
    """p: dict codigo -> (signo, valor) de una muestra. Devuelve meq/L, error y Na+K por diferencia."""
    g = lambda c: valor_calculo(*p[c], regla) if c in p else None
    c = carbonatos(g('ph'), g('alcalinidad'))
    meq = {
        'Ca': g('dureza_calcica') / PEQ_CACO3,
        'Mg': g('dureza_magnesica') / PEQ_CACO3,
        'HCO3': c['hco3_mmol'], 'CO3': 2 * c['co3_mmol'],
        'Cl': g('cloruros') / peq('Cl'), 'SO4': g('sulfatos') / peq('SO4'),
        'NO3': g('nitratos_n') * F_N_NO3 / peq('NO3'), 'F': g('fluoruros') / peq('F'),
    }
    cat = meq['Ca'] + meq['Mg']
    an = meq['HCO3'] + meq['CO3'] + meq['Cl'] + meq['SO4'] + meq['NO3'] + meq['F']
    err = 100 * (cat - an) / (cat + an)
    nak = max(an - cat, 0.0)
    ce_est = (meq['Ca'] * LAMBDA['Ca'] + meq['Mg'] * LAMBDA['Mg'] + nak * LAMBDA['Na'] + meq['HCO3'] * LAMBDA['HCO3']
              + meq['CO3'] * LAMBDA['CO3'] + meq['Cl'] * LAMBDA['Cl'] + meq['SO4'] * LAMBDA['SO4']
              + meq['NO3'] * LAMBDA['NO3'] + meq['F'] * LAMBDA['F'] + c['H_meq'] * LAMBDA['H'])
    return dict(meq=meq, cationes=cat, aniones=an, error_pct=err, nak_dif_meq=nak, nak_dif_mg_Na=nak * MM['Na'],
                ce_estimada=ce_est, carb=c)
