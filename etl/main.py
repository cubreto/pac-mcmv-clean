"""Master ETL entry‑point – python -m etl.main"""
import os, pathlib, click, pandas as pd, sqlalchemy as sa
from etl.transform.mcmv import build_core_df
from etl.load.to_core import upsert_dataframe

DB_URL = os.environ["DB_URL"]
ENGINE = sa.create_engine(DB_URL)

@click.command()
@click.option("--path", default="/data", help="Folder with FAR/FDS/RURAL workbooks")
@click.option("--program", type=click.Choice(["FAR", "FDS", "RURAL", "ALL"], case_sensitive=False), default="ALL")
def run(path: str, program: str):
    path = pathlib.Path(path)
    files = {
        "FAR":   path / "FAR.xlsx",
        "FDS":   path / "FDS.xlsx",
        "RURAL": path / "RURAL.xlsx",
    }
    targets = files.keys() if program == "ALL" else [program]

    core_frames = []
    for prog in targets:
        fp = files[prog]
        if not fp.exists():
            click.echo(f"[WARN] {fp} missing, skipping")
            continue
        click.echo(f"Extracting {prog} → {fp.name}")
        core_frames.append(build_core_df(fp, prog))

    if core_frames:
        df = pd.concat(core_frames, ignore_index=True)
        click.echo(f"Loading {len(df):,} rows into core.projeto …")
        upsert_dataframe(df, "core", "projeto", ENGINE, ["nu_apf"], chunksize=5000)
        click.echo("✅ done")
    else:
        click.echo("Nothing to load ✋")

if __name__ == "__main__":
    run()
