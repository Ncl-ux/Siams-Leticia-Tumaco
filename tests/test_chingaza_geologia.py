import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_rutas_geologia_chingaza():
    app=(ROOT/'app.py').read_text(encoding='utf-8-sig').splitlines()
    active=next(l for l in app if l.startswith('if territorio == "Chingaza" and seccion in {') and '"Mapa y territorio"' in l)
    pending=next(l for l in app if l.startswith('elif territorio == "Chingaza" and seccion in {') and '"Hidrogeoquímica"' in l)
    for sec in ('"Geología"','"Hidrogeología"'):
        assert sec in active and sec not in pending
    tree=ast.parse((ROOT/'siams/chingaza.py').read_text(encoding='utf-8-sig'))
    names={n.name for n in tree.body if isinstance(n,ast.FunctionDef)}
    assert {'geologia_chingaza','hidrogeologia_chingaza'} <= names

def test_figuras_estudios_chuza():
    folder=ROOT/'data/processed/chingaza/geologia'
    for name in ('mapa_geologico_chuza.png','modelo_hidrogeologico_chuza.png'):
        assert (folder/name).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
