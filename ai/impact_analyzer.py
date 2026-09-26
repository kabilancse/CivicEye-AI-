"""
Impact Analysis — for a given identified pattern (or, by default, the
most recent Social Radar run), estimate scale of impact and compare
high-risk areas against overall dataset baselines.
"""

import pandas as pd

from ai.anomaly_detector import FEATURES, detect_patterns


def _high_risk_area_names(patterns: list[dict]) -> list[str]:
    return list({p["area"] for p in patterns if p["severity"] in ("high", "moderate")})


def analyze_impact(df: pd.DataFrame, pattern_id: str = None, patterns: list[dict] = None) -> dict:
    """
    If patterns is not supplied, runs a fresh Social Radar detection.
    If pattern_id is supplied, narrows the analysis to that single pattern's area;
    otherwise aggregates across all currently flagged high/moderate risk areas.
    """
    if patterns is None:
        patterns = detect_patterns(df)

    if pattern_id:
        patterns = [p for p in patterns if p["id"] == pattern_id]

    high_risk_areas = _high_risk_area_names(patterns)

    latest = df.loc[df.groupby("area")["year"].idxmax()] if "year" in df.columns else df
    affected = latest[latest["area"].isin(high_risk_areas)]
    overall = latest

    affected_population = int(affected["enrollment"].sum()) if "enrollment" in affected else None
    total_population = int(overall["enrollment"].sum()) if "enrollment" in overall else None

    important_variables = []
    for col in FEATURES:
        if col not in affected.columns or affected.empty:
            continue
        affected_mean = float(affected[col].mean())
        overall_mean = float(overall[col].mean())
        gap = affected_mean - overall_mean
        important_variables.append({
            "field": col,
            "affected_area_average": round(affected_mean, 1),
            "overall_average": round(overall_mean, 1),
            "gap": round(gap, 1),
        })

    important_variables.sort(key=lambda v: abs(v["gap"]), reverse=True)

    return {
        "pattern_id": pattern_id,
        "high_risk_areas": high_risk_areas,
        "affected_population_estimate": affected_population,
        "total_population_reference": total_population,
        "affected_share_pct": (
            round(affected_population / total_population * 100, 1)
            if affected_population is not None and total_population
            else None
        ),
        "comparison_with_overall_dataset": important_variables,
        "note": (
            "Population and comparison figures are model-based estimates derived from "
            "current dataset records, not confirmed field counts."
        ),
    }
