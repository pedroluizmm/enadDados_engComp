# ENADE 2023 — aprofundamento e correções finais (TASK 13)

## Estado atual e fontes de geração

A revisão aplica as ressalvas da auditoria sem repetir a preparação nem refazer
as análises aprovadas. Os resultados anteriores permanecem idênticos byte a byte.
O estado anterior foi preservado em `historico/task13_antes/`; o histórico das
TASK 09–11 está em `historico/task09_11_antes/`.

Antes desta revisão, `DOCUMENT/main.tex` era a fonte editorial escrita diretamente;
`src/atualizar_relatorio_2023.py` gerava apenas tabelas e indicadores. Agora:

- **Fonte editorial:** `DOCUMENT/modelos/main.tex`.
- **Gerador:** `src/atualizar_relatorio_2023.py` valida as saídas, gera indicadores
  e tabelas e reproduz o modelo em `DOCUMENT/main.tex`.
- **Gráficos:** `src/graficos_2023.py`, usado tanto por `aprofundar_2023.py` quanto
  pelo fluxo de revisão, com os mesmos dados aprovados.
- **Correção discursiva e apresentação:** `src/auditoria_fg_2023.py`.
- **Pacote local:** `src/empacotar_relatorio_2023.py` produz
  `DOCUMENT/enade_2023_overleaf.zip`, sem importação ou envio externo.

O empacotador verifica a validação já existente, sem executar o gerador ou
análises. Os arquivos Overleaf e Prism são cópias idênticas e incluem um manifesto
de versão; há também uma cópia com versão no nome. O diagnóstico e a comparação
dos hashes estão em [versionamento do pacote](versionamento_pacote_2023.md).

Alterações editoriais devem ser feitas no modelo e aplicadas pelo gerador.
A verificação estática exige igualdade entre modelo e relatório gerado.

## Aplicar somente esta revisão

Na raiz, PowerShell, com os dados e a `.venv` existentes:

