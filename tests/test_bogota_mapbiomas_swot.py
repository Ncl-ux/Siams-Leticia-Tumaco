from pathlib import Path
from siams import mapbiomas, swot

ROOT = Path(__file__).resolve().parents[1]


def test_mapbiomas_bogota():
    archivos = mapbiomas.encontrar_csv_coberturas("Bogotá", "B")
    assert len(archivos["anual"]) == len(archivos["serie"]) == 1
    datos = mapbiomas.cargar_csv_cobertura(str(archivos["serie"][0]))
    assert {str(a) for a in range(1985, 2025)}.issubset(datos.columns)
    for nivel in ("Nivel 1", "Nivel 2"):
        assert not mapbiomas.preparar_cobertura_nivel(datos, nivel).empty
    rutas, ambiguos = mapbiomas.buscar_csv_natural_antropico("Bogotá", "B")
    assert len(rutas) == 1 and not ambiguos
    ant, _ = mapbiomas.cargar_csv_natural_antropico(str(rutas[0]))
    assert len(ant) == 80 and set(ant["Clase"]) == {"Natural", "Antrópica"}
    for nombre in mapbiomas.MAPBIOMAS_GIFS_POR_TERRITORIO["Bogotá"].values():
        assert mapbiomas.buscar_gif_mapbiomas("Bogotá", nombre).suffix == ".mp4"


def test_swot_bogota():
    for slug, identificador, n in (("chuza", "6150035523", 33), ("san_rafael", "6120004832", 69)):
        assert swot.buscar_gif_swot(f"swot_bogota_{slug}.mp4").suffix == ".mp4"
        for variable, sufijo in (("WSE", "wse"), ("Área", "area")):
            assert swot.buscar_tarjeta_swot(f"swot_bogota_{slug}_{sufijo}.png").is_file()
            ruta = ROOT / "data/processed/swot" / f"swot_bogota_{slug}_{sufijo}.csv"
            datos = swot._leer_serie_embalse_bogota(ruta, identificador, variable)
            assert len(datos) == n
            assert (datos["Incertidumbre"] >= 0).all()
    assert not swot._archivos_series_swot("Bogotá")
