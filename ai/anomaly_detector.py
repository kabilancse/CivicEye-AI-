"""
Social Radar — unusual-pattern detection.

Uses Isolation Forest over the latest-year snapshot of the education
dataset to flag areas whose combined indicator profile is unusual
relative to the rest of the dataset (e.g. low transport access + high
dropout + low attendance occurring together).

IMPORTANT: this module identifies STATISTICAL ANOMALIES / ASSOCIATIONS.
It never asserts that one indicator causes another. All explanations
use hedged language ("associated with", "co-occurs with", "potential
pattern").
"""

import uuid

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from config import Config

FEATURES = [
    "attendance", "dropout_rate", "transport_access",
    "internet_access", "teacher_ratio", "performance_index",
]

# Indicators where a HIGHER value is worse (used to decide severity/direction wording)
_HIGHER_IS_WORSE = {"dropout_rate", "teacher_ratio"}


def _severity_from_score(score: float, lo: float, hi: float) -> str:
    """Maps an anomaly score (more negative = more unusual) to a severity label."""
    if hi == lo:
        return "moderate"
    normalized = (hi - score) / (hi - lo)  # 0 (least unusual) .. 1 (most unusual)
    if normalized >= 0.75:
        return "high"
    if normalized >= 0.45:
        return "moderate"
    return "low"


def _describe_indicator(col: str, value: float, median: float) -> str:
    diff_pct = ((value - median) / median * 100) if median else 0
    direction = "higher" if diff_pct > 0 else "lower"
    worse = (col in _HIGHER_IS_WORSE) == (diff_pct > 0)
    qualifier = "notably worse than" if worse else "notably better than"
    return f"{col.replace('_', ' ')} is {abs(diff_pct):.0f}% {direction} than the district median ({qualifier} typical)"


def detect_patterns(df: pd.DataFrame, top_n: int = 8) -> list[dict]:
    """
    Runs Isolation Forest on the latest snapshot per area and returns a
    structured list of detected patterns, most unusual first.
    """
    if df.empty or len(df) < 3:
        return []

    working = df.copy()
    X = working[FEATURES].fillna(working[FEATURES].median())

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        contamination=Config.ANOMALY_CONTAMINATION,
        random_state=Config.RANDOM_STATE,
        n_estimators=200,
    )
    model.fit(X_scaled)

    scores = model.decision_function(X_scaled)  # higher = more normal
    predictions = model.predict(X_scaled)  # -1 = anomaly, 1 = normal

    working["_anomaly_score"] = scores
    working["_is_anomaly"] = predictions == -1

    medians = working[FEATURES].median()
    score_lo, score_hi = scores.min(), scores.max()

    anomalies = working[working["_is_anomaly"]].sort_values("_anomaly_score")

    patterns = []
    for _, row in anomalies.head(top_n).iterrows():
        # Rank each feature by how far it deviates (in std units) from the median
        deviations = {}
        for col in FEATURES:
            std = working[col].std() or 1.0
            deviations[col] = abs(row[col] - medians[col]) / std
        top_indicators = sorted(deviations, key=deviations.get, reverse=True)[:3]

        indicator_details = [
            {
                "field": col,
                "value": round(float(row[col]), 1),
                "district_median": round(float(medians[col]), 1),
            }
            for col in top_indicators
        ]

        explanation_parts = [_describe_indicator(col, row[col], medians[col]) for col in top_indicators]
        explanation = (
            "This area shows a potential pattern where "
            + "; ".join(explanation_parts)
            + ". These indicators are statistically associated in this snapshot; "
              "this does not establish that one factor causes another."
        )

        severity = _severity_from_score(row["_anomaly_score"], score_lo, score_hi)

        patterns.append({
            "id": f"pattern-{uuid.uuid4().hex[:10]}",
            "title": f"Unusual indicator combination detected in {row['area']}",
            "area": row["area"],
            "year": int(row["year"]) if "year" in row else None,
            "severity": severity,
            "indicators": indicator_details,
            "explanation": explanation,
            "is_model_estimate": True,
        })

    return patterns
