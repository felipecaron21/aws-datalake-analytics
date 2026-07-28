# AWS Data Lake Analytics

Pipeline de dados construído do zero na AWS, usando o dataset público de e-commerce da Olist. O projeto cobre o ciclo completo de um pipeline de dados real, passando por ingestão, transformação em camadas (bronze, silver e gold), modelagem dimensional em star schema, catalogação, consulta analítica e orquestração automatizada.

## Arquitetura

    Kaggle (Olist dataset)
            |
            v
       S3 (raw layer)
            |
            v
     Glue Jobs (Python Shell) raw para bronze
            |  tipagem dos dados, sem lógica de negócio
            v
       S3 (bronze layer)
            |
            v
     Glue Jobs (Python Shell) bronze para silver
            |  limpeza, enriquecimento e deduplicação
            v
       S3 (silver layer)
            |
            v
     Glue Jobs (Python Shell) silver para gold
            |  modelagem dimensional (star schema)
            v
       S3 (gold layer)
            |
            v
      Glue Crawlers alimentando o Glue Data Catalog
            |
            v
          Athena para consulta SQL

Toda a cadeia é orquestrada via AWS Glue Workflows. Os triggers condicionais garantem que cada camada só seja processada depois que a camada anterior termina com sucesso.

## Stack tecnológico

Armazenamento em Amazon S3. Processamento com AWS Glue (Python Shell jobs). Orquestração via AWS Glue Workflows. Catalogação através do AWS Glue Data Catalog (Crawlers). Consulta analítica com Amazon Athena. Linguagem Python 3.9, usando pandas, pyarrow, boto3 e holidays. Gerenciamento de dependências com Poetry e versionamento do ambiente Python com pyenv. DuckDB entra como ferramenta auxiliar de inspeção local, fora da arquitetura de produção.

## Estrutura do repositório

    src/aws_datalake_analytics/   desenvolvimento e validação local
      raw_to_bronze/              scripts de ingestão e tipagem
      bronze_to_silver/           scripts de limpeza e enriquecimento
      silver_to_gold/             scripts de modelagem dimensional
      utils/                      funções compartilhadas (S3, inspeção)

    glue_jobs/                    versões adaptadas para execução real
      raw_to_bronze/              na AWS via Glue Jobs, com parametrização
      bronze_to_silver/           e imports ajustados para o ambiente Glue
      silver_to_gold/
      utils/

    docs/
      data-model.md                modelagem dimensional (star schema)
      design-decisions.md          decisões técnicas e trade-offs

    data/raw/                      dados brutos, não versionados

Toda a lógica de transformação foi desenvolvida e validada localmente primeiro, usando Poetry e Python 3.9, replicando o ambiente do Glue. Isso permitiu debug rápido e iterativo. Depois de validados, os scripts foram migrados para rodar como Glue Jobs reais na AWS. Essa separação reflete o fluxo comum de desenvolvimento local seguido de deploy em produção, e por isso os dois ambientes coexistem no repositório.

## Modelo de dados

Star schema com quatro dimensões e três fatos.

Dimensões: dim_customers, dim_products, dim_sellers, dim_date.

Fatos: fact_order_items (grão de item de pedido), fact_reviews (grão de review) e fact_payments (grão de parcela de pagamento).

Os detalhes completos da modelagem estão em [docs/data-model.md](docs/data-model.md).

## Decisões técnicas

As decisões relevantes do projeto estão documentadas em [docs/design-decisions.md](docs/design-decisions.md). Isso inclui trade-offs de tipagem, tratamento de nulos, resolução de granularidade em tabelas com múltiplos registros por entidade, estratégia de tratamento de erros, ajustes de permissão IAM e todo o processo de migração para Glue Jobs.

## Camada de consumo (BI)

O projeto não conecta nenhuma ferramenta de BI específica no momento. As camadas silver e gold já estão catalogadas e prontas para conexão com qualquer ferramenta compatível com Athena, como Metabase, Power BI ou Looker. O contexto dessa decisão está registrado em design-decisions.md.

## Como rodar localmente

    poetry install
    poetry run python src/aws_datalake_analytics/raw_to_bronze/orders.py

É necessário ter credenciais AWS configuradas (aws configure) com acesso ao bucket S3 do projeto.