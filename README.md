# 🧾 API SGP QRCode - QRPro

**API RESTful développée avec Flask** pour gérer un système digital d'affiche de produit par QR Code à destination des restaurants, marquis et entreprises e-commerce.

## 📦 Fonctionnalités principales

- 🔐 Authentification (JWT)
- 🍽️ Gestion des restaurants, menus, boissons et articles
- 📆 Disponibilité quotidienne des plats
- 📱 Génération de QR Codes
- 📊 Statistiques des scans (par OS, par date, etc.)
- 💳 Intégration paiement (ex : CinetPay)
- 🧾 Abonnements (Mensuel, Annuel)

---

## 🛠️ Stack technique

- **Python 3.11+**
- **Flask / Flask-RESTful / Flask-JWT-Extended**
- **SQLAlchemy**
- **PostgreSQL** (base de données)
- **Marshmallow** (sérialisation)
- **CORS**, **dotenv**, etc.

---

## 🚀 Installation locale

### 🔧 Prérequis

- Python 3.11+
- PostgreSQL installé
- `pip`

### 🔍 Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/FABRICE2207/api-sgm-qrcode.git
cd api-sgm-qrcode

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sous Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d’environnement
cp .env.example .env  # puis remplir les valeurs

# 5. Créer la base de données
flask db init
flask db migrate
flask db upgrade

# 6. Lancer le serveur
flask run
