# Design Decisions

Este documento registra decisões técnicas relevantes tomadas ao longo do
desenvolvimento do projeto, junto com o raciocínio por trás de cada uma.

## 1. Full Load vs. Incremental (camada raw → bronze)

**Decisão:** todos os jobs de transformação usam **full load** (sobrescrita
completa do arquivo a cada execução), não carga incremental.

**Raciocínio:** o dataset Olist é estático (snapshot histórico do Kaggle, sem
novas linhas chegando ao longo do tempo). Carga incremental existe para reduzir
o custo de reprocessamento recorrente quando há alto volume e alta frequência
de atualização, nenhuma das duas condições se aplica aqui.

## 2. Tratamento de erros por etapa (try/except)

**Decisão:** cada job de transformação é dividido em 3 etapas com tratamento
de erro independente: (1) leitura do S3 + conversão para DataFrame, (2)
tipagem das colunas, (3) conversão para Parquet + escrita no S3.

**Raciocínio:** as etapas têm dependência sequencial, não faz sentido tipar
dados que não foram lidos com sucesso, nem escrever dados que não foram
tipados corretamente. Cada bloco `except` usa `raise` para interromper a
execução imediatamente ao primeiro erro, evitando que etapas subsequentes
rodem sobre dados incompletos ou inválidos, e ainda registra uma mensagem
customizada por etapa, facilitando o diagnóstico do que falhou (importante
quando o script já estiver rodando dentro do Glue, sem acompanhamento em
tempo real, dependendo apenas dos logs).

## 3. Responsabilidade do Glue Crawler

**Decisão:** os scripts Python de transformação são responsáveis por definir
explicitamente os tipos de dado corretos (strings, datas) antes de gravar o
Parquet. O Glue Crawler é usado apenas para catalogar automaticamente o
schema já correto no Glue Data Catalog, não para corrigir tipos.

**Raciocínio:** o Crawler infere e registra o schema a partir dos arquivos já
gravados no S3; ele não participa da geração do arquivo. Se um tipo for
inferido incorretamente pelo pandas na hora da escrita (ex: uma coluna de
data sendo gravada como texto), esse erro fica permanentemente gravado no
Parquet, e o Crawler apenas catalogaria esse erro, sem corrigi-lo.

## 4. Dados sensíveis em campos de texto livre (PII)

**Contexto:** a tabela `order_reviews` contém dois campos de texto livre
preenchidos pelos próprios clientes (`review_comment_title` e
`review_comment_message`). Campos desse tipo, em ambientes reais, representam
um risco de conter PII (Personally Identifiable Information) não intencional —
por exemplo, um cliente que cola um número de telefone ou CPF dentro do
comentário por engano.

**Decisão adotada neste projeto:** nenhum tratamento adicional foi aplicado a
esses campos, além da tipagem padrão (`string`). Essa decisão é justificada
pelo fato de o dataset já ser público, oficialmente disponibilizado e
anonimizado pela própria Olist no Kaggle — não sendo, portanto,
responsabilidade deste pipeline reforçar essa anonimização.

**Caminho alternativo, caso os dados não fossem públicos** (relevante para
contextos reais, como dados bancários/corporativos):

1. **Detecção de PII** em campos de texto livre, via regex ou ferramentas
   especializadas (ex: AWS Comprehend PII detection, Microsoft Presidio),
   identificando padrões como CPF, telefone, e-mail e endereço digitados
   dentro de campos não estruturados.
2. **Mascaramento ou remoção** do dado sensível identificado, substituindo por
   um marcador genérico (ex: `[DADO_REMOVIDO]`) ou removendo o registro,
   dependendo da política de dados da organização.
3. **Momento no pipeline:** esse tratamento deveria ocorrer o mais cedo
   possível — idealmente na ingestão ou logo na camada bronze — evitando que
   dado sensível não tratado se propague para camadas mais expostas (silver/
   gold), consumidas por múltiplos usuários e ferramentas de BI.
4. **Controle de acesso por camada:** em ambientes corporativos, é comum que
   as camadas raw/bronze tenham acesso restrito ao time de engenharia de
   dados, enquanto gold (mais exposta a analistas) já tenha passado por esse
   tratamento — reduzindo a superfície de exposição de dado sensível.

Esse tipo de cuidado é diretamente relacionado a práticas de compliance com
a LGPD (minimização de dados sensíveis armazenados sem necessidade), mesmo
quando o dado aparece de forma não intencional dentro de campos livres.

## 5. Granularidade da tabela `geolocation`

