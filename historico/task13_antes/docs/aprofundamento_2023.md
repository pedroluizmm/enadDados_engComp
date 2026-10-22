# TASK 09–11 — análises aprofundadas e revisão do relatório

## Entregas e execução

Foi preservada uma cópia dos arquivos anteriores em `historico/task09_11_antes/`.
Os ZIPs brutos não foram alterados. Não foram instaladas bibliotecas ou distribuição
LaTeX, nem baixados microdados de 2021. O ambiente não é um repositório Git.

Na raiz, PowerShell, com a `.venv` existente:

```powershell
.\.venv\Scripts\python.exe src/preparar_2023.py
.\.venv\Scripts\python.exe src/verificar_2023.py
.\.venv\Scripts\python.exe src/analisar_2023.py
.\.venv\Scripts\python.exe src/aprofundar_2023.py
.\.venv\Scripts\python.exe src/verificar_reprodutibilidade_2023.py
.\.venv\Scripts\python.exe src/verificar_aprofundamento_2023.py
.\.venv\Scripts\python.exe src/atualizar_relatorio_2023.py
.\.venv\Scripts\python.exe src/verificar_relatorio_2023.py
.\.venv\Scripts\python.exe src/empacotar_relatorio_2023.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`05_comparacao_engenharia.ipynb` mantém a análise anterior e acrescenta o
aprofundamento, as figuras e a auditoria independente. `06_comparacao_bonus.ipynb`
registra a inexistência de dados locais de 2021. Ambos foram executados integralmente.
Use o kernel **Python (projeto-enade)**. Para reexecutar sem histórico no perfil:

```powershell
$env:IPYTHONDIR = "$PWD\tmp\ipython_enade"
$env:JUPYTER_RUNTIME_DIR = "$PWD\tmp\jupyter_enade"
New-Item -ItemType Directory -Force -Path $env:IPYTHONDIR,$env:JUPYTER_RUNTIME_DIR | Out-Null
.\.venv\Scripts\jupyter.exe nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=projeto-enade --ExecutePreprocessor.timeout=300 notebooks/05_comparacao_engenharia.ipynb notebooks/06_comparacao_bonus.ipynb
```

## Inspeção e decisões metodológicas

Foram lidos integralmente os módulos existentes de `src/`, os seis notebooks,
o relatório anterior, as tabelas, o Manual ENADE 2023, os dicionários dos ZIPs
e as perguntas selecionadas do Questionário do Estudante. Os notebooks 01–04
eram estruturas iniciais; o 05 já continha a análise executada.

O relatório anterior repetia objetivos, verificações operacionais e ressalvas em
várias seções, com quatro gráficos parcialmente redundantes. A revisão reúne
metodologia/filtros, seleciona seis figuras em largura de página, acrescenta uma
interpretação após cada uma e remove observações sobre compiladores e arquivo vazio.
Instituição, disciplina e local/ano foram preservados; não foram inventados alunos
ou docente. A fonte ficou ligeiramente menor em contagem aproximada de palavras,
apesar das novas análises (2.286 → 2.232 palavras aproximadas na fonte, incluindo
comandos; isso **não** mede páginas do PDF).

Recorte confirmado: ano 2023, grupo 6411, categorias ENADE 4/5/8, presencial 1;
70 IES, 79 cursos, 1.418 inscritos disponibilizados, 1.209 presentes, 1.203 notas
publicadas utilizáveis, 208 ausentes, seis notas suprimidas e um eliminado.
UNIFOR: IES 555, curso 107689, 30 inscritos, 25 notas, cinco ausentes.
Não houve alteração das contagens para ajustá-las a referências anteriores.

O leitor do dicionário foi corrigido incrementalmente para preservar continuidades
com chave `''`, além de células vazias. Isso recupera as alternativas B–E da
pergunta de trabalho. Os domínios selecionados são conferidos com o questionário.

### Divergência entre XLSX e nota técnica

O XLSX local descreve FG com pesos 60/40 e CE com 85/15. Esses pesos não reproduzem
as notas. A [Nota Técnica oficial nº 12/2024, seção 4](https://download.inep.gov.br/educacao_superior/enade/notas_tecnicas/2024/nota_tecnica_12_calculo_nota_final_enade_2023.pdf)
define FG 65% objetiva/35% discursiva, CE 90%/10%, e geral 25% FG/75% CE.
Esses pesos foram conferidos registro a registro, com erro máximo de 0,101 ponto
permitido para acomodar o arredondamento das notas publicadas a uma casa.
O erro observado consta de `validacao_aprofundamento_2023.json`.
Os valores oficiais não são recalculados ou substituídos.

### FG, CE e correlação

O arq3 reúne as duas notas **no mesmo registro**, permitindo Pearson individual
sem juntar arquivos. Usa-se a mesma definição de notas válidas da preparação:
presença 555, participação 333/555 e NT_GER/NT_FG/NT_CE publicadas. São 1.203 pares,
25 da UNIFOR. Médias, medianas, quartis e DP amostral usam seus denominadores
explícitos. Não há imputação, teste de significância, controle por perfil ou
alegação causal. Subconjuntos institucionais se sobrepõem e incluem a UNIFOR;
o referencial detalhado exclui a UNIFOR para não misturá-la consigo mesma.

| Nota | UNIFOR (n=25) | Todas privadas (n=1.203) | Demais privadas (n=1.178) |
|---|---:|---:|---:|
| Geral | 41,656 | 39,326 | 39,277 |
| FG | 47,776 | 51,550 | 51,630 |
| CE | 39,600 | 35,234 | 35,141 |
| FG objetiva | 57,344 | 55,239 | 55,194 |
| FG discursiva | 29,996 | 44,695 | 45,007 |
| CE objetiva | 42,012 | 37,483 | 37,387 |
| CE discursiva | 17,800 | 14,904 | 14,843 |

DP FG/CE: UNIFOR 12,374/10,721; demais privadas 16,007/13,538.
Pearson: UNIFOR r=0,25077 (n=25); universo r=0,31325 (n=1.203);
demais privadas r=0,31622 (n=1.178). Os pares do mesmo arq3 são comprovados pela
estrutura oficial e pela releitura conjunta, não por uma identidade artificial.
O principal ponto de atenção relativo é a FG discursiva, não a FG objetiva.

### Questões objetivas e discursivas

Os vetores `DS_VT_ACE_OFG/OCE`, escolhas e gabaritos estão juntos no arq3;
são importados como strings. São nove posições FG e 29 CE, com gabarito uniforme
no recorte. A sequência foi conferida com o [gabarito definitivo oficial de
Engenharia da Computação](https://download.inep.gov.br/enade/provas_e_gabaritos/2023_GB_engenharia_da_computacao.pdf):
FG posições 1–9 correspondem a Q1–9; CE posições 1–29, a Q10–38.
A [página oficial da edição](https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enade/provas-e-gabaritos/2023)
identifica a área. Os PDFs tiveram falha de leitura direta no navegador; seus
textos oficiais indexados foram consultados. O gabarito incluído no arq3 é a
referência final das exclusões estatísticas posteriores.

Cada acerto 0/1 é conferido com escolha/gabarito do mesmo registro. Brancos ou
múltiplas respostas permanecem erros quando assim codificados oficialmente.
Códigos 8/9 indicam exclusão e nunca entram como erro, acerto ou percentual zero.
Neste recorte não há exclusão FG nem anulação CE; cinco CE foram excluídas por
discriminação (posições 8,9,10,16,25 = Q17,18,19,25,34). Restam 24 CE válidas.
Todas as notas objetivas são reconciliadas com o vetor de acertos dentro de
0,051 ponto. Cada item válido usa 25 e 1.178 respostas na comparação detalhada.

Exemplos: FG Q3 72,0% contra 61,9%; FG Q4 48,0% contra 57,1%; CE Q23 60,0%
contra 34,2% (+25,8 pontos percentuais); CE Q28 32,0% contra 47,6% (-15,6).
Uma resposta da UNIFOR representa quatro pontos percentuais. Essas diferenças
são exploratórias, sem diagnóstico temático de competências ou testes múltiplos.
As discursivas têm **notas de correção**, não percentuais binários de acerto.
Não se presumem questões equivalentes entre áreas ou edições.

### Questionário: cinco marginais e denominadores

Renda (`QE_I08`, arq14), trabalho (`QE_I10`, arq16), escolaridade do pai
(`QE_I04`, arq10), da mãe (`QE_I05`, arq11) e escola (`QE_I17`, arq23) são
processadas **separadamente**, conservando ausências e multiplicidade. As
proporções de grupo somam contagens e respostas por curso; não são médias simples
dos percentuais dos cursos. Há tabelas completas de categorias por curso/grupo.

| Indicador | UNIFOR | Demais privadas |
|---|---:|---:|
| Renda familiar até 3 salários mínimos (A+B) | 2/29 = 6,9% | 285/1.255 = 22,7% |
| Trabalho de 40 h/semana ou mais (E) | 18/29 = 62,1% | 727/1.255 = 57,9% |
| Pai com graduação/pós (E+F) | 13/29 = 44,8% | 465/1.255 = 37,1% |
| Mãe com graduação/pós (E+F) | 16/29 = 55,2% | 566/1.255 = 45,1% |
| Ensino médio todo público (A) | 3/29 = 10,3% | 634/1.255 = 50,5% |

Cada arquivo tem 30 registros UNIFOR, dos quais 29 respostas publicadas e uma
ausência; demais privadas têm 1.388 registros, 1.255 respostas e 133 ausências.
Ausência de resposta publicada pode incluir sigilo, sem classificação individual
forçada. Os denominadores são calculados independentemente por variável, mesmo
quando coincidem. Não se filtram questionários pela presença/nota de outro arquivo;
29 respondentes não são as mesmas 25 pessoas com nota por presunção posicional.
Trabalho exclui estágio/bolsas; faixas de renda são as do instrumento de 2023.

No notebook, as proporções agregadas são associadas às médias de curso somente
**após** agregação separada. Pearson com peso igual por curso, mínimo dez notas
e dez respostas por variável: 47 cursos para cada indicador. Coeficientes
exploratórios renda/trabalho/pai/mãe/escola: -0,4135/-0,0688/0,2911/0,3434/-0,3983.
Não são efeitos individuais, ajuste causal ou explicação do resultado da UNIFOR.
Essa análise complementar fica fora das figuras do relatório para economizar espaço.

## Figuras e relatório

Sete figuras novas, cada uma com PNG de 300 dpi e PDF vetorial:

- `comparacao_componentes_2023`: Geral, FG, CE em quatro grupos institucionais.
- `relacao_fg_ce_2023`: dispersão individual, com escala 0–100.
- `dispersao_fg_ce_2023`: boxplots FG/CE; fica no notebook.
- `partes_prova_2023`: objetivas e discursivas, com médias numéricas.
- `itens_fg_2023`: nove questões FG.
- `itens_ce_2023`: 29 questões CE, com cinco exclusões identificadas.
- `perfil_socioeconomico_2023`: cinco indicadores, contagens e denominadores.

Seis entram no LaTeX, uma figura principal por página de resultados. Tabelas
reduzidas usam tamanho normal ou `small`, sem `resizebox`. O boxplot e gráficos
anteriores continuam no notebook e no histórico. Todos usam dados reais validados.
PNG e PDF usam a mesma figura Matplotlib; PDFs não incluem timestamps variáveis.

`DOCUMENT/main.tex` tem capa acadêmica, metodologia/filtros, seis seções de
resultados com interpretações, discussão/conclusão e referências. Tem **dez
blocos editoriais pretendidos**, incluindo capa e referências. **Não existe PDF
compilado do relatório e o limite de dez páginas não está verificado.** A ausência
de compilador foi conferida no PATH e nos diretórios usuais de MiKTeX/TeX Live.
Nenhuma distribuição foi instalada. Os PDFs em `resultados/graficos/` são figuras,
não a compilação de `main.tex`.

O pacote `DOCUMENT/enade_2023_overleaf.zip` é autocontido, com `main.tex` na raiz,
tabelas e seis figuras. Os caminhos das figuras são ajustados somente na cópia
do ZIP. O pacote anterior `enade_2023_prism.zip` foi preservado como recebido.

### Revisão humana obrigatória no Overleaf

1. Criar projeto por **Upload Project** com `enade_2023_overleaf.zip`.
2. Selecionar `main.tex` e pdfLaTeX; compilar duas vezes.
3. Contar as páginas físicas do PDF, incluindo capa e referências: máximo dez.
4. Conferir títulos, figuras, legendas, tabelas e referências; não há validação
   visual de um PDF completo sem sua compilação.
5. Se passar de dez, cortar texto redundante ou transferir uma tabela ao notebook,
   preservando as figuras legíveis; não reduzir fontes para ocultar excesso.
6. Confirmar autores, docente e normas acadêmicas. Não foram inventados nomes.

## Validação e limites

O auditor independente relê os ZIPs oficiais com `csv`, `Counter` e `statistics`:
13.596 conferências de contagens, médias, medianas, DP, quartis, Pearson,
proporções por curso/grupo, indicadores e associações agregadas. Isso se soma às
273 conferências estatísticas anteriores. Seis testes de regressão cobrem
domínios, zero/ausência, exclusões, consistência resposta/acerto e Pearson
indefinido. A verificação LaTeX confere ambientes, chaves, citações, referências,
macros, arquivos e igualdade das tabelas com as saídas validadas.

Todas as saídas têm hashes; os ZIPs originais têm os mesmos SHA-256 da preparação
anterior. A auditoria de reprodutibilidade registra separadamente a igualdade
dos resultados com blocos de 50.000 e 17.000 linhas.
Os notebooks afetados foram executados sem células com erro; as sete figuras
foram inspecionadas, e as legendas ajustadas onde cobriam resultados.

Permanecem as ressalvas: 25 notas na UNIFOR; sigilo; perfis e participação
diferentes; curso 1125254 sem vínculo no cadastro de cursos Censo; IES 137
confessional com indicador comunitária zero. Nada disso foi corrigido por
inferência de identidade ou troca de código.

O bônus está **pendente por ausência de microdados locais de ENADE e Censo
2021**. Os dois diretórios contêm apenas `.gitkeep`. Não foram produzidos
resultados nem comparação entre notas brutas de provas diferentes. Não é
viável inferir efeitos socioeconômicos individuais ou competências temáticas
com os procedimentos aqui realizados; não se força essa interpretação.

## Arquivos criados e modificados

Novos módulos: `src/aprofundar_2023.py`, `src/verificar_aprofundamento_2023.py`,
`src/verificar_reprodutibilidade_2023.py`, `src/empacotar_relatorio_2023.py`.
Modificados: `src/preparar_2023.py`,
`src/atualizar_relatorio_2023.py`, `src/verificar_relatorio_2023.py`.
Testes: novo `tests/test_aprofundar_2023.py` e alteração em
`tests/test_preparar_2023.py`. Notebooks 05 e 06 modificados.

Novas tabelas CSV em `resultados/tabelas/`:
`componentes_aprofundados_2023`, `diferencas_componentes_2023`,
`correlacoes_fg_ce_2023`, `acertos_itens_2023`, `socioeconomico_grupos_2023`,
`socioeconomico_cursos_2023`, `indicadores_socioeconomicos_2023`,
`correlacoes_ecologicas_2023`, `dados_ecologicos_cursos_2023`.
Validações: `validacao_aprofundamento_2023.json`,
`validacao_independente_aprofundamento_2023.json` e
`validacao_reprodutibilidade_2023.json`.

Novas extrações em `dados/tratados/2023/aprofundamento/`: arq3 com vetores,
cinco arquivos socioeconômicos separados e definições das variáveis utilizadas.
O dicionário usado pela preparação foi regenerado após corrigir a continuidade
de domínios; os três CSVs anteriores mantêm os valores.

Relatório: `DOCUMENT/main.tex` revisado; tabelas novas `resumo_componentes.tex`,
`correlacoes.tex`, `partes_prova.tex`; `indicadores.tex` ampliado;
`validacao_relatorio_2023.json` atualizado; pacote Overleaf e sua validação criados.
README atualizado. As versões anteriores estão preservadas no histórico.
