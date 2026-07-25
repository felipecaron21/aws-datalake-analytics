import pandas as pd
from aws_datalake_analytics.utils.s3_helpers import (
    criar_cliente_s3,
    ler_csv_do_s3,
    escrever_parquet_no_s3,
)

bucket_name = "aws-datalake-analytics-felipecaron"
raw_key = "raw/product_category_name_translation.csv"
bronze_key = "bronze/category_translate/category_translate.parquet"

cliente_s3 = criar_cliente_s3()

df_category_translate = ler_csv_do_s3(cliente_s3, bucket_name, raw_key)

string_columns = [
    "product_category_name",
    "product_category_name_english",
]

try:
    df_category_translate[string_columns] = df_category_translate[
        string_columns
    ].astype("string")
except Exception as erro:
    print(f"Erro ao aplicar tipagem nas colunas de category_translate: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_category_translate, bucket_name, bronze_key)
