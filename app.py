from flask import Flask
from flask_cors import CORS
from sqlalchemy import inspect
import logging
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# db provided by extensions

from routes import routes as routes_blueprint


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emisi.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from models import Kendaraan, HasilUji
        db.create_all()
        # Ensure nama_instansi column exists for existing DB
        inspector_obj = inspect(db.engine)
        cols = [col['name'] for col in inspector_obj.get_columns('kendaraan')]
        if 'nama_instansi' not in cols:
            db.engine.execute('ALTER TABLE kendaraan ADD COLUMN nama_instansi VARCHAR(100)')

    app.register_blueprint(routes_blueprint)
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
