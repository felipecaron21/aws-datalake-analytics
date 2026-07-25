import pandas as pd
from aws_datalake_analytics.utils.s3_helpers import (
    criar_cliente_s3,
    ler_parquet_do_s3,
    escrever_parquet_no_s3,
)

bucket_name = "aws-datalake-analytics-felipecaron"
bronze_key_products = "bronze/products/products.parquet"
bronze_key_translate = "bronze/category_translate/category_translate.parquet"
silver_key = "silver/products/products.parquet"

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