**Investigação:** ao processar `geolocation`, notou-se que a tabela tem
~1 milhão de linhas, enquanto o dataset tem apenas ~100 mil pedidos — uma
proporção que não se explicava por uma simples correspondência 1:1 com
pedidos ou clientes.

**Descoberta:** verificação direta nos dados mostrou 1.000.163 linhas totais
contra apenas 19.015 valores únicos de `geolocation_zip_code_prefix` — uma
média de ~52 registros de latitude/longitude por prefixo de CEP.

**Conclusão:** a tabela não representa "um CEP = uma coordenada fixa". Um
prefixo de CEP cobre uma área geográfica (não um ponto único), e a tabela
contém múltiplas coordenadas GPS reais distintas que caem dentro da mesma
área de CEP — provavelmente coletadas de endereços reais.

**Implicação para a camada silver (decisão em aberto, a resolver quando essa
camada for construída):** ao usar `geolocation` para enriquecer outras
tabelas via `zip_code_prefix` (ex: obter a lat/long de um cliente ou
vendedor), será necessário decidir uma estratégia de agregação — candidatas
incluem usar a média de lat/long por CEP, ou selecionar uma ocorrência
representativa — já que hoje existe uma relação 1:N entre CEP e coordenadas.

## 6. Onde a modelagem dimensional acontece no pipeline

**Esclarecimento:** a modelagem dimensional (star schema, no caso deste
projeto) é aplicada exclusivamente na camada **gold**. As camadas bronze e
silver são independentes de qual modelagem final será usada — bronze cuida de
ingestão tipada, silver cuida de limpeza/conformação/enriquecimento pontual
das entidades originais, sem reorganizá-las em fato/dimensão.

**Prova de que essa separação está correta:** se a modelagem escolhida
mudasse de star schema para outra abordagem (ex: snowflake schema), nenhuma
alteração seria necessária em bronze ou silver — apenas na forma como a gold
é construída a partir da silver. Isso confirma que a responsabilidade de
modelagem está isolada na camada certa.

## 7. Modelagem relacional (transacional) vs. modelagem dimensional (analítica)

**Contexto da dúvida:** ao pensar em modelagem, surge a pergunta natural —
se o banco transacional que originou os dados (o sistema de produção do
Olist) já foi modelado por um time de desenvolvimento, por que não usar essa
mesma modelagem no banco analítico?

**Esclarecimento:** bancos transacionais (OLTP) sempre passam por um processo
de modelagem, mas usam **modelagem relacional normalizada** (tipicamente 3ª
forma normal) — o objetivo é evitar redundância, garantir integridade
referencial, e otimizar para escritas frequentes (inserir um pedido, atualizar
um status, etc.). É por isso que dados de origem chegam separados em tabelas
como `orders`, `customers`, `products`, `order_items`.

Bancos analíticos (OLAP), por outro lado, usam **modelagem dimensional**
(star schema, no caso deste projeto) — o objetivo é otimizar para leitura e
consulta analítica, aceitando desnormalização proposital (repetição de dados)
em troca de consultas mais simples e rápidas.

**Síntese:** banco transacional = modelagem relacional; banco analítico =
modelagem dimensional. São propósitos opostos (escrita vs. leitura,
integridade vs. performance de consulta), por isso um pipeline de
transformação (bronze → silver → gold) é necessário — não seria possível
simplesmente espelhar a estrutura do banco transacional para uso analítico.

## 8. Estratégias para lidar com nulos gerados por agregação

**Contexto:** ao agregar `geolocation` por CEP usando `mean()`, surgiu a
dúvida sobre o que fazer caso a agregação gerasse valores nulos (cenário
hipotético: um CEP cujos registros de lat/lng já fossem todos nulos na
origem, tornando a média indefinida).

**Validação aplicada neste projeto:** antes de decidir, foi confirmado que
`geolocation_lat` e `geolocation_lng` não possuem nenhum valor nulo na
origem (bronze) — portanto, a agregação por média não gera nulos neste
caso específico, e nenhuma estratégia de tratamento precisou ser aplicada.

**Estratégias possíveis, caso nulos existissem** (registrado como referência
para decisões futuras):

1. **Excluir a linha/grupo** — remove o registro (ex: o CEP) que resultaria
   em nulo. Mais simples, mas perde a informação daquele registro em
   qualquer lugar do modelo que dependa dele.
2. **Substituir por valor sentinela** — atribuir um valor claramente inválido
   (ex: `0.0`) no lugar do nulo. Mantém a linha existindo, mas exige que
   qualquer consumidor downstream saiba identificar e filtrar esse valor.
