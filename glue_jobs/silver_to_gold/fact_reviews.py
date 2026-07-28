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

df_reviews = ler_parquet_do_s3(cliente_s3, bucket_name, silver_key)

try:
    df_reviews["review_creation_date"] = df_reviews[
        "review_creation_date"
    ].dt.normalize()
    df_reviews["review_answer_timestamp"] = df_reviews[
        "review_answer_timestamp"
    ].dt.normalize()
except Exception as erro:
    print(f"Erro ao normalizar as colunas de datas: {erro}")
    raise

try:
    df_reviews = df_reviews.rename(
        columns={
            "review_id": "id_review",
            "order_id": "id_order",
            "review_score": "score",
            "review_comment_title": "comment_title",
            "review_comment_message": "comment_message",
            "review_creation_date": "creation_date",
            "review_answer_timestamp": "answer_date",
        }
    )

    df_reviews = df_reviews[
        [
            "id_review",
            "id_order",
            "score",
            "comment_title",
            "comment_message",
            "creation_date",
            "answer_date",
        ]
    ]
except Exception as erro:
    print(f"Erro ao renomear e selecionar colunas de reviews: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_reviews, bucket_name, gold_key)