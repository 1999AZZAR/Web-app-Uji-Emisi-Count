"""
WSGI config for Uji Emisi Count application.

This module contains the WSGI application used by the application server.
"""
import os
from app_init import app, create_app

# Set the application root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Set the configuration file path
config_path = os.path.join(BASE_DIR, 'config.py')

# Initialize the application
application = app

if __name__ == "__main__":
    # Run any initialization code
    from main import init_db
    init_db()
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)
