# CivicEye AI+ — API Contract

Base URL (local dev): `http://localhost:5000`

All responses are JSON. All error responses have the shape:
```json
{ "error": "human-readable message" }
```

Authenticated endpoints require a header:
```
Authorization: Bearer <token>
```
(also accepted: `X-Auth-Token: <token>`)

**Design principle:** CivicEye is a decision-support tool. Every AI-derived
response uses hedged language ("association", "potential pattern",
"model-based estimate") and never asserts causation. Fields like
`is_model_estimate`, `data_is_synthetic`, and `disclaimer` are part of the
contract — the frontend should surface them, not hide them.

---

## Auth

### `POST /api/auth/register`
Body:
```json
{
  "username": "ngo1",
  "email": "ngo1@example.com",
  "password": "min8chars",
  "role": "citizen | researcher | organization | platform_admin | data_admin",
  "organization_name": "Required only if role = organization"
}
```
`201`:
```json
{ "user": { "id": 1, "username": "ngo1", "email": "ngo1@example.com", "role": "organization" }, "token": "..." }
```
Errors: `400` (validation), `409` (username/email taken)

### `POST /api/auth/login`
Body: `{ "username": "ngo1", "password": "..." }` (or `"email"` instead of `"username"`)
`200`:
```json
{ "user": { "id": 1, "username": "ngo1", "email": "...", "role": "organization", "organization_name": "..." }, "token": "..." }
```
Errors: `400`, `401`

### `GET /api/auth/me` *(auth required)*
`200`: current user object.

---

## Citizen Mode

### `GET /api/citizen/statistics`
`200`:
```json
{
  "areas_covered": 15,
  "latest_year": 2025,
  "average_attendance": 79.4,
  "average_dropout_rate": 9.9,
  "average_transport_access": 63.5,
  "average_internet_access": 63.0,
  "total_enrollment": 15329,
  "data_is_synthetic": true
}
```

### `GET /api/citizen/problems`
Query params (optional): `area`, `type` (`local_info` | `identified_pattern` | `ongoing_initiative` | `completed_initiative`)
`200`:
```json
{
  "items": [
    {
      "id": 1, "title": "...", "description": "...", "area": "Walajabad",
      "item_type": "identified_pattern", "source": "CivicEye Social Radar (demo run)",
      "status": "active", "item_date": "2026-09-01 00:00:00",
      "is_ai_generated_content": true
    }
  ],
  "count": 4
}
```

---

## Social Explorer

### `GET /api/social/patterns`
Query params (optional): `limit` (default 8)
`200`:
```json
{
  "patterns": [
    {
      "id": "pattern-0016280f9e",
      "title": "Unusual indicator combination detected in Chengalpattu",
      "area": "Chengalpattu",
      "year": 2025,
      "severity": "high | moderate | low",
      "indicators": [
        { "field": "performance_index", "value": 40.6, "district_median": 62.0 }
      ],
      "explanation": "This area shows a potential pattern where ... This does not establish that one factor causes another.",
      "is_model_estimate": true
    }
  ],
  "count": 3,
  "data_is_synthetic": true,
  "disclaimer": "Patterns reflect statistical associations in the dataset and are not confirmed causes."
}
```

### `GET /api/social/relationships`
`200`:
```json
{
  "relationships": [
    {
      "source": "transport_access", "target": "dropout_rate",
      "strength": 0.94, "direction": "inverse", "correlation_coefficient": -0.94,
      "interpretation": "Across the dataset, as transport access increases, dropout rate tends to decrease (a strong inverse association, r = -0.94). This describes a statistical pattern only — it does not confirm that one factor causes the other."
    }
  ],
  "count": 5,
  "data_is_synthetic": true,
  "disclaimer": "All relationships describe statistical associations only, not proven causation."
}
```

