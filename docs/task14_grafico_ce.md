# TASK 14 — Figura 5: diferenças de acerto no Componente Específico

## Escopo e dados

Foi substituída somente a Figura 5, mantendo o caminho
`resultados/graficos/itens_ce_2023.pdf` usado pelo LaTeX. A fonte editorial
`DOCUMENT/modelos/main.tex` teve alteradas apenas a legenda e a interpretação
da figura CE; o restante do relatório permanece idêntico. Nenhum outro gráfico,
CSV de resultados ou microdado foi alterado.

A versão anterior foi preservada byte a byte em
`resultados/graficos/itens_ce_absolutos_2023.png/.pdf` e está exibida no notebook 05
como consulta histórica. O estado anterior de código, relatório e notebook e os
hashes dos arquivos protegidos estão em `historico/task14_antes/`.

Fonte dos valores: `resultados/tabelas/acertos_itens_2023.csv`, com hash conferido
contra a validação existente. Cada questão válida usa efetivamente 25 respostas
UNIFOR e 1.178 das demais privadas. Não foram reexecutadas preparação, análises
anteriores ou testes estatísticos.

## Visualização

- 24 questões válidas, em ordem decrescente de diferença;
- diferença = percentual UNIFOR menos percentual das demais privadas, em p.p.;
- linha vertical em zero e escala simétrica de −30 a +30 p.p., obtida arredondando
  para cima o maior módulo observado (25,789474) ao próximo múltiplo de cinco;
- cores discretas para o sinal, com significado explicitado, sem símbolos de
  significância; mesma forma/tamanho dos pontos;
- duas colunas alinhadas com os percentuais absolutos de cada grupo;
- Q23, Q30 e Q28 em negrito e com diferença anotada, como destaques exploratórios;
- Q17, Q18, Q19, Q25 e Q34 fora da área de dados, identificadas em nota como
  excluídas por discriminação, sem receber percentual zero;
- separador decimal brasileiro; fonte oficial e notas metodológicas legíveis.

Valores conferidos:

| Questão | UNIFOR | Demais privadas | Diferença |
|---|---:|---:|---:|
| Q23 | 60,0% (15/25) | 34,210526% (403/1.178) | +25,789474 p.p. |
| Q30 | 80,0% (20/25) | 56,706282% (668/1.178) | +23,293718 p.p. |
| Q28 | 32,0% (8/25) | 47,623090% (561/1.178) | −15,623090 p.p. |

Os 24 percentuais UNIFOR, 24 percentuais do referencial e 24 diferenças foram
reconciliados independentemente com contagens/denominadores da tabela original.
Os percentuais e as diferenças são arredondados apenas para exibição. Cada
acerto da UNIFOR representa quatro pontos percentuais. A seleção dos destaques
foi feita após examinar todos os itens e não demonstra significância ou
fragilidade específica.

## Geradores e reprodução limitada à tarefa

Novo módulo `src/grafico_ce_diferencas_2023.py`: prepara a comparação validando
situações e denominadores, renderiza apenas CE e atualiza somente seus hashes e
metadados. `src/graficos_2023.py` delega o CE à mesma função nas reconstruções
completas; os demais blocos de gráficos não foram alterados ou executados.
O renderer isola seu estilo para reproduzir a mesma figura mesmo quando chamado
de outros contextos Matplotlib/Seaborn.

```powershell
.\.venv\Scripts\python.exe src/grafico_ce_diferencas_2023.py
.\.venv\Scripts\python.exe src/atualizar_relatorio_2023.py --somente-texto
.\.venv\Scripts\python.exe src/verificar_relatorio_2023.py --somente-estatica
.\.venv\Scripts\python.exe src/empacotar_relatorio_2023.py
```

Esses comandos não regeneram os demais gráficos nem recalculam as análises.
O verificador estático confirma que todas as tabelas LaTeX continuam iguais às
da validação anterior, além de conferir ambientes, macros, citações e referências.
O verificador histórico TASK 13 foi compatibilizado com o eixo simétrico de CE;
não foi executado nesta tarefa, pois seu fluxo regenera todas as figuras.

## Validação e entrega

Cinco testes específicos cobrem as 24 diferenças, a ordenação/extremos, rejeição
de zero em item excluído, denominador incorreto, par ausente e independência do
estilo gráfico. Os quatro testes de empacotamento também passaram: nove testes
de software, sem novos testes estatísticos.

Foram verificadas geometricamente a ausência de sobreposição dos números, a
posição da legenda, o cabeçalho das colunas, as notas e a ausência de cortes.
A imagem foi inspecionada visualmente. O notebook 05 foi executado em modo de
consulta, exibindo a nova figura e a antiga, sem regenerar outros gráficos.

O pacote Overleaf e o pacote Prism são idênticos, autocontidos e identificados
como TASK 14, com manifesto e cópia versionada. Os ZIPs foram reabertos para
conferir todos os membros por SHA-256 contra os arquivos locais de distribuição.
`DOCUMENT/validacao_pacote_2023.json` informa o nome da versão vigente e hashes.
`resultados/tabelas/validacao_figura_ce_2023.json` contém as 24 linhas efetivamente
plotadas, a escala e as 72 conferências. `validacao_task14.json` registra a
preservação dos arquivos e do restante do relatório.

**Sem compilador LaTeX local; nenhuma distribuição foi instalada.** Não existe
PDF completo compilado nesta tarefa e o limite de dez páginas, incluindo capa
e referências, continua pendente de confirmação. A nova figura mantém largura
de página e altura menor que a anterior (7,5 contra 8,2 polegadas no arquivo),
sem reduzir as fontes principais. Isso não comprova a paginação final.
