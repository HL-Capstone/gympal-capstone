import sqlite3, pathlib, sys

db_path = pathlib.Path("instance/gympal.sqlite3")
if not db_path.exists():
    print("ERROR: instance/gympal.sqlite3 not found. Run the app or seed.py first.")
    sys.exit(1)

con = sqlite3.connect(str(db_path))
cur = con.cursor()

# include tables and indexes
rows = cur.execute("""
    SELECT type, name, sql
    FROM sqlite_master
    WHERE sql IS NOT NULL
      AND name NOT LIKE 'sqlite_%'
      AND type IN ('table','index')
    ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, name
""").fetchall()

with open("DB_SCHEMA.sql", "w", encoding="utf-8") as f:
    for t, name, sql in rows:
        f.write(sql.strip() + ";\n\n")

con.close()
print("Wrote DB_SCHEMA.sql")
