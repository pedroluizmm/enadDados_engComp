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


def write_main(root=ROOT):
    """Reproduz somente a fonte editorial, sem recalcular tabelas ou estatísticas."""
    template=root/'DOCUMENT/modelos/main.tex'
    require(template.is_file(), 'Fonte editorial DOCUMENT/modelos/main.tex ausente')
    (root/'DOCUMENT/main.tex').write_text(template.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')


def update(root=ROOT):
    base = root / 'resultados/tabelas'
    validation = json.loads((base / 'validacao_analise_2023.json').read_text(encoding='utf-8'))
    require(validation['verificacoes_estatisticas_independentes'] > 0, 'Fase 2 não validada')
    for name, digest in validation['sha256_entradas'].items():
        require(sha256(root / 'dados/tratados/2023' / name) == digest, f'Entrada alterada: {name}')
    for name, digest in validation['sha256_saidas'].items():
        require(sha256(root / name) == digest, f'Saída alterada: {name}')
    from verificar_aprofundamento_2023 import verify_deep
    verify_deep(root)
    from auditoria_fg_2023 import verify_discursive
    verify_discursive(root)
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
    deep = pd.read_csv(base / 'componentes_aprofundados_2023.csv', sep=';').set_index(['grupo','variavel'])
    corr = pd.read_csv(base / 'correlacoes_fg_ce_2023.csv', sep=';').set_index('grupo')
    socio = pd.read_csv(base / 'indicadores_socioeconomicos_2023.csv', sep=';').set_index(['grupo','variavel'])
    diff = pd.read_csv(base / 'diferencas_componentes_2023.csv', sep=';').set_index(['grupo_referencia','variavel'])
    rows = []
    for group, label in [('UNIFOR','UNIFOR'), ('privado_sem_unifor','Demais privadas')]:
        for note, nlabel in NOTES.items():
            r = deep.loc[(group, note)]
            rows.append([label, nlabel, str(int(r.n)), number(r.media,2), number(r.mediana,2), number(r.dp_amostral,2)])
    (out/'resumo_componentes.tex').write_text(make_table(['Grupo','Nota','n','Média','Mediana','DP'], rows, 'llrrrr'), encoding='utf-8')
    rows = [[GROUPS.get(group, 'Demais privadas'), str(int(r.n_pares)), number(r.r_fg_ce,3)] for group,r in corr.iterrows()]
    (out/'correlacoes.tex').write_text(make_table(['Grupo','Pares no arq3','Pearson (r)'], rows, 'lrr'), encoding='utf-8')
    rows = []
    for note, label in [('NT_OBJ_FG','FG objetiva'), ('NT_DIS_FG','FG discursiva'), ('NT_OBJ_CE','CE objetiva'), ('NT_DIS_CE','CE discursiva')]:
        u, p = deep.loc[('UNIFOR',note)], deep.loc[('privado_sem_unifor',note)]
        rows.append([label, number(u.media,2), number(p.media,2), number(u.media-p.media,2)])
    (out/'partes_prova.tex').write_text(make_table(['Parte','UNIFOR','Demais privadas',r'$\Delta$ (pontos)'], rows, 'lrrr'), encoding='utf-8')
    values.update({'CorrelacaoUnifor': number(corr.loc['UNIFOR'].r_fg_ce,3),
                   'CorrelacaoPrivadas': number(corr.loc['privado_presencial'].r_fg_ce,3),
                   'CorrelacaoDemais': number(corr.loc['privado_sem_unifor'].r_fg_ce,3)})
    for note, key in [('NT_GER','Geral'), ('NT_FG','FG'), ('NT_CE','CE')]:
        values['Diferenca'+key] = number(diff.loc[('privado_sem_unifor',note)].diferenca_pontos,2)
    for var, key in [('QE_I08','Renda'), ('QE_I10','Trabalho'), ('QE_I04','Pai'), ('QE_I05','Mae'), ('QE_I17','Escola')]:
        values['PerfilUnifor'+key] = number(socio.loc[('UNIFOR',var)].percentual,1)
        values['PerfilDemais'+key] = number(socio.loc[('privado_sem_unifor',var)].percentual,1)
    # Os textos mais importantes também usam valores gerados, sem transcrição manual.
    for note, key in [('NT_OBJ_FG','ObjetivaFG'), ('NT_DIS_FG','DiscursivaFG'), ('NT_OBJ_CE','ObjetivaCE'), ('NT_DIS_CE','DiscursivaCE')]:
        for group, suffix in [('UNIFOR','Unifor'), ('privado_sem_unifor','Demais')]:
            values['Media'+key+suffix] = number(deep.loc[(group,note)].media,2)
    fg = pd.read_csv(base/'fg_discursiva_respostas_2023.csv', sep=';').set_index('grupo')
    for group,suffix in [('UNIFOR','Unifor'),('privado_sem_unifor','Demais')]:
        r = fg.loc[group]
        for col,key in [('n_brancos','Brancos'),('n_total','Total'),('n_nulos','Nulos'),
                        ('n_fora_tema','ForaTema'),('n_sem_brancos','SemBrancos'),('n_respostas_validas','RespostasValidas')]:
            values['FG'+key+suffix] = int(r[col])
        values['FGPercentualBrancos'+suffix] = number(r.percentual_brancos,1)
        values['FGMediaSemBrancos'+suffix] = number(r.media_sem_brancos,2)
        values['FGMediaRespostasValidas'+suffix] = number(r.media_respostas_validas,2)
    eco = pd.read_csv(base/'correlacoes_ecologicas_2023.csv',sep=';').set_index('variavel')
    values['EcoRenda'] = number(eco.loc['QE_I08'].r_agregado,3)
    values['EcoEscola'] = number(eco.loc['QE_I17'].r_agregado,3)
    values['EcoCursos'] = int(eco.loc['QE_I08'].n_cursos)
    values['MediaSemFinsCE'] = number(s.loc[('sem_fins_lucrativos','NT_CE')].media_participantes)
    (out / 'indicadores.tex').write_text('% Gerado dos CSVs validados. Não editar números manualmente.\n'
        + '\n'.join('\\newcommand{\\' + k + '}{' + str(v) + '}' for k, v in values.items()) + '\n', encoding='utf-8')
    print('Indicadores e seis tabelas LaTeX gerados de arquivos com hashes conferidos.')
    write_main(root)
    print('main.tex reproduzido da fonte editorial DOCUMENT/modelos/main.tex.')
    return values


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--somente-texto',action='store_true',help='Reproduz apenas o modelo, sem recalcular tabelas')
    args=parser.parse_args()
    write_main() if args.somente_texto else update()
