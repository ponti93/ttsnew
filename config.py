# Database configuration
DATABASE_URL = 'postgresql://postgres:incorrect@localhost/pronunciation_app'
SECRET_KEY = 'dev-pronunciation-app-secret-key-2025'

# Flask configuration
FLASK_APP = 'webapp.py'
FLASK_ENV = 'development'

# SQLAlchemy configuration
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Security
WTF_CSRF_SECRET_KEY = 'wtf-csrf-secret-key-change-in-production'