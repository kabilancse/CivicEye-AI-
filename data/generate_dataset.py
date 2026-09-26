"""
Generates a SYNTHETIC/DEMO education dataset for CivicEye AI+.

IMPORTANT: This data is entirely artificial. It is generated with
intentional patterns (e.g. low transport access correlating with higher
dropout) so that the Social Radar / Relationship Analysis / Impact
Analysis modules have something meaningful to detect during development
and demos. It must never be presented to end users as real civic data.

Run: python generate_dataset.py
Output: education.csv (in the same directory)
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

AREAS = [
    "Kanchipuram Urban", "Kanchipuram Rural North", "Kanchipuram Rural South",
    "Sriperumbudur", "Walajabad", "Uthiramerur", "Chengalpattu",
    "Tambaram", "Madurantakam", "Kundrathur", "Tirukalukundram",
    "Cheyyur", "Pallavaram", "Vandalur", "Guduvancheri",
]

YEARS = [2021, 2022, 2023, 2024, 2025]

rows = []
for area in AREAS:
    # Each area gets a "profile" — a persistent underlying disadvantage level.
    # This is what creates realistic, non-random relationships across areas.
    disadvantage = RNG.uniform(0, 1)  # 0 = well-served area, 1 = underserved

    # Slight year-over-year drift so trend analysis has something to show.
    drift = RNG.uniform(-1.5, 1.5)

    for year in YEARS:
        year_index = year - YEARS[0]

        transport_access = np.clip(
            85 - disadvantage * 55 + RNG.normal(0, 5) + year_index * 1.0, 10, 100
        )
        internet_access = np.clip(
            80 - disadvantage * 50 + RNG.normal(0, 6) + year_index * 2.0, 5, 100
        )
        household_income = np.clip(
            45000 - disadvantage * 25000 + RNG.normal(0, 3000) + year_index * 500, 8000, 90000
        )
        teacher_ratio = np.clip(  # students per teacher (higher = worse)
            22 + disadvantage * 20 + RNG.normal(0, 3) - year_index * 0.3, 15, 60
        )

        # attendance and dropout are influenced by transport/internet/teacher_ratio
        attendance = np.clip(
            92
            - disadvantage * 25
            + (transport_access - 60) * 0.05
            + (internet_access - 60) * 0.03
            - (teacher_ratio - 25) * 0.15
            + RNG.normal(0, 3)
            + drift,
            35,
            99,
        )
        dropout_rate = np.clip(
            3
            + disadvantage * 14
            - (transport_access - 60) * 0.04
            - (internet_access - 60) * 0.02
            + (teacher_ratio - 25) * 0.12
            + RNG.normal(0, 1.5)
            - drift * 0.3,
            0.2,
            35,
        )
        enrollment = int(np.clip(
            1200 - disadvantage * 500 + RNG.normal(0, 100) + year_index * 15, 200, 2500
        ))
        performance_index = np.clip(  # 0-100 composite academic performance
            78
            - disadvantage * 30
            + (attendance - 70) * 0.2
            + (internet_access - 60) * 0.05
            - (teacher_ratio - 25) * 0.1
            + RNG.normal(0, 4),
            20,
            100,
        )

        rows.append({
            "area": area,
            "year": year,
            "attendance": round(attendance, 1),
            "dropout_rate": round(dropout_rate, 1),
            "transport_access": round(transport_access, 1),
            "internet_access": round(internet_access, 1),
            "teacher_ratio": round(teacher_ratio, 1),
            "household_income": int(household_income),
            "enrollment": enrollment,
            "performance_index": round(performance_index, 1),
            "data_source": "SYNTHETIC_DEMO",
        })

df = pd.DataFrame(rows)
df.to_csv("education.csv", index=False)
print(f"Generated {len(df)} rows across {len(AREAS)} areas and {len(YEARS)} years.")
print(df.head())
