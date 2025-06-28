from datetime import timedelta
import os
import socket

class Config:
    SECRET_KEY = "votre_cle_secrete"
    JWT_SECRET_KEY = "votre_cle_jwt_ultra_secrete"
    DB_URL = os.environ.get('DB_URL')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_NAME = os.environ.get('DB_NAME')
    DATABASE_URL = 'postgresql+psycopg2://postgres:admin@127.0.0.1/db_sgr'.format(user
        =DB_USER, pw=DB_PASSWORD, url=DB_URL, db=DB_NAME)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # <-- Expiration à 1h
    # Configuration des fichiers uploadés
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    UPLOAD_FOLDER = 'static/plats'
    JWT_VERIFY_SUB = False
    HOST_ADDRESS = socket.gethostbyname(socket.gethostname())+':5000'
    URL_FRONT = socket.gethostbyname(socket.gethostname())+':5173'

    # Créer le dossier s'il n'existe pas
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)