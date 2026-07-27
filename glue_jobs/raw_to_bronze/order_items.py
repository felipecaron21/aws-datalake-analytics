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

df_order_items = ler_csv_do_s3(cliente_s3, bucket_name, raw_key)

string_columns = [
    "order_id",
    "product_id",
    "seller_id",
]

int_columns = [
    "order_item_id",
]

date_columns = [
    "shipping_limit_date",
]

float_columns = [
    "price",
    "freight_value",
]

try:
    df_order_items[string_columns] = df_order_items[string_columns].astype("string")
    df_order_items[int_columns] = df_order_items[int_columns].astype("int")
    df_order_items[date_columns] = df_order_items[date_columns].apply(pd.to_datetime)
    df_order_items[float_columns] = df_order_items[float_columns].astype("float")
except Exception as erro:
    print(f"Erro ao aplicar tipagem nas colunas de order items: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_order_items, bucket_name, bronze_key)