"""Extração reproduzível ENADE/Censo 2023, sem vínculos individuais."""

import argparse
import hashlib
import io
import json
import re
import unicodedata
from pathlib import Path
import warnings
import zipfile

import openpyxl
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARQ1 = ['NU_ANO', 'CO_CURSO', 'CO_IES', 'CO_CATEGAD', 'CO_ORGACAD',
        'CO_GRUPO', 'CO_MODALIDADE', 'CO_MUNIC_CURSO', 'CO_UF_CURSO', 'CO_REGIAO_CURSO']
ARQ3 = ['NU_ANO', 'CO_CURSO', 'TP_PRES', 'TP_PR_GER', 'TP_PR_OB_FG',
        'TP_PR_DI_FG', 'TP_PR_OB_CE', 'TP_PR_DI_CE', 'TP_SFG_D1', 'TP_SCE_D1',
        'NT_GER', 'NT_FG', 'NT_OBJ_FG', 'NT_DIS_FG', 'NT_FG_D1',
        'NT_FG_D1_PT', 'NT_FG_D1_CT', 'NT_CE', 'NT_OBJ_CE', 'NT_DIS_CE', 'NT_CE_D1']
CURSOS = ['NU_ANO_CENSO', 'CO_IES', 'CO_CURSO', 'NO_CURSO',
          'TP_CATEGORIA_ADMINISTRATIVA', 'TP_MODALIDADE_ENSINO',
          'CO_MUNICIPIO', 'NO_MUNICIPIO', 'SG_UF', 'CO_UF', 'CO_REGIAO',
          'TP_DIMENSAO', 'CO_CINE_ROTULO', 'NO_CINE_ROTULO', 'IN_COMUNITARIA', 'IN_CONFESSIONAL']
IES = ['CO_IES', 'NO_IES', 'SG_IES', 'TP_CATEGORIA_ADMINISTRATIVA',
       'SG_UF_IES', 'CO_MUNICIPIO_IES', 'NO_MUNICIPIO_IES', 'IN_COMUNITARIA', 'IN_CONFESSIONAL']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def member(z, suffix):
    names = [n for n in z.namelist() if n.endswith(suffix) and '/~$' not in n]
    require(len(names) == 1, f'Membro ZIP ambíguo/ausente: {suffix}')
    return names[0]


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c)).upper()


def dictionary(z, enade=False):
    name = member(z, '.xlsx')
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Cannot parse header or footer')
        book = openpyxl.load_workbook(io.BytesIO(z.read(name)), read_only=True, data_only=True)
        result = {}
        for sheet in book:
            if enade and normalized(sheet.title) != 'DICIONARIO DE VARIAVEIS':
                continue
            rows = list(sheet.values)
            header = next((r for r in rows if 'NOME' in [normalized(str(v)) for v in r]
                           and ('TIPO' in [normalized(str(v)) for v in r])), None)
            if not enade:
                # Cadastro Censo: códigos na coluna identificada pelo conteúdo, não pela aba ordinal.
                key_col = next((i for i in range(sheet.max_column)
                                if any(r[i] == 'CO_IES' for r in rows)), None)
            else:
                require(header is not None, 'Cabeçalho do dicionário ENADE ausente')
                key_col = [normalized(str(v)) for v in header].index('NOME')
            if key_col is None:
                continue
            entries, current = {}, None
            for row_number, row in enumerate(rows, 1):
                key = row[key_col]
                if isinstance(key, str) and re.fullmatch(r'[A-Z][A-Z0-9]*_[A-Z0-9_]+', key):
                    current = key
                    start = key_col
                    entries[key] = {'tipo': row[start+1] if enade else row[start+2],
                                    'descricao': row[start+3] if enade else row[start+1],
                                    'linhas': [row_number], 'dominio': {}}
                elif key is not None:
                    current = None
                # Linhas vazias NÃO encerram a variável: categoria 8 está em E22 após um intervalo.
                if current:
                    cell = row[key_col+4]
                    if cell is not None:
                        if row_number not in entries[current]['linhas']:
                            entries[current]['linhas'].append(row_number)
                        entries[current].setdefault('texto_dominio', []).append(str(cell))
                        for code, label in re.findall(r'(?:^|\n)\s*(\d+)\s*[.=]\s*([^\n]+)', str(cell)):
                            entries[current]['dominio'][code] = label.strip()
            if entries:
                result[sheet.title] = entries
        book.close()
    require(bool(result), 'Dicionário não identificado')
    return {'membro': name, 'abas': result}


