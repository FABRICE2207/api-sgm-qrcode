from flask import Blueprint, request, jsonify, abort, current_app, send_from_directory, send_file
from models import db, Plats, Restaurants, Abonnements, Categories, Scans
from utils.qr_utils import generate_qr_code
from utils.auth import hash_password, check_password
from werkzeug.utils import secure_filename
import os
import hashlib
from flask_jwt_extended  import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
from sqlalchemy import or_
from sqlalchemy import func
import locale
from user_agents import parse # type: ignore
import calendar
import uuid
import io
import qrcode


api = Blueprint("restaurant_api", __name__)

#Configuration pour le téléchargement de photos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/logos'


def allowed_file(filename):
    return '.' in filename and \
      filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@api.route('/menu/<string:hash_url>/date/aujourd_hui', methods=['GET'])
def menu_par_date(hash_url):
    try:
        date_actuelle = date.today()
        
        results = (db.session.query(Plats, Categories)
                    .join(Restaurants, Plats.restaurant_id == Restaurants.id)
                    .join(Abonnements, Restaurants.id == Abonnements.restaurant_id)
                    .join(Categories, Plats.categories_id == Categories.id)
                    .filter(
                        or_(Abonnements.statut == "Gratuit", Abonnements.statut == "Actif"),
                        Plats.statut == "Disponible",
                        Abonnements.dateDebut <= date_actuelle,
                        Abonnements.dateFin >= date_actuelle,
                        Restaurants.hash_url == hash_url,
                        Plats.date_jour == date_actuelle
                    )
                    .order_by(Categories.nom, Plats.nom)
                    .all())
        
        if not results:
            return jsonify({
                "message": "Aucun menu disponible",
                "date": date_actuelle.strftime("%d-%m-%Y")
            }), 200
        
        # Get restaurant info from first result
        restaurant = {
            "nom": results[0][0].restaurant.nom,
            "logo": results[0][0].restaurant.logo,
            "adresse": results[0][0].restaurant.adresse
        }

        # Group by category
        menu = {}
        for plat, categories in results:
            if categories.nom not in menu:
                menu[categories.nom] = []
            
            menu[categories.nom].append({
                "id": plat.id,
                "nom": plat.nom,
                "description": plat.description,
                "prix": float(plat.prix),
                "image": plat.image,
                "statut": plat.statut,
                "date_jour": plat.date_jour.strftime("%d-%m-%Y"),
                "categories": {
                    "id": categories.id,
                    "nom": categories.nom
                }
            })

        return jsonify({
            "date": date_actuelle.strftime("%d-%m-%Y"),
            "restaurant": restaurant,
            "menu": menu
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Afficher les informations du restaurant by hash
@api.route('/restaurant_info/<string:hash_url>', methods=['GET'])
def get_restaurant_info(hash_url):
    try:
        # Recherche du restaurant par hash_url
        restaurant = Restaurants.query.filter_by(hash_url=hash_url).first()
        
        if not restaurant:
            return jsonify({
                'success': False,
                'message': 'Restaurant non trouvé'
            }), 404
        
        # Envoie de la réponse
        return jsonify({
            'id': restaurant.id,
                'nom': restaurant.nom,
                'hash_url': restaurant.hash_url,
                'logo': restaurant.logo,
                'adresse': restaurant.adresse,
                'telephone': restaurant.telephone,
                'email': restaurant.email,
                'created_at': restaurant.created_at.isoformat() if restaurant.created_at else None,
                'updated_at': restaurant.updated_at.isoformat() if restaurant.updated_at else None,
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur serveur: {str(e)}'
        }), 500

# Affiche l'url du restaurant
@api.route('/init_qrcode', methods=['GET'])
def qrcode_init():
     qr_url, img_path = generate_qr_code(2)
     return jsonify({
         "text": qr_url
     })

# Créer le compte du restaurant
# @api.route('/create', methods=['POST'])
# def create_restaurant():
#     if request.method == 'POST':
#         # Récupération des données du formulaire
#         nom = request.form['nom'] 
#         adresse = request.form['adresse'] 
#         email = request.form['email']
#         password = request.form['password']
#         telephone = request.form['telephone']

        
#         # Validation des champs obligatoires
#         if not nom or not email or not password:
#             return jsonify({'msg': "Tous les champs sont obligatoires"}), 400
        
#         # Vérification des doublons
#         if Restaurants.query.filter_by(email=email).first():
#             return jsonify({'msg': "L'email est déjà utilisé"}), 400
#         if Restaurants.query.filter_by(nom=nom).first():
#             return jsonify({'msg': "Le nom du restaurant est déjà utilisé"}), 400

#         # Génération du hash unique
#         unique_str = f"{email}-{uuid.uuid4()}"
#         hash_url = hashlib.sha256(unique_str.encode()).hexdigest()

#         # Création du restaurant sans logo
#         new_restaurant = Restaurants(
#             nom=nom,
#             adresse=adresse,
#             email=email,
#             password=hash_password(password),
#             telephone=telephone,
#             qr_code_url='',      # temporairement vide
#             qr_code_img='',      # temporairement vide
#             logo='',             # champ logo vide
#             hash_url=hash_url,
#         )
#         db.session.add(new_restaurant)
#         db.session.commit()

#         # Génération du QR code maintenant que l'ID est connu
#         qr_url, img_path = generate_qr_code(new_restaurant.id)

#         # Mise à jour du restaurant avec le QR code
#         new_restaurant.qr_code_url = qr_url
#         new_restaurant.qr_code_img = img_path
#         db.session.commit()

#         return jsonify({
#             'message': 'Restaurant créé avec succès',
#             'restaurant': {
#                 'id': new_restaurant.id,
#                 'nom': new_restaurant.nom,
#                 'statut': new_restaurant.statut,
#                 'hash_url': new_restaurant.hash_url,
#                 'qr_code_url': new_restaurant.qr_code_url,
#                 'qr_code_img': new_restaurant.qr_code_img
#             }
#         }), 201

@api.route('/create', methods=['POST'])
def create_restaurant():
    if request.method == 'POST':
        # Récupération des données du formulaire
        try: 
            type_entreprise = request.form['type_entreprise'] 
            nom = request.form['nom'] 
            adresse = request.form['adresse'] 
            email = request.form['email']
            password = request.form['password']
            telephone = request.form['telephone']

            # Validation des champs obligatoires
            if not nom or not email or not password or not type_entreprise:
                return jsonify({'msg': "Tous les champs sont obligatoires"}), 400
            
            # Vérification des doublons
            if Restaurants.query.filter_by(email=email).first():
                return jsonify({'msg': "L'email est déjà utilisé"}), 400
            if Restaurants.query.filter_by(nom=nom).first():
                return jsonify({'msg': "Le nom du restaurant est déjà utilisé"}), 400

            # Génération du hash unique
            unique_str = f"{email}-{uuid.uuid4()}"
            hash_url = hashlib.sha256(unique_str.encode()).hexdigest()

            # Création du restaurant sans logo
            new_restaurant = Restaurants(
                type_entreprise=type_entreprise,
                nom=nom,
                adresse=adresse,
                email=email,
                password=hash_password(password),
                telephone=telephone,
                qr_code_url='',      # temporairement vide
                qr_code_img='',      # temporairement vide
                logo='',             # champ logo vide
                hash_url=hash_url,
                # date_creation=datetime.utcnow()  # Ajout de la date de création
            )
            db.session.add(new_restaurant)
            db.session.commit()

            # Création de l'abonnement automatique du restaurant gratuit pour 3 jours
            date_debut = date.today()
            date_fin = date_debut + timedelta(days=3)  # Période d'essai de 3 jours
            
            new_abonnement = Abonnements(
                restaurant_id=new_restaurant.id,
                type_abonnement='Démo',
                statut='Gratuit',
                dateDebut=date_debut,
                dateFin=date_fin,
                montant=0
            )
            db.session.add(new_abonnement)
            db.session.commit()

            # Génération du QR code maintenant que l'ID est connu
            qr_url, img_path = generate_qr_code(new_restaurant.id)

            # Mise à jour du restaurant avec le QR code
            new_restaurant.qr_code_url = qr_url
            new_restaurant.qr_code_img = img_path
            db.session.commit()

            return jsonify({
                'message': 'Restaurant créé avec succès - Essai gratuit de 3 jours activé',
                'restaurant': {
                    'id': new_restaurant.id,
                    'type_entreprise': new_restaurant.type_entreprise,
                    'nom': new_restaurant.nom,
                    'email': new_restaurant.email,
                    'hash_url': new_restaurant.hash_url,
                    'qr_code_url': new_restaurant.qr_code_url,
                    'date_creation': new_restaurant.created_at.isoformat(),
                    'abonnement': {
                        'type': new_abonnement.type_abonnement,
                        'statut': new_abonnement.statut,
                        'date_fin': new_abonnement.dateFin.isoformat()
                    }
                }
            }), 201


        except Exception as e:
            return jsonify({'error': str(e)}), 500


# Affiche le logos et images des plats
@api.route('/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# Ce routeur est généralement déjà géré automatiquement :
@api.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(current_app.config['STATIC_FOLDER'], filename)

# Liste de tous les restaurants
@api.route('/liste_restaurants', methods=['GET'])
def get_all_restaurants():
    restaurants = Restaurants.query.all()

    # Compter le nombre total des restaurant
    total_restaurant = len(restaurants)
    return jsonify([
            {
                'id': restaurant.id,
                'type_entreprise': restaurant.type_entreprise,
                'nom': restaurant.nom,
                'adresse': restaurant.adresse,
                'email': restaurant.email,
                'telephone': restaurant.telephone,
                'logo': restaurant.logo,
                'qr_code_url': restaurant.qr_code_url,
                'qr_code_img': restaurant.qr_code_img,
                'created_at': restaurant.created_at.isoformat() if restaurant.created_at else None,
                'updated_at': restaurant.updated_at.isoformat() if restaurant.updated_at else None,
            } 
            for restaurant in restaurants
        ]), 200

# Liste des entreprises en fonction des types
@api.route('/liste_entreprise/<type_entreprise>', methods=['GET'])
def entreprise_type(type_entreprise):
    entreprises = Restaurants.query.filter(
        Restaurants.type_entreprise == type_entreprise
    ).all()

    return jsonify([
        {
            'id': e.id,
            'type_entreprise': e.type_entreprise,
            'nom': e.nom,
            'adresse': e.adresse,
            'email': e.email,
            'telephone': e.telephone,
            'logo': e.logo,
            'qr_code_url': e.qr_code_url,
            'qr_code_img': e.qr_code_img,
            'created_at': e.created_at.isoformat() if e.created_at else None,
            'updated_at': e.updated_at.isoformat() if e.updated_at else None,
        } 
        for e in entreprises
    ]), 200


# Modifier un restaurant  partir de son ID
@api.route('/update_restaurant/<int:id>', methods=['PUT'])
def restaurant_update(id):
    restaurant = Restaurants.query.get(id)
    if not restaurant:
        return jsonify({'message': 'Restaurant non trouvé'}), 404

    # --- Gestion du logo (si envoyé) ---
    logo = request.files.get('logo')
    if logo:
        # Supprimer l'ancien fichier si existant
        if restaurant.logo:
            try:
                os.unlink(os.path.join(current_app.config['UPLOAD_FOLDER'], restaurant.logo))
            except FileNotFoundError:
                pass  # Aucun fichier à supprimer

        # Sauvegarder le nouveau fichier
        filename = secure_filename(logo.filename)
        logo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        restaurant.logo = filename

    # --- Mise à jour des champs texte ---
    restaurant.type_entreprise = request.form.get('type_entreprise', restaurant.type_entreprise)
    restaurant.nom = request.form.get('nom', restaurant.nom)
    restaurant.email = request.form.get('email', restaurant.email)
    restaurant.adresse = request.form.get('adresse', restaurant.adresse)
    restaurant.telephone = request.form.get('telephone', restaurant.telephone)

    # --- Vérification et hash du mot de passe ---
    password = request.form.get('password')
    password_confir = request.form.get('passwordConfir')

    if password or password_confir:
        if password != password_confir:
            return jsonify({'message': 'Les mots de passe ne correspondent pas'}), 400
        restaurant.password = hash_password(password)

    db.session.commit()

    return jsonify({
        'message': 'Restaurant mis à jour avec succès',
        'restaurant': {
            "type_entreprise": restaurant.type_entreprise,
            "nom": restaurant.nom,
            "adresse": restaurant.adresse,
            "email": restaurant.email,
            "telephone": restaurant.telephone,
            "logo": restaurant.logo
        }
    }), 200

# Afficher la liste des catégories d'un restaurant
@api.route('/liste_categorie_restaurant/<int:id>', methods=['GET'])
@jwt_required()
def liste_categorie_restaurant(id):
    plats = Plats.query.filter_by(hash_url=id).all()

    # Compter le nombre total de catégories
    total_plats = len(plats)
    
    return jsonify([
         {
                'id': plat.id,
                'image': plat.image,
                'nom': plat.nom,
                'nom': plat.nom,
                'description': plat.description,
                'prix': plat.prix,
                'restaurant': {
                  'nom': plat.restaurant.nom,
                  'type_entreprise': plat.restaurant.type_entreprise
                },
                'date_jour': plat.date_jour,
                'created_at': plat.created_at.isoformat() if plat.created_at else None,
                'updated_at': plat.updated_at.isoformat() if plat.updated_at else None,
                
                'total': total_plats
            } for plat in plats
        ]), 200

# obtenir un restaurant par son ID
@api.route('/get_restaurant/<int:id>', methods=['GET'])
def get_restaurant_by_id(id):
    restaurant = Restaurants.query.get(id)
    if not restaurant:
        return jsonify({'message': 'Restaurant non trouvé'}), 404
    return jsonify({
        'id': restaurant.id,
        'type_entreprise': restaurant.type_entreprise,
        'nom': restaurant.nom,
        'adresse': restaurant.adresse,
        'email': restaurant.email,
        'telephone': restaurant.telephone,
        'logo': restaurant.logo,
        'qr_code_url': restaurant.qr_code_url,
        'qr_code_img': restaurant.qr_code_img,
        'created_at': restaurant.created_at.isoformat(),
        'updated_at': restaurant.updated_at.isoformat()
    }), 200

# Compter le nombre total des restaurants
@api.route('/count_restaurants', methods=['GET'])
def get_count_restaurants():
    # Compter le nombre total des restaurant
    total_restaurant = len(Restaurants.query.filter_by(type_entreprise="Restaurant").all())
    total_marquis = len(Restaurants.query.filter_by(type_entreprise="Marquis").all())
    total_commerce = len(Restaurants.query.filter_by(type_entreprise="E-commerce").all())
    return jsonify(
        {
             'total_resto': total_restaurant,
            'total_marquis': total_marquis,
            'total_commerce': total_commerce
        }
     )

# Scanner pour connaitre le type de téléphone.
@api.route("/scan", methods=["POST"])
def enregistrer_scan():
    try:
        # 1. Log des données brutes reçues
        print("=== Données brutes reçues ===")
        raw_data = request.data.decode('utf-8')
        print(f"Raw data: {raw_data}")

        # 2. Parsing des données JSON
        data = request.get_json()
        if not data:
            print("Erreur: Aucune donnée JSON reçue")
            return jsonify({"error": "Données JSON requises"}), 400

        print("=== Données JSON parsées ===")
        print(f"Contenu JSON: {data}")

        # 3. Extraction et validation des champs
        restaurant_hash = data.get("restaurant_hash")
        user_agent_str = data.get("user_agent", "")
        scanned_at_str = data.get("scanned_at")

        print(f"Restaurant hash: {restaurant_hash}")
        print(f"User agent: {user_agent_str[:50]}...")  # Log partiel pour éviter la surcharge
        print(f"Scanned at: {scanned_at_str}")

        if not restaurant_hash:
            print("Erreur: restaurant_hash manquant")
            return jsonify({"error": "restaurant_hash manquant"}), 400

        # 4. Recherche du restaurant (avec verrou)
        restaurant = Restaurants.query.filter_by(hash_url=restaurant_hash).first()
        if not restaurant:
            print(f"Erreur: Restaurant non trouvé (hash: {restaurant_hash})")
            return jsonify({"error": "Restaurant introuvable"}), 404

        # 5. Traitement de la date
        try:
            scanned_at = datetime.fromisoformat(scanned_at_str) if scanned_at_str else datetime.utcnow()
        except ValueError as e:
            print(f"Erreur format date: {e}")
            scanned_at = datetime.utcnow()

        print(f"Date traitée: {scanned_at.isoformat()}")

        # 6. Analyse du User-Agent
        try:
            user_agent = parse(user_agent_str)
            device_brand = (user_agent.device.brand or "unknown").lower().strip()
            device_model = (user_agent.device.model or "unknown").lower().strip()

            print(f"Device analysé: {device_brand} {device_model}")
        except Exception as e:
            print(f"Erreur analyse User-Agent: {e}")
            device_brand = device_model = "unknown"

        # 7. Vérification des doublons (transaction sécurisée)
        with db.session.begin_nested():
            existing_scan = Scans.query.filter(
                Scans.restaurant_id == restaurant.id,
                func.lower(Scans.device_model) == device_model,
                func.lower(Scans.device_brand) == device_brand,
                func.date(Scans.scanned_at) == scanned_at.date()
            ).first()

            if existing_scan:
                existing_scan.number_scan_device += 1
                existing_scan.last_scan_at = scanned_at
                print(f"Scan existant mis à jour (ID: {existing_scan.id})")
                db.session.commit()
                return jsonify({
                    "status": "updated",
                    "scan_id": existing_scan.id,
                    "count": existing_scan.number_scan_device
                }), 200

            # 8. Création d'un nouveau scan
            new_scan = Scans(
                restaurant_hash=restaurant.hash_url,
                user_agent=user_agent_str,
                device_brand=device_brand,
                device_model=device_model,
                os_family=user_agent.os.family,  # ✅ corrigé
                os_version=user_agent.os.version_string,  # ✅ corrigé
                browser_family=user_agent.browser.family,  # ✅ corrigé
                scanned_at=scanned_at,
                last_scan_at=scanned_at,
                number_scan_device=1,
                restaurant_id=restaurant.id,
                device_identifier=f"{device_brand}:{device_model}:{restaurant.id}:{scanned_at.date()}"
            )


            db.session.add(new_scan)
            db.session.commit()
            print(f"Nouveau scan créé (ID: {new_scan.id})")

            return jsonify({
                "status": "created",
                "scan_id": new_scan.id,
                "count": 1
            }), 201

    except Exception as e:
        db.session.rollback()
        print(f"ERREUR CRITIQUE: {str(e)}")
        return jsonify({"error": "Erreur serveur", "details": str(e)}), 500



@api.route("/stats/scans/<int:restaurant_id>", methods=["GET"])
def statistiques_scans(restaurant_id):
    # 📅 Stats par jour
    daily_stats = db.session.query(
        func.date(Scans.scanned_at).label('date'),
        func.sum(Scans.number_scan_device).label('total_scans')
    ).filter(
        Scans.restaurant_id == restaurant_id
    ).group_by(
        func.date(Scans.scanned_at)
    ).order_by(
        func.date(Scans.scanned_at).desc()
    ).all()

    # 🗓️ Stats par mois
    monthly_stats = db.session.query(
        func.extract('year', Scans.scanned_at).label('year'),
        func.extract('month', Scans.scanned_at).label('month'),
        func.sum(Scans.number_scan_device).label('total_scans')
    ).filter(
        Scans.restaurant_id == restaurant_id
    ).group_by(
        func.extract('year', Scans.scanned_at),
        func.extract('month', Scans.scanned_at)
    ).order_by(
        func.extract('year', Scans.scanned_at).desc(),
        func.extract('month', Scans.scanned_at).desc()
    ).all()

    # 🌍 Locale pour le français
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except:
        locale.setlocale(locale.LC_TIME, "fr_FR")

    # 📦 Formatage des résultats
    daily_result = [
        {
            "date": stat.date.strftime("%A %d %B %Y").capitalize(),
            "total_scans": stat.total_scans
        }
        for stat in daily_stats
    ]

    monthly_result = [
        {
            "month": f"{calendar.month_name[int(stat.month)]} {int(stat.year)}".capitalize(),
            "total_scans": stat.total_scans
        }
        for stat in monthly_stats
    ]

    return jsonify({
        "restaurant_id": restaurant_id,
        "daily": daily_result,
        "monthly": monthly_result
    }), 200


    
@api.route("/scan/stats/<restaurant_hash>", methods=["GET"])
def stats_scans(restaurant_hash):
    today = date.today()
    total = Scans.query.filter(
        Scans.restaurant_hash == restaurant_hash,
        db.func.date(Scans.scanned_at) == today
    ).count()
    return jsonify({"restaurant_hash": restaurant_hash, "scans_today": total})

# Nombre de scans par OS en fonction de l'entreprise, date et mois
@api.route("/stats/scans_by_os", methods=["GET"])
def stats_scans_par_os():
    # 🌍 Activer la locale française pour le format des dates
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except:
        locale.setlocale(locale.LC_TIME, "fr_FR")

    # 📅 Regrouper par jour
    daily_stats = db.session.query(
        Restaurants.nom.label("restaurant"),
        Scans.os_family.label("os_family"),
        func.date(Scans.scanned_at).label("date"),
        func.sum(Scans.number_scan_device).label("total_scans")
    ).join(Restaurants, Restaurants.id == Scans.restaurant_id) \
     .group_by(
        Restaurants.nom,
        Scans.os_family,
        func.date(Scans.scanned_at)
     ).order_by(func.date(Scans.scanned_at).desc()).all()

    # 📆 Regrouper par mois
    monthly_stats = db.session.query(
        Restaurants.nom.label("restaurant"),
        Scans.os_family.label("os_family"),
        func.extract('year', Scans.scanned_at).label("year"),
        func.extract('month', Scans.scanned_at).label("month"),
        func.sum(Scans.number_scan_device).label("total_scans")
    ).join(Restaurants, Restaurants.id == Scans.restaurant_id) \
     .group_by(
        Restaurants.nom,
        Scans.os_family,
        func.extract('year', Scans.scanned_at),
        func.extract('month', Scans.scanned_at)
     ).order_by(
        func.extract('year', Scans.scanned_at).desc(),
        func.extract('month', Scans.scanned_at).desc()
     ).all()

    # 🧾 Format des résultats
    daily_result = [
        {
            "restaurant": stat.restaurant,
            "os_family": stat.os_family or "Inconnu",
            "date": stat.date.strftime("%A %d %B %Y").capitalize(),
            "total_scans": stat.total_scans
        }
        for stat in daily_stats
    ]

    monthly_result = [
        {
            "restaurant": stat.restaurant,
            "os_family": stat.os_family or "Inconnu",
            "month": f"{calendar.month_name[int(stat.month)]} {int(stat.year)}".capitalize(),
            "total_scans": stat.total_scans
        }
        for stat in monthly_stats
    ]

    return jsonify({
        "daily": daily_result,
        "monthly": monthly_result
    }), 200


# @api.route("/generate_qr/<string:restaurant_name>")
# def generate_qr(restaurant_name):
#     qr_data = f"http://127.0.0.1:5000/api/restaurant/{restaurant_name}"
#     qr_img = qrcode.make(qr_data)

#     img_io = io.BytesIO()
#     qr_img.save(img_io, "PNG")
#     img_io.seek(0)

#     return send_file(
#         img_io,
#         mimetype="image/png",
#         as_attachment=True,
#         download_name=f"qr_code_{restaurant_name}.png"
#     )