# from flask import Blueprint, request, jsonify
# from models import Restaurants, Plats, Categories
# from db import db
# from sqlalchemy import func
# import app
# from flask_jwt_extended  import JWTManager, jwt_required, get_jwt_identity
# from datetime import datetime  # For datetime operations

# api = Blueprint('type_conges_api', __name__)

# @api.route('/create', methods=['POST'])
# @jwt_required()
# def create_type_conges():
#   data = request.get_json()
  
#   type_conges = Type_conges.query.filter_by(nom=data['nom']).first()
#   if type_conges:
#     return jsonify({'message': 'Type de congé existe déjà'}), 400
#   else:
#     new_type_conges = Type_conges(
#       nom=data['nom'],
#       nbre_jours=data['nbre_jours']
#     )
#     db.session.add(new_type_conges)
#     db.session.commit()
#     return jsonify({'message': 'Type de congé créé avec succès'}), 201
  
# @api.route('/getAll', methods=['GET'])
# @jwt_required()
# def getAll_type_conges():
#   datas = Type_conges.query.all()

#   return jsonify([
#     {
#     'nom': datas.nom,
#     'nbre_jours': datas.nbre_jours
#   } for datas in datas
#   ]), 200
  