def read_filtered(z, suffix, columns, predicate, chunksize, counts):
    parts = []
    total = 0
    with z.open(member(z, suffix)) as f:
        for chunk in pd.read_csv(f, sep=';', encoding='cp1252', dtype='string',
                                 usecols=columns, chunksize=chunksize, na_values=['.']):
            total += len(chunk)
            parts.append(chunk.loc[predicate(chunk)].copy())
    result = pd.concat(parts, ignore_index=True)
    counts[suffix] = {'lidos': total, 'selecionados': len(result)}
    return result


def valid_scores(d):
    return (d.TP_PRES.eq('555') & d.TP_PR_GER.isin(['333', '555'])
            & d[['NT_GER', 'NT_FG', 'NT_CE']].notna().all(axis=1)).fillna(False)


def prepare(root=ROOT, chunksize=50000):
    require(chunksize > 0, 'chunksize deve ser positivo')
    paths = [root / 'dados/brutos/enade_2023/microdados_enade_2023.zip',
             root / 'dados/brutos/censo_2023/microdados_censo_da_educacao_superior_2023.zip']
    before = {str(p.relative_to(root)): {'bytes': p.stat().st_size, 'sha256': sha256(p)} for p in paths}
    counts = {}
    with zipfile.ZipFile(paths[0]) as enade, zipfile.ZipFile(paths[1]) as censo:
        dictionaries = {'enade': dictionary(enade, True), 'censo': dictionary(censo)}
        definitions = next(iter(dictionaries['enade']['abas'].values()))
        require(all(c in definitions for c in ARQ1 + ARQ3), 'Variável ENADE sem definição')
        require({'4', '5', '8'} <= definitions['CO_CATEGAD']['dominio'].keys(), 'Categorias ausentes')
        require('6411' in definitions['CO_GRUPO']['dominio'], 'Grupo ausente')
        require('1' in definitions['CO_MODALIDADE']['dominio'], 'Modalidade ausente')
        require({'333', '555'} <= definitions['TP_PR_GER']['dominio'].keys(), 'Validade ausente')
        a = read_filtered(enade, 'microdados2023_arq1.txt', ARQ1,
                          lambda d: d.NU_ANO.eq('2023') & d.CO_GRUPO.eq('6411')
                          & d.CO_CATEGAD.isin(['4', '5', '8']) & d.CO_MODALIDADE.eq('1'), chunksize, counts)
        # Apenas o cadastro é reduzido a uma linha por curso. As repetições do arq1 ficam intactas.
        cadastro = a.drop_duplicates().copy()
        require(not cadastro.CO_CURSO.duplicated().any(), 'Curso com caracterização ENADE conflitante')
        require(((cadastro.CO_IES == '555') & (cadastro.CO_CURSO == '107689')).sum() == 1,
                'Curso UNIFOR ausente ou ambíguo')
        b = read_filtered(enade, 'microdados2023_arq3.txt', ARQ3,
                          lambda d: d.NU_ANO.eq('2023') & d.CO_CURSO.isin(cadastro.CO_CURSO), chunksize, counts)
        for c in [c for c in ARQ3 if c.startswith('NT_')]:
            # Ausência permanece NA; token não numérico inesperado interrompe a execução.
            b[c] = pd.to_numeric(b[c].str.replace(',', '.', regex=False), errors='raise').astype('Float64')
            require(b[c].dropna().between(0, 100).all(), f'Nota fora da escala: {c}')
        b['IN_NOTA_VALIDA'] = valid_scores(b).astype('Int64')
        b['SITUACAO_RESULTADO'] = 'outro_resultado_nao_valido'
        b.loc[b.TP_PRES.isin(['222', '444']), 'SITUACAO_RESULTADO'] = 'ausente'
        b.loc[b.IN_NOTA_VALIDA.eq(1), 'SITUACAO_RESULTADO'] = 'presente_nota_publicada'
        valid_by_course = b.TP_PRES.eq('555').groupby(b.CO_CURSO).transform('sum')
        suppressed = b.TP_PRES.eq('555') & b[['NT_GER', 'NT_FG', 'NT_CE']].isna().all(axis=1) & valid_by_course.eq(1)
        b.loc[suppressed, 'SITUACAO_RESULTADO'] = 'suprimido_sigilo'
        unexplained = b.TP_PRES.eq('555') & b.IN_NOTA_VALIDA.eq(0) & ~suppressed
        require(not unexplained.any(), 'Presença válida sem nota não explicada pela regra de sigilo')
        cursos = read_filtered(censo, 'CURSOS_2023.CSV', CURSOS,
                               lambda d: d.CO_CURSO.isin(cadastro.CO_CURSO), chunksize, counts)
        ies = read_filtered(censo, 'IES_2023.CSV', IES,
                            lambda d: d.CO_IES.isin(cadastro.CO_IES), chunksize, counts)
        require(cursos.NU_ANO_CENSO.eq('2023').all(), 'Ano Censo incorreto')
        require(not cursos.CO_CURSO.duplicated().any(), 'Censo com múltiplas linhas por curso; investigar granularidade')
        require(not ies.CO_IES.duplicated().any(), 'Censo com múltiplas linhas por IES')
        # Código de curso e instituição devem coincidir; homônimos não são usados como chave.
        cursos = cursos.rename(columns={c: c + '_CENSO' for c in CURSOS if c not in ['CO_IES', 'CO_CURSO']})
        ies = ies.rename(columns={c: c + '_IES_CENSO' for c in ['TP_CATEGORIA_ADMINISTRATIVA', 'IN_COMUNITARIA', 'IN_CONFESSIONAL']})
        cadastro = cadastro.merge(cursos, on=['CO_IES', 'CO_CURSO'], how='left',
                                  validate='one_to_one', indicator='VINCULO_CURSO_CENSO')
        cadastro = cadastro.merge(ies, on='CO_IES', how='left', validate='many_to_one', indicator='VINCULO_IES_CENSO')
        expected_category = cadastro.CO_CATEGAD.map({'4': '4', '5': '5', '8': '5'}).astype('string')
        cadastro['CATEGORIA_CENSO_ESPERADA'] = expected_category
        cadastro['DIVERGENCIA_CATEGORIA'] = (expected_category.ne(cadastro.TP_CATEGORIA_ADMINISTRATIVA_CENSO)
                                            | expected_category.ne(cadastro.TP_CATEGORIA_ADMINISTRATIVA_IES_CENSO)).astype('Int64')
        cadastro['DIVERGENCIA_INDICADORES'] = pd.Series(pd.NA, index=cadastro.index, dtype='Int64')
        has_ies = cadastro.VINCULO_IES_CENSO.eq('both')
        expected_flags = (cadastro.CO_CATEGAD.eq('8') & (cadastro.IN_COMUNITARIA_IES_CENSO.eq('1')
                          | cadastro.IN_CONFESSIONAL_IES_CENSO.eq('1'))) | (cadastro.CO_CATEGAD.isin(['4', '5'])
                          & cadastro.IN_COMUNITARIA_IES_CENSO.eq('0') & cadastro.IN_CONFESSIONAL_IES_CENSO.eq('0'))
        cadastro.loc[has_ies, 'DIVERGENCIA_INDICADORES'] = (~expected_flags[has_ies]).astype('Int64')
        cadastro['RESSALVA_CAT8_COMUNITARIA_ZERO'] = (cadastro.CO_CATEGAD.eq('8')
            & cadastro.IN_COMUNITARIA_IES_CENSO.eq('0')).astype('Int64')
        cadastro['DIVERGENCIA_MODALIDADE'] = cadastro.CO_MODALIDADE.ne(cadastro.TP_MODALIDADE_ENSINO_CENSO).astype('Int64')
        cadastro['DIVERGENCIA_MUNICIPIO'] = cadastro.CO_MUNIC_CURSO.ne(cadastro.CO_MUNICIPIO_CENSO).astype('Int64')
        cadastro['CURSO_CENSO_OUTRA_IES'] = cadastro.CO_CURSO.isin(
            cursos.loc[~pd.MultiIndex.from_frame(cursos[['CO_IES', 'CO_CURSO']]).isin(
                pd.MultiIndex.from_frame(cadastro[['CO_IES', 'CO_CURSO']])), 'CO_CURSO']).astype('Int64')
    require(a.groupby('CO_CURSO').size().to_dict() == b.groupby('CO_CURSO').size().to_dict(),
            'Contagens por curso divergem entre arquivos; investigar sem alinhar estudantes')
    after = {str(p.relative_to(root)): {'bytes': p.stat().st_size, 'sha256': sha256(p)} for p in paths}
    require(before == after, 'ZIP alterado durante processamento')
    out = root / 'dados/tratados/2023'
    out.mkdir(parents=True, exist_ok=True)
    outputs = {'cadastro_comparaveis.csv': cadastro, 'enade_arq1_filtrado.csv': a,
               'enade_arq3_desempenho.csv': b}
    checks = {}
    for name, frame in outputs.items():
        frame.to_csv(out / name, sep=';', index=False, encoding='utf-8-sig', na_rep='')
        reread = pd.read_csv(out / name, sep=';', dtype='string', encoding='utf-8-sig')
        require(list(reread.columns) == list(frame.columns) and len(reread) == len(frame), f'CSV inválido: {name}')
        require(reread.isna().equals(frame.isna()), f'Ausências alteradas: {name}')
        # Comparação textual de todos os valores, inclusive multiplicidade de linhas.
        expected = frame.astype('string').fillna('<NA>')
        require(reread.fillna('<NA>').equals(expected), f'Valores alterados no CSV: {name}')
        checks[name] = {'linhas': len(frame), 'sha256': sha256(out / name),
                        'releitura_integral': True, 'repeticoes_identicas_preservadas': int(frame.duplicated().sum())}
    unifor = b[b.CO_CURSO.eq('107689')]
    summary = {
        'filtros': {'NU_ANO': 2023, 'CO_GRUPO': 6411, 'CO_CATEGAD': [4, 5, 8], 'CO_MODALIDADE': 1},
        'instituicoes': int(cadastro.CO_IES.nunique()), 'cursos': len(cadastro),
        'registros_arq1': len(a), 'registros_arq3': len(b),
        'notas_validas': int(b.IN_NOTA_VALIDA.sum()),
        'situacoes_resultado': b.SITUACAO_RESULTADO.value_counts().to_dict(),
        'presenca_valida_sem_notas': int((b.TP_PRES.eq('555') & b.IN_NOTA_VALIDA.eq(0)).sum()),
        'unifor': {'CO_IES': 555, 'CO_CURSO': 107689, 'arq1': int(a.CO_CURSO.eq('107689').sum()),
                   'arq3': len(unifor), 'notas_validas': int(unifor.IN_NOTA_VALIDA.sum()),
                   'TP_PRES': unifor.TP_PRES.value_counts().to_dict()},
        'censo': {c: int(cadastro[c].eq('left_only').sum()) for c in ['VINCULO_CURSO_CENSO', 'VINCULO_IES_CENSO']},
        'divergencias_censo': {c: {'quantidade': int(cadastro[c].fillna(0).sum()),
                                   'nao_avaliaveis': int(cadastro[c].isna().sum())}
                               for c in ['DIVERGENCIA_CATEGORIA', 'DIVERGENCIA_INDICADORES', 'RESSALVA_CAT8_COMUNITARIA_ZERO', 'DIVERGENCIA_MODALIDADE', 'DIVERGENCIA_MUNICIPIO', 'CURSO_CENSO_OUTRA_IES']},
        'ausencias_notas': {c: int(b[c].isna().sum()) for c in ['NT_GER', 'NT_FG', 'NT_CE']},
        'distribuicao_presenca': b.TP_PRES.value_counts().to_dict(),
        'cursos_sem_censo': cadastro.loc[cadastro.VINCULO_CURSO_CENSO.eq('left_only'), ['CO_IES','CO_CURSO','NO_IES']].to_dict('records'),
        'leitura': counts, 'verificacoes_csv': checks, 'zip_antes': before, 'zip_depois': after,
        'zip_intactos': before == after,
        'referencia_unifor_30_25_confirmada': len(unifor) == 30 and int(unifor.IN_NOTA_VALIDA.sum()) == 25,
    }
    (out / 'resumo_tecnico.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'dicionarios_utilizados.json').write_text(json.dumps(dictionaries, ensure_ascii=False, indent=2), encoding='utf-8')
    report = f'''# Preparação corrigida — ENADE/Censo 2023

Instituições: {summary['instituicoes']}; cursos: {summary['cursos']}; inscritos: {len(a)}.
UNIFOR: {len(unifor)} inscritos, {summary['unifor']['notas_validas']} notas publicadas válidas.
Filtros: ano 2023, grupo 6411, categorias 4/5/8 e modalidade presencial 1.
Categoria 8 confirmada em E22 do dicionário; o leitor anterior perdia a definição após linhas vazias.

## Granularidade, compatibilidade e sigilo

Cadastro: uma linha por curso. ENADE/Censo por CO_IES+CO_CURSO (1:1) e IES por CO_IES (N:1).
As linhas anônimas do arq1 e arq3 são preservadas, inclusive repetições legítimas.
Não há merge individual, identidade artificial ou correspondência pela ordem das linhas.
Mapeamento de categorias: ENADE 4→Censo 4; ENADE 5/8→Censo 5.
Os indicadores comunitária/confessional são preservados em ambos os cadastros Censo.
Categoria 5 é conferida com ambos os indicadores zero; categoria 8 com pelo menos um igual a um.
A exigência estrita IN_COMUNITARIA=1 tem uma exceção real: instituição confessional com
IN_COMUNITARIA=0 e IN_CONFESSIONAL=1. RESSALVA_CAT8_COMUNITARIA_ZERO a explicita sem alterar dados.
A definição oficial Comunitária/Confessional justifica mantê-la; não é divergência de domínio.
Cursos sem correspondência: {json.dumps(summary['cursos_sem_censo'], ensure_ascii=False)}.
A ausência no cadastro de cursos não implica inexistência, encerramento ou mudança de código.

IN_NOTA_VALIDA indica notas publicadas utilizáveis: presença 555, participação 333/555 e
três notas principais disponíveis. Zero não é ausência. Notas ausentes permanecem vazias.
SITUACAO_RESULTADO distingue ausente, presente_nota_publicada, suprimido_sigilo e outros inválidos.
Sigilo: presença 555 sem as três notas e apenas um TP_PRES=555 no curso, conforme Manual, p. 7.
Anonimização e proibição de associação individual: Manual, pp. 6–7.
Situações: {json.dumps(summary['situacoes_resultado'], ensure_ascii=False)}.
A UNIFOR tem cinco ausentes, diferentes dos resultados suprimidos de outros cursos.

## Verificações

CSVs relidos integralmente (valores, ausências e multiplicidade); chaves e cardinalidades conferidas;
contagens por curso arq1/arq3 iguais sem identificar pessoas; notas dentro de 0–100.
ZIPs intactos por tamanho/SHA-256 antes/depois: {summary['zip_intactos']}.
Detalhes de leitura, correspondências, divergências e hashes: resumo_tecnico.json.
Definições com aba, linha e domínio: dicionarios_utilizados.json.
Execução e teste manual: docs/preparacao_2023.md.
'''
    (out / 'resumo_tecnico.md').write_text(report, encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chunksize', type=int, default=50000)
    args = parser.parse_args()
    prepare(chunksize=args.chunksize)
