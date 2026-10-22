"""Análise descritiva; joins institucionais somente depois da agregação por curso."""
import json
import math
from pathlib import Path
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from preparar_2023 import ROOT, sha256
from verificar_2023 import verify

NOTAS = ['NT_GER', 'NT_FG', 'NT_CE']
NOMES = {'NT_GER': 'Nota geral', 'NT_FG': 'Formação Geral', 'NT_CE': 'Componente Específico'}
LABELS = {'UNIFOR': 'UNIFOR', 'privado_presencial': 'Privadas presenciais',
          'sem_fins_lucrativos': 'Privadas sem fins lucrativos', 'universidades_privadas': 'Universidades privadas',
          'privado_sem_unifor': 'Privadas sem UNIFOR'}
SOURCE = 'Fonte: INEP, microdados ENADE/Censo 2023. Elaboração própria.'


def analyze(root=ROOT):
    verify(root)  # Não analisar saídas alteradas ou incompatíveis.
    data = root / 'dados/tratados/2023'
    tables, plots = root / 'resultados/tabelas', root / 'resultados/graficos'
    tables.mkdir(exist_ok=True, parents=True)
    plots.mkdir(exist_ok=True, parents=True)
    c = pd.read_csv(data / 'cadastro_comparaveis.csv', sep=';')
    a = pd.read_csv(data / 'enade_arq1_filtrado.csv', sep=';')
    b = pd.read_csv(data / 'enade_arq3_desempenho.csv', sep=';')
    v = b[b.IN_NOTA_VALIDA.eq(1)].copy()
    counts = b.groupby('CO_CURSO').agg(inscritos=('CO_CURSO', 'size'),
                                      presentes=('TP_PRES', lambda x: x.isin([555, 888]).sum()),
                                      presencas_validas_oficiais=('TP_PRES', lambda x: x.eq(555).sum()),
                                      ausentes=('SITUACAO_RESULTADO', lambda x: x.eq('ausente').sum()),
                                      suprimidos=('SITUACAO_RESULTADO', lambda x: x.eq('suprimido_sigilo').sum()),
                                      outros=('SITUACAO_RESULTADO', lambda x: x.eq('outro_resultado_nao_valido').sum()),
                                      n_validas=('IN_NOTA_VALIDA', 'sum'))
    # Primeiramente notas agregadas. Nunca se faz merge dos registros de estudantes.
    stats = v.groupby('CO_CURSO')[NOTAS].agg(['count', 'mean', 'median', 'std', 'sum'])
    stats.columns = ['_'.join(col) for col in stats.columns]
    courses = counts.join(stats).reset_index().merge(c, on='CO_CURSO', validate='one_to_one')
    assert len(courses) == len(c) and courses.inscritos.sum() == len(a)
    courses['DESTAQUE_N10'] = courses.n_validas.ge(10).astype(int)
    groups = {
        'UNIFOR': courses.CO_CURSO.eq(107689),
        'privado_presencial': pd.Series(True, index=courses.index),
        'sem_fins_lucrativos': courses.TP_CATEGORIA_ADMINISTRATIVA_IES_CENSO.eq(5),
        'universidades_privadas': courses.CO_ORGACAD.eq(10028),
        'privado_sem_unifor': courses.CO_CURSO.ne(107689),
    }
    rows, participation = [], []
    checks = 0
    for group, mask in groups.items():
        sub = courses[mask]
        raw = v[v.CO_CURSO.isin(sub.CO_CURSO)]  # Seleção por códigos, sem merge individual.
        students = b[b.CO_CURSO.isin(sub.CO_CURSO)]
        registered = int(sub.inscritos.sum())
        participation.append({'grupo': group, 'instituicoes': sub.CO_IES.nunique(), 'cursos': len(sub),
                              'cursos_com_notas': int(sub.n_validas.gt(0).sum()),
                              'cursos_n10': int(sub.n_validas.ge(10).sum()),
                              **{key: int(sub[key].sum()) for key in ['inscritos','presentes','presencas_validas_oficiais','ausentes','suprimidos','outros','n_validas']},
                              'taxa_participacao_pct': 100 * sub.presentes.sum() / registered,
                              'taxa_ausencia_pct': 100 * sub.ausentes.sum() / registered,
                              'taxa_notas_publicadas_pct': 100 * len(raw) / registered})
        assert registered == len(students)
        for note in NOTAS:
            values = raw[note].to_list()
            n = len(values)
            weighted = sub[note + '_sum'].sum() / n
            mean, median, sd = raw[note].mean(), raw[note].median(), raw[note].std(ddof=1)
            # Cálculos independentes pela biblioteca padrão, a partir das notas filtradas.
            assert math.isclose(mean, statistics.fmean(values), abs_tol=1e-10)
            assert math.isclose(median, statistics.median(values), abs_tol=1e-10)
            assert math.isclose(sd, statistics.stdev(values), abs_tol=1e-10)
            assert math.isclose(mean, weighted, abs_tol=1e-10)
            checks += 4
            rows.append({'grupo': group, 'nota': note, 'n_notas': n,
                         'n_cursos_com_notas': int(sub.n_validas.gt(0).sum()),
                         'media_participantes': mean, 'mediana_participantes': median,
                         'desvio_padrao_amostral': sd,
                         'media_nao_ponderada_cursos': sub[note + '_mean'].mean(),
                         'media_nao_ponderada_cursos_n10': sub.loc[sub.n_validas.ge(10), note + '_mean'].mean()})
    descriptive = pd.DataFrame(rows)
    participation = pd.DataFrame(participation)
    # Conferência independente das estatísticas de cada curso, incluindo amostras pequenas.
    for course, sub in v.groupby('CO_CURSO'):
        row = courses[courses.CO_CURSO.eq(course)].iloc[0]
        for note in NOTAS:
            assert math.isclose(row[note + '_mean'], statistics.fmean(sub[note]), abs_tol=1e-10)
            checks += 1
    assert courses.loc[courses.CO_CURSO.eq(107689), 'n_validas'].item() == 25
    for filename, frame in [('indicadores_participacao_2023.csv', participation),
                            ('estatisticas_grupos_2023.csv', descriptive),
                            ('estatisticas_cursos_2023.csv', courses)]:
        frame.to_csv(tables / filename, sep=';', index=False, encoding='utf-8-sig')
        reread = pd.read_csv(tables / filename, sep=';')
        pd.testing.assert_frame_equal(frame.reset_index(drop=True), reread, check_dtype=False,
                                      check_exact=False, rtol=1e-12, atol=1e-12)
    sns.set_theme(style='whitegrid', font_scale=1.05)
    palette = ['#146B8A', '#E99436', '#488767', '#7862A3']
    filenames = []

    def save(fig, name, note):
        fig.text(0.02, 0.015, SOURCE + '\n' + note, fontsize=9, va='bottom')
        fig.tight_layout(rect=(0, 0.09, 1, 0.96))
        fig.savefig(plots / name, dpi=170, facecolor='white', metadata={'Software': 'projeto-enade'})
        plt.close(fig)
        filenames.append(name)

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    for ax, note in zip(axes, NOTAS):
        # Sobreposição explicitada: UNIFOR integra a distribuição das privadas.
        ax.hist(v[note], bins=np.arange(0, 101, 10), density=True, alpha=.6, label=f'Privadas (n={len(v)})', color=palette[0])
        unifor = v.loc[v.CO_CURSO.eq(107689), note]
        ax.hist(unifor, bins=np.arange(0, 101, 10), density=True, histtype='step', linewidth=2.3,
                label=f'UNIFOR (n={len(unifor)})', color='#C25818')
        ax.set(title=NOMES[note], xlabel='Nota bruta (0–100)', ylabel='Densidade', xlim=(0, 100))
        ax.legend(fontsize=9)
    fig.suptitle('Distribuição das notas publicadas válidas — ENADE 2023', fontsize=15)
    save(fig, 'distribuicao_notas_2023.png', 'Universo privado presencial inclui a UNIFOR. Ausentes e suprimidos não entram nas notas.')

    selected = courses[courses.n_validas.ge(10)]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(selected.n_validas, selected.NT_GER_mean, color=palette[0], alpha=.7,
               label=f'Cursos com n ≥ 10 ({len(selected)} cursos)')
    u = selected[selected.CO_CURSO.eq(107689)].iloc[0]
    ax.scatter([u.n_validas], [u.NT_GER_mean], marker='*', s=240, color='#C25818', label='UNIFOR (n=25)', zorder=5)
    ax.annotate('UNIFOR', (u.n_validas, u.NT_GER_mean), xytext=(8, 9), textcoords='offset points')
    ax.set(xlabel='Notas publicadas válidas por curso (n)', ylabel='Média da nota geral (0–100)',
           ylim=(0, 100), title='Dispersão entre cursos privados presenciais — ENADE 2023')
    ax.legend()
    save(fig, 'dispersao_cursos_2023.png', f'Comparações destacadas usam n ≥ 10. Os {len(courses)-len(selected)} demais cursos permanecem nas tabelas gerais.')

    fig, ax = plt.subplots(figsize=(12, 6))
    chart = descriptive[~descriptive.grupo.eq('privado_sem_unifor')].copy()
    chart['grupo_rotulo'] = chart.grupo.map({g: f'{LABELS[g]}\n(n={int(participation.set_index("grupo").loc[g,"n_validas"])})' for g in groups})
    chart['componente'] = chart.nota.map(NOMES)
    sns.barplot(chart, x='grupo_rotulo', y='media_participantes', hue='componente', ax=ax,
                palette=palette[:3], errorbar=None)
    ax.set(xlabel='', ylabel='Média ponderada por participantes (0–100)', ylim=(0, 100),
           title='Médias das notas publicadas válidas — ENADE 2023')
    ax.legend(title='Componente', ncols=3, fontsize=9, loc='upper center')
    save(fig, 'medias_grupos_2023.png', 'Grupos se sobrepõem e incluem a UNIFOR. Comparação descritiva, sem teste de significância ou ajuste de perfil.')

    fig, ax = plt.subplots(figsize=(11, 5.5))
    p = participation.set_index('grupo').loc[['UNIFOR', 'privado_presencial']]
    left = np.zeros(len(p))
    for key, label, color in [('n_validas','Nota publicada válida',palette[0]), ('suprimidos','Suprimido por sigilo',palette[2]),
                               ('ausentes','Ausente',palette[1]), ('outros','Eliminado/outro','#8D8D8D')]:
        vals = p[key] / p.inscritos * 100
        ax.barh([f'{LABELS[g]} (N={int(p.loc[g,"inscritos"])})' for g in p.index], vals,
                left=left, label=label, color=color)
        for i, value in enumerate(vals):
            if value > 5:
                ax.text(left[i] + value/2, i, f'{value:.1f}%', ha='center', va='center', color='white', fontweight='bold')
        left += vals.to_numpy()
    ax.set(xlabel='Percentual dos inscritos (%)', xlim=(0, 100), title='Situação dos inscritos — ENADE 2023')
    ax.legend(loc='upper center', bbox_to_anchor=(.5, -.14), ncols=2, fontsize=9)
    # Reserva extra para legenda e fonte.
    fig.subplots_adjust(left=.32, right=.98, top=.87, bottom=.32)
    fig.text(.02, .015, SOURCE + '\nPresença válida oficial inclui os suprimidos. Ausência inclui TP_PRES=222 e 444.', fontsize=9)
    fig.savefig(plots / 'participacao_2023.png', dpi=170, facecolor='white')
    plt.close(fig)
    filenames.append('participacao_2023.png')
    result = {'participacao': participation.to_dict('records'), 'estatisticas': descriptive.to_dict('records'),
              'verificacoes_estatisticas_independentes': checks,
              'graficos': filenames, 'notebook_kernel': str(Path(__import__('sys').executable)),
              'sha256_entradas': {p.name: sha256(p) for p in data.glob('*.csv')},
              'sha256_saidas': {str(p.relative_to(root)): sha256(p) for p in list(tables.glob('*_2023.csv')) + [plots / f for f in filenames]}}
    (tables / 'validacao_analise_2023.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'FASE 2: {checks} verificações estatísticas; {len(filenames)} gráficos e 3 tabelas validados.')
    return {'cursos': courses, 'participacao': participation, 'estatisticas': descriptive, 'validacao': result}


if __name__ == '__main__':
    analyze()
