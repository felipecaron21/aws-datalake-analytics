import pandas as pd
from aws_datalake_analytics.utils.s3_helpers import (
    criar_cliente_s3,
    ler_csv_do_s3,
    escrever_parquet_no_s3,
)

bucket_name = "aws-datalake-analytics-felipecaron"
raw_key = "raw/olist_order_payments_dataset.csv"
bronze_key = "bronze/order_payments/order_payments.parquet"

cliente_s3 = criar_cliente_s3()

df_order_payments = ler_csv_do_s3(cliente_s3, bucket_name, raw_key)

string_columns = [
    "order_id",
    "payment_type",
]

int_columns = [
    "payment_sequential",
    "payment_installments",
]

float_columns = [
    "payment_value",
]

try:
    df_order_payments[string_columns] = df_order_payments[string_columns].astype(
        "string"
    )
    df_order_payments[int_columns] = df_order_payments[int_columns].astype("int")
    df_order_payments[float_columns] = df_order_payments[float_columns].astype("float")
except Exception as erro:
    print(f"Erro ao aplicar tipagem nas colunas de order_payments: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_order_payments, bucket_name, bronze_key)
