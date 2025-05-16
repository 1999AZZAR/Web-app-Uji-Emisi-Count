from app_init import app
from models import User
from flask import Flask

def test_users():
    with app.app_context():
        users = User.query.all()
        if users:
            print(f"Found {len(users)} users:")
            for user in users:
                print(f"  - {user.username} (ID: {user.id}, Admin: {user.is_admin()})")
        else:
            print("No users found in database")

if __name__ == '__main__':
    test_users() 