from flask import Flask, render_template, request

app = Flask(__name__)


class BMICalculator:
    def __init__(self, name, weight, height):
        self.name = name
        self.weight = weight
        self.height = height

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


@app.route("/", methods=["GET", "POST"])
def bmi_form():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        try:
            weight = float(request.form["weight"])
            height = float(request.form["height"])
        except (KeyError, TypeError, ValueError):
            return render_template(
                "form.html",
                error="⚠️ Please enter valid numbers for weight and height.")

        if not name:
            return render_template(
                "form.html", error="⚠️ Please enter your name.")
        if not (2 <= weight <= 500):
            return render_template(
                "form.html",
                error="⚠️ Weight must be between 2 and 500 kg.")
        if not (0.5 <= height <= 2.5):
            return render_template(
                "form.html",
                error="⚠️ Height must be in metres, between 0.5 and 2.5 "
                      "(e.g. 1.70 for 170 cm).")

        person = BMICalculator(name, weight, height)
        bmi = person.BMIcal()
        category = person.yourCategory()
        low, high = person.healthy_weight_range()

        return render_template(
            "result.html", name=name, bmi=bmi, category=category,
            healthy_low=low, healthy_high=high, height=height,
            weight=weight, interpretation=INTERPRETATIONS[category])

    return render_template("form.html")


@app.route("/health")
def health():
    return {'status': 'ok'}


if __name__ == "__main__":
    app.run(debug=True)
