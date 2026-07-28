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

df_order_reviews = ler_csv_do_s3(cliente_s3, bucket_name, raw_key)

string_columns = [
    "review_id",
    "order_id",
    "review_comment_title",
    "review_comment_message",
]

int_columns = [
    "review_score",
]

date_columns = [
    "review_creation_date",
    "review_answer_timestamp",
]

try:
    df_order_reviews[string_columns] = df_order_reviews[string_columns].astype("string")
    df_order_reviews[int_columns] = df_order_reviews[int_columns].astype("int")
    df_order_reviews[date_columns] = df_order_reviews[date_columns].apply(
        pd.to_datetime
    )
except Exception as erro:
    print(f"Erro ao aplicar tipagem nas colunas de order_reviews: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_order_reviews, bucket_name, bronze_key)
