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

df_products = ler_parquet_do_s3(cliente_s3, bucket_name, silver_key)

try:
    df_products = df_products.rename(
        columns={
            "product_id": "id_product",
            "product_category_name_english": "category_name",
            "product_name_lenght": "name_lenght",
            "product_description_lenght": "description_lenght",
            "product_photos_qty": "photos_qty",
            "product_weight_g": "weight_g",
            "product_length_cm": "length_cm",
            "product_height_cm": "height_cm",
            "product_width_cm": "width_cm",
        }
    )

    df_products = df_products[
        [
            "id_product",
            "category_name",
            "name_lenght",
            "description_lenght",
            "photos_qty",
            "weight_g",
            "length_cm",
            "height_cm",
            "width_cm",
        ]
    ]
except Exception as erro:
    print(f"Erro ao renomear e selecionar colunas de products: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_products, bucket_name, gold_key)