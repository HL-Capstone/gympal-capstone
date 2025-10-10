# GymPal (MVP – Week 4 Assignment)

## Project Overview
GymPal is a lightweight Python/Flask web application for logging workouts and visualizing strength progress. It allows users to record exercises, view recent workouts, and track weekly best estimated one-rep max (e1RM) using the Epley formula. The dashboard includes simple forecasting to project progress based on at least two weeks of data.

## Architecture Summary
GymPal follows a simple three-layer architecture:
- **Frontend/UI:** HTML templates styled with Bootstrap and dynamic graphs rendered using Chart.js.  
- **Backend:** Flask routes handle workout logging, validation, and metrics APIs.  
- **Persistence:** SQLite database managed with SQLAlchemy ORM defines four core entities: `User`, `Exercise`, `Workout`, and `Set`.  
- **Analytics:** The app computes estimated 1RM values with the Epley formula and applies a simple linear regression for 4-week forecasts.  

This implementation aligns with the Week 3 design: a CRUD flow (create workout → persist → retrieve/list), visualization of progress, and a forecast feature. The main change from the design was running in single-user mode (no authentication) for feasibility, and setting forecasts to appear with two weeks of data instead of three.

## Architecture Delta (Week 5)
New features and improvements added in Week 5:
- **CSV Export:** `/export.csv` lets users download all workout data.  
- **Audit Logging:** `/dev/logs` captures each workout creation for review.  
- **Database Refinement:** Unique constraint `(user_id, name)` on exercises, plus indexes on `(user_id, date)` and `(exercise_id)` for faster queries.  
- **Security Enhancements:** Input validation, secure cookies, custom 404/500 pages, and HTTP security headers (CSP, nosniff, DENY).  
- **Health Check Endpoint:** `/healthz` returns app and DB status.  
- **Performance Baseline:** Benchmarked API response times to ensure stability under light load.


## Prerequisites
- Python 3.11+  
- Windows PowerShell or another terminal  
- (Optional) Git and Visual Studio Code  

## Setup & Run (Development)
Clone the project in PowerShell:

```powershell
# 1. Navigate into the project folder
cd gympal

# 2. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables (PowerShell syntax)
$env:FLASK_APP="app:app"
$env:FLASK_DEBUG="1"

# 5. Run the Flask app
python -m flask run

# 6. Input Seed Data

GymPal includes a seed.py script to pre-populate the database with 10 weeks of Squat workouts.
This ensures the dashboard shows a line and forecast immediately, even without manually logging workouts.

# Make sure the instance/ folder exists in the project root running:
    mkdir instance

# then run the seed script:
    python seed.py

# Verify that the database file was created:
    ls .\instance\gympal.sqlite3


## Default Credentials / User
GymPal runs in single-user mode (no login). 

Start the Flask app:
$env:FLASK_APP="app:app"
python -m flask run

Open the dashboard at http://127.0.0.1:5000
 and confirm you see:
A Squat line with weekly best e1RM values and a 4-week forecast 

# Install pytest if not already installed
    pip install pytest

# Run tests
    pytest -q

# Test Coverage includes
Epley 1RM calculation is accurate.
Forecast only appears after ≥ 2 weeks of data.
Forecast trends never dip below latest actual.
Workout validation (happy path, invalid reps).
Metrics 404 response for unknown exercise.

# End to End (E2E) Test
Keep the Flask app running and then in another PowerShell window run:

-  newman run tests\GymPal.postman_collection.json  -

This simulates a full user journey from dashboard → create workout → view metrics — ensuring all layers work together. I did this by opening a split terminal on the bottom.

# Performance Summary
This is measured with bench.py (it sends 50 requests to /api/metrics/Squat):
avg = 11.83 ms p50 = 15.20 ms p95 = 25.10 ms
Results are pretty good and are within the 20–50 ms target range.


# Week 5 Security checklist

Input validation: /workouts checks that exercise isnt blank, reps > 0, and weight ≥ 0 to prevent bad data and errors.
Secure cookies: HTTPONLY and SAMESITE=Lax reduce XSS/CSRF risk; SECURE=True will be turned on for HTTPS.
Error hygiene: Custom 404/500 pages hide stack traces and log errors server-side.
Security headers: Added DENY, no-referrer, and a CSP limiting scripts/styles to the app and trusted CDN.
Deferred risks and potential next steps include adding CSRF protection and maybe some basic login/auth.

# Endpoints Overview
Endpoint	        Description
/	                Dashboard with charts & forecast
/workouts	        Add or view workouts
/export.csv	        Download all workout data
/api/metrics/<exercise>	Returns weekly best e1RM + forecast (JSON)
/dev/logs	        View recent log entries (dev only)
/healthz	        Health check endpoint (verifies DB connectivity)