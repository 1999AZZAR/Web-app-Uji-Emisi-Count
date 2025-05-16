import os
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from sqlalchemy import inspect
import logging
from extensions import db, csrf
from models import Config, User
from datetime import timedelta

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Set a secret key for session management
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')  # Change this to a secure secret key in production
    
    # Set secure session configuration
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Session timeout
    
    # Ensure the instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Configure database to use instance directory
    db_path = os.path.join(app.instance_path, 'emisi.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize CSRF protection
    csrf.init_app(app)
    
    # Initialize database and Flask-Login
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # User loader callback
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    # Register security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    return app

app = create_app()
