import pandas as pd
from aws_datalake_analytics.utils.s3_helpers import (
    criar_cliente_s3,
    ler_csv_do_s3,
    escrever_parquet_no_s3,
)

bucket_name = "aws-datalake-analytics-felipecaron"
raw_key = "raw/olist_orders_dataset.csv"
bronze_key = "bronze/orders/orders.parquet"

cliente_s3 = criar_cliente_s3()

df_orders = ler_csv_do_s3(cliente_s3, bucket_name, raw_key)

string_columns = ["order_id", "customer_id", "order_status"]
date_columns = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

try:
    df_orders[string_columns] = df_orders[string_columns].astype("string")
    df_orders[date_columns] = df_orders[date_columns].apply(pd.to_datetime)
except Exception as erro:
    print(f"Erro ao aplicar tipagem nas colunas de orders: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_orders, bucket_name, bronze_key)
