"""Gera tabelas e indicadores LaTeX somente de resultados com hashes validados."""
import json
from pathlib import Path
from preparar_2023 import ROOT, require, sha256
import pandas as pd

GROUPS = {'UNIFOR': 'UNIFOR', 'privado_presencial': 'Privadas presenciais',
          'sem_fins_lucrativos': 'Sem fins lucrativos', 'universidades_privadas': 'Universidades privadas'}
NOTES = {'NT_GER': 'Geral', 'NT_FG': 'FG', 'NT_CE': 'CE'}


def number(x, decimals=3):
    return f'{x:.{decimals}f}'.replace('.', ',')


def make_table(headers, rows, spec):
    return '\\begin{tabular}{' + spec + '}\n\\toprule\n' + ' & '.join(headers) + r' \\' + '\n\\midrule\n' + '\n'.join(' & '.join(row) + r' \\' for row in rows) + '\n\\bottomrule\n\\end{tabular}\n'


def update(root=ROOT):
    base = root / 'resultados/tabelas'
    validation = json.loads((base / 'validacao_analise_2023.json').read_text(encoding='utf-8'))
    require(validation['verificacoes_estatisticas_independentes'] > 0, 'Fase 2 não validada')
    for name, digest in validation['sha256_entradas'].items():
        require(sha256(root / 'dados/tratados/2023' / name) == digest, f'Entrada alterada: {name}')
    for name, digest in validation['sha256_saidas'].items():
        require(sha256(root / name) == digest, f'Saída alterada: {name}')
    p = pd.read_csv(base / 'indicadores_participacao_2023.csv', sep=';').set_index('grupo')
    s = pd.read_csv(base / 'estatisticas_grupos_2023.csv', sep=';').set_index(['grupo', 'nota'])
    out = root / 'DOCUMENT/tabelas'
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for group, label in GROUPS.items():
        r = p.loc[group]
        rows.append([label] + [str(int(r[k])) for k in ['instituicoes','cursos','inscritos','n_validas']]
                    + [number(r[k], 2) for k in ['taxa_participacao_pct','taxa_ausencia_pct']])
    (out / 'participacao.tex').write_text(make_table(
        ['Grupo','IES','Cursos','Inscritos','Notas','Presença (\\%)','Ausência (\\%)'], rows, 'lrrrrrr'), encoding='utf-8')
    rows = []
    for group, label in GROUPS.items():
        for note, nlabel in NOTES.items():
            r = s.loc[(group, note)]
            rows.append([label, nlabel, str(int(r.n_notas)), number(r.media_participantes),
                         number(r.mediana_participantes), number(r.desvio_padrao_amostral)])
    (out / 'notas.tex').write_text(make_table(['Grupo','Nota','n','Média','Mediana','DP amostral'], rows, 'llrrrr'), encoding='utf-8')
    rows = []
    for group, label in GROUPS.items():
        r = s.loc[(group, 'NT_GER')]
        rows.append([label, str(int(r.n_cursos_com_notas)), number(r.media_participantes),
                     number(r.media_nao_ponderada_cursos), number(r.media_nao_ponderada_cursos_n10)])
    (out / 'ponderacao.tex').write_text(make_table(['Grupo','Cursos com nota','Ponderada','Igual por curso',r'Igual, $n\geq10$'], rows, 'lrrrr'), encoding='utf-8')
    universe, unifor = p.loc['privado_presencial'], p.loc['UNIFOR']
    values = {'TotalIES': int(universe.instituicoes), 'TotalCursos': int(universe.cursos),
              'TotalInscritos': int(universe.inscritos), 'TotalPresentes': int(universe.presentes),
              'TotalNotas': int(universe.n_validas), 'TotalSuprimidos': int(universe.suprimidos),
              'TotalAusentes': int(universe.ausentes), 'TotalOutros': int(universe.outros),
              'CursosComNotas': int(universe.cursos_com_notas), 'CursosDestaque': int(universe.cursos_n10),
              'UniforInscritos': int(unifor.inscritos), 'UniforNotas': int(unifor.n_validas),
              'UniforAusentes': int(unifor.ausentes),
              'TaxaParticipacao': number(universe.taxa_participacao_pct, 2),
              'TaxaAusencia': number(universe.taxa_ausencia_pct, 2),
              'TaxaUniforParticipacao': number(unifor.taxa_participacao_pct, 2),
              'TaxaUniforAusencia': number(unifor.taxa_ausencia_pct, 2),
              'MediaUniforGeral': number(s.loc[('UNIFOR','NT_GER')].media_participantes),
              'MediaPrivadasGeral': number(s.loc[('privado_presencial','NT_GER')].media_participantes),
              'MediaSemFinsGeral': number(s.loc[('sem_fins_lucrativos','NT_GER')].media_participantes),
              'MediaUniversidadesGeral': number(s.loc[('universidades_privadas','NT_GER')].media_participantes),
              'MediaCursosGeral': number(s.loc[('privado_presencial','NT_GER')].media_nao_ponderada_cursos),
              'MediaSemUniforGeral': number(s.loc[('privado_sem_unifor','NT_GER')].media_participantes),
              'NotasSemUnifor': int(p.loc['privado_sem_unifor'].n_validas),
              'TotalConferencias': validation['verificacoes_estatisticas_independentes']}
    (out / 'indicadores.tex').write_text('% Gerado dos CSVs validados. Não editar números manualmente.\n'
        + '\n'.join('\\newcommand{\\' + k + '}{' + str(v) + '}' for k, v in values.items()) + '\n', encoding='utf-8')
    print('Indicadores e três tabelas LaTeX gerados de arquivos com hashes conferidos.')
    return values


if __name__ == '__main__':
    update()
