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