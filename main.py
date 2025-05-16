import os
import logging
from sqlalchemy import inspect, text
from app_init import app, create_app
from extensions import db
from models import Kendaraan, HasilUji, User, Config
from flask import redirect, url_for

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import blueprints
from blueprints.auth import auth
from blueprints.vehicles import vehicles
from blueprints.tests import tests
from blueprints.reports import reports
from blueprints.api import api

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(vehicles)
app.register_blueprint(tests)
app.register_blueprint(reports)
app.register_blueprint(api)

# Default route redirects to vehicles dashboard
@app.route('/')
def index():
    return redirect(url_for('vehicles.dashboard'))

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

def init_db():
    with app.app_context():
        # Create all tables if they don't exist
        try:
            db.create_all()
        except Exception as e:
            logger.error(f"Error in db.create_all(): {str(e)}")
            # If there's an error, we'll try to handle schema migrations manually
            pass

        # Ensure schema is up to date
        try:
            update_schema()
        except Exception as e:
            logger.error(f"Error in update_schema(): {str(e)}")

        # Ensure we have a default Config if none exists
        try:
            config_exists = db.session.query(db.exists().where(Config.id == 1)).scalar()
            if not config_exists:
                default_config = Config()
                db.session.add(default_config)
                db.session.commit()
        except Exception as e:
            logger.error(f"Error checking or creating config: {str(e)}")
            db.session.rollback()

        # Create admin user if it doesn't exist
        try:
            admin_exists = db.session.query(db.exists().where(User.username == 'admin')).scalar()
            if not admin_exists:
                admin = User(username='admin', email='admin@example.com', role='admin')
                admin.set_password('admin')
                db.session.add(admin)
                db.session.commit()
        except Exception as e:
            logger.error(f"Error checking or creating admin user: {str(e)}")
            db.session.rollback()
    
    return app

def update_schema():
    """Update database schema with any new columns or tables"""
    with app.app_context():
        # Get existing tables
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        # Add audit_logs table if missing
        if 'audit_logs' not in existing_tables:
            logger.info("Creating audit_logs table...")
            db.session.execute(text('''
                CREATE TABLE audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER,
                    action VARCHAR(50) NOT NULL,
                    entity_type VARCHAR(50) NOT NULL,
                    entity_id INTEGER,
                    details TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            '''))
            db.session.commit()
            
        # Update schema for each table that might need columns added
        
        # Only modify existing tables
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        # Kendaraan table updates
        if 'kendaraan' in existing_tables:
            kendaraan_cols = [column['name'] for column in inspector.get_columns('kendaraan')]
            if 'created_at' not in kendaraan_cols:
                logger.info("Adding created_at to kendaraan table")
                db.session.execute(text('ALTER TABLE kendaraan ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP'))
            if 'updated_at' not in kendaraan_cols:
                logger.info("Adding updated_at to kendaraan table")
                db.session.execute(text('ALTER TABLE kendaraan ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP'))
        
        # User table updates
        if 'users' in existing_tables:
            user_cols = [column['name'] for column in inspector.get_columns('users')]
            if 'email' not in user_cols:
                logger.info("Adding email to users table")
                db.session.execute(text('ALTER TABLE users ADD COLUMN email VARCHAR(120) DEFAULT ""'))
            if 'active' not in user_cols:
                logger.info("Adding active to users table")
                db.session.execute(text('ALTER TABLE users ADD COLUMN active BOOLEAN DEFAULT 1'))
            if 'created_at' not in user_cols:
                logger.info("Adding created_at to users table")
                db.session.execute(text('ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP'))
            if 'updated_at' not in user_cols:
                logger.info("Adding updated_at to users table")
                db.session.execute(text('ALTER TABLE users ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP'))
            if 'last_login' not in user_cols:
                logger.info("Adding last_login to users table")
                db.session.execute(text('ALTER TABLE users ADD COLUMN last_login DATETIME'))
        
        # HasilUji table updates
        if 'hasil_uji' in existing_tables:
            hasiluji_cols = [column['name'] for column in inspector.get_columns('hasil_uji')]
            if 'created_at' not in hasiluji_cols:
                logger.info("Adding created_at to hasil_uji table")
                db.session.execute(text('ALTER TABLE hasil_uji ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP'))
            if 'updated_at' not in hasiluji_cols:
                logger.info("Adding updated_at to hasil_uji table")
                db.session.execute(text('ALTER TABLE hasil_uji ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP'))
            
        # Config table updates
        if 'config' in existing_tables:
            config_cols = [column['name'] for column in inspector.get_columns('config')]
            if 'created_at' not in config_cols:
                logger.info("Adding created_at to config table")
                db.session.execute(text('ALTER TABLE config ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP'))
            if 'updated_at' not in config_cols:
                logger.info("Adding updated_at to config table")
                db.session.execute(text('ALTER TABLE config ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP'))
            
        # Commit all schema changes
        db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5005)
