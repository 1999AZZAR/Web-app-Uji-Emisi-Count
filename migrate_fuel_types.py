from app_init import create_app
from models import db, Config
from sqlalchemy import text

def migrate_fuel_types():
    """Convert 'petrol' to 'bensin' and 'diesel' to 'solar' in the database."""
    app = create_app()
    with app.app_context():
        # Update fuel types in the kendaraan table
        print("Converting 'petrol' to 'bensin' and 'diesel' to 'solar' in the database...")
        db.session.execute(text("UPDATE kendaraan SET fuel_type = 'bensin' WHERE fuel_type = 'petrol'"))
        db.session.execute(text("UPDATE kendaraan SET fuel_type = 'solar' WHERE fuel_type = 'diesel'"))
        
        # Commit all changes
        db.session.commit()
        print("Migration successful - fuel types updated to 'bensin' and 'solar'")

if __name__ == "__main__":
    migrate_fuel_types() 