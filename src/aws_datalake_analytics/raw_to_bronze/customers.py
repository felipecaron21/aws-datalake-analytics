import pandas as pd
from aws_datalake_analytics.utils.s3_helpers import (
    criar_cliente_s3,
    ler_csv_do_s3,
    escrever_parquet_no_s3,
)

bucket_name = "aws-datalake-analytics-felipecaron"
raw_key = "raw/olist_customers_dataset.csv"
bronze_key = "bronze/customers/customers.parquet"

cliente_s3 = criar_cliente_s3()

df_customers = ler_csv_do_s3(cliente_s3, bucket_name, raw_key)

string_columns = [
    "customer_id",
    "customer_unique_id",
    "customer_zip_code_prefix",
    "customer_city",
    "customer_state",
]

try:
    df_customers[string_columns] = df_customers[string_columns].astype("string")
except Exception as erro:
    print(f"Erro ao aplicar tipagem nas colunas de customers: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_customers, bucket_name, bronze_key)
