"""Empacota a versão validada, sem executar geradores ou análises estatísticas."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def references(text):
    return re.findall(r'\\(?:input|includegraphics)(?:\[[^]]*\])?\{([^}]+)\}', text)


def safe_member(name):
    path = PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and '\\' not in name and ':' not in name,
            f'Caminho inseguro no pacote: {name}')
    return name


def verify_archive(archive, stage, names):
    """Reabre o ZIP e compara cada membro com sua cópia local de distribuição."""
    checks = {}
    with zipfile.ZipFile(archive) as z:
        require(z.testzip() is None, 'ZIP corrompido')
        require(len(z.namelist()) == len(set(z.namelist())), 'Membros duplicados no ZIP')
        require(set(z.namelist()) == set(names), 'Arquivos ausentes ou extras no ZIP')
        for name in sorted(names):
            safe_member(name)
            local_hash = digest((stage/name).read_bytes())
            zip_hash = digest(z.read(name))
            require(local_hash == zip_hash, f'SHA-256 divergente: {name}')
            checks[name] = {'sha256_local': local_hash, 'sha256_zip': zip_hash, 'iguais': True}
        require(set(references(z.read('main.tex').decode('utf-8'))) <= set(names), 'Dependência não empacotada')
    return checks


def package(root=ROOT):
    folder = root/'DOCUMENT'
    source = folder/'main.tex'
    model = folder/'modelos/main.tex'
    source_bytes = source.read_bytes()
    require(source_bytes == model.read_bytes(), 'main.tex difere do modelo; execute o gerador antes de empacotar')
    validation = json.loads((folder/'validacao_relatorio_2023.json').read_text(encoding='utf-8'))
    require(validation['status']=='validacao_estatica_aprovada' and
            validation['main_tex_sha256']==digest(source_bytes), 'Relatório não corresponde à versão validada')
    text = source_bytes.decode('utf-8')
    for marker in ['FGPercentualBrancosUnifor','FGMediaRespostasValidasDemais','EcoRenda','EcoEscola','fg_discursiva_resposta_2023.pdf']:
        require(marker in text, f'Correção TASK 13 ausente: {marker}')
    indicators = (folder/'tabelas/indicadores.tex').read_text(encoding='utf-8')
    for key,value in {'FGPercentualBrancosUnifor':'32,0', 'FGPercentualBrancosDemais':'5,9',
                      'FGMediaRespostasValidasUnifor':'44,11','FGMediaRespostasValidasDemais':'48,26'}.items():
        require('\\newcommand{\\'+key+'}{'+value+'}' in indicators, f'Indicador TASK 13 não confirmado: {key}')

    # Única transformação editorial admitida: caminho das figuras na cópia de distribuição.
    packaged_text = text.replace('../resultados/graficos/', 'graficos/')
    payload = {'main.tex': packaged_text.encode('utf-8')}
    original_sources = {'main.tex': str(source.relative_to(root))}
    pending = references(packaged_text)
    while pending:
        name = safe_member(pending.pop(0))
        if name in payload:
            continue
        local = root/'resultados'/name if name.startswith('graficos/') else folder/name
        require(local.is_file(), f'Dependência local ausente: {name}')
        payload[name] = local.read_bytes()
        original_sources[name] = str(local.relative_to(root))
        if name.endswith('.tex'):
            pending.extend(references(payload[name].decode('utf-8-sig')))

    signature = digest(json.dumps({n:digest(b) for n,b in sorted(payload.items())},sort_keys=True).encode('utf-8'))
    revision=validation.get('revisao','TASK13')
    require(revision in ['TASK13','TASK14'],'Revisão do relatório desconhecida')
    version = revision+'-'+signature[:12]
    manifest = {'versao': version, 'arquivo_principal': 'main.tex',
                'fonte_editorial': 'DOCUMENT/modelos/main.tex', 'sha256_fonte_validada': digest(source_bytes),
                'sha256_main_distribuicao': digest(payload['main.tex']),
                'transformacao_main': '../resultados/graficos/ → graficos/; nenhum texto analítico alterado',
                'correcoes': ['FG em branco: 8/25 = 32,0%; demais privadas 70/1178 = 5,9%',
                              'FG com resultado válido: 44,11 (n=17) e 48,26 (n=1098)',
                              'Indicadores socioeconômicos e correlações agregadas por curso'],
                'sha256_conteudo': {n:digest(b) for n,b in sorted(payload.items())},
                'fontes_locais': original_sources, 'compilado': False, 'paginas_pdf': None}
    if revision=='TASK14':
        manifest['correcoes'].append('Figura 5: 24 diferenças CE ordenadas, escala simétrica e percentuais absolutos.')
    payload['MANIFESTO_VERSAO.json'] = json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8')
    payload['LEIA-ME.txt'] = (
        f'Relatório ENADE 2023 — versão {version}\n'
        'Arquivo principal: main.tex na raiz. Compilador: pdfLaTeX.\n'
        'TASK 13 confirmada: FG discursiva com 32,0% em branco (8/25), notas condicionais e indicadores socioeconômicos.\n'
        'Confira MANIFESTO_VERSAO.json para identificar a versão e os hashes.\n'
        'Os pacotes overleaf.zip e prism.zip locais são cópias idênticas desta versão.\n'
        'Importação manual pelo usuário; nenhum serviço externo foi utilizado pelo empacotador.\n'
        'Sem compilação local: confirmar máximo de dez páginas, incluindo capa e referências, e revisar o PDF.\n'
    ).encode('utf-8')

    stage = folder/'pacote_latex'
    stage.mkdir(exist_ok=True)
    for name,data in payload.items():
        path = stage/name
        path.parent.mkdir(exist_ok=True,parents=True)
        path.write_bytes(data)
    output = folder/'enade_2023_overleaf.zip'
    temporary = folder/'enade_2023_overleaf.zip.tmp'
    # Metadados fixos evitam versões binárias diferentes para conteúdo idêntico.
    with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(payload):
            info = zipfile.ZipInfo(name, date_time=(1980,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info,payload[name])
    checks = verify_archive(temporary,stage,payload)
    temporary.replace(output)
    archive_bytes = output.read_bytes()
    # Evita que o nome destinado ao Prism continue apontando para o relatório antigo.
    prism = folder/'enade_2023_prism.zip'
    versioned = folder/f'enade_2023_{version}.zip'
    for copy in [prism,versioned]:
        copy.write_bytes(archive_bytes)
        require(digest(copy.read_bytes()) == digest(archive_bytes), 'Cópia do pacote divergente')
        verify_archive(copy,stage,payload)
    # Relê também o arquivo final após a troca atômica.
    verify_archive(output,stage,payload)
    for name,local_name in original_sources.items():
        if name!='main.tex':
            require(checks[name]['sha256_zip']==digest((root/local_name).read_bytes()), f'Dependência difere do original: {name}')
    require(payload['main.tex'].decode('utf-8').replace('graficos/','../resultados/graficos/')==text,
            'Texto do main.tex alterado além dos caminhos permitidos')
    result = {'arquivo': str(output.relative_to(root)), 'versao': version, 'sha256': digest(archive_bytes),
              'copias_identicas': [str(p.relative_to(root)) for p in [prism,versioned]],
              'sha256_main_local_modelo': digest(source_bytes), 'sha256_main_zip': digest(payload['main.tex']),
              'main_igual_apos_ajuste_exclusivo_de_caminhos': True,
              'dependencias_conferidas':len(original_sources)-1, 'arquivos_internos_conferidos':len(checks),
              'sha256_internos_vs_locais': checks, 'autocontido': True, 'task13_confirmada': True,
              'task14_confirmada':revision=='TASK14',
              'analises_executadas': False, 'compilado': False, 'paginas_pdf': None}
    (folder/'validacao_pacote_2023.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='sha256_internos_vs_locais'},ensure_ascii=False,indent=2))
    return result


if __name__=='__main__':
    package()
