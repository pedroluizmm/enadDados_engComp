"""TASK 09–10: itens no próprio arq3 e perfis marginais, sem pareamento entre arquivos."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import statistics
import sys
import zipfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from preparar_2023 import ROOT, ARQ3, dictionary, read_filtered, require, sha256, valid_scores
from verificar_2023 import verify

GROUPS = {
    'UNIFOR': 'UNIFOR', 'privado_presencial': 'Privadas presenciais',
    'sem_fins_lucrativos': 'Sem fins lucrativos',
    'universidades_privadas': 'Universidades privadas',
    'privado_sem_unifor': 'Privadas sem UNIFOR',
}
SOCIO = {'QE_I08': 14, 'QE_I10': 16, 'QE_I04': 10, 'QE_I05': 11, 'QE_I17': 23}
INDICATORS = {
    'QE_I08': ('Renda familiar até 3 salários mínimos', ['A', 'B']),
    'QE_I10': ('Trabalho: 40 horas semanais ou mais', ['E']),
    'QE_I04': ('Pai com graduação ou pós-graduação', ['E', 'F']),
    'QE_I05': ('Mãe com graduação ou pós-graduação', ['E', 'F']),
    'QE_I17': ('Ensino médio todo em escola pública', ['A']),
}
EXTRA = [f'NU_ITEM_O{s}{t}' for s in ['FG', 'CE'] for t in ['', '_Z', '_X', '_N']]
EXTRA += [f'DS_VT_{kind}_O{s}{end}' for s in ['FG', 'CE']
          for kind, end in [('GAB', '_FIN'), ('ESC', ''), ('ACE', '')]]
COLOR_U, COLOR_P = '#C15B20', '#176783'
SOURCE = 'Fonte: INEP, microdados ENADE/Censo 2023; elaboração própria.'


def group_codes(c):
    return {
        'UNIFOR': set(c.loc[c.CO_CURSO.eq('107689'), 'CO_CURSO']),
        'privado_presencial': set(c.CO_CURSO),
        'sem_fins_lucrativos': set(c.loc[c.TP_CATEGORIA_ADMINISTRATIVA_IES_CENSO.eq('5'), 'CO_CURSO']),
        'universidades_privadas': set(c.loc[c.CO_ORGACAD.eq('10028'), 'CO_CURSO']),
        'privado_sem_unifor': set(c.loc[c.CO_CURSO.ne('107689'), 'CO_CURSO']),
    }


def pearson_checked(x, y):
    """Pandas conferido pela fórmula de covariância com biblioteca padrão."""
    x, y = list(map(float, x)), list(map(float, y))
    if len(x) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return float('nan')
    mx, my = statistics.fmean(x), statistics.fmean(y)
    manual = sum((a-mx)*(b-my) for a, b in zip(x, y)) / math.sqrt(
        sum((a-mx)**2 for a in x) * sum((b-my)**2 for b in y))
    result = pd.Series(x).corr(pd.Series(y), method='pearson')
    require(math.isclose(result, manual, abs_tol=1e-12), 'Correlação não reconciliada')
    return float(result)


def item_records(v, groups):
    """Só contabiliza 0/1; 8/9 são exclusões, jamais erro ou acerto."""
    rows, audit = [], {}
    for section, length in [('FG', 9), ('CE', 29)]:
        ace, gab, esc = (f'DS_VT_ACE_O{section}', f'DS_VT_GAB_O{section}_FIN', f'DS_VT_ESC_O{section}')
        require(v[gab].nunique() == 1, 'Gabaritos diferentes no mesmo grupo/edição')
        key = v[gab].iloc[0]
        require(len(key) == length, 'Tamanho de gabarito inesperado')
        # Gabarito definitivo oficial de Engenharia da Computação 2023,
        # consultado em 18/10/2026. O arq3 substitui os itens excluídos por 9.
        published = {'FG': 'DDBAECABE', 'CE': 'BCADECEDBBBAEADDECABECBDCECCA'}[section]
        require(len(published) == length and all(a == p or a in '89XZ' for a, p in zip(key, published)),
                'Sequência incompatível com o gabarito oficial da área')
        for _, r in v.iterrows():
            require(all(pd.notna(r[k]) and len(r[k]) == length for k in [ace, gab, esc]),
                    'Vetor ausente ou com tamanho incorreto em nota publicada')
            expected_valid = length - sum(int(r[f'NU_ITEM_O{section}_{k}']) for k in ['Z', 'X', 'N'])
            require(int(r[f'NU_ITEM_O{section}']) == length, 'Número de itens inconsistente')
            require(sum(a in '01' for a in r[ace]) == expected_valid, 'Exclusões não reconciliadas')
            for answer, correct, hit in zip(r[esc], r[gab], r[ace]):
                if correct in 'ABCDE':
                    require(hit in '01' and int(hit) == int(answer == correct), 'Resposta/acerto divergentes')
                else:
                    require(correct in '89XZ' and hit == {'X': '9', 'Z': '8'}.get(correct, correct),
                            'Exclusão divergente')
            reconstructed = 100 * r[ace].count('1') / expected_valid
            require(abs(reconstructed-float(r[f'NT_OBJ_{section}'])) <= .051,
                    'Nota objetiva não reconciliada com vetor de acertos')
        audit[section] = {'itens_totais': length, 'gabarito_final': key,
                          'posicoes_excluidas': [i+1 for i, k in enumerate(key) if k not in 'ABCDE'],
                          'registros_conferidos': len(v)}
        for group, codes in groups.items():
            sub = v[v.CO_CURSO.isin(codes)]
            for i in range(length):
                counts = Counter(s[i] for s in sub[ace])
                n = counts['0'] + counts['1']
                rows.append({'grupo': group, 'componente': section, 'posicao_vetor': i+1,
                             'questao_caderno': i+1 if section=='FG' else i+10,
                             'gabarito_final': key[i], 'situacao': 'valido' if key[i] in 'ABCDE' else 'excluido_discriminacao' if key[i] in '9X' else 'anulado',
                             'n_base_notas': len(sub), 'n_respostas_validas': n,
                             'acertos': counts['1'], 'erros': counts['0'],
                             'excluidos': counts['8']+counts['9'],
                             'percentual_acerto': 100*counts['1']/n if n else np.nan})
    return pd.DataFrame(rows), audit


def analyze(root=ROOT, chunksize=50000):
    require(chunksize > 0, 'chunksize deve ser positivo')
    verify(root)
    out = root / 'dados/tratados/2023/aprofundamento'
    tables, plots = root / 'resultados/tabelas', root / 'resultados/graficos'
    out.mkdir(parents=True, exist_ok=True)
    c = pd.read_csv(root/'dados/tratados/2023/cadastro_comparaveis.csv', sep=';', dtype='string')
    groups = group_codes(c)
    raw_paths = [root/'dados/brutos/enade_2023/microdados_enade_2023.zip',
                 root/'dados/brutos/censo_2023/microdados_censo_da_educacao_superior_2023.zip']
    before = {str(p.relative_to(root)): sha256(p) for p in raw_paths}
    counts, qfiles = {}, {}
    with zipfile.ZipFile(raw_paths[0]) as z:
        definitions = dictionary(z, True)
        d = next(iter(definitions['abas'].values()))
        for var in list(SOCIO)+EXTRA:
            require(var in d, f'Variável sem definição oficial: {var}')
        b = read_filtered(z, 'microdados2023_arq3.txt', ARQ3+EXTRA,
                          lambda f: f.NU_ANO.eq('2023') & f.CO_CURSO.isin(c.CO_CURSO), chunksize, counts)
        for col in ARQ3:
            if col.startswith('NT_'):
                b[col] = pd.to_numeric(b[col].str.replace(',', '.', regex=False), errors='raise')
        b['IN_NOTA_VALIDA'] = valid_scores(b).astype(int)
        # A releitura inteira do arq3 conserva notas, vetores e respostas NA MESMA linha.
        old = pd.read_csv(root/'dados/tratados/2023/enade_arq3_desempenho.csv', sep=';')
        for col in ['NT_GER', 'NT_FG', 'NT_CE']:
            np.testing.assert_allclose(b[col].to_numpy(dtype=float, na_value=np.nan), old[col], equal_nan=True)
        require(b.CO_CURSO.tolist() == old.CO_CURSO.astype(str).tolist(), 'Releitura do arq3 alterou registros')
        for var, arq in SOCIO.items():
            q = read_filtered(z, f'microdados2023_arq{arq}.txt', ['NU_ANO', 'CO_CURSO', var],
                              lambda f: f.NU_ANO.eq('2023') & f.CO_CURSO.isin(c.CO_CURSO), chunksize, counts)
            require(q.groupby('CO_CURSO').size().to_dict() == b.groupby('CO_CURSO').size().to_dict(),
                    f'Cobertura por curso divergente: {var}')
            qfiles[var] = q  # Mantidos separados: não há identidade comum aos arquivos.
    v = b[b.IN_NOTA_VALIDA.eq(1)].copy()
    correlations, components, differences = [], [], []
    for group, codes in groups.items():
        sub = v[v.CO_CURSO.isin(codes)]
        correlations.append({'grupo': group, 'metodo': 'Pearson', 'n_pares': len(sub),
                             'r_fg_ce': pearson_checked(sub.NT_FG, sub.NT_CE),
                             'nivel': 'individual_mesmo_arq3'})
        for col in ['NT_GER', 'NT_FG', 'NT_CE', 'NT_OBJ_FG', 'NT_DIS_FG', 'NT_OBJ_CE', 'NT_DIS_CE']:
            vals = sub[col].dropna().astype(float)
            mean, sd = statistics.fmean(vals), statistics.stdev(vals)
            require(math.isclose(mean, vals.mean(), abs_tol=1e-10), 'Média inconsistente')
            require(math.isclose(sd, vals.std(), abs_tol=1e-10), 'Dispersão inconsistente')
            components.append({'grupo': group, 'variavel': col, 'n': len(vals), 'media': mean,
                               'mediana': statistics.median(vals), 'dp_amostral': sd,
                               'q1': vals.quantile(.25), 'q3': vals.quantile(.75)})
    comp = pd.DataFrame(components)
    for group in groups:
        if group == 'UNIFOR':
            continue
        for col in comp.variavel.unique():
            u = comp[(comp.grupo=='UNIFOR') & (comp.variavel==col)].iloc[0]
            ref = comp[(comp.grupo==group) & (comp.variavel==col)].iloc[0]
            differences.append({'grupo_referencia': group, 'variavel': col,
                                'n_unifor': int(u.n), 'n_referencia': int(ref.n),
                                'media_unifor': u.media, 'media_referencia': ref.media,
                                'diferenca_pontos': u.media-ref.media})
    # Valida os pesos publicados; o erro permitido decorre de arredondamento a uma casa.
    weighting = {}
    for name, observed, predicted in [
        ('geral', v.NT_GER, .25*v.NT_FG+.75*v.NT_CE),
        # A NT 12/2024 corrige os pesos desatualizados na descrição do XLSX.
        ('fg', v.NT_FG, .65*v.NT_OBJ_FG+.35*v.NT_DIS_FG),
        ('ce', v.NT_CE, .90*v.NT_OBJ_CE+.10*v.NT_DIS_CE)]:
        error = float((observed-predicted).abs().max())
        require(error <= .101, f'Pesos oficiais incompatíveis: {name}')
        weighting[name] = error
    items, audit = item_records(v, groups)
    socio_rows, course_rows, indicators, labels = [], [], [], {}
    for var, q in qfiles.items():
        labels[var] = {code: label for line in d[var].get('texto_dominio', [])
                       for code, label in re.findall(r'(?:^|\n)\s*([A-Z])\s*=\s*([^\n]+)', line)}
        require(bool(labels[var]), f'Domínio categórico ausente: {var}')
        require(q[var].dropna().isin(labels[var]).all(), f'Resposta fora do domínio: {var}')
        # Calcula cada marginal por curso antes de qualquer relação com notas.
        for course, rows in q.groupby('CO_CURSO'):
            n = int(rows[var].notna().sum())
            for code, label in labels[var].items():
                count = int(rows[var].eq(code).sum())
                course_rows.append({'CO_CURSO': course, 'variavel': var, 'categoria': code,
                                    'rotulo': label, 'n_arquivo': len(rows), 'n_respondentes': n,
                                    'n_ausentes': len(rows)-n, 'contagem': count,
                                    'percentual_respondentes': 100*count/n if n else np.nan})
        for group, codes in groups.items():
            sub = q[q.CO_CURSO.isin(codes)]
            answers = sub[var].dropna().tolist()
            n, counter = len(answers), Counter(answers)
            require(sum(counter.values()) == n, 'Denominador socioeconômico inconsistente')
            for code, label in labels[var].items():
                socio_rows.append({'grupo': group, 'variavel': var, 'arquivo': f'arq{SOCIO[var]}',
                                   'categoria': code, 'rotulo': label, 'n_arquivo': len(sub),
                                   'n_respondentes': n, 'n_ausentes': len(sub)-n,
                                   'contagem': counter[code], 'percentual_respondentes': 100*counter[code]/n if n else np.nan})
            label, selected = INDICATORS[var]
            hit = sum(counter[k] for k in selected)
            # Conferência independente, percorrendo as respostas originais.
            require(hit == sum(answer in selected for answer in answers), 'Proporção não reconciliada')
            indicators.append({'grupo': group, 'variavel': var, 'indicador': label,
                               'categorias': '+'.join(selected), 'contagem': hit, 'n_respondentes': n,
                               'n_ausentes': len(sub)-n, 'n_arquivo': len(sub),
                               'percentual': 100*hit/n if n else np.nan})
    socio = pd.DataFrame(socio_rows)
    bycourse = pd.DataFrame(course_rows)
    indicator = pd.DataFrame(indicators)
    correlations = pd.DataFrame(correlations)
    differences = pd.DataFrame(differences)
    # Extra complementar: associação ECOLÓGICA, com pelo menos 10 notas e respostas.
    ecology, ecology_data = [], []
    grade_means = v.groupby('CO_CURSO').agg(n_notas=('NT_GER', 'size'), media_geral=('NT_GER', 'mean'))
    for var, (label, selected) in INDICATORS.items():
        marginal = bycourse[(bycourse.variavel==var) & bycourse.categoria.isin(selected)]
        marginal = marginal.groupby('CO_CURSO').agg(contagem=('contagem', 'sum'), n_respondentes=('n_respondentes', 'first'))
        joined = grade_means.join(marginal, how='inner', validate='one_to_one')
        joined = joined[(joined.n_notas>=10) & (joined.n_respondentes>=10)].copy()
        joined['proporcao'] = joined.contagem/joined.n_respondentes
        joined['variavel'] = var
        ecology_data.append(joined.reset_index())
        ecology.append({'variavel': var, 'indicador': label, 'n_cursos': len(joined), 'metodo': 'Pearson',
                        'r_agregado': pearson_checked(joined.proporcao, joined.media_geral),
                        'unidade': 'curso', 'peso': 'igual_por_curso', 'min_notas_respostas': 10})
    frames = {'componentes_aprofundados_2023.csv': comp, 'diferencas_componentes_2023.csv': differences,
              'correlacoes_fg_ce_2023.csv': correlations, 'acertos_itens_2023.csv': items,
              'socioeconomico_grupos_2023.csv': socio, 'socioeconomico_cursos_2023.csv': bycourse,
              'indicadores_socioeconomicos_2023.csv': indicator,
              'correlacoes_ecologicas_2023.csv': pd.DataFrame(ecology),
              'dados_ecologicos_cursos_2023.csv': pd.concat(ecology_data, ignore_index=True)}
    for name, f in frames.items():
        f.to_csv(tables/name, sep=';', index=False, encoding='utf-8-sig')
        pd.testing.assert_frame_equal(f.reset_index(drop=True).astype({'CO_CURSO': str}) if 'CO_CURSO' in f else f,
                                      pd.read_csv(tables/name, sep=';', dtype={'CO_CURSO': str}),
                                      check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-12)
    b.to_csv(out/'enade_arq3_itens.csv', sep=';', index=False, encoding='utf-8-sig')
    for var, q in qfiles.items():
        q.to_csv(out/f'{var}.csv', sep=';', index=False, encoding='utf-8-sig')
    (out/'dicionario_variaveis.json').write_text(json.dumps({k: d[k] for k in list(SOCIO)+EXTRA}, ensure_ascii=False, indent=2), encoding='utf-8')
    names = plot_all(v, comp, items, indicator, plots)
    require(before == {str(p.relative_to(root)): sha256(p) for p in raw_paths}, 'Dados originais alterados')
    bonus = {year: [str(p.relative_to(root)) for p in (root/f'dados/brutos/{year}').rglob('*')
                   if p.is_file() and p.stat().st_size] for year in ['enade_2021', 'censo_2021']}
    result = {'status': 'aprovado', 'python': sys.executable, 'leitura': counts,
              'n_notas': len(v), 'n_pares_mesmo_arq3': len(v), 'auditoria_itens': audit,
              'erro_maximo_ponderacao': weighting, 'zip_sha256': before, 'zip_intactos': True,
              'bonus_2021': {'arquivos_locais': bonus, 'status': 'pendente_sem_microdados' if not all(bonus.values()) else 'requer_avaliacao'},
              'graficos': names, 'posicoes_vetores': 'FG posições 1–9 = questões 1–9; CE posições 1–29 = questões 10–38. Sequência validada com gabarito oficial.',
              'divergencia_dicionario': 'Pesos FG 60/40 e CE 85/15 no XLSX incompatíveis com as notas. Usados FG 65/35 e CE 90/10, conforme NT 12/2024.',
              'sha256_entradas': {str(p.relative_to(root)): sha256(p) for p in (root/'dados/tratados/2023').glob('*.csv')},
              'sha256_saidas': {str(p.relative_to(root)): sha256(p) for p in
                                [tables/name for name in frames] + list(out.glob('*')) + [plots/name for name in names]}}
    (tables/'validacao_aprofundamento_2023.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Aprofundamento aprovado: {len(v)} pares; 9 FG + 24 CE válidos; 5 marginais socioeconômicas; {len(names)} arquivos de figuras.')
    return {'componentes': comp, 'correlacoes': correlations, 'diferencas': differences, 'itens': items,
            'socioeconomico': socio, 'indicadores': indicator, 'ecologicas': pd.DataFrame(ecology), 'validacao': result}


def plot_all(v, comp, items, indicator, plots):
    sns.set_theme(style='whitegrid', context='notebook', font_scale=1.25)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.titleweight': 'bold', 'pdf.fonttype': 42})
    names = []

    def save(fig, stem, note):
        fig.text(.02, .012, SOURCE+'\n'+note, fontsize=11, va='bottom')
        fig.tight_layout(rect=(0, .15 if fig.get_figheight()<7 else .10, 1, .99))
        for ext in ['png', 'pdf']:
            name = stem+'.'+ext
            fig.savefig(plots/name, dpi=300, facecolor='white',
                        metadata={'Creator': 'projeto-enade', 'CreationDate': None, 'ModDate': None} if ext=='pdf' else None)
            names.append(name)
        plt.close(fig)

    labels = {'NT_GER': 'Nota geral', 'NT_FG': 'Formação Geral', 'NT_CE': 'Componente Específico'}
    fig, ax = plt.subplots(figsize=(9, 6.4))
    keys = ['UNIFOR', 'privado_presencial', 'sem_fins_lucrativos', 'universidades_privadas']
    for j, (group, color) in enumerate(zip(keys, [COLOR_U, COLOR_P, '#39835A', '#7963A6'])):
        sub = comp[(comp.grupo==group) & comp.variavel.isin(labels)].set_index('variavel').loc[list(labels)]
        yy = np.arange(3)+(j-1.5)*.16
        ax.scatter(sub.media, yy, s=65, color=color, label=f'{GROUPS[group]}\n(n={int(sub.n.iloc[0])})')
        for x, y in zip(sub.media, yy):
            ax.text(x+1.8, y, f'{x:.2f}', va='center', fontsize=12, color=color)
    ax.set(yticks=np.arange(3), yticklabels=list(labels.values()), xlim=(0, 100),
           xlabel='Média da nota bruta (0–100)', title='Desempenho por componente e grupo')
    ax.invert_yaxis()
    ax.legend(loc='lower right', fontsize=11)
    save(fig, 'comparacao_componentes_2023', 'Grupos incluem a UNIFOR e se sobrepõem. Médias por participante; sem teste de significância.')

    fig, ax = plt.subplots(figsize=(8, 6.8))
    p, u = v[v.CO_CURSO.ne('107689')], v[v.CO_CURSO.eq('107689')]
    ax.scatter(p.NT_FG, p.NT_CE, s=18, alpha=.23, color=COLOR_P, label=f'Privadas sem UNIFOR (n={len(p)})')
    ax.scatter(u.NT_FG, u.NT_CE, s=50, alpha=.9, color=COLOR_U, edgecolor='white', linewidth=.5, label=f'UNIFOR (n={len(u)})')
    ax.set(xlim=(0, 100), ylim=(0, 100), xlabel='Formação Geral (0–100)', ylabel='Componente Específico (0–100)', title='Relação individual entre FG e CE')
    ax.legend(loc='upper left', fontsize=12)
    save(fig, 'relacao_fg_ce_2023', 'Cada ponto usa as duas notas do mesmo registro do arq3. Sobreposição de pontos é possível.')

    fig, ax = plt.subplots(figsize=(9, 5.3))
    box = v[['CO_CURSO', 'NT_FG', 'NT_CE']].copy()
    box['grupo'] = np.where(box.CO_CURSO.eq('107689'), 'UNIFOR (n=25)', 'Privadas sem UNIFOR (n=1178)')
    box = box.melt(id_vars=['grupo'], value_vars=['NT_FG', 'NT_CE'], var_name='componente', value_name='nota')
    sns.boxplot(data=box, x='nota', y='componente', hue='grupo', hue_order=['UNIFOR (n=25)', 'Privadas sem UNIFOR (n=1178)'], palette=[COLOR_U, COLOR_P], ax=ax)
    ax.set(xlim=(0, 100), xlabel='Nota bruta (0–100)', ylabel='', yticks=[0, 1], yticklabels=['Formação Geral', 'Componente Específico'], title='Dispersão de FG e CE')
    ax.legend(title='', loc='center right', fontsize=11, ncols=2)
    save(fig, 'dispersao_fg_ce_2023', 'Caixa: quartis; linha: mediana; hastes até 1,5 intervalo interquartil; pontos: valores além das hastes.')

    fig, ax = plt.subplots(figsize=(9, 5.5))
    parts = {'NT_OBJ_FG': 'FG objetiva', 'NT_DIS_FG': 'FG discursiva', 'NT_OBJ_CE': 'CE objetiva', 'NT_DIS_CE': 'CE discursiva'}
    for group, offset, color in [('UNIFOR', -.16, COLOR_U), ('privado_sem_unifor', .16, COLOR_P)]:
        sub = comp[comp.grupo.eq(group)].set_index('variavel').loc[list(parts)]
        ax.barh(np.arange(4)+offset, sub.media, height=.28, color=color, label=f'{GROUPS[group]} (n={int(sub.n.iloc[0])})')
        for i, x in enumerate(sub.media):
            ax.text(x+1, i+offset, f'{x:.2f}', va='center', fontsize=12)
    ax.set(yticks=np.arange(4), yticklabels=list(parts.values()), xlim=(0, 100), xlabel='Média da nota bruta (0–100)', title='Partes objetivas e discursivas')
    ax.invert_yaxis()
    ax.legend(loc='lower right', fontsize=12)
    save(fig, 'partes_prova_2023', 'Notas discursivas são médias de correção (0–100), não percentuais de acerto.')

    for section, height in [('FG', 6), ('CE', 11)]:
        fig, ax = plt.subplots(figsize=(8, 9.2) if section=='CE' else (9, height))
        base = items[(items.grupo=='UNIFOR') & (items.componente==section)]
        for group, offset, color in [('UNIFOR', -.12, COLOR_U), ('privado_sem_unifor', .12, COLOR_P)]:
            sub = items[(items.grupo==group) & (items.componente==section)]
            ax.scatter(sub.percentual_acerto, sub.posicao_vetor+offset, color=color, s=45,
                       label=f'{GROUPS[group]} (n={int(sub.n_base_notas.iloc[0])})')
        excluded = base[base.situacao.ne('valido')]
        for i in excluded.posicao_vetor:
            ax.axhspan(i-.42, i+.42, color='#EEEEEE', zorder=0)
            ax.text(50, i, 'Excluído por discriminação', ha='center', va='center', fontsize=12, color='#555555')
        ax.set(yticks=base.posicao_vetor, yticklabels=[f'Q {i:02d}' for i in base.questao_caderno],
               ylim=(.4, len(base)+.6), xlim=(0, 100), xlabel='Acertos entre respostas válidas ao item (%)',
               title=f'Acertos por questão objetiva de {section}')
        ax.invert_yaxis()
        ax.legend(loc='lower right' if section=='FG' else 'upper right', fontsize=12)
        save(fig, f'itens_{section.lower()}_2023', 'Questões do caderno oficial da área. Itens excluídos não entram nos percentuais de acerto.')

    fig, ax = plt.subplots(figsize=(9, 6.7))
    for group, offset, color in [('UNIFOR', -.15, COLOR_U), ('privado_sem_unifor', .15, COLOR_P)]:
        sub = indicator[indicator.grupo.eq(group)].set_index('variavel').loc[list(INDICATORS)]
        ax.scatter(sub.percentual, np.arange(5)+offset, s=65, color=color, label=GROUPS[group])
        for i, (_, r) in enumerate(sub.iterrows()):
            ax.text(r.percentual+2, i+offset, f'{r.percentual:.1f}% ({int(r.contagem)}/{int(r.n_respondentes)})', va='center', fontsize=11, color=color)
    ax.set(yticks=np.arange(5), yticklabels=['Renda familiar\naté 3 salários mínimos', 'Trabalho de\n40 h/semana ou mais', 'Pai com graduação\nou pós-graduação', 'Mãe com graduação\nou pós-graduação', 'Ensino médio todo\nem escola pública'],
           xlim=(0, 115), xticks=np.arange(0, 101, 20), xlabel='Percentual dos respondentes válidos (%)', title='Perfil socioeconômico: marginais por arquivo')
    ax.invert_yaxis()
    ax.legend(loc='upper right', fontsize=12)
    save(fig, 'perfil_socioeconomico_2023', 'Denominadores específicos de cada pergunta. Respondentes não são necessariamente os participantes com nota.')
    return names


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chunksize', type=int, default=50000)
    args = parser.parse_args()
    analyze(chunksize=args.chunksize)
