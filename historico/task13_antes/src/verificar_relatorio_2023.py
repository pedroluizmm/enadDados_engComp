"""Verificações estáticas LaTeX; não substituem compilação/revisão visual."""
import json
import re
import shutil

from preparar_2023 import ROOT, require, sha256
from atualizar_relatorio_2023 import update


def verify_report(root=ROOT):
    folder = root / 'DOCUMENT'
    original = {p.name: sha256(p) for p in (folder / 'tabelas').glob('*.tex')}
    update(root)
    require(original == {p.name: sha256(p) for p in (folder / 'tabelas').glob('*.tex')},
            'Tabelas do relatório não correspondiam aos resultados validados')
    main = (folder / 'main.tex').read_text(encoding='utf-8')
    texts = [main] + [p.read_text(encoding='utf-8') for p in (folder / 'tabelas').glob('*.tex')]
    # Remove comentários preservando percentuais escapados, e verifica chaves/ambientes.
    for source in texts:
        clean = re.sub(r'(?<!\\)%[^\n]*', '', source)
        depth = 0
        for token in re.findall(r'\\[{}]|[{}]', clean):
            if token == '{':
                depth += 1
            elif token == '}':
                depth -= 1
            require(depth >= 0, 'Fechamento de chave sem abertura')
        require(depth == 0, 'Chaves desbalanceadas')
        stack = []
        for kind, env in re.findall(r'\\(begin|end)\{([^}]+)\}', clean):
            if kind == 'begin':
                stack.append(env)
            else:
                require(bool(stack) and stack.pop() == env, f'Ambiente inválido: {env}')
        require(not stack, 'Ambiente aberto')
    require(main.count(r'\begin{document}') == main.count(r'\end{document}') == 1, 'Documento inválido')
    paths = re.findall(r'\\(?:input|includegraphics)(?:\[[^]]*\])?\{([^}]+)\}', main)
    for name in paths:
        require((folder / name).is_file(), f'Arquivo referenciado ausente: {name}')
    labels = re.findall(r'\\label\{([^}]+)\}', main)
    refs = re.findall(r'\\(?:ref|pageref)\{([^}]+)\}', main)
    require(len(labels) == len(set(labels)), 'Rótulos duplicados')
    require(set(refs) <= set(labels), 'Referência não resolvida')
    bib = set(re.findall(r'\\bibitem\{([^}]+)\}', main))
    cites = re.findall(r'\\cite(?:\[[^]]*\])?\{([^}]+)\}', main)
    require({v for cite in cites for v in cite.split(',')} <= bib, 'Citação sem referência')
    macros = re.findall(r'\\newcommand\{\\([A-Za-z]+)\}',
                        (folder / 'tabelas/indicadores.tex').read_text(encoding='utf-8'))
    require(bool(macros), 'Indicadores não definidos')
    for command in set(re.findall(r'\\([A-Za-z]+)', main)):
        if command.startswith(('Total','Media','Taxa','Unifor','Cursos','Notas','Correlacao','Diferenca','Perfil')):
            require(command in macros, f'Indicador não definido: {command}')
    compiler = next((shutil.which(c) for c in ['pdflatex','lualatex','xelatex'] if shutil.which(c)), None)
    require(main.count(r'\begin{figure}') == 6, 'Seleção de figuras inesperada')
    require(not any(s in main for s in ['arquivo recebido estava vazio', 'compilador LaTeX disponível']),
            'Observação operacional no texto acadêmico')
    # Dez blocos editoriais NÃO equivalem a dez páginas compiladas.
    editorial = main.count(r'\clearpage') + 2
    require(editorial <= 10, 'Mais de dez blocos editoriais')
    result = {'status': 'validacao_estatica_aprovada', 'compilador': compiler,
              'compilado': False, 'paginas_pdf': None, 'limite_10_paginas_verificado': False,
              'blocos_editoriais_planejados': editorial,
              'figuras': len([p for p in paths if p.endswith(('.png','.pdf'))]),
              'arquivos_referenciados': paths, 'tabelas_reconciliadas_com_csv': True,
              'chaves_ambientes_citacoes_referencias': True,
              'main_tex_sha256': sha256(folder / 'main.tex'),
              'limitacoes': ['Autoria estudantil e identificação docente não confirmadas',
                             'Sem compilação: paginação, limite obrigatório de dez páginas e aparência do PDF não verificados']}
    (folder / 'validacao_relatorio_2023.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == '__main__':
    verify_report()
