import pandas as pd, pathlib as pl

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
