import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

def get_db_url():
    # Fix Render's postgres:// -> postgresql://
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    if not db_url:
        db_url = 'sqlite:///' + os.path.join(basedir, 'splitwise.db')
    return db_url

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production-please')
    SQLALCHEMY_DATABASE_URI = get_db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False  # Disable CSRF in dev for easier testing if desired, or leave it True. We'll leave it True to match prod.
    WTF_CSRF_ENABLED = True

class ProductionConfig(Config):
    DEBUG = False
    # Ensure production uses strong secret key
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # We can add production-specific init here

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