3. **Manter o nulo** — não decidir nada na silver, deixando o tratamento
   (excluir, substituir, ignorar) a critério de quem for consumir o dado na
   gold ou na ferramenta de BI, conforme o contexto de uso específico.

**Critério de decisão:** não existe estratégia universalmente correta — a
escolha depende do que a coluna afetada será usada para fazer downstream
(ex: nulos em coordenadas geográficas tendem a quebrar visualizações de mapa
em ferramentas de BI, o que pesaria a favor de exclusão ou tratamento
explícito antes da gold).

## 9. DuckDB como ferramenta auxiliar de inspeção de dados

**Contexto:** ao longo do desenvolvimento das camadas silver/gold, surgiu a
necessidade de visualizar e validar o conteúdo dos arquivos Parquet
armazenados no S3, sem precisar baixá-los manualmente a cada verificação.

**Decisão:** adotado o DuckDB como ferramenta auxiliar de inspeção local,
instalado como dependência de desenvolvimento (`--group dev`), já que não
participa da lógica do pipeline em produção (Glue) — serve apenas como
camada de conveniência para o desenvolvedor.

**Por que DuckDB:** capacidade de consultar arquivos Parquet diretamente no
S3 via SQL, sem necessidade de download prévio, permitindo validação rápida
de schema e conteúdo a qualquer momento do desenvolvimento. Também reforça
uma ferramenta já usada anteriormente no TCC (arquitetura Lakehouse com
dbt + DuckDB), mantendo consistência de ferramentas entre os dois projetos
de portfólio.

**Nota de compatibilidade:** assim como outras dependências deste projeto,
o DuckDB precisou ser fixado em uma versão específica (`<1.4`, resultando
em `1.3.2`) devido à descontinuação de suporte ao Python 3.9 nas versões
mais recentes da biblioteca — mesmo padrão de conflito já observado com
`pyarrow`, `pandas` e `boto3`.

## 10. DuckDB vs. Athena — por que não são ferramentas concorrentes

**Dúvida original:** já que o Athena existe na arquitetura do projeto e serve
justamente para consultas ad-hoc (consultas pontuais, feitas na hora, sem
planejamento prévio — em oposição a consultas estruturadas e recorrentes de
produção), por que adicionar o DuckDB como mais uma ferramenta na stack, ao
invés de usar o Athena para inspecionar os dados durante o desenvolvimento?

**Esclarecimento:** a comparação não é "DuckDB vs. Athena" como ferramentas
concorrentes — é sobre **em que momento do pipeline cada uma está
disponível**.

O Athena só consegue consultar uma tabela que já está registrada no Glue
Data Catalog, e esse registro só acontece depois que um **Crawler** roda
sobre os dados. Como o Crawler ainda não foi criado neste ponto do projeto,
o Athena literalmente não "enxerga" os arquivos Parquet em `silver/` e
`gold/` — para ele, essas pastas no S3 ainda são invisíveis, mesmo contendo
dados válidos.

**Conclusão:**
- **Antes do Crawler existir** (fase atual de desenvolvimento): DuckDB serve
  como ferramenta de inspeção rápida, sem necessidade de catalogação, sem
  custo de AWS, direto do terminal local.
- **Depois que o Crawler catalogar silver/gold**: o Athena assume o papel de
  consulta ad-hoc oficial da arquitetura, integrado ao fluxo real do projeto
  (S3 → Glue → Athena → QuickSight).

O DuckDB não faz parte da arquitetura final do pipeline — é uma ferramenta
de bastidor, usada apenas pelo desenvolvedor durante a fase de construção,
preenchendo a lacuna temporal que existe antes da catalogação via Crawler.
No diagrama de arquitetura final do projeto, apenas o Athena aparece como
camada de consulta.

## 11. Dimensão dim_date — propósito, geração e feriados

**Propósito da tabela:** centralizar e padronizar atributos derivados de
data (ano, mês, trimestre, dia da semana, nome do mês, feriados) para
consumo analítico, evitando que cada consulta precise recalcular essas
derivações repetidamente, e garantindo consistência entre diferentes
relatórios/dashboards que dependem de noções de tempo.

**Estratégia de geração — dataset estático (este projeto):** como o dataset
Olist é estático, o intervalo de datas da dimensão foi definido varrendo
todas as colunas de data disponíveis em `orders` (`order_purchase_timestamp`,
`order_approved_at`, `order_delivered_carrier_date`,
`order_delivered_customer_date`, `order_estimated_delivery_date`) e
`order_reviews` (`review_creation_date`, `review_answer_timestamp`),
calculando o mínimo e o máximo entre todas elas.

