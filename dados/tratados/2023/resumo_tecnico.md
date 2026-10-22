# Preparação corrigida — ENADE/Censo 2023

Instituições: 70; cursos: 79; inscritos: 1418.
UNIFOR: 30 inscritos, 25 notas publicadas válidas.
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
Cursos sem correspondência: [{"CO_IES": "137", "CO_CURSO": "1125254", "NO_IES": "CENTRO UNIVERSITÁRIO SAGRADO CORAÇÃO"}].
A ausência no cadastro de cursos não implica inexistência, encerramento ou mudança de código.

IN_NOTA_VALIDA indica notas publicadas utilizáveis: presença 555, participação 333/555 e
três notas principais disponíveis. Zero não é ausência. Notas ausentes permanecem vazias.
SITUACAO_RESULTADO distingue ausente, presente_nota_publicada, suprimido_sigilo e outros inválidos.
Sigilo: presença 555 sem as três notas e apenas um TP_PRES=555 no curso, conforme Manual, p. 7.
Anonimização e proibição de associação individual: Manual, pp. 6–7.
Situações: {"presente_nota_publicada": 1203, "ausente": 208, "suprimido_sigilo": 6, "outro_resultado_nao_valido": 1}.
A UNIFOR tem cinco ausentes, diferentes dos resultados suprimidos de outros cursos.

## Verificações

CSVs relidos integralmente (valores, ausências e multiplicidade); chaves e cardinalidades conferidas;
contagens por curso arq1/arq3 iguais sem identificar pessoas; notas dentro de 0–100.
ZIPs intactos por tamanho/SHA-256 antes/depois: True.
Detalhes de leitura, correspondências, divergências e hashes: resumo_tecnico.json.
Definições com aba, linha e domínio: dicionarios_utilizados.json.
Execução e teste manual: docs/preparacao_2023.md.
