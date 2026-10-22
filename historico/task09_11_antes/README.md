# Análise de Desempenho no ENADE — Engenharia e Ciência da Computação (UNIFOR)

Projeto acadêmico desenvolvido para a disciplina de **Ciência dos Dados** da **Universidade de Fortaleza (UNIFOR)**.

## 🎯 Objetivos do Projeto

- **Objetivo Principal:** Analisar o desempenho dos estudantes concluintes de **Engenharia da Computação da UNIFOR** na edição do **ENADE 2023**, comparando os resultados com cursos equivalentes de outras instituições de ensino superior privadas.
- **Análise Complementar (Bônus):** Comparar indicadores do curso de Engenharia da Computação com **Ciência da Computação da própria UNIFOR** (ENADE 2021). Ressalta-se que, por pertencerem a áreas e edições distintas do ENADE, **não serão comparadas diretamente notas brutas** como se fossem provas idênticas, mas sim indicadores relativos, padronizados ou contextuais.

---

## 📁 Estrutura do Repositório

```text
projeto-enade/
├── README.md               # Apresentação e documentação geral do projeto
├── .gitignore              # Arquivos e pastas ignorados no controle de versão
├── requirements.txt        # Dependências e bibliotecas Python necessárias
├── dados/
│   ├── brutos/             # Microdados originais obtidos do INEP (não versionados)
│   │   ├── enade_2023/     # Microdados do ENADE 2023
│   │   ├── censo_2023/     # Microdados do Censo da Educação Superior 2023
│   │   ├── enade_2021/     # Microdados do ENADE 2021
│   │   └── censo_2021/     # Microdados do Censo da Educação Superior 2021
│   └── tratados/           # Bases processadas e consolidadas para análise
├── notebooks/              # Jupyter Notebooks de inspeção, processamento e análise
│   ├── 01_inspecao_censo.ipynb
│   ├── 02_inspecao_enade.ipynb
│   ├── 03_identificacao_cursos.ipynb
│   ├── 04_preprocessamento.ipynb
│   ├── 05_comparacao_engenharia.ipynb
│   └── 06_comparacao_bonus.ipynb
├── src/                    # Módulos e scripts reutilizáveis em Python
├── resultados/             # Saídas geradas pelas análises
│   ├── graficos/           # Visualizações e figuras exportadas
│   └── tabelas/            # Tabelas resumo e relatórios estatísticos
└── docs/
    └── fontes_de_dados.md  # Links oficiais e documentação dos dados do INEP
```

---

## 🚀 Como Executar

1. Instalar as dependências do projeto listadas em `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
2. Realizar o download dos microdados do INEP nas pastas correspondentes em `dados/brutos/` (conforme instruções em [`docs/fontes_de_dados.md`](docs/fontes_de_dados.md)).
3. Abrir e executar os notebooks na ordem numérica estabelecida.

### Preparação, análise e relatório de 2023

Os ZIPs locais de 2023 e a `.venv` existente são suficientes; não é necessário
instalar novas bibliotecas. Na raiz, em PowerShell:

```powershell
.\.venv\Scripts\python.exe src\preparar_2023.py
.\.venv\Scripts\python.exe src\verificar_2023.py
.\.venv\Scripts\python.exe src\analisar_2023.py
.\.venv\Scripts\python.exe src\atualizar_relatorio_2023.py
.\.venv\Scripts\python.exe src\verificar_relatorio_2023.py
```

O notebook `05_comparacao_engenharia.ipynb` está executado e usa o kernel
**Python (projeto-enade)**. [Preparação corrigida](docs/preparacao_2023.md) e
[metodologia, resultados e testes manuais](docs/analise_2023.md) documentam as fases.
Resultados: 70 IES, 79 cursos, 1.418 inscritos e 1.203 notas publicadas válidas;
UNIFOR: 30 inscritos e 25 notas. Tabelas e quatro gráficos estão em `resultados/`.

[Relatório LaTeX](DOCUMENT/main.tex): criado porque o arquivo recebido estava
vazio; tabelas e indicadores são gerados dos resultados validados. Sem compilador
LaTeX disponível, passou por verificações estáticas; autoria e aparência final
do PDF precisam de revisão humana. A comparação com 2021 continua futura.

