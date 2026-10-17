"""Pruebas de lectura y cálculo de hidrogeoquímica, sin requerir Streamlit."""
from __future__ import annotations
import sys
from pathlib import Path
import unittest

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ))
from siams import hidrogeoquimica_nucleo as hq
from siams.hidrogeoquimica_datos import (
    BASE, normalizar_base, analizar, detalle_irca, leer_carga, parametros_de, preparar_manual,
)


class PruebasHidrogeoquimica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datos = normalizar_base(pd.read_csv(BASE,dtype={"informe":str}))
        cls.resultados = analizar(cls.datos)

    def test_conteos(self):
        self.assertEqual(len(self.datos),223)
        self.assertEqual(self.datos.id_muestra.nunique(),9)
        self.assertEqual(self.datos.grupo_punto.nunique(),4)

    def test_irca_39915(self):
        r=self.resultados.query("informe == '39915'").iloc[0]
        self.assertAlmostEqual(r.irca,69.8,places=1)
        self.assertAlmostEqual(r.irca_max,73.5,places=1)
        self.assertEqual(r.nivel,"Alto")

    def test_otros_informes(self):
        esperados={'39741':3.7,'39742':78.4,'39916':51.2,'40016':51.2,'40017':71.0}
        for inf, esperada in esperados.items():
            r=self.resultados[self.resultados.informe==inf].iloc[0]
            self.assertAlmostEqual(r.irca,esperada,places=1,msg=inf)

    def test_bicarbonato_balance(self):
        r=self.resultados[self.resultados.informe=='39915'].iloc[0]
        self.assertAlmostEqual(r.hco3_mg,24.42,places=1)
        self.assertAlmostEqual(r.error_balance_pct,-47.5,places=1)

    def test_csv_subido(self):
        archivo=leer_carga('datos.csv',BASE.read_bytes())
        r=normalizar_base(archivo)
        self.assertEqual(len(r),223)

    def test_excel_original(self):
        p=RAIZ/'Recursos_Hidrogeoquimica'/'SIAMS_fisicoquimicos_plantilla.xlsx'
        archivo=leer_carga('datos.xlsx',p.read_bytes())
        self.assertEqual(len(normalizar_base(archivo)),223)

    def test_duplicado_falla(self):
        muestra=self.datos.iloc[[0]].copy()
        with self.assertRaisesRegex(ValueError,"duplicados"):
            normalizar_base(pd.concat([muestra,muestra]))

    def test_unidad_nitratos_no_inferida(self):
        muestra=self.datos.iloc[[0]].copy()
        muestra['parametro']='nitratos_n'
        muestra['unidad']='mg/L NO3-'
        with self.assertRaisesRegex(ValueError,"Unidad incompatible"):
            normalizar_base(muestra)

    def test_ld_es_intervalo(self):
        x=self.datos[self.datos.informe=='39917']
        tabla, resumen=detalle_irca(x)
        self.assertAlmostEqual(resumen['irca'],3.1,places=1)
        self.assertAlmostEqual(resumen['irca_max'],56.2,places=1)
        self.assertGreater(len(tabla),0)

    def test_escenario_nitrato(self):
        a=analizar(self.datos,nitratos_en_no3=False)
        b=analizar(self.datos,nitratos_en_no3=True)
        self.assertEqual(a.shape,b.shape)
        # El escenario es efectivamente independiente y no muta la base.
        self.assertEqual(self.datos.loc[self.datos.parametro=='nitratos_n','unidad'].iloc[0],'mg/L N-NO3-')



if __name__=='__main__': unittest.main()
