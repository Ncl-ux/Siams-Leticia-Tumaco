import ast,csv,math,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_isotopos_mensuales_y_calculo_exceso():
    p=ROOT/'data/processed/chingaza/isotopos/lluvia_mensual.csv'
    with p.open(encoding='utf-8-sig') as f:
        reader=csv.DictReader(f);rows=list(reader)
    assert set(reader.fieldnames)=={'periodo','totalizador','estacion','altitud_m','d18O','d2H','exceso_deuterio','fuente'}
    assert len(rows)==18
    assert {(r['periodo'],r['totalizador']) for r in rows}=={(f'2023-{m:02d}',t) for m in range(5,11) for t in ('T1','T2','T3')}
    for r in rows:
        assert re.fullmatch(r'\d{4}-\d{2}',r['periodo'])
        assert math.isclose(float(r['exceso_deuterio']),float(r['d2H'])-8*float(r['d18O']),abs_tol=1e-8)
        assert 'BASE_UNAL.xlsx' in r['fuente']

def test_rutas_isotopos_chingaza():
    lines=(ROOT/'app.py').read_text(encoding='utf-8-sig').splitlines()
    active=next(l for l in lines if l.startswith('if territorio == "Chingaza" and seccion in {') and '"Mapa y territorio"' in l)
    pending=next(l for l in lines if l.startswith('elif territorio == "Chingaza" and seccion in {') and '"Hidrogeoquímica"' in l)
    assert '"Isótopos"' in active and '"Isótopos"' not in pending
    tree=ast.parse((ROOT/'siams/chingaza.py').read_text(encoding='utf-8-sig'))
    assert sum(isinstance(n,ast.FunctionDef) and n.name=='isotopos_chingaza' for n in tree.body)==1
