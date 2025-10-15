from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import csv, io
from datetime import date
from collections import defaultdict
import logging, sys, os
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
load_dotenv()


from sqlalchemy import create_engine, Column, Integer, Float, String, Date, ForeignKey, UniqueConstraint, Index, text

from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship, scoped_session


LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("gympal")
logger.setLevel(logging.INFO)

fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

# file
fh = RotatingFileHandler(os.path.join(LOG_DIR, "app.log"), maxBytes=500_000, backupCount=2)
fh.setFormatter(fmt); fh.setLevel(logging.INFO)
logger.addHandler(fh)

# console
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(fmt); ch.setLevel(logging.INFO)
logger.addHandler(ch)


# ---------- DB setup ----------
DB_URL = os.environ.get("DATABASE_URL") or "sqlite:///instance/gympal.sqlite3"

class Base(DeclarativeBase):
    pass

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    units = Column(String(8), default="lb")
    exercises = relationship("Exercise", back_populates="user", cascade="all, delete-orphan")
    workouts = relationship("Workout", back_populates="user", cascade="all, delete-orphan")

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(80), nullable=False)
    tag = Column(String(24), default="General")
    user = relationship("User", back_populates="exercises")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_exercise_user_name"),
    )
class Workout(Base):
    __tablename__ = "workouts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, default=date.today)
    notes = Column(String(255), default="")
    user = relationship("User", back_populates="workouts")
    sets = relationship("Set", back_populates="workout", cascade="all, delete-orphan")

class Set(Base):
    __tablename__ = "sets"
    id = Column(Integer, primary_key=True)
    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    reps = Column(Integer, nullable=False)
    weight = Column(Float, nullable=True)
    workout = relationship("Workout", back_populates="sets")
    exercise = relationship("Exercise")

# ---------- Indexes ----------
Index("ix_workouts_user_date", Workout.user_id, Workout.date)
Index("ix_sets_exercise", Set.exercise_id)

def init_db():
    Base.metadata.create_all(engine)

# ---------- Metrics ----------
def epley_e1rm(weight: float, reps: int) -> float:
    if not weight or not reps or reps <= 0:
        return 0.0
    return float(weight) * (1.0 + reps / 30.0)

def weekly_best_e1rm(session, user_id: int, exercise_name: str):
    """Return [{'iso_week': '2025-W34', 'best_e1rm': 225.0}, ...]"""
    rows = (
        session.query(Workout.date, Set.weight, Set.reps, Exercise.name)
        .join(Set, Set.workout_id == Workout.id)
        .join(Exercise, Exercise.id == Set.exercise_id)
        .filter(Workout.user_id == user_id, Exercise.name.ilike(exercise_name))
        .order_by(Workout.date.asc())
        .all()
    )
    by_week = defaultdict(float)
    for d, w, r, _ in rows:
        y, wnum, _ = d.isocalendar()
        best = epley_e1rm(w or 0, r or 0)
        by_week[(y, wnum)] = max(by_week[(y, wnum)], best)
    out = []
    for (y, wnum), best in sorted(by_week.items()):
        out.append({"iso_week": f"{y}-W{wnum:02d}", "best_e1rm": round(best, 2)})
    return out

def linear_forecast(values, weeks_ahead=4):
    # your requirement: allow as few as 2 points
    n = len(values)
    if n < 2:
        return []
    x = list(range(n))
    xm = sum(x)/n
    ym = sum(values)/n
    num = sum((xi-xm)*(yi-ym) for xi, yi in zip(x, values))
    den = sum((xi-xm)**2 for xi in x) or 1.0
    slope = num/den
    intercept = ym - slope*xm
    return [round(intercept + slope*(n+i), 2) for i in range(1, weeks_ahead+1)]

# ---------- Flask ----------
app = Flask(__name__, instance_relative_config=True)
app.config["SECRET_KEY"] = "dev-secret"
init_db()

# Single-user mode (no auth)
def get_user(session):
    u = session.query(User).filter_by(email="default@local").first()
    if not u:
        u = User(email="default@local")
        session.add(u); session.commit()
    return u

# Seed a small exercise library on first visit
DEFAULT_EXERCISES = [
    ("Squat","Legs"), ("Bench Press","Chest"), ("Deadlift","Back"), ("Overhead Press","Shoulders"),
    ("Barbell Curl","Biceps"), ("Triceps Pushdown","Triceps"), ("Lateral Raise","Shoulders")
]

@app.route("/")
def index():
    db = SessionLocal()
    try:
        user = get_user(db)
        for name, tag in DEFAULT_EXERCISES:
            if not db.query(Exercise).filter_by(user_id=user.id, name=name).first():
                db.add(Exercise(user_id=user.id, name=name, tag=tag))
        db.commit()
        return render_template("index.html")
    finally:
        SessionLocal.remove()

