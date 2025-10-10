from datetime import date, timedelta
from random import choice
from app import SessionLocal, init_db, User, Exercise, Workout, Set

def run():
    init_db()
    db = SessionLocal()
    try:
        # default single user
        u = db.query(User).filter_by(email="default@local").first()
        if not u:
            u = User(email="default@local"); db.add(u); db.commit(); db.refresh(u)

        # ensure Squat exists
        squat = db.query(Exercise).filter_by(user_id=u.id, name="Squat").first()
        if not squat:
            squat = Exercise(user_id=u.id, name="Squat", tag="Legs")
            db.add(squat); db.commit(); db.refresh(squat)

        # create 10 weeks of squat, +5 per week, 5x5 each workout
        start = date.today() - timedelta(weeks=10)
        for wk in range(10):
            w = Workout(user_id=u.id, date=start + timedelta(weeks=wk, days=choice([0,1,2])), notes="Seeded workout")
            db.add(w); db.commit(); db.refresh(w)
            base = 135 + wk * 5
            for _ in range(5):
                db.add(Set(workout_id=w.id, exercise_id=squat.id, reps=5, weight=base))
            db.commit()

        print("Seeded demo data. Restart Flask and refresh the dashboard.")
    finally:
        SessionLocal.remove()

if __name__ == "__main__":
    run()
