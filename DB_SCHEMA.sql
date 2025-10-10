CREATE TABLE exercises (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	tag VARCHAR(24), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_exercise_user_name UNIQUE (user_id, name), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE sets (
	id INTEGER NOT NULL, 
	workout_id INTEGER NOT NULL, 
	exercise_id INTEGER NOT NULL, 
	reps INTEGER NOT NULL, 
	weight FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(workout_id) REFERENCES workouts (id), 
	FOREIGN KEY(exercise_id) REFERENCES exercises (id)
);

CREATE TABLE users (
	id INTEGER NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	units VARCHAR(8), 
	PRIMARY KEY (id), 
	UNIQUE (email)
);

CREATE TABLE workouts (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	date DATE, 
	notes VARCHAR(255), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_sets_exercise ON sets (exercise_id);

CREATE INDEX ix_workouts_user_date ON workouts (user_id, date);

