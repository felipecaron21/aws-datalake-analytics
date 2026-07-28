import sys
import pandas as pd
from awsglue.utils import getResolvedOptions
from s3_helpers import (
    criar_cliente_s3,
    ler_parquet_do_s3,
    escrever_parquet_no_s3,
)

args = getResolvedOptions(sys.argv, ["bucket_name", "bronze_key_products", "bronze_key_translate", "silver_key"])

bucket_name = args["bucket_name"]
bronze_key_products = args["bronze_key_products"]
bronze_key_translate = args["bronze_key_translate"]
silver_key = args["silver_key"]

cliente_s3 = criar_cliente_s3()

df_products = ler_parquet_do_s3(cliente_s3, bucket_name, bronze_key_products)
df_category_translate = ler_parquet_do_s3(cliente_s3, bucket_name, bronze_key_translate)

try:
    df_products = df_products.merge(
        df_category_translate, on="product_category_name", how="left"
    )
except Exception as erro:
    print(f"Erro ao aplicar merge de products com category_translate: {erro}")
    raise

escrever_parquet_no_s3(cliente_s3, df_products, bucket_name, silver_key)