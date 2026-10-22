# Fontes Oficiais de Dados

Este documento registra as fontes oficiais de dados fornecidas para o desenvolvimento do projeto e as instruções sobre onde alocar os arquivos após o download.

---

## 🔗 Links Oficiais (INEP)

1. **Microdados do ENADE:**
   - **URL Oficial:** [https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enade](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enade)
   - **Edições Utilizadas:**
     - **2023:** Avaliação de cursos da área de Engenharia (inclui Engenharia da Computação).
     - **2021:** Avaliação de cursos da área de Computação / Exatas (inclui Ciência da Computação).

2. **Microdados do Censo da Educação Superior:**
   - **URL Oficial:** [https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior)
   - **Edições Utilizadas:**
     - **2023:** Dados institucionais e de cursos para o ano de 2023.
     - **2021:** Dados institucionais e de cursos para o ano de 2021.

---

## 📂 Mapeamento de Diretórios para os Arquivos Baixados

Após realizar o download e descompactação dos microdados oficiais do INEP, os arquivos devem ser organizados estritamente nas respectivas pastas dentro de `dados/brutos/`:

| Base de Dados | Edição | Diretório Destino no Projeto |
| :--- | :--- | :--- |
| **ENADE** | **2023** | `dados/brutos/enade_2023/` |
| **Censo da Educação Superior** | **2023** | `dados/brutos/censo_2023/` |
| **ENADE** | **2021** | `dados/brutos/enade_2021/` |
| **Censo da Educação Superior** | **2021** | `dados/brutos/censo_2021/` |

> **Nota:** As pastas de 2023 e 2021 são mantidas rigorosamente separadas para evitar conflito entre os esquemas e definições das edições.

