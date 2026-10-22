"""ZIP autocontido para Overleaf: apenas ajusta os caminhos das figuras na cópia."""
import json
import re
import zipfile

from preparar_2023 import ROOT, require, sha256
from verificar_relatorio_2023 import verify_report


def package(root=ROOT):
    verify_report(root)
    folder = root/'DOCUMENT'
    text = (folder/'main.tex').read_text(encoding='utf-8').replace('../resultados/graficos/', 'graficos/')
    paths = re.findall(r'\\(?:input|includegraphics)(?:\[[^]]*\])?\{([^}]+)\}', text)
    output = folder/'enade_2023_overleaf.zip'
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('main.tex', text.encode('utf-8'))
        for relative in paths:
            source = root/'resultados'/relative if relative.startswith('graficos/') else folder/relative
            require(source.is_file(), f'Arquivo ausente no pacote: {relative}')
            z.write(source, relative)
        z.writestr('LEIA-ME.txt', ('Relatório ENADE 2023 — revisão TASK 13\n'
            'Pacote local autocontido para importação futura pelo usuário no Prism ou Overleaf.\n'
            'Arquivo principal: main.tex. Compilador: pdfLaTeX. Recompile duas vezes.\n'
            'Confira o total físico do PDF, incluindo capa e referências: máximo 10 páginas.\n'
            'Foram removidas quebras forçadas; o relatório não foi compilado no ambiente local.\n'
            'Se ultrapassar 10, reduza texto redundante ou transfira uma tabela ao notebook; preserve gráficos legíveis.\n'
            'Confira cortes, sobreposição, fontes, legendas, referências e identificação acadêmica.\n'
            'Autoria estudantil e docente não foram inventados; devem ser confirmados pelo grupo.\n').encode('utf-8'))
    with zipfile.ZipFile(output) as z:
        require(z.testzip() is None, 'ZIP corrompido')
        require(set(paths) <= set(z.namelist()), 'Dependências faltantes no ZIP')
        require(z.read('main.tex').decode('utf-8') == text, 'Fonte divergente no ZIP')
    result = {'arquivo': str(output.relative_to(root)), 'sha256': sha256(output),
              'dependencias_conferidas': len(paths), 'autocontido': True,
              'compilado': False, 'paginas_pdf': None}
    (folder/'validacao_pacote_2023.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == '__main__':
    package()
