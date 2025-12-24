from routes.database import db, User
from app import app

with app.app_context():
    # Method 1: Delete by username
    username_to_delete = input("Enter username to delete (or 'all' to delete all users): ")
    
    if username_to_delete.lower() == 'all':
        # Delete all users
        count = User.query.delete()
        db.session.commit()
        print(f"Deleted {count} user(s)")
    else:
        # Delete specific user
        user = User.query.filter_by(username=username_to_delete).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            print(f"Deleted user: {user.username}")
        else:
            print(f"User '{username_to_delete}' not found")
    
    # Show remaining users
    remaining = User.query.all()
    print(f"\nRemaining users: {len(remaining)}")
    for u in remaining:
        print(f"  - {u.username}")