**Cálculo do intervalo:** para cada tabela, calculou-se o mínimo/máximo por
coluna (resultando em uma Series de valores parciais por tabela). Essas
Series foram unidas com `pd.concat()`, e um segundo `.min()`/`.max()` foi
aplicado sobre o resultado concatenado para chegar a um único valor final —
evitando a necessidade de unir fisicamente as tabelas inteiras (uma
alternativa mais custosa seria um UNION de todas as linhas antes de ordenar
e filtrar extremos).

**Decisão sobre datas estimadas/futuras:** `order_estimated_delivery_date`
foi incluída no cálculo do intervalo, mesmo sendo uma data projetada — isso
estica o intervalo da dimensão para além da última data "real" do dataset,
garantindo que qualquer análise usando essa coluna encontre correspondência
via join.

**Equivalente em produção:** em um dataset que cresce ao longo do tempo, a
prática comum é gerar a dimensão cobrindo um intervalo futuro generoso (ex:
até o final do ano corrente), ajustando periodicamente (ex: início de cada
ano), já que a tabela é barata de manter (poucas colunas, um registro por
dia). O princípio de "gerar mais do que o estritamente necessário agora" é
o mesmo em ambos os cenários — muda apenas a origem do intervalo (calculado
a partir dos dados existentes vs. definido de forma prospectiva).

**Geração do calendário e atributos derivados:** utilizou-se `pd.date_range()`
para gerar uma sequência diária entre o mínimo e o máximo calculados, seguida
da extração de atributos via o acessador `.dt` do pandas (`.dt.year`,
`.dt.month`, `.dt.quarter`, `.dt.day_name()`, `.dt.month_name()`). O horário
herdado dos timestamps originais foi removido com `.dt.normalize()`, já que
a granularidade da dimensão é diária, não intra-dia.

**Feriados nacionais:** adicionada uma coluna booleana `is_holiday`, usando
a biblioteca `holidays` (calendário `holidays.Brazil()`) combinada com
`.apply()` e uma função `lambda` (função anônima definida em uma única
linha, usada quando a lógica é simples e não reaproveitada em outro lugar).

**Classificação da dependência `holidays`:** ao contrário do DuckDB (usado
apenas para inspeção local, nunca participando do dado gerado), a biblioteca
`holidays` gera uma coluna que compõe o dado final gravado na gold — por
isso foi classificada como dependência de **produção** (mesmo grupo de
`boto3`, `pandas`, `pyarrow`), não de desenvolvimento. O critério de
classificação é: "essa dependência participa da lógica de negócio que gera
o dado final, ou é apenas uma ferramenta auxiliar do desenvolvedor?".

**Nota de compatibilidade:** `holidays` precisou ser fixado em `<0.60`
(resultando em `0.59`) devido à descontinuação de suporte ao Python 3.9 nas
versões mais recentes — mesmo padrão de conflito já observado com outras
dependências deste projeto.

## 12. Troubleshooting: permissão restrita por caminho na IAM Role do Glue

**Problema encontrado:** ao criar o segundo Crawler (`silver_crawler`), ele
executou com status "Completed", mas catalogou 0 tabelas — nenhum erro
explícito apareceu na interface do Crawler.

