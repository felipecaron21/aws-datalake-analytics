import pandas as pd
from aws_datalake_analytics.utils.s3_helpers import (
    criar_cliente_s3,
    ler_parquet_do_s3,
    escrever_parquet_no_s3,
)

bucket_name = "aws-datalake-analytics-felipecaron"
bronze_key = "bronze/customers/customers.parquet"
silver_key = "silver/customers/customers.parquet"

cliente_s3 = criar_cliente_s3()

df_customers = ler_parquet_do_s3(cliente_s3, bucket_name, bronze_key)

escrever_parquet_no_s3(cliente_s3, df_customers, bucket_name, silver_key)
