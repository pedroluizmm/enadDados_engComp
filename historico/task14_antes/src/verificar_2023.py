"""Validação independente dos CSVs e hashes, sem associações individuais."""
import json
import pandas as pd
from preparar_2023 import ROOT, sha256


def verify(root=ROOT):
    out = root / 'dados/tratados/2023'
    s = json.loads((out / 'resumo_tecnico.json').read_text(encoding='utf-8'))
    a = pd.read_csv(out / 'enade_arq1_filtrado.csv', sep=';')
    b = pd.read_csv(out / 'enade_arq3_desempenho.csv', sep=';')
    c = pd.read_csv(out / 'cadastro_comparaveis.csv', sep=';')
    assert a.NU_ANO.eq(2023).all() and b.NU_ANO.eq(2023).all()
    assert a.CO_GRUPO.eq(6411).all() and a.CO_CATEGAD.isin([4, 5, 8]).all()
    assert a.CO_MODALIDADE.eq(1).all() and not c.CO_CURSO.duplicated().any()
    assert set(a.CO_CURSO) == set(b.CO_CURSO) == set(c.CO_CURSO)
    assert a.groupby('CO_CURSO').size().to_dict() == b.groupby('CO_CURSO').size().to_dict()
    assert c.CO_IES.nunique() == s['instituicoes'] and len(c) == s['cursos']
    expected = c.CO_CATEGAD.map({4: 4, 5: 5, 8: 5})
    found = c.VINCULO_CURSO_CENSO.eq('both')
    assert c.loc[found, 'TP_CATEGORIA_ADMINISTRATIVA_CENSO'].eq(expected[found]).all()
    assert c.TP_CATEGORIA_ADMINISTRATIVA_IES_CENSO.eq(expected).all()
    assert c.loc[found, 'TP_MODALIDADE_ENSINO_CENSO'].eq(1).all()
    for flag in ['IN_COMUNITARIA', 'IN_CONFESSIONAL']:
        assert c.loc[found, flag + '_CENSO'].eq(c.loc[found, flag + '_IES_CENSO']).all()
    assert c.DIVERGENCIA_INDICADORES.eq(0).all()
    usable = b.TP_PRES.eq(555) & b.TP_PR_GER.isin([333, 555]) & b[['NT_GER','NT_FG','NT_CE']].notna().all(axis=1)
    assert usable.astype(int).equals(b.IN_NOTA_VALIDA)
    assert b.loc[b.SITUACAO_RESULTADO.eq('ausente'), ['NT_GER','NT_FG','NT_CE']].isna().all().all()
    for course in b.loc[b.SITUACAO_RESULTADO.eq('suprimido_sigilo'), 'CO_CURSO']:
        rows = b[b.CO_CURSO.eq(course)]
        assert rows.TP_PRES.eq(555).sum() == 1 and rows.NT_GER.isna().all()
    assert len(a[a.CO_CURSO.eq(107689)]) == 30
    assert b.loc[b.CO_CURSO.eq(107689), 'IN_NOTA_VALIDA'].sum() == 25
    for name, info in s['verificacoes_csv'].items():
        assert sha256(out / name) == info['sha256'], name
    assert s['zip_antes'] == s['zip_depois']
    for name, info in s['zip_antes'].items():
        assert sha256(root / name) == info['sha256'], name
    print('FASE 1 APROVADA: filtros, chaves, notas, sigilo, UNIFOR, CSVs e ZIPs.')
    return s


if __name__ == '__main__':
    verify()
