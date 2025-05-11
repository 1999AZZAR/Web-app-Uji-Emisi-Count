import os
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from sqlalchemy import inspect
import logging
from extensions import db
from models import Config, User

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Set a secret key for session management
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key in production
    
    # Configure database to use instance directory
    db_path = os.path.join(app.instance_path, 'emisi.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database and Flask-Login
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'routes.login'
    
    # User loader callback
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app

app = create_app()
