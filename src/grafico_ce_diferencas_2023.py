"""TASK 14: diferenças descritivas por item CE, exclusivamente da tabela validada."""
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

from preparar_2023 import ROOT, require, sha256

EXCLUDED = {17,18,19,25,34}


def prepare_comparison(items):
    records = items[items.componente.eq('CE') & items.grupo.isin(['UNIFOR','privado_sem_unifor'])].copy()
    require(not records.duplicated(['grupo','questao_caderno']).any(), 'Item/grupo duplicado')
    require(len(records)==58, 'Esperados 29 itens em cada um dos dois grupos')
    excluded = records[records.questao_caderno.isin(EXCLUDED)]
    require(len(excluded)==10 and excluded.percentual_acerto.isna().all()
            and excluded.n_respostas_validas.eq(0).all() and excluded.situacao.eq('excluido_discriminacao').all(),
            'Itens excluídos devem permanecer sem percentual e sem denominador')
    valid = records[~records.questao_caderno.isin(EXCLUDED)]
    require(valid.situacao.eq('valido').all() and valid.percentual_acerto.notna().all(), 'Item válido inconsistente')
    for group,n in [('UNIFOR',25),('privado_sem_unifor',1178)]:
        sub=valid[valid.grupo.eq(group)]
        require(len(sub)==24 and sub.n_respostas_validas.eq(n).all() and sub.n_base_notas.eq(n).all(),
                f'Denominador inesperado: {group}')
        require(np.allclose(sub.percentual_acerto,100*sub.acertos/sub.n_respostas_validas,atol=1e-10,rtol=0),
                'Percentual não corresponde à contagem publicada')
    result=valid.pivot(index='questao_caderno',columns='grupo',values='percentual_acerto')
    result=result.rename(columns={'UNIFOR':'percentual_unifor','privado_sem_unifor':'percentual_demais'})
    result['diferenca_pp']=result.percentual_unifor-result.percentual_demais
    return result.reset_index().sort_values(['diferenca_pp','questao_caderno'],ascending=[False,True]).reset_index(drop=True)


def render_ce_difference(items, plots):
    data=prepare_comparison(items)
    limit=5*math.ceil(float(data.diferenca_pp.abs().max())/5)
    positive,negative='#176783','#A86A43'
    rc=dict(matplotlib.rcParamsDefault)
    rc.update({'font.family':'DejaVu Sans','font.size':11.5,'pdf.fonttype':42})
    with plt.rc_context(rc):
        fig=plt.figure(figsize=(8,7.5),facecolor='white')
        ax=fig.add_axes([.09,.225,.57,.605])
        cols=fig.add_axes([.70,.225,.28,.605],sharey=ax)
        y=np.arange(len(data))
        colors=[positive if value>=0 else negative for value in data.diferenca_pp]
        for i,r in data.iterrows():
            ax.hlines(i,0,r.diferenca_pp,color=colors[i],alpha=.45,linewidth=1.4)
            ax.scatter(r.diferenca_pp,i,color=colors[i],s=43,zorder=3)
            bold=int(r.questao_caderno) in {23,30,28}
            if bold:
                ax.annotate(f'{r.diferenca_pp:+.1f}'.replace('.',','),(r.diferenca_pp,i),
                            xytext=(-7 if r.diferenca_pp>0 else 7,0),textcoords='offset points',
                            ha='right' if r.diferenca_pp>0 else 'left',va='center',fontsize=11,fontweight='bold',color=colors[i],
                            bbox={'facecolor':'white','edgecolor':'none','pad':.4})
            for x,value in [(.23,r.percentual_unifor),(.72,r.percentual_demais)]:
                cols.text(x,i,f'{value:.1f}'.replace('.',','),ha='center',va='center',
                          fontsize=11.5,fontweight='bold' if bold else 'normal')
        ax.set(yticks=y,yticklabels=[f'Q{q}' for q in data.questao_caderno],
               xlim=(-limit,limit),ylim=(len(data)-.5,-.5),xlabel='Diferença UNIFOR − demais privadas (p.p.)')
        for tick,q in zip(ax.get_yticklabels(),data.questao_caderno):
            tick.set_fontweight('bold' if q in {23,30,28} else 'normal')
        ax.set_xticks(np.arange(-limit,limit+1,10))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x:g}'.replace('.',',')))
        ax.grid(axis='x',color='#DADADA',linewidth=.6)
        ax.grid(axis='y',visible=False)
        ax.axvline(0,color='#444444',linewidth=1.4,zorder=2)
        for spine in ['top','right','left']:
            ax.spines[spine].set_visible(False)
        ax.tick_params(axis='y',length=0,pad=7)
        cols.set_xlim(0,1)
        cols.set_axis_off()
        for i in y:
            cols.hlines(i+.48,0,1,color='#ECECEC',linewidth=.5)
        cols.text(.23,1.025,'UNIFOR\n(%)',transform=cols.transAxes,ha='center',va='bottom',fontsize=10.5,fontweight='bold')
        cols.text(.72,1.025,'Demais privadas\n(%)',transform=cols.transAxes,ha='center',va='bottom',fontsize=10,fontweight='bold')
        fig.suptitle('Componente Específico: diferenças de acerto por questão',fontsize=13.5,y=.992)
        fig.text(.5,.947,'24 questões válidas | UNIFOR: n=25; demais privadas: n=1.178',ha='center',fontsize=10.5)
        legend=fig.legend([Line2D([],[],marker='o',linestyle='',color=positive),Line2D([],[],marker='o',linestyle='',color=negative)],
                         ['Percentual maior na UNIFOR','Percentual menor na UNIFOR'],loc='upper center',
                         bbox_to_anchor=(.5,.942),ncols=2,frameon=False,fontsize=10)
        fig.text(.015,.117,'Diferenças descritivas e exploratórias; cada acerto da UNIFOR equivale a 4 p.p.',fontsize=9.5)
        fig.text(.015,.086,'Excluídas por discriminação: Q17, Q18, Q19, Q25 e Q34 (sem percentual).',fontsize=9.5)
        fig.text(.015,.055,'Destaques em negrito: Q23, Q30 e Q28; seleção exploratória, sem teste de significância.',fontsize=9.5)
        fig.text(.015,.018,'Fonte: INEP, ENADE/Censo 2023; elaboração própria.',fontsize=9.5)
        fig.canvas.draw()
        renderer=fig.canvas.get_renderer()
        require(not legend.get_window_extent(renderer).overlaps(ax.get_window_extent()),'Legenda sobre os dados')
        require(all(not legend.get_window_extent(renderer).overlaps(t.get_window_extent(renderer)) for t in cols.texts[-2:]),
                'Legenda sobreposta ao cabeçalho das colunas')
        # Cada coluna deve manter suas 24 células sem sobreposição vertical.
        for x in [.23,.72]:
            boxes=[t.get_window_extent(renderer) for t in cols.texts if t.get_position()[0]==x and t.get_transform()==cols.transData]
            require(all(not a.overlaps(b) for a,b in zip(boxes,boxes[1:])), 'Células numéricas sobrepostas')
        for text in fig.texts+cols.texts+[ax.xaxis.label]:
            b=text.get_window_extent(renderer)
            require(b.x0>=0 and b.y0>=0 and b.x1<=fig.bbox.width and b.y1<=fig.bbox.height,'Texto cortado na figura')
        require(not ax.xaxis.label.get_window_extent(renderer).overlaps(fig.texts[2].get_window_extent(renderer)),
                'Rótulo do eixo sobreposto à nota metodológica')
        files=[]
        for ext in ['png','pdf']:
            name='itens_ce_2023.'+ext
            fig.savefig(plots/name,dpi=300,facecolor='white',
                        metadata={'Creator':'projeto-enade','CreationDate':None,'ModDate':None} if ext=='pdf' else None)
            files.append(name)
        plt.close(fig)
    visual={'figura':'itens_ce_2023','eixos_x':[[-limit,limit]],'legenda_fora_dados':True,
            'fonte_unica':True,'tipo':'diferencas_pp_ordenadas','n_questoes':24,
            'denominadores':{'UNIFOR':25,'demais_privadas':1178},'excluidas':sorted(EXCLUDED),
            'linhas':data.to_dict('records'),'novos_testes_estatisticos':False}
    return files,visual


