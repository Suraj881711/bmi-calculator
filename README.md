# ⚖️ BMI & Health Metrics Calculator — Advanced

A Flask web app that goes far beyond a basic BMI calculator: enter
your details in metric **or** imperial units and get your BMI,
category, healthy weight range, **BMR**, **TDEE**, an estimated
**body-fat percentage** and a **personalised daily calorie target** —
with every calculation saved to a history page that shows your trend
over time. A beginner-friendly OOP project (a `BMICalculator` class
does all the maths); there is no machine-learning model in this
project — every number comes from the standard published formulas
named below.

## Features

- **BMI + category** — Underweight / Normal / Overweight / Obese, with
  a plain-language interpretation and the **healthy weight range** for
  your height
- **Unit support** — height in **metres, centimetres or feet+inches**;
  weight in **kilograms or pounds**, converted exactly
  (1 lb = 0.45359237 kg, 1 in = 0.0254 m)
- **BMR (Mifflin-St Jeor)** — basal metabolic rate from weight,
  height, age and gender
- **TDEE** — BMR × activity multiplier for five activity levels
  (sedentary 1.2 · light 1.375 · moderate 1.55 · active 1.725 ·
  very active 1.9)
- **Body-fat % estimate** — Deurenberg formula
  (1.20×BMI + 0.23×age − 10.8×sex − 5.4)
- **Personalised calorie target** — TDEE adjusted for your goal:
  lose (−500 kcal) · maintain (±0) · gain (+300 kcal), never below
  1,200 kcal/day
- **History with trend** — every calculation is stored in SQLite with
  a timestamp; the history page lists all past results and shows
  count, average BMI, and first → latest BMI change
- **Friendly validation** — bad or out-of-range input (including
  values that only become invalid *after* unit conversion) returns a
  clear error message, never a server crash

## What's advanced in this version

The original version took only a name, a weight in kg and a height in
metres, and showed just BMI + category. This version adds:

- **Real health formulas** — Mifflin-St Jeor BMR, activity-based TDEE,
  Deurenberg body-fat estimate and goal-based calorie targets, all as
  testable methods on the original `BMICalculator` class
- **A unit-conversion layer** (`weight_to_kg` / `height_to_m`) so
  imperial users get exactly the same maths as metric users
- **Persistence** — a SQLite history (stdlib `sqlite3`) instead of
  one-off results, plus a small trend summary (average / first /
  latest / change)
- **Validation after conversion**, so e.g. a weight entered in pounds
  is checked against the kg limits once converted
- A **pytest test-suite** (`test_app.py`, 10 tests) covering unit
  conversions, formula values for known examples (e.g. male, 70 kg,
  175 cm, age 25 → BMR 1673.75), metric/imperial/cm end-to-end flows,
  validation, and history recording

Example: male, 70 kg at 1.75 m, age 25, moderate activity →
BMI **22.86 (Normal weight)**, healthy range 56.7–76.3 kg,
BMR **1673.75 kcal**, TDEE **2594.31 kcal**, body-fat ≈ **17.0%**.

## Tech stack

- Python, Flask (Jinja templates), SQLite (stdlib `sqlite3`)
- pytest for tests

## How to run

```bash
pip install -r requirements.txt
python bmi_app.py
```

Open http://127.0.0.1:5000, fill the form, and use the
**History** link to see past calculations.

Run the tests with:

```bash
pip install pytest
pytest test_app.py
```

## Files

- `bmi_app.py` — Flask app + `BMICalculator` class + unit converters
  + SQLite history (routes `/`, `/history`, `/health`)
- `test_app.py` — pytest suite (Flask test client, throwaway DB)
- `BMI.ipynb` — the original notebook version of the calculator,
  kept as-is
- `templates/form.html`, `templates/result.html`,
  `templates/history.html`
- `bmi_history.db` — created at runtime (git-ignored, not shipped)

## Note

BMI, BMR, TDEE and body-fat values here are standard formula
*estimates* for learning purposes — they are not medical measurements
or medical advice.
