# Análise exploratória e relatório — TASK 07–08

## Ordem e execução

As fases usam READ → APPLY → VERIFY → MANUAL TEST. A análise verifica os hashes e
as condições da preparação antes de calcular resultados; o relatório usa apenas
as tabelas aprovadas. Não há novas dependências, downloads, commits ou dados de 2021.

```powershell
.\.venv\Scripts\python.exe src\preparar_2023.py
.\.venv\Scripts\python.exe src\verificar_2023.py
.\.venv\Scripts\python.exe src\analisar_2023.py
.\.venv\Scripts\python.exe src\atualizar_relatorio_2023.py
.\.venv\Scripts\python.exe src\verificar_relatorio_2023.py
```

Para a experiência interativa, abra `notebooks/05_comparacao_engenharia.ipynb`,
selecione **Python (projeto-enade)** e execute todas as células. O notebook
confere `sys.executable`, executa o módulo reutilizável e mostra tabelas/figuras.
Na execução automatizada, o diretório do IPython deve ser local ao projeto para
evitar tentar gravar o histórico no perfil do usuário:

```powershell
$env:IPYTHONDIR = "$PWD\tmp\ipython_enade"
$env:JUPYTER_RUNTIME_DIR = "$PWD\tmp\jupyter_enade"
New-Item -ItemType Directory -Force -Path $env:IPYTHONDIR,$env:JUPYTER_RUNTIME_DIR | Out-Null
.\.venv\Scripts\jupyter.exe nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=projeto-enade notebooks\05_comparacao_engenharia.ipynb
```

## Definições e denominadores

- Universo: 70 IES, 79 cursos, 1.418 inscritos; 71 cursos com notas publicadas,
  dos quais 47 têm n ≥ 10. Todos os 79 permanecem na descrição geral.
- Presença operacional: TP_PRES em 555/888; neste recorte só há 555. São 1.209
  presenças (85,26%). Ausência: 222/444, 208 registros (14,67%). Um eliminado
  (334) é separado; participação e ausência não precisam somar 100%.
- Resultado oficial válido: TP_PRES=555, incluindo seis resultados suprimidos.
  As estatísticas usam 1.203 notas publicadas utilizáveis (84,84% dos inscritos),
  com presença 555, participação 333/555 e três notas disponíveis.
- UNIFOR: 30 inscritos, 25 presentes com notas (83,33%), cinco ausentes (16,67%).
- Sem fins lucrativos: categoria do cadastro IES Censo=5, incluindo ENADE 5 e 8;
  36 IES/39 cursos, 755 inscritos e 676 notas. Universidades privadas:
  CO_ORGACAD ENADE=10028, 20 IES/29 cursos, 601 inscritos e 521 notas.
  Os grupos se sobrepõem e incluem a UNIFOR. Há também linha de conferência
  para o universo sem UNIFOR (1.178 notas).

O arq3 é agregado por curso antes de qualquer junção com dados institucionais.
Só há seleção de registros por conjunto de códigos para conferir estatísticas,
sem relacionar indivíduos entre arquivos. Desvio-padrão amostral: ddof=1.
Média dos participantes pondera as médias de curso pelo número de notas;
média não ponderada atribui peso igual a cada curso com notas. Cursos sem notas
não têm médias nem recebem zero. A tabela também mostra média dos cursos com n ≥ 10.

Notas brutas (0–100) não são o Conceito Enade (indicador de curso em escala 1–5).
O projeto não calcula Conceito Enade nem testa significância ou causalidade.

## Resultados descritivos validados

Médias geral/FG/CE: UNIFOR **41,656 / 47,776 / 39,600**; universo privado
**39,326 / 51,550 / 35,234**; sem fins lucrativos **42,440 / 52,737 / 38,989**;
universidades privadas **38,164 / 50,505 / 34,033**.

UNIFOR tem nota geral e CE observadas acima do universo privado agregado e FG
abaixo dele; sua nota geral fica abaixo do subconjunto sem fins lucrativos.
São diferenças descritivas das notas publicadas, sem inferência de superioridade.
Os perfis, tamanhos, participação e contexto dos cursos não foram controlados.
As médias geral ponderada e não ponderada do universo são 39,326 e 38,005,
respectivamente, mostrando que o peso dos cursos muda o resumo do conjunto.

## Saídas e conferência manual

Em `resultados/tabelas/`:

- `indicadores_participacao_2023.csv`: denominadores e taxas de cada grupo.
- `estatisticas_grupos_2023.csv`: média, mediana, desvio-padrão e médias de cursos.
- `estatisticas_cursos_2023.csv`: os 79 cursos, inclusive n pequeno/zero, com cadastro.
- `validacao_analise_2023.json`: 273 verificações estatísticas independentes,
  hashes de entradas/saídas e caminho do Python.

Em `resultados/graficos/`: `distribuicao_notas_2023.png`,
`dispersao_cursos_2023.png`, `medias_grupos_2023.png`, `participacao_2023.png`.
Todos têm título, escala, fonte e amostras; a dispersão usa os 47 cursos com n ≥ 10.
Os outros cursos não são ocultados nas tabelas e nas estatísticas gerais.

1. Abra o notebook e confira que todas as células têm execução e nenhuma exceção.
2. Abra os três CSVs com separador `;` e confira os denominadores acima.
3. Filtre `CO_CURSO=107689` na tabela de cursos: n=25, média geral=41,656.
4. Em estatísticas de grupos, confira UNIFOR: medianas geral/FG/CE = 41,2/50,6/38,0
   e desvios-padrão = 9,3014/12,3740/10,7207.
5. Abra as quatro imagens e confira fontes, legendas, unidades e identificação da UNIFOR.
6. Leia `DOCUMENT/main.tex` e as tabelas LaTeX geradas em `DOCUMENT/tabelas/`.

## Limitações e situação do relatório

O arquivo `DOCUMENT/main.tex` recebido tinha **zero bytes**: não havia capa,
autoria ou seções anteriores recuperáveis para preservar. O relatório foi criado
usando apenas a instituição e a disciplina confirmadas no README, sem inventar
alunos, professor, entrevistas ou referências. Autoria e requisitos formais da
entrega precisam ser revisados pelo grupo. A comparação de 2021 é apenas futura.

Não foi encontrado compilador `pdflatex`, `xelatex` ou `lualatex` no PATH.
Nenhuma distribuição foi instalada. A validação estática verifica ambientes,
chaves, referências, citações, arquivos de figuras/tabelas e correspondência das
tabelas com os CSVs validados. Sem compilação, paginação e aparência final do PDF
permanecem para revisão humana.

Para compilar em uma instalação LaTeX existente, na raiz:

```powershell
Set-Location DOCUMENT
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Ressalvas de dados: curso 1125254 sem cadastro Censo, IES confessional sem
indicador comunitária, seis resultados suprimidos e heterogeneidade das amostras.
As notas suprimidas não podem ser reconstruídas; o manual impede associação
individual entre arquivos. A análise usa somente as notas publicadas.
