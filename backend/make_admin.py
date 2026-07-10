from database.db import SessionLocal
from models.user import User

db = SessionLocal()

email = input("Enter your email: ")

user = (
    db.query(User)
    .filter(User.email == email)
    .first()
)

if user:
    user.role = "admin"
    db.commit()

    print("User is now admin.")

else:
    print("User not found.")

db.close()