def update_ce_only(root=ROOT):
    tables=root/'resultados/tabelas'
    table=tables/'acertos_itens_2023.csv'
    audit_path=tables/'validacao_aprofundamento_2023.json'
    audit=json.loads(audit_path.read_text(encoding='utf-8'))
    name=str(table.relative_to(root))
    require(sha256(table)==audit['sha256_saidas'][name], 'Tabela de itens não corresponde à validação')
    files,visual=render_ce_difference(pd.read_csv(table,sep=';'),root/'resultados/graficos')
    # Conferência independente de TODAS as proporções/diferenças pela biblioteca padrão.
    with table.open(encoding='utf-8-sig',newline='') as stream:
        raw=list(csv.DictReader(stream,delimiter=';'))
    for row in visual['linhas']:
        question=str(row['questao_caderno'])
        source={r['grupo']:r for r in raw if r['componente']=='CE' and r['questao_caderno']==question}
        u,p=source['UNIFOR'],source['privado_sem_unifor']
        pu=100*int(u['acertos'])/int(u['n_respostas_validas'])
        pp=100*int(p['acertos'])/int(p['n_respostas_validas'])
        require(all(math.isclose(a,b,abs_tol=1e-10) for a,b in
                    [(row['percentual_unifor'],pu),(row['percentual_demais'],pp),(row['diferenca_pp'],pu-pp)]),
                'Diferença/percentual não reconciliado com a tabela original')
    for filename in files:
        path=root/'resultados/graficos'/filename
        audit['sha256_saidas'][str(path.relative_to(root))]=sha256(path)
    audit['revisao_task14']='Somente Figura 5: 24 diferenças CE ordenadas e percentuais absolutos.'
    audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    metadata_path=tables/'validacao_visual_graficos_2023.json'
    metadata=json.loads(metadata_path.read_text(encoding='utf-8'))
    metadata['figuras']=[visual if r['figura']=='itens_ce_2023' else r for r in metadata['figuras']]
    metadata_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    visual.update({'status':'aprovado','conferencias_numericas':72,
                   'sha256_tabela_original':sha256(table),
                   'sha256_figuras':{f:sha256(root/'resultados/graficos'/f) for f in files},
                   'compilado':False,'paginas_pdf':None})
    (tables/'validacao_figura_ce_2023.json').write_text(json.dumps(visual,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Figura CE atualizada: 24 diferenças e 48 percentuais conferidos; denominadores 25/1.178.')
    return visual


if __name__=='__main__':
    update_ce_only()
