"""Regressões metodológicas: exclusão de itens e identidade interna do registro."""
import math
from pathlib import Path
import sys
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from aprofundar_2023 import item_records, pearson_checked


class DeepAnalysisTests(unittest.TestCase):
    def record(self):
        row = {'CO_CURSO': '107689'}
        for section, key in [('FG','DDBAECABE'), ('CE','BCADECE999BAEAD9ECABECBD9ECCA')]:
            hits = ''.join('1' if k in 'ABCDE' else k for k in key)
            row.update({f'DS_VT_GAB_O{section}_FIN': key, f'DS_VT_ESC_O{section}': key,
                        f'DS_VT_ACE_O{section}': hits, f'NU_ITEM_O{section}': len(key),
                        f'NU_ITEM_O{section}_Z': 0, f'NU_ITEM_O{section}_X': key.count('9'),
                        f'NU_ITEM_O{section}_N': 0, f'NT_OBJ_{section}': 100.0})
        return row

    def test_excluded_items_have_no_denominator_or_percentage(self):
        result, _ = item_records(pd.DataFrame([self.record()]), {'UNIFOR': {'107689'}})
        excluded = result[result.situacao.ne('valido')]
        self.assertEqual(len(excluded), 5)
        self.assertTrue(excluded.percentual_acerto.isna().all())
        self.assertTrue(excluded.n_respostas_validas.eq(0).all())
        self.assertEqual(excluded.questao_caderno.tolist(), [17,18,19,25,34])

    def test_inconsistent_answer_and_hit_stops_analysis(self):
        row = self.record()
        row['DS_VT_ESC_OFG'] = 'A'+row['DS_VT_ESC_OFG'][1:]
        with self.assertRaisesRegex(ValueError, 'Resposta/acerto'):
            item_records(pd.DataFrame([row]), {'UNIFOR': {'107689'}})

    def test_pearson_constant_or_insufficient_sample_is_undefined(self):
        self.assertTrue(math.isnan(pearson_checked([1,1,1], [2,3,4])))
        self.assertTrue(math.isnan(pearson_checked([1,2], [2,3])))
        self.assertAlmostEqual(pearson_checked([1,2,3], [3,2,1]), -1)


if __name__ == '__main__':
    unittest.main()