@app.route("/workouts", methods=["GET", "POST"])
def workouts():
    db = SessionLocal()
    try:
        user = get_user(db)

        if request.method == "POST":
            # --- read inputs (use .get to avoid error) ---
            ex_name  = (request.form.get("exercise") or "").strip()
            reps_raw = (request.form.get("reps") or "").strip()
            weight_raw = (request.form.get("weight") or "").strip()
            notes    = request.form.get("notes", "")
            date_str = request.form.get("date") or str(date.today())

            # --- validate inputs ---
            if not ex_name:
                flash("Please enter or select an exercise.", "warning")
                return redirect(url_for("workouts"))

            # reps must be a positive whole number (no decimals)
            if not reps_raw.isdigit() or int(reps_raw) <= 0:
                flash("Reps must be a positive whole number.", "warning")
                return redirect(url_for("workouts"))

            # weight must be a number bigger than 0
            try:
                weight_val = float(weight_raw)
                if weight_val < 0:
                    raise ValueError
            except ValueError:
                flash("Weight must be a non-negative number.", "warning")
                return redirect(url_for("workouts"))

            # --- look up or create the exercise ---
            ex = db.query(Exercise).filter_by(user_id=user.id, name=ex_name).first()
            if not ex:
                ex = Exercise(user_id=user.id, name=ex_name, tag="General")
                db.add(ex); db.commit(); db.refresh(ex)

            # --- save workout + set ---
            w = Workout(user_id=user.id, date=date.fromisoformat(date_str), notes=notes)
            db.add(w); db.commit(); db.refresh(w)

            db.add(Set(workout_id=w.id, exercise_id=ex.id, reps=int(reps_raw), weight=weight_val))
            db.commit()

            # --- log the action right after saving ---
            logger.info(
                f"workout_created user={user.id} exercise={ex_name} "
                f"reps={int(reps_raw)} weight={weight_val} date={date_str}"
            )

            flash("Workout added!", "success")
            return redirect(url_for("workouts"))

        # --- GET: render form + recent workouts ---
        ex_names = [e.name for e in db.query(Exercise)
                    .filter_by(user_id=user.id)
                    .order_by(Exercise.name).all()]

        items = (db.query(Workout)
                   .filter_by(user_id=user.id)
                   .order_by(Workout.date.desc())
                   .limit(20).all())

        rows = []
        for w in items:
            pairs = (db.query(Set, Exercise)
                     .join(Exercise, Exercise.id == Set.exercise_id)
                     .filter(Set.workout_id == w.id).all())
            rows.append((w, [(ex.name, s.reps, s.weight) for s, ex in pairs]))

        return render_template("workouts.html", ex_names=ex_names, workouts=rows)
    finally:
        SessionLocal.remove()


@app.route("/api/metrics/<exercise>")
def api_metrics(exercise):
    db = SessionLocal()
    try:
        user = get_user(db)
        points = weekly_best_e1rm(db, user.id, exercise)
        if not points:
            # helpful message + correct status
            return jsonify({"error": f"No data for exercise '{exercise}'"}), 404
        values = [p["best_e1rm"] for p in points]
        forecast = linear_forecast(values, weeks_ahead=4) if len(values) >= 2 else []
        return jsonify({"points": points, "forecast": forecast})
    finally:
        SessionLocal.remove()

@app.route("/export.csv")
def export_csv():
    db = SessionLocal()
    try:
        user = get_user(db)
        rows = (
            db.query(Workout.date, Exercise.name, Set.reps, Set.weight, Workout.notes)
              .join(Set, Set.workout_id == Workout.id)
              .join(Exercise, Exercise.id == Set.exercise_id)
              .filter(Workout.user_id == user.id)
              .order_by(Workout.date.desc(), Workout.id.desc())
              .all()
        )
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["date", "exercise", "reps", "weight", "notes"])
        for d, ex, reps, wt, notes in rows:
            writer.writerow([d.isoformat(), ex, reps, wt if wt is not None else "", notes or ""])
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=gympal_export.csv"}
        )
    finally:
        SessionLocal.remove()

@app.route("/dev/logs", strict_slashes=False)
def dev_logs():
    try:
        with open(os.path.join(LOG_DIR, "app.log"), "r", encoding="utf-8") as f:
            lines = f.readlines()[-200:]  # last 200 lines
        return Response("".join(lines), mimetype="text/plain")
    except FileNotFoundError:
        return Response("No logs yet.\n", mimetype="text/plain")

@app.route("/healthz")
def healthz():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "db": "ok"}), 200
    except Exception as e:
        logger.error(f"healthz error: {e}")
        return jsonify({"status": "degraded"}), 500
    finally:
        SessionLocal.remove()


app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # SESSION_COOKIE_SECURE=True,  # enable if serving over HTTPS
)

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"server_error: {e}")
    return render_template("500.html"), 500

@app.after_request
def add_security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    # Allow our site + jsDelivr (Chart.js & Bootstrap if you use it)
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' https://cdn.jsdelivr.net; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    return resp

