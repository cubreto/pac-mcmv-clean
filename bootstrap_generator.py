#!/usr/bin/env python3
"""
PAC-MCMV Clean Bootstrap Generator
Creates all files and directory structure for the PAC-MCMV project
"""

import os
import pathlib
from typing import Dict, Any

def create_file(path: pathlib.Path, content: str) -> None:
    """Create a file with the given content, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {path}")

def create_bootstrap_project(base_path: str = ".") -> None:
    """Create the complete PAC-MCMV project structure."""
    
    base = pathlib.Path(base_path)
    
    # File contents dictionary
    files = {
        # Root level files
        ".gitignore": """__pycache__/
*.pyc
.env*
.vscode/
.idea/
*.db
*.log
# Docker
*.pid
# Build
*.egg-info/
__dist__/
""",

        "docker-compose.clean.yml": """version: "3.9"
services:
  db_v2:
    image: postgres:15-alpine
    container_name: pac-db-v2
    environment:
      POSTGRES_DB: pac_mcmv_v2
      POSTGRES_PASSWORD: V2secret
    ports: ["55432:5432"]
    volumes:
      - db_data_v2:/var/lib/postgresql/data

  etl_v2:
    build: ./etl
    container_name: pac-etl-v2
    environment:
      DB_URL: postgresql://postgres:V2secret@db_v2:5432/pac_mcmv_v2
    depends_on: [db_v2]
    volumes:
      - ./sample_data:/data:ro

  dashboard_v2:
    build: ./dashboards/streamlit
    container_name: pac-dash-v2
    environment:
      DB_URL: postgresql://postgres:V2secret@db_v2:5432/pac_mcmv_v2
    ports: ["8503:8501"]
    depends_on: [db_v2]
volumes:
  db_data_v2:
""",

        "README.md": """# PAC‑MCMV Clean Stack (v2)

```bash
# 1. Clone
# 2. Place the three source Excel files in sample_data/
# 3. Build & run
$ docker compose -f docker-compose.clean.yml up --build -d
# 4. Trigger ETL once
$ docker compose -f docker-compose.clean.yml run --rm etl_v2
# 5. Open http://localhost:8503
```

All logic lives here; legacy stack remains untouched.
""",

        # Database SQL files
        "db/sql/001_create_core_schema.sql": """-- Core / staging separation
CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS core;

-- Staging tables are 1‑to‑1 with source sheets (created by COPY)
-- Core tables normalised for the KPIs