```powershell
.\.venv\Scripts\python.exe src/auditoria_fg_2023.py
.\.venv\Scripts\python.exe src/atualizar_relatorio_2023.py
.\.venv\Scripts\python.exe src/verificar_task13.py
.\.venv\Scripts\python.exe src/empacotar_relatorio_2023.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Esse fluxo relê resultados existentes, calcula apenas a distinção discursiva
solicitada e regenera a apresentação. Não executa preparação ou novas análises.
Os notebooks 01–04 são estruturas iniciais incompletas, não etapas obrigatórias.
O notebook 05 consulta as tabelas e figuras aprovadas, sem reprocessá-las; o 06
documenta a falta de dados de 2021. Não houve instalação ou download nesta tarefa.

Para reconstruir todo o projeto em outro momento, a sequência completa está no
README. A reprodução anterior com blocos de 50.000/17.000 linhas permanece como
evidência histórica; seus hashes de figuras anteriores não representam a revisão
visual atual. `validacao_task13.json` documenta o estado desta entrega.

## Correção da interpretação da FG discursiva

O arq3 contém uma única questão discursiva de FG. A classificação usa
`TP_SFG_D1`, consultado no dicionário oficial local:

- 333: questão em branco, nota zero;
- 335: resposta nula;
- 336: resposta divergente da temática;
- 555: questão com resultado válido.

Não se identifica branco pela nota zero: uma resposta de código 555 pode ter
nota zero e permanece no grupo válido. Não são feitos vínculos individuais
entre arquivos. O universo é o mesmo de 1.203 notas publicadas utilizáveis.

| Indicador | UNIFOR | Demais privadas |
|---|---:|---:|
| Todos os resultados | 25 | 1.178 |
| Questão em branco (333) | 8/25 = 32,0% | 70/1.178 = 5,9% |
| Média de todos | 29,996 ≈ 30,00 | 45,007 ≈ 45,01 |
| Sem brancos (exclui apenas 333) | 44,112 (n=17) | 47,850 (n=1.108) |
| Respostas com resultado válido (555) | 44,112 (n=17) | 48,255 ≈ 48,26 (n=1.098) |
| Respostas nulas (335) | 0 | 6 |
| Respostas fora da temática (336) | 0 | 4 |

**Nova interpretação:** a diferença agregada de 15,01 pontos é acentuada pela
maior frequência de brancos na UNIFOR; entre respostas válidas, a diferença é
4,14 pontos. A comparação condicional descreve grupos selecionados por resposta,
não identifica efeito causal ou motivos dos brancos, nem demonstra dificuldade
de escrita ou falta de conhecimento. Não foram acrescentados testes inferenciais.

O rótulo da auditoria “entre quem respondeu” foi explicitado como **código 555**:
1.098 não equivale ao total sem brancos (1.108), pois exclui também os dez casos
335/336. Isso evita chamar nulos ou fora da temática de brancos.

Ressalva preservada: três casos de código 336 têm NT_DIS_FG positivas (9, 11 e
14), com componente de Língua Portuguesa e conteúdo zero; o quarto tem nota zero.
Os valores publicados são mantidos, apesar da descrição genérica “nota=zero” no
dicionário. Não se fez recodificação ou interpretação adicional desses casos.

Saídas: `fg_discursiva_respostas_2023.csv` e `validacao_fg_discursiva_2023.json`.
A função Pandas foi conferida independentemente por releitura do ZIP oficial com
`csv`/`statistics`: 50 verificações, usando as situações e notas do mesmo registro.

## Resultados e metodologia preservados

Filtros: ano 2023, grupo 6411 (Engenharia de Computação I), modalidade presencial
1 e categorias ENADE 4/5/8. ENADE 4 corresponde a Censo 4; ENADE 5/8, a Censo 5.
Junções institucionais usam códigos, com validação de cardinalidade; notas e
questionários são agregados por curso antes de relacionar arquivos distintos.
Não há deduplicação de registros de estudantes, imputação de notas ou alinhamento
posicional entre arquivos.

Recorte confirmado: 70 IES, 79 cursos, 1.418 inscritos disponibilizados, 1.209
presentes, 1.203 notas publicadas utilizáveis, 208 ausentes, seis resultados
suprimidos e um eliminado. UNIFOR: IES 555, curso 107689, 30 inscritos, 25 notas
e cinco ausentes. Presença 555 inclui sigilo; notas utilizáveis exigem presença
555, participação 333/555 e NT_GER/NT_FG/NT_CE disponíveis. Zeros são preservados.

| Média | UNIFOR (n=25) | Universo privado (n=1.203) | Sem fins lucrativos (n=676) |
|---|---:|---:|---:|
| Geral | 41,656 | 39,326 | 42,440 |
| FG | 47,776 | 51,550 | 52,737 |
| CE | 39,600 | 35,234 | 38,989 |

O referencial sem fins lucrativos contextualiza a média geral menor da UNIFOR
e seu CE próximo ao do grupo. Os grupos institucionais se sobrepõem e incluem
a UNIFOR; “demais privadas” a exclui. Não há conclusão de superioridade geral.
Pearson FG–CE: UNIFOR 0,25077 (n=25), universo 0,31325 (n=1.203), demais privadas
0,31622 (n=1.178). DP é amostral. Não há inferência causal ou teste de superioridade.

Os pesos oficiais permanecem FG 65/35 (objetiva/discursiva), CE 90/10 e geral
25% FG/75% CE, conforme a Nota Técnica 12/2024 citada no relatório. Os pesos
desatualizados 60/40 e 85/15 do XLSX não são utilizados. As notas oficiais não
são recalculadas ou substituídas.

## Questões e contexto socioeconômico

Preservados os vetores, percentuais e denominadores por item. Há nove FG válidos
e 24 CE válidos entre 29 posições. Q17/18/19/25/34 do CE foram excluídas por
discriminação: ficam sem percentual, nunca recebem zero como erro. Escolhas,
gabaritos e acertos são conferidos dentro do arq3.

Os destaques FG Q3/Q4 e CE Q23/Q28 foram escolhidos **após examinar todos os
itens**, por serem os extremos positivo/negativo da diferença UNIFOR–demais
privadas em cada componente. São achados exploratórios, sem testes múltiplos,
fragilidades comprovadas ou atribuição de competências. Na UNIFOR, uma resposta
equivale a quatro pontos percentuais.

Foram preservadas as cinco marginais socioeconômicas, com denominadores próprios:

| Indicador | UNIFOR | Demais privadas |
|---|---:|---:|
| Renda familiar até 3 salários mínimos | 2/29 = 6,9% | 285/1.255 = 22,7% |
| Trabalho de 40 h/semana ou mais | 18/29 = 62,1% | 727/1.255 = 57,9% |
| Pai com graduação/pós-graduação | 13/29 = 44,8% | 465/1.255 = 37,1% |
| Mãe com graduação/pós-graduação | 16/29 = 55,2% | 566/1.255 = 45,1% |
| Ensino médio todo em escola pública | 3/29 = 10,3% | 634/1.255 = 50,5% |

Cada variável tem uma ausência publicada na UNIFOR e 133 nas demais privadas.
Trabalho exclui estágio e bolsas; as faixas de renda seguem 2023. Não se relacionam
as 29 respostas às 25 notas por presunção de identidade.

Nos 47 cursos com pelo menos dez notas e dez respostas por indicador, proporções
de baixa renda e de ensino médio todo público se associam negativamente à média
geral (Pearson -0,413471 e -0,398259). A unidade é **curso**, com peso igual;
não existe aqui associação individual renda–nota. Correlação não estabelece
causalidade nem atribui diferenças exclusivamente ao perfil socioeconômico.
As outras correlações preservadas são trabalho -0,068826, pai 0,291139 e mãe
0,343449. Nenhuma foi recalculada para alterar as conclusões aprovadas.

## Apresentação e redução do relatório

O relatório reúne objetivo/metodologia, resultados em subseções e uma seção de
discussão, limitações e conclusão. Foram removidas oito quebras `clearpage`,
repetições entre tabelas/parágrafos e introduções redundantes. A capa e referências
permanecem. As figuras mantêm largura de página e interpretações imediatamente
próximas; não foram reduzidas para ocultar excesso de páginas.

Oito figuras PNG 300 dpi/PDF vetorial usam os mesmos dados aprovados. Seis entram
no relatório: médias institucionais, diagnóstico da FG discursiva, relação FG–CE,
itens FG, itens CE e perfil socioeconômico. Partes da prova e boxplots ficam como
complementos no notebook.

Mudanças visuais: legendas fora da área de dados, vírgula decimal, unidades
uniformes, fonte oficial uma única vez por figura, menos margens vazias e eixo
socioeconômico estritamente 0–100%. Detalhes metodológicos ficam nas legendas
LaTeX, sem repetir notas inteiras embutidas nos gráficos. O novo gráfico de FG
separa frequência de brancos e três denominadores das médias.

`validacao_visual_graficos_2023.json` registra os limites dos eixos e o teste de
que as legendas não interceptam os eixos de dados. A inspeção visual das imagens
complementa essa verificação geométrica; não substitui o PDF completo.

## Validação, pacote e pendências

- O verificador anterior continua conferindo 13.596 resultados independentes.
- A distinção discursiva acrescenta 50 conferências no arq3 oficial.
- Oito testes incluem zero válido versus branco, 335/336 separados e interrupção
  diante de situação inesperada, além das regressões anteriores.
- Os 32 arquivos protegidos (dados brutos/tratados e CSVs já existentes) são
  comparados com os hashes anteriores à TASK 13. Isso inclui os diretórios de 2021.
- O gerador reproduz o modelo, as macros e as tabelas; a validação estática
  confere chaves, ambientes, referências, citações e dependências.
- O pacote é reaberto para conferir integridade, conteúdo de `main.tex` e todos
  os arquivos referenciados, inclusive figuras e indicadores.

O ZIP autocontido mantém `main.tex` na raiz, `tabelas/` e `graficos/`, ajustando
os caminhos apenas na cópia. Nenhum serviço externo foi usado ou projeto
importado automaticamente. O usuário poderá importá-lo posteriormente no Prism
ou Overleaf e selecionar pdfLaTeX.

**Não há compilador LaTeX disponível e nenhuma distribuição foi instalada.**
Não foi produzido PDF compilado do relatório. Quantidade de páginas, cumprimento
do limite obrigatório de dez incluindo referências e layout final continuam
pendentes. A fonte não usa contagem de “blocos editoriais” como comprovação de
páginas. Após a importação manual: compilar duas vezes, contar páginas físicas,
inspecionar cortes/legendas/tabelas/referências e confirmar autoria/docente.

O bônus de 2021 permanece pendente; só há `.gitkeep` nos diretórios. Não foram
baixados ou alterados microdados dessa edição. Permanecem as ressalvas cadastrais
do curso 1125254 e da IES 137. Nenhum dado foi ajustado para coincidir com referência.

## Arquivos da revisão

Novos: `src/auditoria_fg_2023.py`, `src/graficos_2023.py`, `src/verificar_task13.py`,
`tests/test_auditoria_fg_2023.py`, `DOCUMENT/modelos/main.tex`,
`resultados/tabelas/fg_discursiva_respostas_2023.csv`, suas validações e
`fg_discursiva_resposta_2023.png/.pdf`.

Modificados: `src/aprofundar_2023.py` (usa o mesmo renderer e conserva a correção
em reconstruções completas), `src/atualizar_relatorio_2023.py`,
`src/verificar_relatorio_2023.py`, `src/empacotar_relatorio_2023.py`,
`DOCUMENT/main.tex`, `DOCUMENT/tabelas/indicadores.tex`, pacote ZIP e validações,
sete figuras anteriores em ambos os formatos, notebook 05, README e esta documentação.
Os CSVs das análises anteriores e todos os arquivos de dados permanecem intactos.
