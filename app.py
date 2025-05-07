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


def create_app():
    app = Flask(__name__)
    CORS(app)
    # Set a secret key for session management
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key in production
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/himawan/Documents/Learning/Web app Uji Emisi Count/emisi.db'
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
        # Drop all tables first to ensure clean start
        db.drop_all()
        db.create_all()
        
        # Create default admin user
        admin_user = User(username='admin', email='admin@example.com', role='admin')
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        # Create 25 general users
        base_password = 'user123'
        for i in range(1, 26):
            username = f'user{i:02d}'
            email = f'user{i:02d}@example.com'
            user = User(username=username, email=email, role='general')
            user.set_password(base_password)
            db.session.add(user)
        
        # Create default configuration
        default_config = Config(
            co_max=5.0,
            co2_min=15.0,
            hc_max=200.0,
            o2_min=18.0,
            lambda_min=0.95,
            lambda_max=1.05
        )
        db.session.add(default_config)
        
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
