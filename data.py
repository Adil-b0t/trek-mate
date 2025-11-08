# Fetch all users
from app import app, db, User

with app.app_context():
    users = User.query.all()
    for u in users:
        print(f"ID: {u.id}, Name: {u.name}, Email: {u.email}, Role: {u.role}, Created: {u.created_at}")
        