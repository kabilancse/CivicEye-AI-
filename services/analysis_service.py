"""
Analysis service — thin orchestration layer between routes and the AI
modules. Keeps routes free of ML/data-wrangling logic.
"""

from ai.anomaly_detector import detect_patterns
from ai.impact_analyzer import analyze_impact
from ai.predictor import analyze_trends
from ai.relationship_analyzer import analyze_relationships
from services.data_service import get_education_data, get_latest_year_snapshot, is_synthetic


def get_social_patterns(top_n: int = 8) -> dict:
    df = get_education_data()
    snapshot = get_latest_year_snapshot(df)
    patterns = detect_patterns(snapshot, top_n=top_n)
    return {
        "patterns": patterns,
        "count": len(patterns),
        "data_is_synthetic": is_synthetic(df),
        "disclaimer": "Patterns reflect statistical associations in the dataset and are not confirmed causes.",
    }


def get_social_relationships() -> dict:
    df = get_education_data()
    relationships = analyze_relationships(df)
    return {
        "relationships": relationships,
        "count": len(relationships),
        "data_is_synthetic": is_synthetic(df),
        "disclaimer": "All relationships describe statistical associations only, not proven causation.",
    }


def get_social_impact(pattern_id: str = None) -> dict:
    df = get_education_data()
    snapshot = get_latest_year_snapshot(df)
    patterns = detect_patterns(snapshot)
    impact = analyze_impact(snapshot, pattern_id=pattern_id, patterns=patterns)
    impact["data_is_synthetic"] = is_synthetic(df)
    return impact


def get_social_trends(area: str = None) -> dict:
    df = get_education_data()
    trends = analyze_trends(df, area=area)
    return {
        "trends": trends,
        "count": len(trends),
        "data_is_synthetic": is_synthetic(df),
        "disclaimer": "Trend forecasts are simple model-based projections, not guaranteed outcomes.",
    }


def get_citizen_statistics() -> dict:
    df = get_education_data()
    snapshot = get_latest_year_snapshot(df)
    return {
        "areas_covered": int(snapshot["area"].nunique()),
        "latest_year": int(snapshot["year"].max()) if "year" in snapshot else None,
        "average_attendance": round(float(snapshot["attendance"].mean()), 1),
        "average_dropout_rate": round(float(snapshot["dropout_rate"].mean()), 1),
        "average_transport_access": round(float(snapshot["transport_access"].mean()), 1),
        "average_internet_access": round(float(snapshot["internet_access"].mean()), 1),
        "total_enrollment": int(snapshot["enrollment"].sum()),
        "data_is_synthetic": is_synthetic(df),
    }
