import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = "dev-secret-key-change-me"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "instance", "finance.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = True
    WTF_CSRF_ENABLED = False  # CSRF protection intentionally not used in this project

    # Folders the app creates on startup (see app.py)
    UPLOAD_FOLDER = os.path.join(basedir, "uploads")
    EXPORT_FOLDER = os.path.join(basedir, "exports")
    MODEL_FOLDER = os.path.join(basedir, "trained_models")

    # Mail (Flask-Mail) - fill in once email features (OTP, password reset) are built
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME='patel37983672@gmail.com'
    MAIL_PASSWORD='jiuzhlgkoihzzflg'
    MAIL_DEFAULT_SENDER='patel37983672@gmail.com'
