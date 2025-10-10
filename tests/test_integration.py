import os
os.environ["DATABASE_URL"] = "sqlite:///instance/test_integration.sqlite3"  # use isolated test DB

import pytest
from app import app, init_db, SessionLocal

@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    """Ensure a clean database before each test."""
    init_db()
    yield
    try:
        SessionLocal.remove()
    except Exception:
        pass


def test_log_workout_happy_path():
    """Test a valid POST /workouts flow."""
    client = app.test_client()
    rv = client.post("/workouts", data={
        "date": "2025-09-15",
        "exercise": "Squat",
        "reps": "5",
        "weight": "185",
        "notes": "integration test"
    }, follow_redirects=True)
    assert rv.status_code == 200
    # confirm success flash is shown
    assert b"Workout added!" in rv.data


def test_log_workout_invalid_reps():
    """Test invalid reps (0) triggers validation message."""
    client = app.test_client()
    rv = client.post("/workouts", data={
        "date": "2025-09-15",
        "exercise": "Squat",
        "reps": "0",
        "weight": "185",
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert b"Reps must be a positive whole number." in rv.data


def test_metrics_404_for_unknown_exercise():
    """Test that /api/metrics/<exercise> returns 404 for unknown exercise."""
    client = app.test_client()
    rv = client.get("/api/metrics/NotARealLift")
    assert rv.status_code == 404
    data = rv.get_json()
    assert "error" in data
