"""Pruebas del panel Landsat: selección rigurosa y compuestos independientes."""
import json
import pandas as pd

from siams import landsat


def test_no_se_rehabilitan_escenas_rechazadas():
    meta = pd.DataFrame({
        "cumple": [True, False, True, True],
        "nube_aoi_pct": [5.0, 2.0, 19.9, 30.0],
    })
    # La escena originalmente rechazada con 2 % no se recupera por bajar el umbral.
    filtradas = landsat._escenas_landsat_validas(meta, 10.0)
    assert filtradas.index.tolist() == [0]
    filtradas = landsat._escenas_landsat_validas(meta, 20.0)
    assert filtradas.index.tolist() == [0, 2]


def test_compuesto_usa_imagenes_de_su_carpeta(tmp_path):
    carpeta = tmp_path / "Leticia"
    origen = carpeta / "compuestos"
    origen.mkdir(parents=True)
    (origen / "natural.jpg").write_bytes(b"imagen")
    (origen / "falso.jpg").write_bytes(b"imagen")
    ficha = {
        "periodo": "2023-06 a 2025-09",
        "publicable": True,
        "imagenes": {"color_natural": "natural.jpg", "falso_color": "falso.jpg"},
    }
    (origen / "leticia_compuesto.json").write_text(
        json.dumps(ficha), encoding="utf-8"
    )
    compuestos = landsat._compuestos_landsat(carpeta)
    assert len(compuestos) == 1
    assert set(compuestos[0]["imagenes"]) == {"color_natural", "falso_color"}
    assert all(imagen.parent == origen for imagen in compuestos[0]["imagenes"].values())


def test_no_se_cargan_imagenes_fuera_de_la_carpeta_del_compuesto(tmp_path):
    carpeta = tmp_path / "Leticia"
    origen = carpeta / "compuestos"
    origen.mkdir(parents=True)
    (origen / "x_compuesto.json").write_text(json.dumps({
        "imagenes": {"color_natural": "../privado.jpg"}
    }), encoding="utf-8")
    compuestos = landsat._compuestos_landsat(carpeta)
    assert len(compuestos) == 1
    assert compuestos[0]["imagenes"] == {}


def test_metas_de_archivo_no_reinterpretan_aceptacion(tmp_path, monkeypatch):
    carpeta = tmp_path / "Leticia"
    carpeta.mkdir()
    (carpeta / "metadatos_escenas.csv").write_text(
        "fecha,id_escena,cumple,nube_aoi_pct\n"
        "2025-07-02,LC08_L2SP_001001_20250702_02_T1,False,1.0\n"
        "2025-07-04,LC08_L2SP_001001_20250704_02_T1,True,15.0\n",
        encoding="utf-8",
    )
    df = landsat._metadatos_landsat(carpeta)
    assert len(df) == 2
    assert len(landsat._escenas_landsat_validas(df, 20.0)) == 1
    assert len(landsat._escenas_landsat_validas(df, 10.0)) == 0
