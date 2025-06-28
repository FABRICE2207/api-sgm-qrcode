import qrcode
import os
import datetime
from models import db, Restaurants
from config import Config

def generate_qr_code(restaurant_id):
    restaurant = Restaurants.query.get(restaurant_id)
    
    qr_url = f"http://{Config.URL_FRONT}/menu_restaurant/{restaurant.hash_url}"
    img = qrcode.make(qr_url)
    filename = f"qr_{restaurant_id}_unique.png"
    path = f"static/qrcodes/{filename}"
    img.save(path)
    
    public_url = f"http://127.0.0.1:5000/static/qrcodes/{filename}"
    return qr_url, public_url  # retourne l'URL publique, pas juste le chemin
