import os, pandas as pd, sqlalchemy as sa
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
