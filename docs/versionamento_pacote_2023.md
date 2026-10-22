# Verificação do versionamento do pacote LaTeX

Fluxo: READ → VERIFY → APPLY → VERIFY. Nenhuma análise estatística foi executada.

## Diagnóstico anterior à correção

`DOCUMENT/main.tex` e `DOCUMENT/modelos/main.tex` eram idênticos byte a byte e
coincidiam com a versão aprovada em `validacao_relatorio_2023.json`:

`94802581ae46d8dcc6f32ed32ea1d64a3540549c0e7ab5c394c07bb7fd8c5b2f`

O `main.tex` do ZIP **Overleaf local já continha a TASK 13**. Seu texto era
igual ao relatório local após a substituição exclusiva de caminhos
`../resultados/graficos/` por `graficos/`, necessária à estrutura autocontida.
Essa transformação explica seu SHA-256 diferente:

`4aa8b4b4f8ed3f7b87ce4a0dd2ea5a375c568fa754a204f82098b6288f138092`

O pacote `enade_2023_overleaf.zip` anterior tinha SHA-256:

`08c660226eec1693d7b3d5d6cc65a8067153db0f1fdae57b62150fd15a3362fa`

Por outro lado, `DOCUMENT/enade_2023_prism.zip` continha **o relatório antigo**,
com quatro figuras antigas e sem a análise atual da não resposta discursiva ou
dos indicadores socioeconômicos. Seu `main.tex` tinha SHA-256:

`b02c8b6f966b39037660605c4c29ae314f4adde43e9cdd369f3f7599301cd6b7`

A divergência local identificada era a coexistência de dois ZIPs com versões
diferentes: o gerador atualizava o pacote Overleaf e deixava o arquivo de nome
Prism antigo. Não foi reproduzida uma versão antiga dentro do ZIP Overleaf local.
Sem acesso ao conteúdo efetivamente importado no Prism, não se pode confirmar
se foi usado o outro ZIP, uma cópia anterior ou um projeto anterior. Não se
atribui o problema a cache ou ao serviço sem evidência.

Os arquivos anteriores foram preservados em
`historico/versionamento_pacote_antes/`, junto do empacotador anterior e dos hashes
das 36 entradas protegidas.

## Correção aplicada

- O empacotador exige igualdade literal entre modelo e relatório, e SHA-256
  correspondente à validação existente. Não regenera o relatório ou recalcula
  estatísticas: rejeita uma fonte divergente ou não validada.
- Confere os marcadores TASK 13 e os indicadores já gerados: 32,0% (8/25)
  em branco na UNIFOR, 5,9% no referencial, notas de 44,11/48,26 entre respostas
  válidas e a presença das análises socioeconômicas.
- Cria a cópia de distribuição em `DOCUMENT/pacote_latex/`, com `main.tex`,
  indicadores e seis figuras, todos com caminhos relativos a essa raiz.
- Acrescenta `MANIFESTO_VERSAO.json` e instruções com identificação do conteúdo.
- Gera ZIP determinístico: o mesmo conteúdo reproduz os mesmos bytes e versão.
- Mantém `enade_2023_overleaf.zip` e `enade_2023_prism.zip` idênticos, além de uma
  cópia com versão no nome, eliminando a ambiguidade anterior.

Versão desta entrega: **TASK13-ab7dd05d5a58**.

Pacotes idênticos:

- `DOCUMENT/enade_2023_overleaf.zip`;
- `DOCUMENT/enade_2023_prism.zip`;
- `DOCUMENT/enade_2023_TASK13-ab7dd05d5a58.zip`.

SHA-256 dos três:

`c9dcff511730023afe39bbe3b896411d04d7b67c4d4528d66c168126df7d83d9`

## Verificação após a reconstrução

Os ZIPs foram reabertos e submetidos à verificação CRC e SHA-256 de **todos os
dez membros** contra os arquivos locais em `DOCUMENT/pacote_latex/`. Indicadores
e figuras também foram comparados diretamente com suas fontes locais originais.
O `main.tex` foi comparado com a fonte validada após desfazer somente o ajuste
de caminhos. Não houve mudança de texto analítico.

Estrutura:

```text
main.tex
tabelas/indicadores.tex
graficos/comparacao_componentes_2023.pdf
graficos/fg_discursiva_resposta_2023.pdf
graficos/relacao_fg_ce_2023.pdf
graficos/itens_fg_2023.pdf
graficos/itens_ce_2023.pdf
graficos/perfil_socioeconomico_2023.pdf
MANIFESTO_VERSAO.json
LEIA-ME.txt
```

`DOCUMENT/validacao_pacote_2023.json` registra os hashes locais/internos e a
identificação da versão. `DOCUMENT/validacao_versionamento_2023.json` registra
a preservação dos dados, CSVs e fontes validadas. Os quatro testes específicos
conferem igualdade de fontes/dependências/cópias, rejeição de fonte não validada,
detecção de membro adulterado e reprodução binária do ZIP.

Para reempacotar apenas uma fonte já validada:

```powershell
.\.venv\Scripts\python.exe src/empacotar_relatorio_2023.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_empacotar_relatorio_2023.py -v
```

Não houve importação automática no Prism ou uso de serviços externos. A
paginação e o limite de dez páginas continuam dependentes de compilação.
