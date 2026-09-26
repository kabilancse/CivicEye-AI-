"""
Data loading + cleaning for the Education MVP domain.

This module is the single source of truth for "clean" data — every AI
module and route should get its dataframe from here rather than reading
the CSV directly, so cleaning rules only live in one place.
"""

import pandas as pd

from config import Config

_NUMERIC_COLUMNS = [
    "attendance", "dropout_rate", "transport_access", "internet_access",
    "teacher_ratio", "household_income", "enrollment", "performance_index",
]

_cache = {"df": None}


def load_raw_dataframe() -> pd.DataFrame:
    return pd.read_csv(Config.EDUCATION_CSV_PATH)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleaning rules:
    - drop exact duplicate rows
    - coerce numeric columns, drop rows that fail to parse
    - clip out-of-range values to sane bounds (percentages 0-100, etc.)
    - fill isolated missing numeric values with the column median
    - strip whitespace from text columns
    """
    df = df.copy()
    df = df.drop_duplicates()

    for col in ["area"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    for col in _NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows missing the key identifying fields
    df = df.dropna(subset=["area", "year"]) if "year" in df.columns else df.dropna(subset=["area"])

    # Fill remaining numeric gaps with column median (keeps dataset usable for small demo data)
    for col in _NUMERIC_COLUMNS:
        if col in df.columns and df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())

    # Clip percentage-like fields to 0-100
    for col in ["attendance", "transport_access", "internet_access"]:
        if col in df.columns:
            df[col] = df[col].clip(0, 100)
    if "dropout_rate" in df.columns:
        df["dropout_rate"] = df["dropout_rate"].clip(0, 100)
    if "performance_index" in df.columns:
        df["performance_index"] = df["performance_index"].clip(0, 100)

    df = df.reset_index(drop=True)
    return df


def get_education_data(force_reload: bool = False) -> pd.DataFrame:
    """Returns the cleaned education dataframe, cached in memory after first load."""
    if _cache["df"] is None or force_reload:
        raw = load_raw_dataframe()
        _cache["df"] = clean_dataframe(raw)
    return _cache["df"]


def get_latest_year_snapshot(df: pd.DataFrame = None) -> pd.DataFrame:
    """Returns one row per area — the most recent year available for each."""
    if df is None:
        df = get_education_data()
    if "year" not in df.columns:
        return df
    idx = df.groupby("area")["year"].idxmax()
    return df.loc[idx].reset_index(drop=True)


def is_synthetic(df: pd.DataFrame = None) -> bool:
    df = df if df is not None else get_education_data()
    if "data_source" in df.columns and len(df) > 0:
        return bool((df["data_source"] == "SYNTHETIC_DEMO").all())
    return True  # default to flagging as synthetic unless proven otherwise