**Diagnóstico:** investigando os logs do CloudWatch (acessíveis via "View
CloudWatch logs" na tela de execuções do Crawler), foi identificado um erro
`AccessDenied` (S3, código 403) ao tentar ler os arquivos Parquet da camada
silver.

**Causa raiz:** a IAM Role criada automaticamente pelo assistente do Glue
(`AWSGlueServiceRole-datalake_analytics`) recebeu uma política customizada
gerada com base no caminho S3 informado na criação do **primeiro** Crawler
(gold) — restringindo o `Resource` da política apenas a `gold/*`. Como essa
mesma role foi reutilizada para o Crawler de silver, o acesso a `silver/*`
foi negado.

**Correção:** edição manual da política customizada
(`AWSGlueServiceRole-datalake_analytics-EZCRC-s3Policy`), adicionando um
segundo ARN à lista de `Resource`, cobrindo também `silver/*`, mantendo a
mesma condição de segurança existente (`aws:ResourceAccount`).

**Aprendizado:** ao reutilizar uma IAM Role gerada automaticamente pelo
assistente de um serviço AWS para múltiplos recursos (neste caso, múltiplos
Crawlers apontando para caminhos S3 diferentes), é necessário revisar e
ajustar manualmente as políticas de acesso — o assistente tende a restringir
permissões ao escopo exato informado no momento da criação, não antecipando
usos futuros da mesma role.

## 14. Decisão sobre ferramenta de BI final

**Contexto:** o plano original era usar Amazon QuickSight como camada de
visualização final (S3 → Glue → Athena → QuickSight). Ao investigar o setup
real, foram encontrados empecilhos relevantes na ferramenta (mudanças de
produto e modelo de custo) que a tornaram inviável para este projeto de
portfólio pessoal.

**Decisão final:** como o objetivo principal deste projeto sempre foi a
engenharia de dados — pipeline, modelagem dimensional e arquitetura AWS —
e esse objetivo já foi atingido, optou-se por **não conectar nenhuma
ferramenta de BI** neste momento. As camadas silver e gold, já catalogadas
no Glue Data Catalog e consultáveis via Athena, ficam documentadas como
prontas para conexão com qualquer ferramenta de BI compatível.

## 15. Migração para Glue Jobs — desenvolvimento local vs. execução em produção

**Contexto:** após validar toda a lógica de transformação rodando localmente
(via Poetry, com debug interativo), decidiu-se migrar os scripts para
rodarem como **Glue Jobs** (Python Shell) — refletindo um pipeline de dados
real, que não depende de execução manual em uma máquina local.

**Coexistência de dois ambientes:** o código em `src/aws_datalake_analytics/`
(local) não foi descontinuado — ele representa a camada de desenvolvimento
e validação, onde a lógica de negócio foi construída e testada
iterativamente. Uma pasta separada, `glue_jobs/`, contém versões adaptadas
desses scripts para execução real na AWS. Essa separação reflete um fluxo
profissional comum: desenvolver e validar localmente (rápido, barato,
interativo) antes de migrar para produção (mais lento de iterar, mas fiel
ao ambiente real).

**Ajustes necessários na migração:**
1. **Parametrização:** valores antes fixos no código (nome do bucket,
   caminhos de arquivo) passaram a ser recebidos via `getResolvedOptions`,
   lidos a partir de "Job parameters" configurados no Glue — permitindo
   reutilizar o mesmo script para diferentes ambientes/caminhos sem alterar
   código-fonte.
2. **Bibliotecas de terceiros:** o Glue Python Shell (Python 3.9) já vem com
   bibliotecas comuns pré-instaladas (incluindo pandas), simplificando a
   migração. Bibliotecas adicionais (ex: pyarrow, holidays) podem ser
   adicionadas via parâmetro `--additional-python-modules`, sem necessidade
   de empacotamento manual.
3. **Módulos próprios do projeto:** o módulo `utils/s3_helpers.py`, que no
   ambiente local é importado como parte de um pacote estruturado (via
   Poetry), precisou ser disponibilizado como arquivo avulso via o campo
   "Referenced files path" do Glue Job — mudando a forma de import de
   `from aws_datalake_analytics.utils.s3_helpers import ...` (caminho de
   pacote) para `from s3_helpers import ...` (arquivo solto).

**Troubleshooting encontrado — permissões por caminho no S3:**
Ao rodar o primeiro Job, três erros sucessivos de permissão apareceram, um
de cada vez, à medida que o script tentava acessar diferentes prefixos do
bucket (`scripts/`, depois `raw/`, depois `bronze/`) — todos negados pela
mesma política restritiva por caminho já identificada anteriormente (ver
item 12). Cada erro foi resolvido adicionando o prefixo faltante à lista de
`Resource` da política.

**Decisão de manter granularidade na política, mesmo após múltiplas
correções:** considerou-se simplificar a política liberando o bucket inteiro
de uma vez, evitando repetir esse processo a cada novo caminho acessado.
Optou-se por **manter a política granular**, por prefixo específico,
mesmo sendo mais trabalhoso — para preservar a coerência com o princípio de
menor privilégio (least privilege) já adotado desde a criação do usuário
IAM no início do projeto.

## 16. Orquestração com Glue Workflows

**Contexto:** com todos os 24 Glue Jobs criados (9 raw_to_bronze, 8
bronze_to_silver, 7 silver_to_gold), surgiu a necessidade de garantir a
ordem correta de execução entre as camadas — silver não deve rodar antes
que toda a bronze termine com sucesso, e o mesmo vale para gold em relação
à silver.

**Diferença entre agendamento e orquestração:** um simples agendamento
(schedule) por horário não garante essa dependência — jobs poderiam rodar
fora de ordem ou sobre dados incompletos caso uma etapa anterior atrasasse.
Orquestração define explicitamente a dependência entre etapas ("rode X,
espere sucesso, só então rode Y"), independente de horário.

**Solução adotada:** AWS Glue Workflows, com a seguinte estrutura de
triggers e jobs: