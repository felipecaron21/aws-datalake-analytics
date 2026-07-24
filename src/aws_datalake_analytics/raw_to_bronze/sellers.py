import pandas as pd
from aws_datalake_analytics.utils.s3_helpers import (
    criar_cliente_s3,
    ler_csv_do_s3,
    escrever_parquet_no_s3,
)

bucket_name = "aws-datalake-analytics-felipecaron"
raw_key = "raw/olist_sellers_dataset.csv"
bronze_key = "bronze/sellers/sellers.parquet"

cliente_s3 = criar_cliente_s3()

df_sellers = ler_csv_do_s3(cliente_s3, bucket_name, raw_key)

string_columns = [
    "seller_id",
    "seller_zip_code_prefix",
    "seller_city",
    "seller_state",
]

try:
    df_sellers[string_columns] = df_sellers[string_columns].astype("string")
except Exception as erro:
    print(f"Erro ao aplicar tipagem nas colunas de sellers: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_sellers, bucket_name, bronze_key)
