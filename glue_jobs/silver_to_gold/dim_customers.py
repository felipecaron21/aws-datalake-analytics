import sys
import pandas as pd
from awsglue.utils import getResolvedOptions
from s3_helpers import (
    criar_cliente_s3,
    ler_parquet_do_s3,
    escrever_parquet_no_s3,
)

args = getResolvedOptions(sys.argv, ["bucket_name", "silver_key_customers", "silver_key_orders", "gold_key"])

bucket_name = args["bucket_name"]
silver_key_customers = args["silver_key_customers"]
silver_key_orders = args["silver_key_orders"]
gold_key = args["gold_key"]

cliente_s3 = criar_cliente_s3()

df_customers = ler_parquet_do_s3(cliente_s3, bucket_name, silver_key_customers)
df_orders = ler_parquet_do_s3(cliente_s3, bucket_name, silver_key_orders)

try:
    df_customers = df_customers.merge(df_orders, on="customer_id", how="left")
except Exception as erro:
    print(f"Erro ao fazer merge entre customers e orders: {erro}")
    raise

try:
    df_customers = df_customers.sort_values("order_purchase_timestamp", ascending=False)
    df_customers = df_customers.drop_duplicates(
        subset="customer_unique_id", keep="first"
    )
except Exception as erro:
    print(f"Erro ao ordenar e selecionar primeiro registro: {erro}")
    raise

try:
    df_customers = df_customers.rename(
        columns={
            "customer_unique_id": "id_customer",
            "customer_zip_code_prefix": "zip_code",
            "customer_city": "city",
            "customer_state": "state",
        }
    )

    df_customers = df_customers[["id_customer", "zip_code", "city", "state"]]
except Exception as erro:
    print(f"Erro ao renomear e selecionar colunas: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_customers, bucket_name, gold_key)