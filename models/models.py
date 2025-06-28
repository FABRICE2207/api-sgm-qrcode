from datetime import datetime
from db import db
import json
from utils.auth import hash_password

def create_admin_user():
    username = "admin"
    email = "admin@example.com"
    password = "admin123"

    # Vérifie si l’utilisateur existe déjà
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        print("L'utilisateur admin existe déjà.")
        return

    # Création d’un nouvel utilisateur avec mot de passe hashé
    hashed_password = hash_password(password)
    new_user = User(username=username, email=email, password=hashed_password)
    
    db.session.add(new_user)
    db.session.commit()
    print("Utilisateur admin créé avec succès.")


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    # telephone = db.Column(db.String(10), nullable=False)
    # roles = db.Column(db.String(50), nullable=False)
    # photos = db.Column(db.String(30), nullable=False)
    # departement = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Restaurants(db.Model):
    __tablename__ = 'restaurant'
    id = db.Column(db.Integer, primary_key=True)
    type_entreprise = db.Column(db.String(120), nullable=False)
    nom = db.Column(db.String(120), unique=True, nullable=False)
    adresse = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    telephone = db.Column(db.String(10), nullable=False)
    qr_code_url = db.Column(db.String(255), nullable=False)
    qr_code_img = db.Column(db.String(120), nullable=False)
    hash_url = db.Column(db.String(128), unique=True, nullable=False)
    # roles = db.Column(db.String(50), nullable=False)
    logo = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    plats = db.relationship('Plats', backref='restaurant', lazy=True)
    abonnements = db.relationship('Abonnements', backref='restaurant', lazy=True)
    categories = db.relationship('Categories', backref='restaurant', lazy=True)
    scans = db.relationship('Scans', backref='restaurant', lazy=True)
    paiements = db.relationship('Paiements', backref='restaurant', lazy=True)

class Abonnements(db.Model):
    __tablename__ = 'abonnements'
    id = db.Column(db.Integer, primary_key=True)
    type_abonnement = db.Column(db.String(15), nullable=False)
    montant = db.Column(db.Integer, nullable=False)
    dateDebut = db.Column(db.DateTime, nullable=False)
    dateFin = db.Column(db.DateTime, nullable=False)
    statut = db.Column(db.String(15), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    paiements = db.relationship('Paiements', backref='abonnements', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Plats(db.Model):
    __tablename__ = 'plats'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(120), nullable=False)
    prix = db.Column(db.Integer, nullable=False)
    date_jour = db.Column(db.DateTime, nullable=False)
    statut = db.Column(db.String(15), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    categories_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Categories(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    plats = db.relationship('Plats', backref='categories', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Scans(db.Model):
    __tablename__ = 'scans'
    id = db.Column(db.Integer, primary_key=True)
    restaurant_hash = db.Column(db.String(255), nullable=False)
    user_agent = db.Column(db.Text, nullable=False)
    
    # Device Info
    device_brand = db.Column(db.String(100), nullable=False)
    device_model = db.Column(db.String(100), nullable=False)
    device_identifier = db.Column(
        db.String(255), 
        nullable=False,
        unique=True,
        comment="Format: brand:model:restaurant_id:YYYY-MM-DD"
    )
    
    # OS Info
    os_family = db.Column(db.String(50), nullable=False)
    os_version = db.Column(db.String(50), nullable=False)
    
    # Browser Info
    browser_family = db.Column(db.String(50), nullable=False)
    browser_version = db.Column(db.String(50))
    
    # Scan Metadata
    scanned_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    last_scan_at = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    number_scan_device = db.Column(db.Integer, nullable=False, default=1)
    
    # Relations
    restaurant_id = db.Column(
        db.Integer, 
        db.ForeignKey('restaurant.id', ondelete='CASCADE'),
        nullable=False
    )
    device_identifier = db.Column(db.String(255), unique=True, nullable=False)

class Paiements(db.Model):
    __tablename__ = 'paiements'
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(250), nullable=False, unique=True)
    amount = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(5), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    channels = db.Column(db.String(15), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="En attente")
    mode_paiement = db.Column(db.String(50), default="CinetPay")
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    abonnement_id = db.Column(db.Integer, db.ForeignKey('abonnements.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    