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

df_payments = ler_parquet_do_s3(cliente_s3, bucket_name, silver_key)

try:
    df_payments = df_payments.rename(
        columns={
            "order_id": "id_order",
            "payment_sequential": "sequential",
            "payment_type": "type",
            "payment_installments": "installments",
            "payment_value": "value",
        }
    )
except Exception as erro:
    print(f'Erro ao renomear colunas de payments: {erro}')
    raise

escrever_parquet_no_s3(cliente_s3, df_payments, bucket_name, gold_key)
