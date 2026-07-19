import pandas as pd
import boto3
import io

s3_client = boto3.client("s3")

bucket_name = "aws-datalake-analytics-felipecaron"
raw_key = "raw/olist_orders_dataset.csv"
bronze_key = "bronze/orders/orders.parquet"

#Etapa 1: leitura do S3 (raw) e conversão para df
try:
    response = s3_client.get_object(Bucket=bucket_name, Key=raw_key)
    csv_content = response["Body"].read()
    df_orders = pd.read_csv(io.BytesIO(csv_content))
except Exception as erro:
    print(f"Erro ao ler o arquivo raw do S3: {erro}")
    raise

#Etapa 2: tipagem das colunas
try:
    string_columns = ["order_id", "customer_id", "order_status"]
    date_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]

    df_orders[string_columns] = df_orders[string_columns].astype("string")
    df_orders[date_columns] = df_orders[date_columns].apply(pd.to_datetime)
except Exception as erro:
    print(f"Erro ao aplicar a tipagem das colunas: {erro}")
    raise

#Etapa 3: conversão para parquet e escrita no S3 (bronze)
try:
    parquet_buffer = io.BytesIO()
    df_orders.to_parquet(parquet_buffer, engine="pyarrow", index=False)

    s3_client.put_object(
        Bucket=bucket_name,
        Key=bronze_key,
        Body=parquet_buffer.getvalue()
    )
except Exception as erro:
    print(f"Erro ao escrever o arquivo bronze no S3: {erro}")
    raise