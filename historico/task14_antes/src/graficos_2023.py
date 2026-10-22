"""Figuras de apresentação TASK 13, geradas das mesmas tabelas e registros validados."""
import json

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import seaborn as sns

from preparar_2023 import require
from auditoria_fg_2023 import summarize_discursive

U, P = '#C15B20', '#176783'
SOURCE = 'Fonte: INEP, ENADE/Censo 2023; elaboração própria.'


def decimal(value, digits=2):
    return f'{value:.{digits}f}'.replace('.', ',')


def render(v, comp, items, indicator, plots):
    sns.set_theme(style='whitegrid', font_scale=1.2)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'pdf.fonttype': 42})
    names, visual = [], []
    group_labels = {'UNIFOR': 'UNIFOR', 'privado_presencial': 'Privadas presenciais',
                    'sem_fins_lucrativos': 'Sem fins lucrativos', 'universidades_privadas': 'Universidades privadas'}

    def save(fig, stem, axes, handles=None, labels=None, top=.87):
        legend = None
        if handles:
            legend = fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(.5, .995),
                                ncols=2, fontsize=11, frameon=False)
        # Uma fonte por figura; detalhes metodológicos ficam na legenda LaTeX.
        fig.text(.015, .012, SOURCE, fontsize=10, va='bottom')
        for ax in axes:
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x:g}'.replace('.', ',')))
        fig.tight_layout(rect=(0, .065, 1, top), h_pad=1.5)
        fig.canvas.draw()
        if legend:
            bounds = legend.get_window_extent(fig.canvas.get_renderer())
            require(all(not bounds.overlaps(ax.get_window_extent()) for ax in axes), 'Legenda cobre área de dados')
        visual.append({'figura': stem, 'eixos_x': [list(ax.get_xlim()) for ax in axes],
                       'legenda_fora_dados': True, 'fonte_unica': True})
        for ext in ['png', 'pdf']:
            name = stem+'.'+ext
            fig.savefig(plots/name, dpi=300, facecolor='white',
                        metadata={'Creator': 'projeto-enade', 'CreationDate': None, 'ModDate': None} if ext=='pdf' else None)
            names.append(name)
        plt.close(fig)

    def two_groups(ax, group_label=True):
        handles, labels = ax.get_legend_handles_labels()
        return handles, labels

    fig, ax = plt.subplots(figsize=(8.2, 5.1))
    notes = ['NT_GER', 'NT_FG', 'NT_CE']
    for j, (group, color) in enumerate(zip(group_labels, [U, P, '#39835A', '#7963A6'])):
        sub = comp[comp.grupo.eq(group)].set_index('variavel').loc[notes]
        yy = np.arange(3)+(j-1.5)*.18
        ax.scatter(sub.media, yy, s=55, color=color, label=f'{group_labels[group]}\n(n={int(sub.n.iloc[0])})')
        for x, y in zip(sub.media, yy):
            ax.text(x+1.7, y, decimal(x), va='center', fontsize=11, color=color)
    ax.set(yticks=np.arange(3), yticklabels=['Nota geral','Formação Geral','Componente\nEspecífico'],
           xlim=(0,100), xlabel='Média da nota bruta (0–100)')
    ax.invert_yaxis()
    save(fig, 'comparacao_componentes_2023', [ax], *two_groups(ax), top=.80)

    p = v[v.CO_CURSO.astype(str).ne('107689')]
    u = v[v.CO_CURSO.astype(str).eq('107689')]
    fig, ax = plt.subplots(figsize=(7.5, 5.4))
    ax.scatter(p.NT_FG, p.NT_CE, s=16, alpha=.25, color=P, label=f'Demais privadas (n={len(p)})')
    ax.scatter(u.NT_FG, u.NT_CE, s=45, color=U, edgecolor='white', linewidth=.5, label=f'UNIFOR (n={len(u)})')
    ax.set(xlim=(0,100), ylim=(0,100), xlabel='Formação Geral (0–100)', ylabel='Componente Específico (0–100)')
    save(fig, 'relacao_fg_ce_2023', [ax], *two_groups(ax))

    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    box = v[['CO_CURSO','NT_FG','NT_CE']].copy()
    box['grupo'] = np.where(box.CO_CURSO.astype(str).eq('107689'), 'UNIFOR (n=25)', 'Demais privadas (n=1.178)')
    box = box.melt(id_vars='grupo', value_vars=['NT_FG','NT_CE'], var_name='componente', value_name='nota')
    sns.boxplot(data=box, x='nota', y='componente', hue='grupo', hue_order=['UNIFOR (n=25)','Demais privadas (n=1.178)'],
                palette=[U,P], ax=ax)
    handles, labels = two_groups(ax)
    ax.get_legend().remove()
    ax.set(xlim=(0,100), xlabel='Nota bruta (0–100)', ylabel='', yticks=[0,1],
           yticklabels=['Formação Geral','Componente\nEspecífico'])
    save(fig, 'dispersao_fg_ce_2023', [ax], handles, labels)

    fig, ax = plt.subplots(figsize=(8.2, 4.5))
    parts = ['NT_OBJ_FG','NT_DIS_FG','NT_OBJ_CE','NT_DIS_CE']
    for group, offset, color, label in [('UNIFOR',-.16,U,'UNIFOR (n=25)'), ('privado_sem_unifor',.16,P,'Demais privadas (n=1.178)')]:
        sub = comp[comp.grupo.eq(group)].set_index('variavel').loc[parts]
        ax.barh(np.arange(4)+offset, sub.media, height=.28, color=color, label=label)
        for i,x in enumerate(sub.media):
            ax.text(x+1, i+offset, decimal(x), va='center', fontsize=11)
    ax.set(yticks=np.arange(4), yticklabels=['FG objetiva','FG discursiva','CE objetiva','CE discursiva'],
           xlim=(0,100), xlabel='Média da nota bruta (0–100)')
    ax.invert_yaxis()
    save(fig, 'partes_prova_2023', [ax], *two_groups(ax))

    diagnostic = summarize_discursive(v, {'UNIFOR': {'107689'}, 'privado_sem_unifor': set(p.CO_CURSO.astype(str))}).set_index('grupo')
    fig, axes = plt.subplots(2, 1, figsize=(8.2, 6.2), gridspec_kw={'height_ratios':[1,1.7]})
    ax = axes[0]
    for i,(group,color) in enumerate([('UNIFOR',U),('privado_sem_unifor',P)]):
        r = diagnostic.loc[group]
        ax.barh(i, r.percentual_brancos, height=.45, color=color)
        ax.text(r.percentual_brancos+1.5, i, f'{decimal(r.percentual_brancos,1)}% ({int(r.n_brancos)}/{int(r.n_total)})', va='center', fontsize=11)
    ax.set(yticks=[0,1], yticklabels=['UNIFOR','Demais privadas'], xlim=(0,100), xlabel='Questão em branco (%)')
    ax.invert_yaxis()
    ax = axes[1]
    fields = [('media_todos','n_total'),('media_sem_brancos','n_sem_brancos'),('media_respostas_validas','n_respostas_validas')]
    for group,offset,color,label in [('UNIFOR',-.13,U,'UNIFOR'),('privado_sem_unifor',.13,P,'Demais privadas')]:
        r = diagnostic.loc[group]
        ax.scatter([r[a] for a,_ in fields], np.arange(3)+offset, color=color, s=45, label=label)
        for i,(mean,n) in enumerate(fields):
            ax.text(r[mean]+2, i+offset, f'{decimal(r[mean])} (n={int(r[n])})', va='center', color=color, fontsize=11)
    ax.set(yticks=np.arange(3), yticklabels=['Todos','Sem brancos','Respostas válidas\n(código 555)'],
           xlim=(0,100), xlabel='Média da nota discursiva de FG (0–100)')
    ax.invert_yaxis()
    save(fig, 'fg_discursiva_resposta_2023', list(axes), *two_groups(ax), top=.90)

    for section in ['FG','CE']:
        fig, ax = plt.subplots(figsize=(8.2, 4.8 if section=='FG' else 8.2))
        base = items[(items.grupo=='UNIFOR') & (items.componente==section)]
        for group,offset,color,label in [('UNIFOR',-.12,U,'UNIFOR (n=25)'),('privado_sem_unifor',.12,P,'Demais privadas (n=1.178)')]:
            sub = items[(items.grupo==group) & (items.componente==section)]
            ax.scatter(sub.percentual_acerto, sub.posicao_vetor+offset, color=color, s=36, label=label)
        for i in base.loc[base.situacao.ne('valido'),'posicao_vetor']:
            ax.axhspan(i-.42,i+.42,color='#EEEEEE',zorder=0)
            ax.text(50,i,'Excluído por discriminação',ha='center',va='center',fontsize=11,color='#555555')
        ax.set(yticks=base.posicao_vetor, yticklabels=[f'Q {i:02d}' for i in base.questao_caderno],
               ylim=(.4,len(base)+.6), xlim=(0,100), xlabel='Acertos entre respostas válidas ao item (%)')
        ax.invert_yaxis()
        save(fig, f'itens_{section.lower()}_2023', [ax], *two_groups(ax), top=.91 if section=='CE' else .87)

    fig, ax = plt.subplots(figsize=(8.2,5.3))
    variables = ['QE_I08','QE_I10','QE_I04','QE_I05','QE_I17']
    for group,offset,color,label in [('UNIFOR',-.15,U,'UNIFOR'),('privado_sem_unifor',.15,P,'Demais privadas')]:
        sub = indicator[indicator.grupo.eq(group)].set_index('variavel').loc[variables]
        ax.scatter(sub.percentual,np.arange(5)+offset,color=color,s=55,label=label)
        for i,(_,r) in enumerate(sub.iterrows()):
            # Rótulos ficam dentro da escala real, sem ampliar o eixo além de 100%.
            left = r.percentual>60
            ax.annotate(f'{decimal(r.percentual,1)}% ({int(r.contagem)}/{int(r.n_respondentes)})',
                        (r.percentual,i+offset), xytext=(-7 if left else 7,0), textcoords='offset points',
                        ha='right' if left else 'left',va='center',fontsize=10.5,color=color)
    ax.set(yticks=np.arange(5), yticklabels=['Renda familiar\naté 3 salários mínimos','Trabalho de\n40 h/semana ou mais',
           'Pai com graduação\nou pós-graduação','Mãe com graduação\nou pós-graduação','Ensino médio todo\nem escola pública'],
           xlim=(0,100),xticks=np.arange(0,101,20),xlabel='Percentual dos respondentes válidos (%)')
    ax.invert_yaxis()
    save(fig,'perfil_socioeconomico_2023',[ax],*two_groups(ax))
    (plots.parent/'tabelas/validacao_visual_graficos_2023.json').write_text(
        json.dumps({'status':'geometria_aprovada','figuras':visual},ensure_ascii=False,indent=2),encoding='utf-8')
    return names
