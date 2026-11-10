"""Tests for the advanced BMI & health metrics calculator.
Run with: pytest test_app.py

Uses a throwaway SQLite database for history tests, so the real
bmi_history.db is never touched.
"""
import pytest

import bmi_app
from bmi_app import (ACTIVITY_MULTIPLIERS, BMICalculator, GOAL_ADJUSTMENTS,
                     height_to_m, weight_to_kg)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(bmi_app, "DB_PATH", str(tmp_path / "test_bmi.db"))
    bmi_app.app.config["TESTING"] = True
    with bmi_app.app.test_client() as c:
        yield c


def post_calc(client, **overrides):
    data = {
        "name": "Test User", "age": "25", "gender": "male",
        "weight": "70", "weight_unit": "kg",
        "height": "1.75", "height_unit": "m", "height_in": "",
        "activity": "moderate", "goal": "maintain",
    }
    data.update(overrides)
    return client.post("/", data=data)


# ------------------------------------------------------------- unit maths
def test_unit_conversions():
    assert weight_to_kg(100, "kg") == 100
    assert weight_to_kg(100, "lb") == pytest.approx(45.359237)
    assert height_to_m(1.75, "m") == 1.75
    assert height_to_m(175, "cm") == 1.75
    # 5 ft 9 in = 69 in = 1.7526 m
    assert height_to_m(5, "ft", 9) == pytest.approx(1.7526)


def test_metric_bmi_and_category():
    person = BMICalculator("T", 70, 1.75, age=25, gender="male")
    assert person.BMIcal() == 22.86
    assert person.yourCategory() == "Normal weight"
    low, high = person.healthy_weight_range()
    assert (low, high) == (56.7, 76.3)


def test_bmr_tdee_bodyfat_and_target_values():
    # Known example: male, 70 kg, 175 cm, 25 years
    # BMR = 10*70 + 6.25*175 - 5*25 + 5 = 1673.75
    person = BMICalculator("T", 70, 1.75, age=25, gender="male")
    assert person.bmr() == 1673.75
    assert person.tdee("moderate") == pytest.approx(
        1673.75 * ACTIVITY_MULTIPLIERS["moderate"])
    # Deurenberg: 1.20*22.86 + 0.23*25 - 10.8*1 - 5.4 = 16.98
    assert person.body_fat_percentage() == pytest.approx(16.98, abs=0.05)
    tdee = person.tdee("moderate")
    assert person.calorie_target("moderate", "maintain") == tdee
    assert person.calorie_target("moderate", "lose") == \
        tdee + GOAL_ADJUSTMENTS["lose"]
    assert person.calorie_target("moderate", "gain") == \
        tdee + GOAL_ADJUSTMENTS["gain"]


def test_female_bmr():
    # Female: 10*60 + 6.25*165 - 5*30 - 161 = 1320.25
    person = BMICalculator("T", 60, 1.65, age=30, gender="female")
    assert person.bmr() == 1320.25


# -------------------------------------------------------------- web flows
def test_metric_calculation_flow(client):
    resp = post_calc(client)
    assert resp.status_code == 200
    assert b"22.86" in resp.data
    assert b"Normal weight" in resp.data
    assert b"1673.75" in resp.data  # BMR on the result page


def test_imperial_calculation_flow(client):
    # 154 lb = 69.85 kg; 5 ft 9 in = 1.7526 m -> BMI = 22.74 (Normal)
    resp = post_calc(client, weight="154", weight_unit="lb",
                     height="5", height_unit="ft", height_in="9")
    assert resp.status_code == 200
    assert b"22.74" in resp.data
    assert b"Normal weight" in resp.data


def test_cm_height_flow(client):
    resp = post_calc(client, height="175", height_unit="cm")
    assert resp.status_code == 200
    assert b"22.86" in resp.data  # same as 1.75 m


def test_validation_errors_do_not_crash(client):
    resp = post_calc(client, weight="abc")
    assert resp.status_code == 200
    assert b"valid numbers" in resp.data
    resp = post_calc(client, weight="9999")
    assert b"between" in resp.data
    resp = post_calc(client, height="0")
    assert b"between" in resp.data
    resp = post_calc(client, name="")
    assert b"enter your name" in resp.data
    resp = post_calc(client, age="2")
    assert b"Age must be between" in resp.data


def test_history_recording_and_trend(client):
    post_calc(client)                                   # BMI 22.86
    post_calc(client, weight="90")                      # BMI 29.39
    records = bmi_app.load_history()
    assert len(records) == 2
    assert records[0]["bmi"] == 29.39  # newest first
    trend = bmi_app.history_trend(records)
    assert trend["count"] == 2
    assert trend["first_bmi"] == 22.86
    assert trend["latest_bmi"] == 29.39
    assert trend["average_bmi"] == pytest.approx(26.12, abs=0.01)
    assert trend["change"] == pytest.approx(6.53, abs=0.01)
    resp = client.get("/history")
    assert resp.status_code == 200
    assert b"Calculation History" in resp.data
    assert b"Average BMI" in resp.data


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}
