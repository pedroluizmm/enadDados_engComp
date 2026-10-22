"""Correção TASK 13: não resposta e notas da única discursiva de FG, no arq3."""
import csv
import io
import json
import math
import statistics
import zipfile

import pandas as pd

from preparar_2023 import ROOT, member, require, sha256


def summarize_discursive(v, groups):
    rows = []
    for group, codes in groups.items():
        sub = v[v.CO_CURSO.astype(str).isin(codes)].copy()
        status = pd.to_numeric(sub.TP_SFG_D1, errors='raise')
        scores = pd.to_numeric(sub.NT_DIS_FG, errors='raise')
        require(status.isin([333, 335, 336, 555]).all() and scores.notna().all(),
                'Situação discursiva inesperada entre notas publicadas')
        require(scores[status.eq(333)].eq(0).all(), 'Questão em branco com nota não zero')
        n = len(sub)
        no_blank, valid = scores[status.ne(333)], scores[status.eq(555)]
        rows.append({'grupo': group, 'n_total': n, 'n_brancos': int(status.eq(333).sum()),
                     'percentual_brancos': 100*status.eq(333).sum()/n,
                     'n_nulos': int(status.eq(335).sum()), 'n_fora_tema': int(status.eq(336).sum()),
                     'n_sem_brancos': len(no_blank), 'n_respostas_validas': len(valid),
                     'media_todos': scores.mean(), 'media_sem_brancos': no_blank.mean(),
                     'media_respostas_validas': valid.mean()})
    return pd.DataFrame(rows)


def verify_discursive(root=ROOT):
    """Reprodução independente por csv/statistics, sem usar a função Pandas acima."""
    from aprofundar_2023 import group_codes
    c = pd.read_csv(root/'dados/tratados/2023/cadastro_comparaveis.csv', sep=';', dtype='string')
    groups = group_codes(c)
    table = pd.read_csv(root/'resultados/tabelas/fg_discursiva_respostas_2023.csv', sep=';').set_index('grupo')
    with zipfile.ZipFile(root/'dados/brutos/enade_2023/microdados_enade_2023.zip') as z:
        with z.open(member(z, 'microdados2023_arq3.txt')) as f:
            raw = [r for r in csv.DictReader(io.TextIOWrapper(f, encoding='cp1252'), delimiter=';')
                   if r['NU_ANO']=='2023' and r['CO_CURSO'] in groups['privado_presencial']
                   and r['TP_PRES']=='555' and r['TP_PR_GER'] in ['333','555']
                   and all(r[k] not in ['', '.'] for k in ['NT_GER','NT_FG','NT_CE'])]
    checks = 0
    for group, codes in groups.items():
        records = [r for r in raw if r['CO_CURSO'] in codes]
        count = lambda code: sum(r['TP_SFG_D1']==code for r in records)
        no_blank = [float(r['NT_DIS_FG']) for r in records if r['TP_SFG_D1']!='333']
        valid = [float(r['NT_DIS_FG']) for r in records if r['TP_SFG_D1']=='555']
        expected = {'n_total': len(records), 'n_brancos': count('333'),
                    'percentual_brancos': 100*count('333')/len(records),
                    'n_nulos': count('335'), 'n_fora_tema': count('336'),
                    'n_sem_brancos': len(no_blank), 'n_respostas_validas': len(valid),
                    'media_todos': statistics.fmean(float(r['NT_DIS_FG']) for r in records),
                    'media_sem_brancos': statistics.fmean(no_blank),
                    'media_respostas_validas': statistics.fmean(valid)}
        for key, value in expected.items():
            require(math.isclose(float(table.loc[group, key]), value, abs_tol=1e-10), f'FG discursiva: {group}/{key}')
            checks += 1
    result = {'status': 'aprovado', 'conferencias_independentes': checks,
              'definicoes': {'brancos': 'TP_SFG_D1=333', 'sem_brancos': 'TP_SFG_D1!=333',
                            'respostas_validas': 'TP_SFG_D1=555; exclui também 335 e 336'},
              'fonte': 'Releitura do arq3 oficial, csv/statistics; sem vínculos entre arquivos',
              'ressalva_336': 'Há três notas publicadas positivas em código 336 (9, 11 e 14). Valores preservados, sem recodificação.',
              'sha256_tabela': sha256(root/'resultados/tabelas/fg_discursiva_respostas_2023.csv')}
    (root/'resultados/tabelas/validacao_fg_discursiva_2023.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'FG discursiva: {checks} conferências independentes aprovadas.')
    return result


def refresh_presentation(root=ROOT):
    """Regenera apenas apresentação e correção requerida; conserva tabelas aprovadas."""
    from aprofundar_2023 import group_codes, plot_all
    base = root/'resultados/tabelas'
    audit_path = base/'validacao_aprofundamento_2023.json'
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    for key in ['sha256_entradas', 'sha256_saidas', 'zip_sha256']:
        for name, digest in audit[key].items():
            require(sha256(root/name)==digest, f'Entrada/saída anterior alterada: {name}')
    protected = {p.name: sha256(p) for p in base.glob('*.csv') if p.name!='fg_discursiva_respostas_2023.csv'}
    v = pd.read_csv(root/'dados/tratados/2023/aprofundamento/enade_arq3_itens.csv', sep=';', dtype={'CO_CURSO': str})
    v = v[v.IN_NOTA_VALIDA.eq(1)].copy()
    c = pd.read_csv(root/'dados/tratados/2023/cadastro_comparaveis.csv', sep=';', dtype='string')
    diagnostic = summarize_discursive(v, group_codes(c))
    diagnostic.to_csv(base/'fg_discursiva_respostas_2023.csv', sep=';', index=False, encoding='utf-8-sig')
    verify_discursive(root)
    names = plot_all(v, pd.read_csv(base/'componentes_aprofundados_2023.csv', sep=';'),
                     pd.read_csv(base/'acertos_itens_2023.csv', sep=';'),
                     pd.read_csv(base/'indicadores_socioeconomicos_2023.csv', sep=';'), root/'resultados/graficos')
    audit['graficos'] = names
    for name in names:
        path = root/'resultados/graficos'/name
        audit['sha256_saidas'][str(path.relative_to(root))] = sha256(path)
    table = base/'fg_discursiva_respostas_2023.csv'
    audit['sha256_saidas'][str(table.relative_to(root))] = sha256(table)
    audit['revisao_task13'] = 'Apresentação regenerada a partir das tabelas aprovadas; diagnóstico discursivo conferido no arq3.'
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    require(protected == {p.name: sha256(p) for p in base.glob('*.csv') if p.name!='fg_discursiva_respostas_2023.csv'},
            'Tabela aprovada alterada durante revisão visual')
    print('Apresentação atualizada; tabelas anteriores preservadas byte a byte.')
    return diagnostic


if __name__=='__main__':
    refresh_presentation()
