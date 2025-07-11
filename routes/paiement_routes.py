from flask import Blueprint, request, jsonify
from models import db, Paiements, Abonnements
import os
import requests
import uuid
from datetime import datetime, timedelta
api = Blueprint("paiements_api", __name__)

# Clé API de paiement
CINETPAY_APIKEY = os.getenv("CINETPAY_APIKEY")

# Site id
CINETPAY_SITE_ID = os.getenv("CINETPAY_SITE_ID")

# Notification
CINETPAY_NOTIFY_URL = os.getenv("CINETPAY_NOTIFY_URL")

# Retourne url
CINETPAY_RETURN_URL = os.getenv("CINETPAY_RETURN_URL")

# Route paiement
@api.route("/paiements_initier", methods=["POST"])
def initier_paiement():
    data = request.get_json()
    montant = data.get("montant")
    abonnement_id = data.get("abonnement_id")
    restaurant_id = data.get("restaurant_id")

    # if not all([montant, abonnement_id, restaurant_id]):
    #     return jsonify({"error": "Données incomplètes"}), 400

    abonnement = Abonnements.query.filter_by(id=abonnement_id, restaurant_id=restaurant_id).first()
    if not abonnement:
        return jsonify({"error": "Abonnement introuvable"}), 404

    transaction_id = f"PMT-ABN-{uuid.uuid4().hex[:20]}".upper()

    url = "https://api-checkout.cinetpay.com/v2/payment"
    

    payload = {
        "apikey": CINETPAY_APIKEY, # APIKEY de cinetpay
        "site_id": CINETPAY_SITE_ID, # ID du site de cinetpay
        "transaction_id": transaction_id,
        "amount": montant,
        "currency": "XOF",
        "description":f"Paiement de l'abonnement {abonnement.type_abonnement} pour l'affichage de votre produit",
        "notify_url": CINETPAY_NOTIFY_URL,  
        "return_url": CINETPAY_RETURN_URL,      
        "channels": "ALL",
        "invoice_data":{
            "Reste à payer":"25 000fr",
            "Matricule":"24OPO25",
            "Annee-scolaire":"2020-2021"
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        # 💳 Appel vers CinetPay
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        print(result)

        if result["code"] == '201' and result["data"]["payment_url"]:
            # Enregistrer le paiement en base
            paiement = Paiements(
                transaction_id=transaction_id,
                amount=montant,
                currency="XOF",
                description=payload["description"],
                # notify_url=payload["notify_url"],
                # return_url=payload["return_url"],
                channels="ALL",
                status="En attente",
                restaurant_id=restaurant_id,
                abonnement_id=abonnement_id
            )

            db.session.add(paiement)
            db.session.commit()

            return jsonify(result), 201
        else:
            return jsonify({
                "error": "Échec de la création du paiement",
                "details": result
            }), 400

    except Exception as e:
        return jsonify({"error": "Erreur serveur", "message": str(e)}), 500

# Liste des paiements
@api.route("/liste_paiement", methods=["GET"])
def paiement_liste():
    # Afficher les paiements les plus récents en premiers
    paiements = Paiements.query.order_by(Paiements.created_at.desc()).all()
    return jsonify([
        {
            'transaction_id': paiement.transaction_id,
            'amount': paiement.amount,
            'currency': paiement.currency,
            'description': paiement.description,
            'channels': paiement.channels,
            'status': paiement.status,
            'restaurant': {
                'id': paiement.restaurant_id,
                'nom': paiement.restaurant.nom,
            },
            'mode_paiement': paiement.mode_paiement,
            'abonnements': {
                'id': paiement.abonnement_id,
                'type_abonnement': paiement.abonnements.type_abonnement
            },
            'created_at': paiement.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'total': len(paiements), # format lisible
        } for paiement in paiements
    ]), 200

# Route de notification
# Route de notification
@api.route("/confirmation_paiement", methods=["POST"])
def confirmation_paiement():  # Correction du nom de la fonction (confimation -> confirmation)
    data = request.form
    transaction_id = data.get("transaction_id")
    status = data.get("status")  # 'ACCEPTED', 'REFUSED', 'CANCELLED'

    # Validation des données reçues
    if not transaction_id or not status:
        return jsonify({"error": "Données de transaction incomplètes"}), 400

    # Recherche du paiement dans la base de données
    paiement = Paiements.query.filter_by(transaction_id=transaction_id).first()
    if not paiement:
        return jsonify({"error": "Paiement introuvable"}), 404

    try:
        # Mise à jour du statut du paiement
        paiement.status = status
        db.session.commit()

        # Activation de l'abonnement si le paiement est accepté
        if status == "ACCEPTED":
            abonnement = Abonnements.query.get(paiement.abonnement_id)
            if abonnement:
                abonnement.statut = "Actif"
                db.session.commit()

        return jsonify({
            "message": "Paiement confirmé !",
            "transaction_id": transaction_id,
            "status": status
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erreur lors du traitement: {str(e)}"}), 500
    
from flask import request, jsonify
import hashlib
from datetime import datetime

@api.route("/notification_paiement", methods=["POST"])
def notification_paiement():
    # 1. Récupération et validation des données
    data = request.form
    required_fields = ['cpm_trans_id', 'cpm_site_id', 'cpm_amount', 'cpm_currency', 'signature', 'payment_method', 'cel_phone_num', 'cpm_result']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Données de notification incomplètes"}), 400

    # 2. Vérification de la signature
    api_key = os.getenv("CINETPAY_API_KEY")  # À stocker dans les variables d'environnement
    signature_data = f"{data['cpm_trans_id']}{data['cpm_site_id']}{data['cpm_amount']}{data['cpm_currency']}{api_key}"
    generated_signature = hashlib.sha256(signature_data.encode()).hexdigest()
    
    if generated_signature != data['signature']:
        return jsonify({"error": "Signature invalide"}), 403

    # 3. Traitement du paiement
    try:
        transaction_id = data['cpm_trans_id']
        status = "ACCEPTED" if data['cpm_result'] == "00" else "REFUSED"
        amount = int(data['cpm_amount'])
        # phone = data['cel_phone_num']
        method = data['payment_method']
        
        # Recherche du paiement
        paiement = Paiements.query.filter_by(transaction_id=transaction_id).first()
        
        if not paiement:
            return jsonify({"error": "Transaction introuvable"}), 404
            
        # Mise à jour du paiement
        paiement.status = status
        paiement.montant = amount
        paiement.methode_paiement = method
        # paiement.telephone = phone
        paiement.updated_at = datetime.utcnow()
        
        db.session.commit()

        # Si paiement accepté, activer l'abonnement
        if status == "ACCEPTED":
            abonnement = Abonnements.query.get(paiement.abonnement_id)
            if abonnement:
                abonnement.statut = "Actif"
                abonnement.date_debut = datetime.utcnow()
                abonnement.date_fin = datetime.utcnow() + timedelta(days=30)  # Exemple: 1 mois
                db.session.commit()

                # Ici vous pourriez ajouter un email de confirmation
                # ou une notification SMS

        # Réponse obligatoire pour CinetPay
        return jsonify({
            "status": "success",
            "message": "Notification traitée avec succès",
            "transaction_id": transaction_id,
            "code": data['cpm_result']
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Erreur de traitement",
            "details": str(e)
        }), 500