import pandas as pd
from aws_datalake_analytics.utils.s3_helpers import (
    criar_cliente_s3,
    ler_parquet_do_s3,
    escrever_parquet_no_s3,
)

bucket_name = "aws-datalake-analytics-felipecaron"
bronze_key = "bronze/geolocation/geolocation.parquet"
silver_key = "silver/geolocation/geolocation.parquet"

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
