from flask import Blueprint, request, jsonify, current_app, send_from_directory
from models import db, Plats, Restaurants
from werkzeug.utils import secure_filename
import os
from datetime import datetime, date
from flask_jwt_extended  import jwt_required
from sqlalchemy import func

api = Blueprint("plat_api", __name__)

#Configuration pour le téléchargement de photos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/plats'


def allowed_file(filename):
    return '.' in filename and \
      filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ajouter un plats
@api.route('/create_plat', methods=['POST'])
def plat_create():
    # Récupérer les données du formulaire
    if request.method == 'POST':
        try:
            # Récupération des données
            nom = request.form.get('nom')
            description = request.form.get('description')
            date_jour = request.form.get('date_jour')
            file_image = request.files.get('image')
            prix = request.form.get('prix')
            categories_id = request.form.get('categories_id')
            restaurant_id = request.form.get('restaurant_id')

            # Validation des champs obligatoires
            if not all([nom, description, date_jour, file_image, prix, categories_id, restaurant_id]):
                return jsonify({'error': 'Veuillez remplir tous les champs obligatoires'}), 400

            # Vérification du fichier image
            if not file_image or not allowed_file(file_image.filename):
                return jsonify({'error': "Type de fichier non autorisé. Formats acceptés: PNG, JPG, JPEG, WEBP"}), 400

            # Sauvegarde de l'image
            filename = secure_filename(file_image.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file_image.save(file_path)

            # Création du plat avec statut par défaut
            new_plat = Plats(
                nom=nom,
                description=description,
                date_jour=date_jour,
                image=filename,
                prix=prix,
                categories_id=categories_id,
                restaurant_id=restaurant_id,
                statut="Pas disponible"  # Champ statut avec valeur par défaut
            )

            db.session.add(new_plat)
            db.session.commit()

            return jsonify({
                'message': 'Plat créé avec succès',
                'plat': {
                    'id': new_plat.id,
                    'nom': new_plat.nom,
                    'statut': new_plat.statut
                }
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Erreur lors de la création du plat: {str(e)}'}), 500
        
# Afficher les images
@api.route('/plats/<filename>', methods=['GET'])
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# Obtenir un plats by du restaurant
@api.route('/get_plat/<int:id>', methods=['GET'])
def categorie_by_id(id):
    plat = Plats.query.get(id)
    if not plat:
        return jsonify({'message': 'plat non trouvée'}), 404
    return jsonify(
         {
                'id': plat.id,
                'nom': plat.nom,
                'description': plat.description,
                'date': plat.date_jour,
                'image': plat.image,
                'prix': plat.prix,
                'categories' : {
                  'id': plat.categories_id,
                  'nom': plat.categories.nom,
                },
                'restaurant': {
                  'id': plat.restaurant_id,
                  'nom': plat.restaurant.nom
                },
                'statut': plat.statut,
            }
        ), 200


# Afficher la liste des catégories
@api.route('/liste_plats', methods=['GET'])
def plats_liste():
    plats = Plats.query.all()
    return jsonify([
         {
                'id': plat.id,
                'nom': plat.nom,
                'description': plat.description,
                'date_jour': plat.date_jour,
                'image': plat.image,
                'prix': plat.prix,
                'categories' : {
                  'id': plat.categories_id,
                  'nom': plat.categories.nom,
                },
                'restaurant': {
                  'id': plat.restaurant_id,
                  'nom': plat.restaurant.nom
                },
                'statut': plat.statut,
            } for plat in plats
        ]), 200

# supprimer le plat
@api.route('/delete/<int:plat_id>', methods=['DELETE'])
def delete_plat(plat_id):
    plat = Plats.query.get(plat_id)

    if not plat:
        return jsonify({'message': 'Plat non trouvé'}), 404

    # Supprimer l'image du disque si elle existe
    if plat.image:  # suppose que le champ est `image` et stocke le nom de fichier
        image_path = os.path.join(current_app.root_path, 'static/uploads', plat.image)
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                return jsonify({'message': 'Erreur lors de la suppression de l’image', 'error': str(e)}), 500
    try:
        db.session.delete(plat)
        db.session.commit()
        return jsonify({'message': 'Plat supprimé avec succès'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Erreur lors de la suppression du plat', 'error': str(e)}), 500

# Modification de l'image
@api.route('/update/<int:id>', methods=['PUT'])
def plat_update(id):
    plat = Plats.query.get(id)

    if not plat:
        return jsonify({'message': 'Plat non trouvé'}), 404
  
    # Gestion de l'image (optionnelle)
    image = request.files.get('image')
    if image:
        # Supprimer l'ancienne image si elle existe
        if plat.image:
            try:
                os.unlink(os.path.join(current_app.config['UPLOAD_FOLDER'], plat.image))
            except FileNotFoundError:
                pass  # Le fichier n'existe déjà pas, on continue
        
        # Sauvegarder la nouvelle image
        filename = secure_filename(image.filename)
        image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        plat.image = filename
    
    # Extraire et mettre à jour les champs texte
    if request.form.get('nom'):
        plat.nom = request.form.get('nom')
    if request.form.get('description'):
        plat.description = request.form.get('description')
    if request.form.get('prix'):
        plat.prix = request.form.get('prix')
    if request.form.get('date_jour'):
        plat.date_jour = request.form.get('date_jour')
    if request.form.get('categories_id'):
        plat.categories_id = request.form.get('categories_id')
    if request.form.get('restaurant_id'):
        plat.restaurant_id = request.form.get('restaurant_id')

    db.session.commit()
    
    return jsonify({
        'message': 'Plat mis à jour avec succès',
        'plat': {
            "nom": plat.nom,
            "image": plat.image,
            "description": plat.description,
            "prix": plat.prix,
            "date_jour": plat.date_jour,
            "restaurant": {
                "id": plat.restaurant.id,
                "nom": plat.restaurant.nom
            },
            "categories": {
                "id": plat.categories.id,
                "nom": plat.categories.nom
            },
        }
    }), 200
      

# Nombre de plats disponible et non
@api.route('/count_plats', methods=['GET'])
def compter_plats():
    nbre_dispo = Plats.query.filter_by(statut='Disponible').count()
    nbre_indispo = Plats.query.filter_by(statut='Pas disponible').count()

    return jsonify({
        "nbre_dispo": nbre_dispo,
        "nbre_indispo": nbre_indispo
    }), 200

@api.route('/count_by_restaurant/<int:id>', methods=['GET'])
def count_plats_by_restaurant(id):
    plats_dispo = Plats.query.filter_by(restaurant_id=id, statut="Disponible").count()
    plats_indispo = Plats.query.filter_by(restaurant_id=id, statut="Pas disponible").count()

    return jsonify({
        'nbre_dispo': plats_dispo,
        'nbre_indispo': plats_indispo
    }), 200

# Les plats en fonction de la date du jour
@api.route('/plat_jour_restaurant/<int:restaurant_id>/date/<string:date_str>', methods=['GET'])
def menu_par_date(restaurant_id, date_str):
    try:
        if date_str == "aujourd'hui":
            date_obj = date.today()
        else:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Format de date invalide. Utilisez JJ-MM-AAAA ou 'aujourd'hui'."}), 400
    
    # Filtrer par restaurant_id, date_jour et statut = "Disponible"
    plats = Plats.query.filter_by(restaurant_id=restaurant_id, date_jour=date_obj, statut="Disponible").all()

    if not plats:
      return jsonify({"error": "Aucun plat trouvé disponible pour la date du jour."}), 404

    return jsonify([{
        "restaurant": {
            "id": p.restaurant.id,
            "nom": p.restaurant.nom,
            "logo": p.restaurant.logo,
        },
        'categories' : {
                  'nom': p.categories.nom,
                },
        "date_jour": p.date_jour.strftime("%d-%m-%Y"),
        "nom": p.nom,
        "prix": p.prix,
        "description": p.description,
        "image": p.image,
        "statut": p.statut
    } for p in plats]), 200


    # Afficher la liste des catégories d'un restaurant

@api.route('/liste_plats_restaurant/<int:id>', methods=['GET'])
@jwt_required()
def liste_categorie_restaurant(id):
    plats = Plats.query.filter_by(restaurant_id=id).all()

    # Compter le nombre total de catégories
    total_plats = len(plats)
    
    return jsonify([
         {
                'id': plat.id,
                'image': plat.image,
                'nom': plat.nom,
                'description': plat.description,
                'prix': plat.prix,
                'date_jour': plat.date_jour,
                'created_at': plat.created_at.isoformat() if plat.created_at else None,
                'updated_at': plat.updated_at.isoformat() if plat.updated_at else None,
                'restaurant': {
                  'id': plat.restaurant_id,
                  'nom': plat.restaurant.nom
                },
                'categories': {
                  'id': plat.categories_id,
                  'nom': plat.categories.nom
                },
                'statut': plat.statut,
                'total': total_plats
            } for plat in plats
        ]), 200

# Changer le statut en disponible ou pas disponible
@api.route('/update_statut_plat/<int:plat_id>', methods=['PUT'])
def update_plat_statut(plat_id):
    try:
        plat = Plats.query.get(plat_id)
        
        if not plat:
            return jsonify({'error': 'Plat non trouvé'}), 404

        # Alterner le statut
        if plat.statut == "Disponible":
            plat.statut = "Pas disponible"
        else:
            plat.statut = "Disponible"

        db.session.commit()

        return jsonify({
            'message': 'Statut du plat mis à jour avec succès',
            'plat': {
                'id': plat.id,
                'nom': plat.nom,
                'nouveau_statut': plat.statut
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Nombre de plats par restaurant
@api.route('/number_by_restaurant', methods=['GET'])
def nombre_plats_par_restaurant():
    try:
        # LEFT JOIN pour inclure tous les restaurants même ceux sans plat
        resultats = (
            db.session.query(Restaurants.nom, func.count(Plats.id))
            .outerjoin(Plats, Restaurants.id == Plats.restaurant_id)
            .group_by(Restaurants.nom)
            .all()
        )

        # Résultat au format liste de dictionnaires
        data = [{"restaurant": nom, "nombre": nombre} for nom, nombre in resultats]

        return jsonify(data), 200

    except Exception as e:
        print("Erreur :", e)
        return jsonify({"message": "Erreur serveur"}), 500

@api.route('/line_chart_data', methods=['GET'])
def get_line_chart_data():
    try:
        # 1. Toutes les dates où des plats ont été créés
        dates = db.session.query(func.date(Plats.created_at))\
            .distinct()\
            .order_by(func.date(Plats.created_at)).all()
        dates = [d[0] for d in dates]

        # 2. Tous les restaurants
        restaurants = db.session.query(Restaurants.id, Restaurants.nom).all()

        # 3. Initialiser un dict { (date, restaurant): 0 }
        data_dict = {
            (date, resto.nom): 0
            for date in dates
            for resto in restaurants
        }

        # 4. Récupérer les vrais nombres de plats
        results = db.session.query(
            func.date(Plats.created_at).label("jour"),
            Restaurants.nom.label("restaurant"),
            func.count(Plats.id).label("nombre")
        ).join(Restaurants, Plats.restaurant_id == Restaurants.id)\
         .group_by(func.date(Plats.created_at), Restaurants.nom)\
         .all()

        # 5. Mise à jour avec les vraies valeurs
        for jour, restaurant, nombre in results:
            data_dict[(jour, restaurant)] = nombre

        # 6. Convertir en liste
        final_data = [
            {
                "date": date.strftime("%Y-%m-%d"),
                "restaurant": restaurant,
                "nombre": data_dict[(date, restaurant)]
            }
            for (date, restaurant) in data_dict
        ]

        return jsonify(final_data), 200

    except Exception as e:
        print("Erreur dans line_chart_data avec tous les restaurants :", e)
        return jsonify({"error": "Erreur serveur"}), 500