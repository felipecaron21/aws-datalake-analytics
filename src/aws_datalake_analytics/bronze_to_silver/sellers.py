import pandas as pd
from aws_datalake_analytics.utils.s3_helpers import (
    criar_cliente_s3,
    ler_parquet_do_s3,
    escrever_parquet_no_s3,
)

bucket_name = "aws-datalake-analytics-felipecaron"
bronze_key = "bronze/sellers/sellers.parquet"
silver_key = "silver/sellers/sellers.parquet"

cliente_s3 = criar_cliente_s3()

df_sellers = ler_parquet_do_s3(cliente_s3, bucket_name, bronze_key)

escrever_parquet_no_s3(cliente_s3, df_sellers, bucket_name, silver_key)
