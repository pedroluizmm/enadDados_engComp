"""Auditoria independente: releitura com csv/Counter/statistics dos arquivos oficiais."""
from collections import Counter
import csv
import io
import json
import math
import statistics
import zipfile

from preparar_2023 import ROOT, require, sha256, member


def verify_deep(root=ROOT):
    base = root/'resultados/tabelas'
    audit = json.loads((base/'validacao_aprofundamento_2023.json').read_text(encoding='utf-8'))
    for key in ['sha256_entradas', 'sha256_saidas', 'zip_sha256']:
        for name, digest in audit[key].items():
            require(sha256(root/name) == digest, f'Hash divergente: {name}')

    def read(path):
        with path.open(encoding='utf-8-sig', newline='') as f:
            return list(csv.DictReader(f, delimiter=';'))

    cadastro = read(root/'dados/tratados/2023/cadastro_comparaveis.csv')
    groups = {'UNIFOR': {r['CO_CURSO'] for r in cadastro if r['CO_CURSO']=='107689'},
              'privado_presencial': {r['CO_CURSO'] for r in cadastro},
              'privado_sem_unifor': {r['CO_CURSO'] for r in cadastro if r['CO_CURSO']!='107689'},
              'sem_fins_lucrativos': {r['CO_CURSO'] for r in cadastro if r['TP_CATEGORIA_ADMINISTRATIVA_IES_CENSO']=='5'},
              'universidades_privadas': {r['CO_CURSO'] for r in cadastro if r['CO_ORGACAD']=='10028'}}
    checks = Counter()

    def same(actual, expected, kind):
        require(math.isclose(float(actual), float(expected), abs_tol=1e-9), f'{kind}: {actual} != {expected}')
        checks[kind] += 1

    with zipfile.ZipFile(root/'dados/brutos/enade_2023/microdados_enade_2023.zip') as z:
        def raw(suffix):
            with z.open(member(z, suffix)) as f:
                return [r for r in csv.DictReader(io.TextIOWrapper(f, encoding='cp1252'), delimiter=';')
                        if r['NU_ANO']=='2023' and r['CO_CURSO'] in groups['privado_presencial']]

        b = raw('microdados2023_arq3.txt')
        v = [r for r in b if r['TP_PRES']=='555' and r['TP_PR_GER'] in ['333','555']
             and all(r[k] not in ['', '.'] for k in ['NT_GER','NT_FG','NT_CE'])]
        same(len(v), audit['n_notas'], 'denominadores')
        for row in read(base/'componentes_aprofundados_2023.csv'):
            values = [float(r[row['variavel']]) for r in v if r['CO_CURSO'] in groups[row['grupo']]
                      and r[row['variavel']] not in ['', '.']]
            q = statistics.quantiles(values, n=4, method='inclusive')
            for col, expected in [('n', len(values)), ('media', statistics.fmean(values)),
                                  ('mediana', statistics.median(values)), ('dp_amostral', statistics.stdev(values)),
                                  ('q1', q[0]), ('q3', q[2])]:
                same(row[col], expected, 'estatisticas')
        for row in read(base/'correlacoes_fg_ce_2023.csv'):
            records = [r for r in v if r['CO_CURSO'] in groups[row['grupo']]]
            same(row['n_pares'], len(records), 'denominadores')
            same(row['r_fg_ce'], statistics.correlation([float(r['NT_FG']) for r in records],
                                                       [float(r['NT_CE']) for r in records]), 'correlacoes_individuais')
        for row in read(base/'acertos_itens_2023.csv'):
            records = [r for r in v if r['CO_CURSO'] in groups[row['grupo']]]
            idx = int(row['posicao_vetor'])-1
            counts = Counter(r['DS_VT_ACE_O'+row['componente']][idx] for r in records)
            n = counts['0']+counts['1']
            for col, expected in [('n_respostas_validas', n), ('acertos', counts['1']),
                                  ('erros', counts['0']), ('excluidos', counts['8']+counts['9'])]:
                same(row[col], expected, 'itens')
            if n:
                same(row['percentual_acerto'], 100*counts['1']/n, 'itens')
            else:
                require(row['percentual_acerto']=='', 'Item excluído recebeu percentual')
        raw_q = {var: raw(f'microdados2023_arq{arq}.txt') for var, arq in
                 [('QE_I08',14), ('QE_I10',16), ('QE_I04',10), ('QE_I05',11), ('QE_I17',23)]}
        for filename, course_level in [('socioeconomico_grupos_2023.csv', False), ('socioeconomico_cursos_2023.csv', True)]:
            for row in read(base/filename):
                codes = {row['CO_CURSO']} if course_level else groups[row['grupo']]
                records = [r for r in raw_q[row['variavel']] if r['CO_CURSO'] in codes]
                answers = [r[row['variavel']] for r in records if r[row['variavel']] not in ['', '.']]
                count = answers.count(row['categoria'])
                for col, expected in [('n_arquivo', len(records)), ('n_respondentes', len(answers)),
                                      ('n_ausentes', len(records)-len(answers)), ('contagem', count)]:
                    same(row[col], expected, 'proporcoes_marginais')
                if answers:
                    same(row['percentual_respondentes'], 100*count/len(answers), 'proporcoes_marginais')
                else:
                    require(row['percentual_respondentes']=='', 'Sem respondentes recebeu percentual')
        for row in read(base/'indicadores_socioeconomicos_2023.csv'):
            records = [r for r in raw_q[row['variavel']] if r['CO_CURSO'] in groups[row['grupo']]]
            answers = [r[row['variavel']] for r in records if r[row['variavel']] not in ['', '.']]
            count = sum(a in row['categorias'].split('+') for a in answers)
            same(row['contagem'], count, 'indicadores')
            same(row['percentual'], 100*count/len(answers), 'indicadores')
        # Reconstrói os dados ecológicos SOMENTE depois de agregar cada arquivo por curso.
        grades = {}
        for course in groups['privado_presencial']:
            notes = [float(r['NT_GER']) for r in v if r['CO_CURSO']==course]
            if len(notes)>=10:
                grades[course] = statistics.fmean(notes)
        choices = {'QE_I08': ['A','B'], 'QE_I10': ['E'], 'QE_I04': ['E','F'],
                   'QE_I05': ['E','F'], 'QE_I17': ['A']}
        for row in read(base/'correlacoes_ecologicas_2023.csv'):
            var = row['variavel']
            pairs = []
            for course, grade in grades.items():
                answers = [r[var] for r in raw_q[var] if r['CO_CURSO']==course and r[var] not in ['', '.']]
                if len(answers)>=10:
                    pairs.append((sum(a in choices[var] for a in answers)/len(answers), grade))
            same(row['n_cursos'], len(pairs), 'ecologicas')
            same(row['r_agregado'], statistics.correlation([p[0] for p in pairs], [p[1] for p in pairs]), 'ecologicas')
    result = {'status': 'aprovado', 'origem': 'releitura ZIP oficial via csv, Counter e statistics',
              'verificacoes': dict(checks), 'total_verificacoes': sum(checks.values()),
              'hashes_entradas_saidas_brutos_conferidos': True,
              'sem_pareamento_individual_entre_arquivos': True}
    (base/'validacao_independente_aprofundamento_2023.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == '__main__':
    verify_deep()
