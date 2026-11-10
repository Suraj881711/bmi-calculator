# bmi_app.py — Advanced BMI & Health Metrics Calculator
#
# Upgrades over the original BMI-only version:
#   * Unit support: height in metres, centimetres or feet+inches;
#     weight in kilograms or pounds
#   * Age + gender inputs feeding real health formulas:
#       - BMR (Mifflin-St Jeor) and TDEE (activity multipliers)
#       - Body-fat % estimate (Deurenberg formula)
#       - Personalised daily calorie target for lose / maintain / gain
#   * Every calculation is stored in SQLite with a timestamp; a history
#     page lists past results and shows a simple trend
#   * Full input validation with friendly errors, /health as JSON
#
# The `BMICalculator` class and its original methods (BMIcal,
# yourCategory, healthy_weight_range) are kept; the class now works in
# canonical units (kg, metres) and gains the new metric methods.
import os
import sqlite3

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("BMI_DB_PATH",
                         os.path.join(BASE_DIR, "bmi_history.db"))

LB_TO_KG = 0.45359237
INCH_TO_M = 0.0254

# TDEE = BMR x activity multiplier (standard Mifflin-St Jeor practice)
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,     # little or no exercise
    "light": 1.375,       # light exercise 1-3 days/week
    "moderate": 1.55,     # moderate exercise 3-5 days/week
    "active": 1.725,      # hard exercise 6-7 days/week
    "very_active": 1.9,   # very hard exercise / physical job
}
ACTIVITY_LABELS = {
    "sedentary": "Sedentary (little or no exercise)",
    "light": "Light (exercise 1–3 days/week)",
    "moderate": "Moderate (exercise 3–5 days/week)",
    "active": "Active (hard exercise 6–7 days/week)",
    "very_active": "Very active (physical job / athlete)",
}

# Daily calorie adjustment vs TDEE for each goal
GOAL_ADJUSTMENTS = {"lose": -500, "maintain": 0, "gain": 300}
GOAL_LABELS = {
    "lose": "Lose weight",
    "maintain": "Maintain weight",
    "gain": "Gain weight",
}
MIN_CALORIE_TARGET = 1200  # never recommend eating below this


# ------------------------------------------------------------ unit helpers
def weight_to_kg(value, unit):
    """Convert a weight value to kilograms. unit: 'kg' or 'lb'."""
    if unit == "lb":
        return value * LB_TO_KG
    return float(value)


def height_to_m(value, unit, inches=0.0):
    """Convert a height to metres.
    unit 'm'  -> value is metres
    unit 'cm' -> value is centimetres
    unit 'ft' -> value is feet, plus `inches`
    """
    if unit == "cm":
        return value / 100.0
    if unit == "ft":
        return (value * 12.0 + inches) * INCH_TO_M
    return float(value)


# -------------------------------------------------------------- calculator
class BMICalculator:
    """Health metrics for one person. Weight in kg, height in metres
    (canonical units — convert before constructing)."""

    def __init__(self, name, weight, height, age=None, gender=None):
        self.name = name
        self.weight = weight
        self.height = height
        self.age = age
        self.gender = gender  # 'male' or 'female'

    def BMIcal(self):
        bmi = self.weight / (self.height ** 2)
        return round(bmi, 2)

    def yourCategory(self):
        bmi = self.BMIcal()
        if bmi < 18.5:
            return "Underweight"
        elif 18.5 <= bmi < 25:
            return "Normal weight"
        elif 25 <= bmi < 30:
            return "Overweight"
        else:
            return "Obese"

    def healthy_weight_range(self):
        """Weight range (kg) that gives a Normal BMI (18.5-24.9)
        for this person's height."""
        low = 18.5 * (self.height ** 2)
        high = 24.9 * (self.height ** 2)
        return round(low, 1), round(high, 1)

    def bmr(self):
        """Basal Metabolic Rate via the Mifflin-St Jeor equation.
        Needs age and gender; returns None without them."""
        if self.age is None or self.gender not in ("male", "female"):
            return None
        base = (10 * self.weight + 6.25 * (self.height * 100)
                - 5 * self.age)
        return round(base + (5 if self.gender == "male" else -161), 2)

    def tdee(self, activity="sedentary"):
        """Total Daily Energy Expenditure = BMR x activity multiplier."""
        bmr = self.bmr()
        if bmr is None:
            return None
        return round(bmr * ACTIVITY_MULTIPLIERS[activity], 2)

    def body_fat_percentage(self):
        """Body-fat % estimate via the Deurenberg formula:
        BF% = 1.20 x BMI + 0.23 x age - 10.8 x sex - 5.4
        (sex = 1 for male, 0 for female). Needs age and gender."""
        if self.age is None or self.gender not in ("male", "female"):
            return None
        sex = 1 if self.gender == "male" else 0
        bf = 1.20 * self.BMIcal() + 0.23 * self.age - 10.8 * sex - 5.4
        return round(bf, 1)

    def calorie_target(self, activity="sedentary", goal="maintain"):
        """Personalised daily calorie target: TDEE adjusted for the
        goal, floored at MIN_CALORIE_TARGET."""
        tdee = self.tdee(activity)
        if tdee is None:
            return None
        target = tdee + GOAL_ADJUSTMENTS[goal]
        return round(max(target, MIN_CALORIE_TARGET), 2)


