import pandas as pd, sqlalchemy as sa

def upsert_dataframe(df: pd.DataFrame, schema: str, table: str, engine: sa.Engine, pk_cols, chunksize=10000):
    """Naïve UPSERT via temporary table + MERGE (Postgres ≥15)."""
    with engine.begin() as cx:
        tmp = sa.text(f"CREATE TEMP TABLE tmp AS SELECT * FROM {schema}.{table} WITH NO DATA;")
        cx.execute(tmp)
        df.to_sql("tmp", con=cx, index=False, if_exists="append")
        cols = ','.join(df.columns)
        pk = ','.join(pk_cols)
        merge_sql = f"""
        INSERT INTO {schema}.{table} ({cols})
        SELECT {cols} FROM tmp
        ON CONFLICT ({pk}) DO UPDATE SET
          {', '.join(f'{c}=EXCLUDED.{c}' for c in df.columns if c not in pk_cols)};
        """
        cx.execute(sa.text(merge_sql))
