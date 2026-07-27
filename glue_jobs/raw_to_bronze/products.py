import sys
import pandas as pd
from awsglue.utils import getResolvedOptions
from s3_helpers import (
    criar_cliente_s3,
    ler_csv_do_s3,
    escrever_parquet_no_s3,
)

args = getResolvedOptions(sys.argv, ["bucket_name", "raw_key", "bronze_key"])

bucket_name = args["bucket_name"]
raw_key = args["raw_key"]
bronze_key = args["bronze_key"]

cliente_s3 = criar_cliente_s3()

df_products = ler_csv_do_s3(cliente_s3, bucket_name, raw_key)

string_columns = [
    "product_id",
    "product_category_name",
]

int64_columns = [
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
]

float_columns = [
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]

try:
    df_products[string_columns] = df_products[string_columns].astype("string")
    df_products[int64_columns] = df_products[int64_columns].astype("Int64")
    df_products[float_columns] = df_products[float_columns].astype("float")
except Exception as erro:
    print(f"Erro ao aplicar tipagem nas colunas de products: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_products, bucket_name, bronze_key)