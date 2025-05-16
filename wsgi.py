"""
WSGI config for Uji Emisi Count application.

This module contains the WSGI application used by the application server.
"""
import os
from app_init import create_app

# Create application instance
app = create_app()

if __name__ == "__main__":
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)
