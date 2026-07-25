import pandas as pd
from aws_datalake_analytics.utils.s3_helpers import (
    criar_cliente_s3,
    ler_parquet_do_s3,
    escrever_parquet_no_s3,
)

bucket_name = "aws-datalake-analytics-felipecaron"
bronze_key = "bronze/order_reviews/order_reviews.parquet"
silver_key = "silver/order_reviews/order_reviews.parquet"

cliente_s3 = criar_cliente_s3()

df_order_reviews = ler_parquet_do_s3(cliente_s3, bucket_name, bronze_key)

escrever_parquet_no_s3(cliente_s3, df_order_reviews, bucket_name, silver_key)
