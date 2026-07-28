import sys
import pandas as pd
from awsglue.utils import getResolvedOptions
from s3_helpers import (
    criar_cliente_s3,
    ler_parquet_do_s3,
    escrever_parquet_no_s3,
)

args = getResolvedOptions(sys.argv, ["bucket_name", "silver_key_order_items", "silver_key_orders", "silver_key_customers", "gold_key"])

bucket_name = args["bucket_name"]
silver_key_order_items = args["silver_key_order_items"]
silver_key_orders = args["silver_key_orders"]
silver_key_customers = args["silver_key_customers"]
gold_key = args["gold_key"]

cliente_s3 = criar_cliente_s3()

df_order_items = ler_parquet_do_s3(cliente_s3, bucket_name, silver_key_order_items)
df_orders = ler_parquet_do_s3(cliente_s3, bucket_name, silver_key_orders)
df_customers = ler_parquet_do_s3(cliente_s3, bucket_name, silver_key_customers)

try:
    df_order_items = df_order_items.merge(df_orders, on="order_id", how="left")

    df_order_items = df_order_items.merge(df_customers, on="customer_id", how="left")
except Exception as erro:
    print(f"Erro ao fazer merge de orders e customers na tabela de order_items: {erro}")
    raise

try:
    df_order_items["order_purchase_timestamp"] = df_order_items[
        "order_purchase_timestamp"
    ].dt.normalize()
except Exception as erro:
    print(f"Erro ao normalizar coluna de data da compra: {erro}")
    raise

try:
    df_order_items = df_order_items.rename(
        columns={
            "order_id": "id_order",
            "order_item_id": "id_item",
            "product_id": "id_product",
            "seller_id": "id_seller",
            "customer_unique_id": "id_customer",
            "order_purchase_timestamp": "purchase_date",
        }
    )

    df_order_items = df_order_items[
        [
            "id_order",
            "id_item",
            "id_product",
            "id_seller",
            "id_customer",
            "purchase_date",
            "price",
            "freight_value",
        ]
    ]
except Exception as erro:
    print(f"Erro ao renomear e selecionar colunas de order_items: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_order_items, bucket_name, gold_key)