CREATE TABLE IF NOT EXISTS core.projeto (
  nu_apf             BIGINT PRIMARY KEY,
  programa           TEXT NOT NULL,             -- FAR / FDS / RURAL
  sg_uf              TEXT,
  no_municipio       TEXT,
  qt_uh              INTEGER,
  vr_total_operacao  NUMERIC(18,2),
  dt_inicio_obra     DATE,
  dt_previsao_entrega DATE,
  pc_obra_realizada  NUMERIC(5,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS core.beneficiario (
  id SERIAL PRIMARY KEY,
  nu_apf BIGINT REFERENCES core.projeto(nu_apf),
  sexo   CHAR(1),
  vr_compra NUMERIC(18,2)
);
""",

        "db/sql/002_create_kpi_views.sql": """CREATE OR REPLACE VIEW kpi_vw_portfolio AS
SELECT
  COUNT(*)                            AS total_projects,
  SUM(qt_uh)                          AS total_housing_units,
  SUM(vr_total_operacao)              AS total_investment,
  ROUND(AVG(pc_obra_realizada),2)     AS avg_completion
FROM core.projeto;

CREATE OR REPLACE VIEW kpi_vw_programa AS
SELECT programa,
       COUNT(*)                   AS total_projects,
       SUM(qt_uh)                 AS total_units,
       SUM(vr_total_operacao)     AS total_investment,
       ROUND(AVG(pc_obra_realizada),2) AS avg_completion
FROM core.projeto
GROUP BY programa;
""",

        # ETL files
        "etl/Dockerfile": """FROM python:3.11-slim
WORKDIR /app
COPY etl/ /app/etl
RUN pip install --no-cache-dir pandas sqlalchemy openpyxl click
ENTRYPOINT ["python", "-m", "etl.main"]
""",

        "etl/__init__.py": """# empty – marks the package
""",

        "etl/main.py": '''"""Master ETL entry‑point – python -m etl.main"""
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
''',

        "etl/transform/__init__.py": """# shared helpers live here later
""",

        "etl/transform/mcmv.py": '''import pandas as pd, pathlib as pl

CORE_COLUMNS = {
    "NU_APF":           "nu_apf",
    "SG_UF":            "sg_uf",
    "NO_MUNICIPIO":     "no_municipio",
    "NU_QT_UH":         "qt_uh",
    "VR_TOTAL_OPERACAO": "vr_total_operacao",
    "DT_INICIO_OBRA":    "dt_inicio_obra",
    "DT_PREVISAO_ENTREGA_DO_EMPREENDIMENTO": "dt_previsao_entrega",
    "PC_OBRA_REALIZADA": "pc_obra_realizada",
}

CAD_SHEET = "HISTB010_MONITORAMENTO_CADASTRO"
MOV_SHEET = "HISTB012_MOVIMENTO_OBRA"


def build_core_df(xlsx_path: pl.Path, programa: str) -> pd.DataFrame:
    """Return a dataframe ready for core.projeto"""
    cad = pd.read_excel(xlsx_path, sheet_name=CAD_SHEET, engine="openpyxl")
    mov = pd.read_excel(xlsx_path, sheet_name=MOV_SHEET, engine="openpyxl")[["NU_APF","PC_OBRA_REALIZADA","DT_PREVISAO_ENTREGA_DO_EMPREENDIMENTO"]]

    merged = cad.merge(mov, on="NU_APF", how="left", suffixes=("","_mov"))
    merged["programa"] = programa

    df = merged.rename(columns=CORE_COLUMNS)[list(CORE_COLUMNS.values()) + ["programa"]]
    # clean types
    date_cols = ["dt_inicio_obra","dt_previsao_entrega"]
    for c in date_cols:
        df[c] = pd.to_datetime(df[c], errors="coerce").dt.date
    df["pc_obra_realizada"] = pd.to_numeric(df["pc_obra_realizada"], errors="coerce").fillna(0)
    return df
''',

        "etl/load/to_core.py": '''import pandas as pd, sqlalchemy as sa

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
''',

        "etl/load/__init__.py": """# load module
""",

        # Dashboard files
        "dashboards/streamlit/Dockerfile": """FROM python:3.11-slim
WORKDIR /app
COPY app.py /app/
RUN pip install streamlit sqlalchemy pandas psycopg2-binary
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
""",

        "dashboards/streamlit/app.py": '''import os, pandas as pd, sqlalchemy as sa
import streamlit as st

engine = sa.create_engine(os.environ["DB_URL"])

st.title("🏗️ PAC‑MCMV Clean Dashboard v2")

with st.spinner("loading KPIs …"):
    kpi_port = pd.read_sql("SELECT * FROM kpi_vw_portfolio", engine)
    cols = st.columns(3)
    cols[0].metric("Projects", f"{int(kpi_port.total_projects[0]):,}")
    cols[1].metric("Housing units", f"{int(kpi_port.total_housing_units[0]):,}")
    cols[2].metric("Avg % complete", f"{kpi_port.avg_completion[0]} %")

st.markdown("### By Programme")
st.dataframe(pd.read_sql("SELECT * FROM kpi_vw_programa", engine))
''',

        # Test files
        "tests/test_etl_smoke.py": '''import subprocess, pathlib, sqlalchemy as sa, os

def test_etl_smoke():
    repo = pathlib.Path(__file__).resolve().parents[1]
    compose = ["docker", "compose", "-f", repo/"docker-compose.clean.yml", "run", "--rm", "etl_v2"]
    res = subprocess.run(compose, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
''',

        "tests/__init__.py": """# tests module
""",
    }

    # Create all files
    print(f"Creating PAC-MCMV project structure in: {base.absolute()}")
    print("=" * 60)
    
    for file_path, content in files.items():
        full_path = base / file_path
        create_file(full_path, content)
    
    # Create empty directories
    empty_dirs = [
        "sample_data"
    ]
    
    for dir_path in empty_dirs:
        dir_full_path = base / dir_path
        dir_full_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directory is tracked
        gitkeep_path = dir_full_path / ".gitkeep"
        create_file(gitkeep_path, "# Keep this directory in git\n")
    
    print("=" * 60)
    print("✅ Project structure created successfully!")
    print()
    print("Next steps:")
    print("1. Copy your Excel files (FAR.xlsx, FDS.xlsx, RURAL.xlsx) to sample_data/")
    print("2. Run: docker compose -f docker-compose.clean.yml up --build -d")
    print("3. Run: docker compose -f docker-compose.clean.yml run --rm etl_v2")
    print("4. Open: http://localhost:8503")
    print()
    print("File structure created:")
    
    # Show directory tree
    def show_tree(directory: pathlib.Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
        if current_depth >= max_depth:
            return
        
        items = sorted([item for item in directory.iterdir() if not item.name.startswith('.')])
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item.name}")
            
            if item.is_dir() and current_depth < max_depth - 1:
                extension = "    " if is_last else "│   "
                show_tree(item, prefix + extension, max_depth, current_depth + 1)
    
    show_tree(base)

if __name__ == "__main__":
    import sys
    
    # Get target directory from command line argument or use current directory
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    
    create_bootstrap_project(target_dir)
