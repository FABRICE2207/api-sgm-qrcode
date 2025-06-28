from flask import Flask, jsonify
from config import Config
from db import db
from utils.auth import bcrypt, hash_password  # <-- Assure-toi que c'est bien importé
# from utils.auth import bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS  # <-- Ajout
from flask_migrate import Migrate
from routes.user_routes import api as user_api
from routes.categorie_routes import api as categories_api
from routes.restaurant_routes import api as restaurants_api
from routes.plat_routes import api as plats_api
from routes.abonnement_routes import api as abonnements_api
from routes.paiement_routes import api as paiements_api
# from routes.type_conges_routes import api as type_conges_api
from routes.tokens import tokens_bp as tokens
from routes.auth_routes import auth_api
import os
from models import create_admin_user
from flask_migrate import upgrade

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    # Configuration de base
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static','uploads')
    app.config['STATIC_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    app.config['JWT_DECODE_ALIASES'] = {'sub': None}  # Désactive la vérification du sujet
    JWTManager(app)
    db.init_app(app)
    migrate = Migrate(app, db)  # <-- Ajoute cette ligne
    bcrypt.init_app(app)

    # Autorise toutes les origines et tous les headers/methods pour le dev
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Enregistre le blueprint des routes utilisateur
    app.register_blueprint(user_api, url_prefix='/api/users')
    # Enregistre le blueprint des routes de categories
    app.register_blueprint(categories_api, url_prefix='/api/categories')

    # Enregistre le blueprint des routes de restaurants
    app.register_blueprint(restaurants_api, url_prefix='/api/restaurants')
    # Enregistre le blueprint des routes de plats
    app.register_blueprint(plats_api, url_prefix='/api/plats')
    # Enregistre le blueprint des routes de plats
    app.register_blueprint(abonnements_api, url_prefix='/api/abonnements')

    # Ajoute cette ligne pour le blueprint des tokens
    app.register_blueprint(tokens, url_prefix='/api')
    # Enregistre le blueprint des routes d'authentification
    app.register_blueprint(auth_api, url_prefix='/api/login')
    # Enregistre le blueprint des routes de paiement
    app.register_blueprint(paiements_api, url_prefix='/api/paiements')
    
    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():     # ✅ entre dans le contexte Flask
        upgrade()               # (optionnel) applique les migrations
        create_admin_user()     # 👈 appelle ta fonction ici
    app.run(debug=True)