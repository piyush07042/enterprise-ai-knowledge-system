from sqlalchemy import text
from database.db import engine

with engine.connect() as conn:
    try:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        )
        conn.commit()
        print("✅ role column added successfully.")
    except Exception as e:
        print("Error:", e)