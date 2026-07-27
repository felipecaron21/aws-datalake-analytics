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

df_geolocation = ler_csv_do_s3(cliente_s3, bucket_name, raw_key)

string_columns = [
    "geolocation_zip_code_prefix",
    "geolocation_city",
    "geolocation_state",
]

float_columns = [
    "geolocation_lat",
    "geolocation_lng",
]

try:
    df_geolocation[string_columns] = df_geolocation[string_columns].astype("string")
    df_geolocation[float_columns] = df_geolocation[float_columns].astype("float")
except Exception as erro:
    print(f"Erro ao aplicar tipagem nas colunas de geolocation: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_geolocation, bucket_name, bronze_key)