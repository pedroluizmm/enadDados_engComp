# Preparação corrigida — ENADE/Censo 2023 (TASK 06)

Filtro: ano 2023, CO_GRUPO=6411, CO_CATEGAD em 4/5/8, CO_MODALIDADE=1.
O dicionário ENADE define **8. Comunitária/Confessional em E22**. A interpretação
anterior estava errada: o leitor interrompia o domínio em linhas vazias. Agora a
aba é identificada por nome normalizado e os domínios por estrutura, preservando
intervalos vazios e registrando linhas de origem. Os ZIPs são lidos diretamente,
em chunks, com seleção de colunas. Não há novas instalações ou alteraçães nos brutos.

Mapeamento: ENADE 4→Censo 4; ENADE 5/8→Censo 5. IN_COMUNITARIA e
IN_CONFESSIONAL são preservados em ambos os cadastros Censo, com sufixos.
Categoria 5 tem ambos zero neste recorte; 8 tem pelo menos um igual a um.

**Ressalva:** IES 137, CENTRO UNIVERSITÁRIO SAGRADO CORAÇÃO, curso 1125254,
categoria ENADE 8, tem IN_COMUNITARIA=0 e IN_CONFESSIONAL=1 no cadastro IES.
A exigência estrita comunitária=1 não ocorre nesse caso, mas a classificação
é compatível com o domínio Comunitária/Confessional. O campo
RESSALVA_CAT8_COMUNITARIA_ZERO explicita o caso, sem alterar o indicador.
Esse curso não aparece em nenhuma IES no cadastro de cursos Censo. A IES 137
foi encontrada. Inspeção dos seus 64 registros de cursos encontrou Engenharia
de Computação sob código 1637080. Não existe comprovação de equivalência ou
sucessão; não se fez pareamento por nome ou substituição de código. O curso
ENADE permanece, com atributos de curso Censo ausentes e atributos da IES presentes.

Resultado: **70 instituições, 79 cursos, 1.418 inscritos**, 1.209 presenças
válidas oficiais (TP_PRES=555), 1.203 notas publicadas válidas. UNIFOR: 30
inscritos, 25 com notas e 5 ausentes.

O Manual ENADE 2023, pp. 6–7, explica a separação/ordenação dos arquivos para
anonimização; p. 7 informa a supressão de resultados quando existe apenas uma
presença válida (555) no curso. O manual foi lido com pypdf já instalado no
Python do sistema, sem instalação; pipelines e notebook usam a .venv.
Há seis resultados suprimidos no universo corrigido: cinco do recorte anterior
mais um adicionado com categoria 8. Todos têm presença 555, notas vazias e apenas
uma presença 555 no curso. SITUACAO_RESULTADO separa suprimido_sigilo dos 208
ausentes (207 código 222 e 1 código 444), 1.203 presentes com nota e um eliminado
(334). A UNIFOR tem cinco ausentes, distintos dos resultados suprimidos.
IN_NOTA_VALIDA indica nota **publicada utilizável**: presença 555, participação
333/555, três notas principais disponíveis. Zero é mantido; vazios e ponto são
ausências, sem imputação. A presença válida oficial inclui os seis suprimidos.

Cadastro: uma linha por curso. Arq1/arq3: registros anônimos com repetições
originais preservadas. Somente o cadastro é deduplicado. Junções Censo por
CO_IES+CO_CURSO (1:1), IES por CO_IES (N:1). Não há associação individual entre
arquivos, identificação artificial ou alinhamento posicional. CSVs UTF-8 BOM,
separador ponto e vírgula, ponto decimal e células vazias como ausências.

## Reexecutar e conferir manualmente (PowerShell, na raiz)

```powershell
.\.venv\Scripts\python.exe src\preparar_2023.py
.\.venv\Scripts\python.exe src\verificar_2023.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
$c = Import-Csv dados\tratados\2023\cadastro_comparaveis.csv -Delimiter ';'
$n = Import-Csv dados\tratados\2023\enade_arq3_desempenho.csv -Delimiter ';'
($c.CO_IES | Sort-Object -Unique).Count # 70
$c.Count # 79
$n.Count # 1418
$c | Where-Object CO_IES -eq '555' | Format-List
($n | Where-Object CO_CURSO -eq '107689').Count # 30
($n | Where-Object { $_.CO_CURSO -eq '107689' -and $_.IN_NOTA_VALIDA -eq '1' }).Count # 25
$n | Group-Object SITUACAO_RESULTADO | Select-Object Name,Count
$c | Where-Object VINCULO_CURSO_CENSO -eq 'left_only' | Format-List
$s = Get-Content dados\tratados\2023\resumo_tecnico.json -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($e in $s.zip_antes.PSObject.Properties) {
  [pscustomobject]@{Arquivo=$e.Name; Intacto=((Get-FileHash -LiteralPath $e.Name -Algorithm SHA256).Hash.ToLower() -eq $e.Value.sha256)}
}
```

Reexecução opcional com --chunksize 17000 deve preservar os hashes dos CSVs.
O pipeline relê os CSVs integralmente, compara valores, ausências e multiplicidade;
verifica cardinalidades, escala, contagens por curso e hashes dos ZIPs. O verificador
repete condições independentemente nos CSVs gravados. Os detalhes constam em
resumo_tecnico.json e dicionarios_utilizados.json.
