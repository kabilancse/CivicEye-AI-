"""
Simulation service — thin wrapper around ai.simulator for the routes layer.
"""

from ai.simulator import run_simulation
from services.data_service import get_education_data, is_synthetic


def run_whatif_simulation(scenario_inputs: dict, area: str = None, outcome_field: str = None) -> dict:
    df = get_education_data()
    kwargs = {"area": area}
    if outcome_field:
        kwargs["outcome_field"] = outcome_field
    result = run_simulation(df, scenario_inputs, **kwargs)
    result["data_is_synthetic"] = is_synthetic(df)
    return result
