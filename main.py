import os
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from sqlalchemy import inspect
import logging
from extensions import db
from models import Kendaraan, HasilUji, User, Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# db provided by extensions

from routes import routes as routes_blueprint


def check_database_health():
    """Check if database is healthy and recreate if needed."""
    try:
        # Check if all required tables exist
        inspector = inspect(db.engine)
        required_tables = ['kendaraan', 'users', 'config', 'hasil_uji']
        existing_tables = inspector.get_table_names()
        
        if not all(table in existing_tables for table in required_tables):
            logger.warning("Database schema is incomplete. Recreating database...")
            return False
            
        # Check if config table has initial data
        config = Config.query.first()
        if not config:
            logger.warning("Config table is empty. Recreating database...")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False

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
    
    # Initialize database with default data
    with app.app_context():
        # Check database health and recreate if needed
        if not check_database_health():
            logger.info("Recreating database...")
            db.drop_all()
            db.create_all()
            
            # Create default configuration if needed
            config = Config.query.first()
            if not config:
                config = Config(
                    co_max=0.5,
                    co2_min=8.0,
                    hc_max=200.0,
                    o2_min=2.0,
                    lambda_min=0.95,
                    lambda_max=1.05
                )
                db.session.add(config)
                db.session.commit()
                
            # Create all users in one transaction
            base_password = 'user123'
            
            # Create admin user
            admin_user = User(username='admin', email='admin@example.com', role='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            
            # Create 25 general users
            for i in range(1, 26):
                username = f'user{i}'
                email = f'user{i}@example.com'
                user = User(username=username, email=email, role='general')
                user.set_password(base_password)
                db.session.add(user)
            
            db.session.commit()
            logger.info("Database recreated successfully")
        
        # Maintain users if database exists
        else:
            # Check and create admin user if needed
            admin_user = User.query.filter_by(role='admin').first()
            if not admin_user:
                admin_user = User(username='admin', email='admin@example.com', role='admin')
                admin_user.set_password('admin123')
                db.session.add(admin_user)
            
            # Check and create missing general users
            general_users = User.query.filter_by(role='general').all()
            if len(general_users) < 25:
                base_password = 'user123'
                existing_usernames = {user.username for user in general_users}
                
                # Create missing users starting from the next available number
                for i in range(1, 26):
                    username = f'user{i}'
                    if username not in existing_usernames:
                        email = f'user{i}@example.com'
                        user = User(username=username, email=email, role='general')
                        user.set_password(base_password)
                        db.session.add(user)
                
            db.session.commit()
        
        # Commit all changes
        db.session.commit()
        logger.info('Database initialized with default data')
        
        # Ensure nama_instansi column exists for existing DB
        inspector_obj = inspect(db.engine)
        cols = [col['name'] for col in inspector_obj.get_columns('kendaraan')]
        if 'nama_instansi' not in cols:
            db.engine.execute('ALTER TABLE kendaraan ADD COLUMN nama_instansi VARCHAR(100)')
        inspector_obj = inspect(db.engine)
        cols = [col['name'] for col in inspector_obj.get_columns('kendaraan')]
        if 'nama_instansi' not in cols:
            db.engine.execute('ALTER TABLE kendaraan ADD COLUMN nama_instansi VARCHAR(100)')

    app.register_blueprint(routes_blueprint)
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
