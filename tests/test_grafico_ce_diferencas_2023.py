"""Regressões de dados e renderização da Figura 5, sem testes inferenciais."""
from pathlib import Path
import sys
import tempfile
import unittest

import matplotlib.pyplot as plt
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from grafico_ce_diferencas_2023 import prepare_comparison,render_ce_difference,EXCLUDED


class CEDifferenceTests(unittest.TestCase):
    def setUp(self):
        self.items=pd.read_csv(ROOT/'resultados/tabelas/acertos_itens_2023.csv',sep=';')

    def test_all_valid_differences_and_extremes(self):
        data=prepare_comparison(self.items)
        self.assertEqual(len(data),24)
        self.assertFalse(set(data.questao_caderno)&EXCLUDED)
        self.assertTrue(data.diferenca_pp.is_monotonic_decreasing)
        self.assertEqual(data.questao_caderno.iloc[:2].tolist(),[23,30])
        self.assertEqual(data.questao_caderno.iloc[-1],28)
        for _,row in data.iterrows():
            raw=self.items[(self.items.componente=='CE') & (self.items.questao_caderno==row.questao_caderno)].set_index('grupo')
            u=100*int(raw.loc['UNIFOR','acertos'])/25
            p=100*int(raw.loc['privado_sem_unifor','acertos'])/1178
            self.assertAlmostEqual(row.percentual_unifor,u)
            self.assertAlmostEqual(row.percentual_demais,p)
            self.assertAlmostEqual(row.diferenca_pp,u-p)

    def test_excluded_zero_is_rejected(self):
        self.items.loc[(self.items.componente=='CE') & self.items.questao_caderno.eq(17),'percentual_acerto']=0
        with self.assertRaisesRegex(ValueError,'Itens excluídos'):
            prepare_comparison(self.items)

    def test_changed_denominator_is_rejected(self):
        self.items.loc[(self.items.grupo=='UNIFOR') & (self.items.componente=='CE') & self.items.questao_caderno.eq(23),'n_respostas_validas']=24
        with self.assertRaisesRegex(ValueError,'Denominador inesperado'):
            prepare_comparison(self.items)

    def test_missing_pair_is_rejected(self):
        missing=self.items[~((self.items.grupo=='UNIFOR') & (self.items.componente=='CE') & self.items.questao_caderno.eq(23))]
        with self.assertRaisesRegex(ValueError,'29 itens'):
            prepare_comparison(missing)

    def test_render_is_independent_of_other_graph_styles(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as directory:
            dest=Path(directory)
            render_ce_difference(self.items,dest)
            first={p.name:p.read_bytes() for p in dest.glob('*')}
            with plt.rc_context({'axes.labelsize':42,'xtick.labelsize':30,'axes.facecolor':'pink'}):
                render_ce_difference(self.items,dest)
            self.assertEqual(first,{p.name:p.read_bytes() for p in dest.glob('*')})


if __name__=='__main__':
    unittest.main()
