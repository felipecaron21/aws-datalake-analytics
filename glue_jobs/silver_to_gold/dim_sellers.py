import sys
import pandas as pd
from awsglue.utils import getResolvedOptions
from s3_helpers import (
    criar_cliente_s3,
    ler_parquet_do_s3,
    escrever_parquet_no_s3,
)

args = getResolvedOptions(sys.argv, ["bucket_name", "silver_key", "gold_key"])

bucket_name = args["bucket_name"]
silver_key = args["silver_key"]
gold_key = args["gold_key"]

cliente_s3 = criar_cliente_s3()

df_sellers = ler_parquet_do_s3(cliente_s3, bucket_name, silver_key)

try:
    df_sellers = df_sellers.rename(
        columns={
            "seller_id": "id_seller",
            "seller_zip_code_prefix": "zip_code",
            "seller_city": "city",
            "seller_state": "state",
        }
    )
except Exception as erro:
    print(f"Erro ao renomear as colunas de sellers: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_sellers, bucket_name, gold_key)