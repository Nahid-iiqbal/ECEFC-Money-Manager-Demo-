from routes.database import db, User
from app import app

with app.app_context():
    users = User.query.all()
    
    if users:
        print(f"Found {len(users)} user(s) in database:")
        for user in users:
            print(f"  ID: {user.id}, Username: {user.username}, Created: {user.created_at}")
    else:
        print("No users found in database.")
