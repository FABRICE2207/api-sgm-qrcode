from flask import Blueprint, request, jsonify, current_app, send_from_directory
from models import Categories
from db import db
from flask_jwt_extended  import JWTManager, jwt_required, get_jwt_identity

api = Blueprint('categorie_api', __name__)

# Ajout du catégorie
@api.route('/add_categorie', methods=['POST'])
@jwt_required()
def add():
    data = request.get_json()

    categorie_existante =  Categories.query.filter_by(nom=data['nom'], restaurant_id=data['restaurant_id']).first()
    if categorie_existante:
        return jsonify({'msg': "Le nom de la catégorie est déjà utilisé pour ce restaurant"}), 400

    categorie = Categories(
      nom = data['nom'],
      restaurant_id = data['restaurant_id']
    )
    db.session.add(categorie)
    db.session.commit()
    return jsonify({'message': 'Categorie ajoutée avec succès'}), 201

# Afficher la liste des catégories
@api.route('/liste_categorie', methods=['GET'])
def liste():
    categories = Categories.query.order_by(Categories.id.desc()).all()
    return jsonify([
         {
                'id': categorie.id,
                'nom': categorie.nom,
                'created_at': categorie.created_at.isoformat() if categorie.created_at else None,
                'updated_at': categorie.updated_at.isoformat() if categorie.updated_at else None,
                'restaurant': {
                  'id': categorie.restaurant_id,
                  'nom': categorie.restaurant.nom
                } 
            } for categorie in categories
        ]), 200

# Afficher une catégorie
@api.route('/get_categorie/<int:id>', methods=['GET'])
def categorie_by_id(id):
    categorie = Categories.query.get(id)
    if not categorie:
        return jsonify({'message': 'Catégorie non trouvée'}), 404
    return jsonify({
        'id': categorie.id,
        'nom': categorie.nom,
    }), 200

# Modification de la catégorie
@api.route('/update_categorie/<int:id>', methods=['PUT'])
def update_categorie(id):
    # Récupérer la catégorie par son ID
    categorie = Categories.query.get(id)

    # Vérifier si la catégorie existe
    if not categorie:
        return jsonify({'message': 'Catégorie non trouvée'}), 404
    
    # Récupérer les données de la requête
    data = request.get_json()
    
    # Mise à jour des champs
    if 'nom' in data:
        categorie.nom = data['nom']

    # Sauvegarder les modifications
    db.session.commit()
    
    # Retourner la réponse
    return jsonify({
        'message': 'Catégorie mise à jour avec succès',
        'Catégorie': {
            "id": categorie.id,
            "nom": categorie.nom
        }
    }), 200
      


# Afficher la liste des catégories d'un restaurant
@api.route('/liste_categorie_restaurant/<int:id>', methods=['GET'])
@jwt_required()
def liste_categorie_restaurant(id):
    categories = Categories.query.filter(Categories.restaurant_id==id).order_by(Categories.id.desc()).all()

    # Compter le nombre total de catégories
    total_categories = len(categories)
    
    return jsonify([
         {
                'id': categorie.id,
                'nom': categorie.nom,
                'created_at': categorie.created_at.isoformat() if categorie.created_at else None,
                'updated_at': categorie.updated_at.isoformat() if categorie.updated_at else None,
                'restaurant': {
                  'id': categorie.restaurant_id,
                  'nom': categorie.restaurant.nom
                },
                'total': total_categories
            } for categorie in categories
        ]), 200

# supprimer le plat
@api.route('/delete_categorie/<int:id>', methods=['DELETE'])
def delete_plat(id):
    categorie = Categories.query.get(id)

    if not categorie:
        return jsonify({'message': 'Catégorie non trouvé'}), 404

    db.session.delete(categorie)
    db.session.commit()
    return jsonify({'message': 'Plat supprimé avec succès'}), 200

