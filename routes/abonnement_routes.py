from flask import Blueprint, request, jsonify
from models import Abonnements
from datetime import datetime, date
from flask_jwt_extended  import jwt_required
from sqlalchemy import func
from db import db

api = Blueprint("abonnement_api", __name__)

# Ajout de l'abonnement
@api.route('/update_abonnement/<id>', methods=['PUT'])
def update_abonnement(id):
  
    abonnement = Abonnements.query.get(id)

    if not abonnement:
        return jsonify({'message': 'Abonnement non trouvé'}), 404

    # Récupérer les données de la requête
    data = request.get_json()

    if 'type_abonnement' and 'montant' and 'dateDebut' and 'dateFin' and 'statut' in data:
        abonnement.type_abonnement = data['type_abonnement']
        abonnement.montant = data['montant']
        abonnement.dateDebut = data['dateDebut']
        abonnement.dateFin = data['dateFin']
        abonnement.statut = data['statut']

    # db.session.add(abonnement)
    db.session.commit()
    return jsonify({
                'message': "Votre abonnement est cours d'attente pour paiement...",
                    "type_abonnement": abonnement.type_abonnement,
                    "montant": abonnement.montant,
                    "dateDebut": abonnement.dateDebut,
                    "dateFin": abonnement.dateFin,
                    "statut": abonnement.statut,
                    }), 200

# Afficher la liste des catégories
@api.route('/liste_abonnement', methods=['GET'])
def liste():
    abonnements = Abonnements.query.all()

    return jsonify([
         {
                'id': abonnement.id,
                'type_abonnement': abonnement.type_abonnement,
                'montant': abonnement.montant,
                'dateDebut': abonnement.dateDebut,
                'dateFin': abonnement.dateFin,
                'statut': abonnement.statut,
                'created_at': abonnement.created_at.isoformat() if abonnement.created_at else None,
                'updated_at': abonnement.updated_at.isoformat() if abonnement.updated_at else None,
                'restaurant': {
                  'id': abonnement.restaurant_id,
                  'nom': abonnement.restaurant.nom
                } 
            } for abonnement in abonnements
        ]), 200


#  Obtenir l'abonnment en fonction de son id
@api.route('/get_abonnement_by_restaurant/<int:restaurant_id>', methods=['GET'])
def get_abonnement_by_restaurant(restaurant_id):
    abonnement = Abonnements.query.filter_by(restaurant_id=restaurant_id).first()
    
    if not abonnement:
        return jsonify({'message': 'Aucun abonnement trouvé pour ce restaurant'}), 404

    return jsonify({
        'id': abonnement.id,
        'type_abonnement': abonnement.type_abonnement,
        'montant': abonnement.montant,
        'statut': abonnement.statut,
        'dateDebut': abonnement.dateDebut.isoformat() if abonnement.dateDebut else None,
        'dateFin': abonnement.dateFin.isoformat() if abonnement.dateFin else None,
        'restaurant_id': abonnement.restaurant_id,
    }), 200

# Changer le statut en actif ou expié
@api.route('/change_statut_abonnement/<int:id>', methods=['PUT'])
def update_plat_statut(id):
    try:
        abonnement = Abonnements.query.get(id)
        
        if not abonnement:
            return jsonify({'error': 'Abonnement non trouvé'}), 404

        # Alterner le statut
        if abonnement.statut == "Actif":
            abonnement.statut = "Expiré"
        else:
            abonnement.statut = "Actif"

        db.session.commit()

        return jsonify({
            'message': "Statut de l'abonnement mis à jour avec succès",
            'abonnement': {
                'id': abonnement.id,
                'type_abonnement': abonnement.type_abonnement,
                'nouveau_statut': abonnement.statut
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500