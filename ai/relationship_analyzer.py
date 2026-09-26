"""
Relationship Analysis — statistical associations between indicator pairs.

Uses Pearson correlation over the full historical dataset. Results are
explicitly framed as associations, never as causal relationships.
"""

import pandas as pd

# Pairs we specifically care about for the education MVP, plus the
# human-readable interpretation template for each direction.
PAIRS = [
    ("transport_access", "dropout_rate"),
    ("internet_access", "attendance"),
    ("teacher_ratio", "performance_index"),
    ("household_income", "performance_index"),
    ("attendance", "performance_index"),
]


def _strength_label(r: float) -> str:
    abs_r = abs(r)
    if abs_r >= 0.7:
        return "strong"
    if abs_r >= 0.4:
        return "moderate"
    if abs_r >= 0.2:
        return "weak"
    return "negligible"


def _direction_label(r: float) -> str:
    return "inverse" if r < 0 else "direct"


def analyze_relationships(df: pd.DataFrame) -> list[dict]:
    results = []
    for source, target in PAIRS:
        if source not in df.columns or target not in df.columns:
            continue
        subset = df[[source, target]].dropna()
        if len(subset) < 3:
            continue

        r = float(subset[source].corr(subset[target]))
        strength = _strength_label(r)
        direction = _direction_label(r)

        direction_word = "tends to decrease" if direction == "inverse" else "tends to increase"
        interpretation = (
            f"Across the dataset, as {source.replace('_', ' ')} increases, "
            f"{target.replace('_', ' ')} {direction_word} "
            f"(a {strength} {direction} association, r = {r:.2f}). "
            "This describes a statistical pattern only — it does not confirm "
            "that one factor causes the other."
        )

        results.append({
            "source": source,
            "target": target,
            "strength": round(abs(r), 2),
            "direction": direction,
            "correlation_coefficient": round(r, 3),
            "interpretation": interpretation,
        })

    return results
