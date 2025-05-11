import os
from main import app

# Set the application root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Set the configuration file path
config_path = os.path.join(BASE_DIR, 'config.py')

# Initialize the application
application = app

if __name__ == '__main__':
    application.run()
