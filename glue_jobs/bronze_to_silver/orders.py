import sys
import pandas as pd
from awsglue.utils import getResolvedOptions
from s3_helpers import (
    criar_cliente_s3,
    ler_parquet_do_s3,
    escrever_parquet_no_s3,
)

args = getResolvedOptions(sys.argv, ["bucket_name", "bronze_key", "silver_key"])

bucket_name = args["bucket_name"]
bronze_key = args["bronze_key"]
silver_key = args["silver_key"]

cliente_s3 = criar_cliente_s3()

df_orders = ler_parquet_do_s3(cliente_s3, bucket_name, bronze_key)

escrever_parquet_no_s3(cliente_s3, df_orders, bucket_name, silver_key)
