"""Evita confundir nota zero, branco e resposta com resultado válido."""
from pathlib import Path
import sys
import unittest

import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from auditoria_fg_2023 import summarize_discursive


class DiscursiveAuditTests(unittest.TestCase):
    def test_blank_and_nonblank_invalid_are_separate_from_valid_zero(self):
        v = pd.DataFrame({'CO_CURSO':['1']*5, 'TP_SFG_D1':[333,555,555,335,336],
                          'NT_DIS_FG':[0,0,40,0,9]})
        r = summarize_discursive(v,{'grupo':{'1'}}).iloc[0]
        self.assertEqual(r.n_brancos,1)
        self.assertEqual(r.n_sem_brancos,4)
        self.assertEqual(r.n_respostas_validas,2)
        self.assertEqual(r.n_nulos,1)
        self.assertEqual(r.n_fora_tema,1)
        self.assertAlmostEqual(r.media_todos,9.8)
        self.assertAlmostEqual(r.media_sem_brancos,12.25)
        self.assertAlmostEqual(r.media_respostas_validas,20)

    def test_unknown_status_stops_before_interpretation(self):
        v = pd.DataFrame({'CO_CURSO':['1'], 'TP_SFG_D1':[888], 'NT_DIS_FG':[0]})
        with self.assertRaisesRegex(ValueError,'Situação discursiva inesperada'):
            summarize_discursive(v,{'grupo':{'1'}})


if __name__=='__main__':
    unittest.main()
