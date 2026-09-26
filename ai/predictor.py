"""
Trend / Future Analysis — simple, non-exaggerated trend estimation.

Uses ordinary least-squares linear regression per (area, indicator) over
available years. This is intentionally simple: the goal is to show
direction and rough magnitude of change, not to make confident long-range
forecasts. Extrapolation is limited to a short horizon and always labeled
as a model-based estimate.
"""

import numpy as np
import pandas as pd

TREND_FIELDS = ["attendance", "dropout_rate", "transport_access", "internet_access", "performance_index"]
MAX_FORECAST_YEARS_AHEAD = 2


def _linear_trend(years: np.ndarray, values: np.ndarray) -> dict:
    if len(years) < 2:
        return None
    slope, intercept = np.polyfit(years, values, 1)
    # R^2 for a rough confidence signal
    predicted = slope * years + intercept
    ss_res = np.sum((values - predicted) ** 2)
    ss_tot = np.sum((values - np.mean(values)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {"slope": float(slope), "intercept": float(intercept), "r_squared": round(float(max(r_squared, 0)), 2)}


def analyze_trends(df: pd.DataFrame, area: str = None) -> list[dict]:
    if "year" not in df.columns:
        return []

    results = []
    areas = [area] if area else sorted(df["area"].unique())

    for a in areas:
        area_df = df[df["area"] == a].sort_values("year")
        if area_df.empty:
            continue
        years = area_df["year"].to_numpy(dtype=float)

        field_trends = {}
        for field in TREND_FIELDS:
            if field not in area_df.columns:
                continue
            values = area_df[field].to_numpy(dtype=float)
            trend = _linear_trend(years, values)
            if trend is None:
                continue

            direction = "increasing" if trend["slope"] > 0.05 else ("decreasing" if trend["slope"] < -0.05 else "stable")
            last_year = int(years.max())
            forecast_year = last_year + MAX_FORECAST_YEARS_AHEAD
            forecast_value = trend["slope"] * forecast_year + trend["intercept"]

            field_trends[field] = {
                "direction": direction,
                "annual_change_estimate": round(trend["slope"], 2),
                "confidence_r_squared": trend["r_squared"],
                "forecast_year": forecast_year,
                "forecast_value_estimate": round(float(forecast_value), 1),
            }

        results.append({
            "area": a,
            "years_covered": [int(years.min()), int(years.max())],
            "trends": field_trends,
            "note": (
                f"Forecasts extend only {MAX_FORECAST_YEARS_AHEAD} years ahead using a simple linear "
                "model and are rough, model-based estimates — not guaranteed outcomes."
            ),
        })

    return results
