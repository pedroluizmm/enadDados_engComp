"""Verifica preservação, diagnóstico discursivo e reprodução da apresentação TASK 13."""
import json
import re

import pandas as pd

from preparar_2023 import ROOT, require, sha256
from verificar_2023 import verify
from auditoria_fg_2023 import refresh_presentation


def verify_revision(root=ROOT):
    verify(root)
    protected = json.loads((root/'historico/task13_antes/entradas_protegidas.json').read_text(encoding='utf-8'))
    require(all(sha256(root/name)==digest for name,digest in protected.items()), 'Dado ou CSV aprovado foi alterado')
    base = root/'resultados/tabelas'
    audit = json.loads((base/'validacao_aprofundamento_2023.json').read_text(encoding='utf-8'))
    names = audit['graficos']
    paths = [root/'resultados/graficos'/n for n in names]+[base/'fg_discursiva_respostas_2023.csv']
    before = {str(p.relative_to(root)):sha256(p) for p in paths}
    refresh_presentation(root)
    require(before=={str(p.relative_to(root)):sha256(p) for p in paths}, 'Renderer não reproduziu figuras/diagnóstico')
    visual = json.loads((base/'validacao_visual_graficos_2023.json').read_text(encoding='utf-8'))
    require(len(visual['figuras'])==8, 'Figuras ausentes')
    require(all(f['legenda_fora_dados'] and f['fonte_unica'] and all(lim==[0,100] for lim in f['eixos_x'])
                for f in visual['figuras']), 'Escala ou legenda incorreta')
    fg = pd.read_csv(base/'fg_discursiva_respostas_2023.csv',sep=';').set_index('grupo')
    require((fg.loc['UNIFOR',['n_total','n_brancos','n_respostas_validas']].to_numpy()==[25,8,17]).all(), 'UNIFOR divergente')
    require((fg.loc['privado_sem_unifor',['n_total','n_brancos','n_sem_brancos','n_respostas_validas']].to_numpy()==[1178,70,1108,1098]).all(),
            'Denominadores do referencial divergentes')
    previous=(root/'historico/task13_antes/DOCUMENT/main.tex').read_text(encoding='utf-8')
    main=(root/'DOCUMENT/main.tex').read_text(encoding='utf-8')
    require(sha256(root/'DOCUMENT/main.tex')==sha256(root/'DOCUMENT/modelos/main.tex'), 'Gerador divergente do modelo')
    require(not re.search(r'\\(?:clearpage|newpage)\b',main), 'Quebra forçada no relatório')
    notebook=json.loads((root/'notebooks/05_comparacao_engenharia.ipynb').read_text(encoding='utf-8'))
    cells=[c for c in notebook['cells'] if c['cell_type']=='code']
    require(all(c['execution_count'] is not None for c in cells), 'Notebook não executado')
    require(not any(o.get('output_type')=='error' for c in cells for o in c.get('outputs',[])), 'Erro no notebook')
    # Não manter hashes antigos das figuras como se fossem uma validação atual.
    historical_path=base/'validacao_reprodutibilidade_2023.json'
    historical=json.loads(historical_path.read_text(encoding='utf-8'))
    historical['escopo']='Histórico da TASK 09–11, anterior à revisão visual TASK 13'
    historical['vigencia_figuras']='historica; apresentação atual verificada em validacao_task13.json'
    historical_path.write_text(json.dumps(historical,ensure_ascii=False,indent=2),encoding='utf-8')
    result={'status':'aprovado','arquivos_protegidos_intactos':len(protected),
            'zip_oficiais_e_2021_preservados':True,'csvs_aprovados_preservados':True,
            'figuras_reproduzidas':len(names)//2,'arquivos_render_diagnostico_identicos':len(paths),
            'comparacao_fg_sem_pareamento_entre_arquivos':True,
            'fonte_editorial':'DOCUMENT/modelos/main.tex','gerador_reproduz_fonte':True,
            'palavras_aproximadas_fonte_antes':len(re.findall(r'\b\w+\b',previous)),
            'palavras_aproximadas_fonte_depois':len(re.findall(r'\b\w+\b',main)),
            'quebras_forcadas_antes':previous.count(r'\clearpage'),'quebras_forcadas_depois':0,
            'notebook_05_celulas_executadas':len(cells),'compilado':False,'paginas_pdf':None,
            'limite_dez_paginas_verificado':False,
            'sha256_arquivos_protegidos':protected,'sha256_apresentacao':before}
    (base/'validacao_task13.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if not k.startswith('sha256')},ensure_ascii=False,indent=2))
    return result


if __name__=='__main__':
    verify_revision()
