import duckdb


def inspecionar_dados(query):
    duckdb.sql("INSTALL httpfs;")
    duckdb.sql("LOAD httpfs;")
    duckdb.sql("CALL load_aws_credentials();")
    duckdb.sql("SET s3_region='us-east-1';")
    resultado = duckdb.sql(query)
    resultado.show()


if __name__ == "__main__":
    inspecionar_dados(
        "SELECT * FROM 's3://aws-datalake-analytics-felipecaron/silver/customers/customers.parquet' LIMIT 10"
    )
