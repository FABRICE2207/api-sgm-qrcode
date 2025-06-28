from flask import Blueprint, request, jsonify
from models import db, Paiements, Abonnements
import os
import requests
import uuid
CINETPAY_APIKEY = os.getenv("CINETPAY_APIKEY")

api = Blueprint("paiements_api", __name__)

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
        "apikey": "208502353263ef823645c149.22531677",
        "site_id": "365756",
        "transaction_id": transaction_id,
        "amount": montant,
        "currency": "XOF",
        "description":f"Paiement de l'abonnement {abonnement.type_abonnement} pour affichage de menu",
        # "notify_url": "https://ton-domaine.com/api/paiement/notify",  
        # "return_url": "https://ton-domaine.com/paiement/status",      
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

# Route de notification
@api.route("/confirmation_paiement", methods=["POST"])
def notification_cinetpay():
    data = request.form
    transaction_id = data.get("transaction_id")
    status = data.get("status")  # 'ACCEPTED', 'REFUSED', 'CANCELLED'

    paiement = Paiements.query.filter_by(transaction_id=transaction_id).first()
    if not paiement:
        return jsonify({"error": "Paiement introuvable"}), 404

    paiement.status = status
    db.session.commit()

    # Optionnel : activer l'abonnement si le paiement est accepté
    if status == "ACCEPTED":
        abonnement = Abonnements.query.get(paiement.abonnement_id)
        abonnement.statut = "Actif"
        db.session.commit()

    return jsonify({"message": "Notification traitée"}), 200

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
