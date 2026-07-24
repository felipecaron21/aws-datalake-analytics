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