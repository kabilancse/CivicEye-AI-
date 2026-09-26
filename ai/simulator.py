"""
What-If Simulation.

Fits a simple, interpretable linear regression predicting an outcome
indicator (default: dropout_rate) from the modifiable indicators
(transport_access, internet_access, teacher_ratio, household_income).
The user supplies hypothetical values for one or more inputs; the model
predicts the resulting outcome and compares it to the current baseline.

This is explicitly a MODEL-BASED SCENARIO ESTIMATE, not a guaranteed
real-world result — every response is labeled as such.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

INPUT_FIELDS = ["transport_access", "internet_access", "teacher_ratio", "household_income"]
DEFAULT_OUTCOME_FIELD = "dropout_rate"


def _train_model(df: pd.DataFrame, outcome_field: str):
    available_inputs = [f for f in INPUT_FIELDS if f in df.columns]
    working = df[available_inputs + [outcome_field]].dropna()
    X = working[available_inputs].to_numpy()
    y = working[outcome_field].to_numpy()

    model = LinearRegression()
    model.fit(X, y)
    return model, available_inputs, working


def run_simulation(df: pd.DataFrame, scenario_inputs: dict, area: str = None,
                    outcome_field: str = DEFAULT_OUTCOME_FIELD) -> dict:
    """
    scenario_inputs: dict of {field: hypothetical_value}, e.g.
        {"transport_access": 70, "internet_access": 80}
    area: optional — if given, baseline is that area's latest values;
          otherwise the dataset-wide average is used as baseline.
    """
    if outcome_field not in df.columns:
        raise ValueError(f"Unknown outcome field: {outcome_field}")

    model, available_inputs, working = _train_model(df, outcome_field)

    if area:
        area_df = df[df["area"] == area]
        if area_df.empty:
            raise ValueError(f"Unknown area: {area}")
        baseline_row = area_df.sort_values("year").iloc[-1] if "year" in area_df.columns else area_df.iloc[0]
        baseline_values = {f: float(baseline_row[f]) for f in available_inputs}
    else:
        baseline_values = {f: float(working[f].mean()) for f in available_inputs}

    current_outcome = float(model.predict([[baseline_values[f] for f in available_inputs]])[0])

    scenario_values = dict(baseline_values)
    unknown_fields = [f for f in scenario_inputs if f not in available_inputs]
    for field, value in scenario_inputs.items():
        if field in scenario_values:
            scenario_values[field] = float(value)

    scenario_outcome = float(model.predict([[scenario_values[f] for f in available_inputs]])[0])

    # Clip to sane bounds for rate-style outcomes
    if outcome_field in ("dropout_rate", "attendance", "performance_index"):
        current_outcome = float(np.clip(current_outcome, 0, 100))
        scenario_outcome = float(np.clip(scenario_outcome, 0, 100))

    result = {
        "outcome_field": outcome_field,
        "area": area or "dataset_average",
        "baseline_inputs": {k: round(v, 1) for k, v in baseline_values.items()},
        "scenario_inputs_applied": {k: round(v, 1) for k, v in scenario_values.items()},
        "current_outcome": round(current_outcome, 1),
        "scenario_outcome": round(scenario_outcome, 1),
        "estimated_change": round(scenario_outcome - current_outcome, 1),
        "model_r_squared": round(float(model.score(
            working[available_inputs].to_numpy(), working[outcome_field].to_numpy()
        )), 2),
        "label": "model-based scenario estimate — not a guaranteed result",
    }
    if unknown_fields:
        result["ignored_fields"] = unknown_fields
    return result
