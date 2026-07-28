import sys
import pandas as pd
from awsglue.utils import getResolvedOptions
from s3_helpers import (
    criar_cliente_s3,
    ler_parquet_do_s3,
    escrever_parquet_no_s3,
)

args = getResolvedOptions(sys.argv, ["bucket_name", "bronze_key", "silver_key"])

bucket_name = args["bucket_name"]
bronze_key = args["bronze_key"]
silver_key = args["silver_key"]

cliente_s3 = criar_cliente_s3()

df_geolocation = ler_parquet_do_s3(cliente_s3, bucket_name, bronze_key)

try:
    df_geolocation = (
        df_geolocation.groupby("geolocation_zip_code_prefix")
        .agg({"geolocation_lat": "mean", "geolocation_lng": "mean"})
        .reset_index()
    )
except Exception as erro:
    print(f"Erro ao calcular média e agrupar CEP: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_geolocation, bucket_name, silver_key)