### `GET /api/social/impact`
Query params (optional): `pattern_id` (narrows to a single pattern's area; omit to aggregate across all currently flagged high/moderate-risk areas)
`200`:
```json
{
  "pattern_id": null,
  "high_risk_areas": ["Chengalpattu", "Cheyyur", "Vandalur"],
  "affected_population_estimate": 3539,
  "total_population_reference": 15329,
  "affected_share_pct": 23.1,
  "comparison_with_overall_dataset": [
    { "field": "transport_access", "affected_area_average": 72.2, "overall_average": 63.5, "gap": 8.7 }
  ],
  "note": "Population and comparison figures are model-based estimates derived from current dataset records, not confirmed field counts.",
  "data_is_synthetic": true
}
```

### `GET /api/social/trends`
Query params (optional): `area` (omit for all areas)
`200`:
```json
{
  "trends": [
    {
      "area": "Walajabad",
      "years_covered": [2021, 2025],
      "trends": {
        "attendance": {
          "direction": "increasing | decreasing | stable",
          "annual_change_estimate": 0.45,
          "confidence_r_squared": 0.06,
          "forecast_year": 2027,
          "forecast_value_estimate": 78.4
        }
      },
      "note": "Forecasts extend only 2 years ahead using a simple linear model and are rough, model-based estimates — not guaranteed outcomes."
    }
  ],
  "count": 15,
  "data_is_synthetic": true,
  "disclaimer": "Trend forecasts are simple model-based projections, not guaranteed outcomes."
}
```

### `POST /api/social/simulation`
Body: any subset of `transport_access`, `internet_access`, `teacher_ratio`, `household_income`, plus optional `area` and `outcome_field` (default `dropout_rate`).
```json
{ "transport_access": 70, "internet_access": 80 }
```
`200`:
```json
{
  "outcome_field": "dropout_rate",
  "area": "dataset_average",
  "baseline_inputs": { "transport_access": 59.8, "internet_access": 58.5, "teacher_ratio": 30.9, "household_income": 33703.9 },
  "scenario_inputs_applied": { "transport_access": 70.0, "internet_access": 80.0, "teacher_ratio": 30.9, "household_income": 33703.9 },
  "current_outcome": 10.5,
  "scenario_outcome": 7.7,
  "estimated_change": -2.8,
  "model_r_squared": 0.93,
  "label": "model-based scenario estimate — not a guaranteed result",
  "data_is_synthetic": true
}
```
Errors: `400` (empty body / unknown area / unknown outcome_field)

---

## Action Center *(intervention workflow, not a complaint system)*

### `GET /api/actions`
Public. Query params (optional): `area`, `status` (`proposed`|`in_progress`|`completed`|`verified`), `problem_id`
`200`: `{ "interventions": [ {...} ], "count": 1 }`

### `POST /api/actions` *(auth required — roles: organization, platform_admin, data_admin)*
Body:
```json
{ "problem_id": "pattern-xyz", "title": "Add school bus route", "description": "...", "area": "Chengalpattu", "evidence": "Radar pattern + field visit" }
```
`201`: the created intervention row (status defaults to `proposed`).

### `PUT /api/actions/{id}` *(auth required — creator org, or platform_admin)*
Body: any of `title`, `description`, `status`, `evidence`, `progress_notes`, `outcome`.
`200`: the updated intervention row.
Errors: `403` (not the creator / not an admin), `404`

---

## Admin

### `GET /api/admin/users` *(platform_admin)*
### `PATCH /api/admin/users/{id}/role` *(platform_admin)* — body: `{ "role": "..." }`
### `GET /api/admin/dataset/summary` *(data_admin, platform_admin)*
### `POST /api/admin/dataset/reload` *(data_admin, platform_admin)* — re-reads and re-cleans the CSV
### `GET /api/admin/civic-items` *(data_admin, platform_admin)*
### `POST /api/admin/civic-items` *(data_admin, platform_admin)* — body: `title`, `item_type`, `source` (required), plus `description`, `area`, `status`

---

## Misc

### `GET /api/health`
`200`: `{ "status": "ok", "service": "CivicEye AI+ backend" }`

---

## Notes for frontend developers
- Every dataset-derived response includes `data_is_synthetic: true` while the MVP runs on the generated demo dataset (`data/education.csv`, tagged `data_source: SYNTHETIC_DEMO`). Surface this in the UI (e.g. a small "Demo Data" badge) — never present it as live/real civic data.
- `severity`, `strength`, and `direction` fields are stable enum-like strings safe to map to UI colors/icons.
- All monetary values (`household_income`) are in INR, unformatted integers.
- If any AI feature is temporarily broken during development, its route will keep returning the same JSON shape shown above with placeholder values — the shape is the contract, not the values.
