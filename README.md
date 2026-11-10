# ⚖️ BMI Calculator

A small Flask web app that calculates your Body Mass Index (BMI) from
your weight and height and tells you your category — Underweight,
Normal, Overweight or Obese. A beginner OOP + Flask project (a
`BMICalculator` class does the maths); there is no machine-learning
model in this project.

## What it does

Enter your name, weight (kg) and height (in metres — e.g. 1.70 for
170 cm). The app shows:

- Your BMI, rounded to 2 decimals
- Your category with a short interpretation of what it means
- The **healthy weight range for your height** (the weight band that
  gives a Normal BMI of 18.5–24.9)

Example: 70 kg at 1.75 m → BMI **22.86 (Normal weight)**, healthy range
56.7–76.3 kg.

## Fixes & upgrades in this version

- **Crash fixed:** height 0 (or a non-numeric weight) previously crashed
  the app with a server error; inputs are now validated with friendly
  error messages (weight 2–500 kg, height 0.5–2.5 m).
- **Healthy-weight range added** for the entered height.
- **Category interpretation added** — a plain-language line under the
  category (the category itself was already computed by the original
  code).

## Tech stack

- Python, Flask

## How to run

```bash
pip install -r requirements.txt
python bmi_app.py
```

Open http://127.0.0.1:5000 and submit the form.

## Files

- `bmi_app.py` — Flask app + `BMICalculator` class (routes `/`,
  `/health`)
- `BMI.ipynb` — notebook version of the calculator
- `templates/form.html`, `templates/result.html`
