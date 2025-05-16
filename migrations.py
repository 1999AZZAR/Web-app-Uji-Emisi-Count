import os
from flask_migrate import Migrate, MigrateCommand, init, migrate, upgrade
from app_init import app, create_app
from extensions import db
from models import Kendaraan, HasilUji, User, Config

# Initialize migration
migrate = Migrate(app, db)

def init_migrations():
    # Create migrations directory if it doesn't exist
    if not os.path.exists('migrations'):
        print("Initializing migrations directory...")
        with app.app_context():
            init()
            
def create_migration(message=None):
    # Create a migration script
    with app.app_context():
        if message:
            migrate(message=message)
        else:
            migrate()
            
def apply_migrations():
    # Apply all migrations
    with app.app_context():
        upgrade()
        
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'init':
            init_migrations()
        elif command == 'migrate':
            message = sys.argv[2] if len(sys.argv) > 2 else None
            create_migration(message)
        elif command == 'upgrade':
            apply_migrations()
        else:
            print("Unknown command. Use 'init', 'migrate', or 'upgrade'.")
    else:
        print("Please provide a command: 'init', 'migrate', or 'upgrade'.") 