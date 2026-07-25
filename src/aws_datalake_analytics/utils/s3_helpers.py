import boto3
import io
import pandas as pd


def criar_cliente_s3():
    return boto3.client("s3")


def ler_csv_do_s3(cliente_s3, bucket, key):
    try:
        response = cliente_s3.get_object(Bucket=bucket, Key=key)
        csv_content = response["Body"].read()
        df = pd.read_csv(io.BytesIO(csv_content))
        return df
    except Exception as erro:
        print(f"Erro ao ler o arquivo do S3 (bucket={bucket}, key={key}): {erro}")
        raise


def ler_parquet_do_s3(cliente_s3, bucket, key):
    try:
        response = cliente_s3.get_object(Bucket=bucket, Key=key)
        parquet_content = response["Body"].read()
        df = pd.read_parquet(io.BytesIO(parquet_content))
        return df
    except Exception as erro:
        print(
            f"Erro ao ler o arquivo parquet do S3 (bucket={bucket}, key={key}): {erro}"
        )
        raise


def escrever_parquet_no_s3(cliente_s3, dataframe, bucket, key):
    try:
        parquet_buffer = io.BytesIO()
        dataframe.to_parquet(parquet_buffer, engine="pyarrow", index=False)

        cliente_s3.put_object(Bucket=bucket, Key=key, Body=parquet_buffer.getvalue())
    except Exception as erro:
        print(f"Erro ao escrever o arquivo no S3 (bucket={bucket}, key={key}): {erro}")
        raise
