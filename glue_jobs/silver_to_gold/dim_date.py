import sys
import pandas as pd
import holidays
from awsglue.utils import getResolvedOptions
from s3_helpers import (
    criar_cliente_s3,
    ler_parquet_do_s3,
    escrever_parquet_no_s3,
)

args = getResolvedOptions(sys.argv, ["bucket_name", "silver_key_orders", "silver_key_order_reviews", "gold_key"])

bucket_name = args["bucket_name"]
silver_key_orders = args["silver_key_orders"]
silver_key_order_reviews = args["silver_key_order_reviews"]
gold_key = args["gold_key"]

cliente_s3 = criar_cliente_s3()

df_orders = ler_parquet_do_s3(cliente_s3, bucket_name, silver_key_orders)
df_order_reviews = ler_parquet_do_s3(cliente_s3, bucket_name, silver_key_order_reviews)


try:
    min_orders = df_orders[
        [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    ].min()

    max_orders = df_orders[
        [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    ].max()

    min_reviews = df_order_reviews[
        [
            "review_creation_date",
            "review_answer_timestamp",
        ]
    ].min()

    max_reviews = df_order_reviews[
        [
            "review_creation_date",
            "review_answer_timestamp",
        ]
    ].max()

    df_min = pd.concat([min_orders, min_reviews])
    df_max = pd.concat([max_orders, max_reviews])

    date_min = df_min.min()
    date_max = df_max.max()
except Exception as erro:
    print(f"Erro ao extrair min/max: {erro}")
    raise

try:
    datas = pd.date_range(start=date_min, end=date_max, freq="D")

    df_date = pd.DataFrame({"date": datas})

    df_date["date"] = df_date["date"].dt.normalize()
    df_date["year"] = df_date["date"].dt.year
    df_date["month"] = df_date["date"].dt.month
    df_date["quarter"] = df_date["date"].dt.quarter
    df_date["day_of_week"] = df_date["date"].dt.day_name()
    df_date["name_of_month"] = df_date["date"].dt.month_name()
except Exception as erro:
    print(f"Erro ao criar dataframe e colunas de dim_dates: {erro}")
    raise

try:
    feriados_brasil = holidays.Brazil()

    df_date["is_holiday"] = df_date["date"].apply(lambda data: data in feriados_brasil)
except Exception as erro:
    print(f'Erro ao criar coluna de feriados no brasil: {erro}')
    raise

escrever_parquet_no_s3(cliente_s3, df_date, bucket_name, gold_key)