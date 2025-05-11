import os
from app_init import app

# Set the application root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Set the configuration file path
config_path = os.path.join(BASE_DIR, 'config.py')

# Initialize the application
application = app

# If you need to run any initialization code, you can do it here
# For example, database initialization
if __name__ == '__main__':
    from main import init_db
    init_db()
    app.run()