INTERPRETATIONS = {
    "Underweight": "Your BMI is below the healthy range. Consider a "
                   "nutritious, calorie-rich diet and consult a doctor "
                   "if this is unintentional.",
    "Normal weight": "Great — your BMI is in the healthy range. "
                     "Keep up your current lifestyle!",
    "Overweight": "Your BMI is above the healthy range. Regular "
                  "exercise and a balanced diet can help bring it down.",
    "Obese": "Your BMI is in the obese range. It is a good idea to "
             "consult a healthcare professional for a personalised plan.",
}


# ------------------------------------------------------------------- store
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS calculations (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT,
            age            INTEGER,
            gender         TEXT,
            weight_kg      REAL,
            height_m       REAL,
            bmi            REAL,
            category       TEXT,
            bmr            REAL,
            tdee           REAL,
            body_fat       REAL,
            activity       TEXT,
            goal           TEXT,
            calorie_target REAL,
            created_at     TEXT NOT NULL
                DEFAULT (datetime('now', 'localtime'))
        )
        """)
    return conn


def save_calculation(record):
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO calculations (name, age, gender, weight_kg, "
            "height_m, bmi, category, bmr, tdee, body_fat, activity, "
            "goal, calorie_target) VALUES "
            "(:name, :age, :gender, :weight_kg, :height_m, :bmi, "
            ":category, :bmr, :tdee, :body_fat, :activity, :goal, "
            ":calorie_target)", record)
        conn.commit()
    finally:
        conn.close()


def load_history():
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM calculations ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def history_trend(records):
    """Simple trend summary over the stored history (records are
    newest-first): count, average BMI, first vs latest BMI and the
    change between them."""
    if not records:
        return None
    bmis = [r["bmi"] for r in records]
    first = records[-1]["bmi"]   # oldest entry
    latest = records[0]["bmi"]   # newest entry
    return {
        "count": len(records),
        "average_bmi": round(sum(bmis) / len(bmis), 2),
        "first_bmi": first,
        "latest_bmi": latest,
        "change": round(latest - first, 2),
    }


# ------------------------------------------------------------------ routes
@app.route("/", methods=["GET", "POST"])
def bmi_form():
    if request.method == "POST":
        form = request.form
        name = form.get("name", "").strip()

        # --- parse numbers (friendly error, never a crash) -------------
        try:
            weight_raw = float(form["weight"])
            height_raw = float(form["height"])
            inches_raw = float(form.get("height_in") or 0)
            age = int(float(form["age"]))
        except (KeyError, TypeError, ValueError):
            return render_template(
                "form.html",
                error="⚠️ Please enter valid numbers for weight, "
                      "height and age.")

        weight_unit = form.get("weight_unit", "kg")
        height_unit = form.get("height_unit", "m")
        gender = form.get("gender", "")
        activity = form.get("activity", "sedentary")
        goal = form.get("goal", "maintain")
        if weight_unit not in ("kg", "lb") or height_unit not in (
                "m", "cm", "ft"):
            return render_template(
                "form.html", error="⚠️ Please choose valid units.")
        if activity not in ACTIVITY_MULTIPLIERS or goal not in \
                GOAL_ADJUSTMENTS:
            return render_template(
                "form.html",
                error="⚠️ Please choose a valid activity level and goal.")

        # --- convert to canonical units --------------------------------
        weight = round(weight_to_kg(weight_raw, weight_unit), 2)
        height = round(height_to_m(height_raw, height_unit, inches_raw), 4)

        # --- validate ----------------------------------------------------
        if not name:
            return render_template(
                "form.html", error="⚠️ Please enter your name.")
        if not (2 <= weight <= 500):
            return render_template(
                "form.html",
                error="⚠️ Your weight works out to "
                      f"{weight} kg — please enter a weight between "
                      "2 and 500 kg.")
        if not (0.5 <= height <= 2.5):
            return render_template(
                "form.html",
                error="⚠️ Your height works out to "
                      f"{height} m — please enter a height between "
                      "0.5 and 2.5 m.")
        if not (5 <= age <= 120):
            return render_template(
                "form.html",
                error="⚠️ Age must be between 5 and 120 years.")
        if gender not in ("male", "female"):
            return render_template(
                "form.html",
                error="⚠️ Please select a gender — the BMR, TDEE and "
                      "body-fat formulas need it.")

        person = BMICalculator(name, weight, height, age=age,
                               gender=gender)
        bmi = person.BMIcal()
        category = person.yourCategory()
        low, high = person.healthy_weight_range()
        bmr = person.bmr()
        tdee = person.tdee(activity)
        body_fat = person.body_fat_percentage()
        target = person.calorie_target(activity, goal)

        save_calculation({
            "name": name, "age": age, "gender": gender,
            "weight_kg": weight, "height_m": height, "bmi": bmi,
            "category": category, "bmr": bmr, "tdee": tdee,
            "body_fat": body_fat, "activity": activity, "goal": goal,
            "calorie_target": target,
        })

        return render_template(
            "result.html", name=name, bmi=bmi, category=category,
            healthy_low=low, healthy_high=high, height=height,
            weight=weight, age=age, gender=gender, bmr=bmr, tdee=tdee,
            body_fat=body_fat, activity_label=ACTIVITY_LABELS[activity],
            goal_label=GOAL_LABELS[goal], calorie_target=target,
            interpretation=INTERPRETATIONS[category])

    return render_template("form.html")


@app.route("/history")
def history_page():
    records = load_history()
    return render_template("history.html", records=records,
                           trend=history_trend(records))


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
