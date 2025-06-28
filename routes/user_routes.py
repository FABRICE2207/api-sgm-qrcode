from flask import Blueprint, request, jsonify
from models import User
from db import db
from utils.auth import hash_password, check_password
from flask_jwt_extended import create_access_token


api = Blueprint('user_api', __name__)

# Configuration pour le téléchargement de photos
# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# UPLOAD_FOLDER = 'static/uploads'


# def allowed_file(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Inscription de l'utilisateur
@api.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'] 
        email = request.form['email']
        password = request.form['password']
        # telephone = request.form['telephone']
        # roles = request.form['roles']
        # file_image = request.files.get('photos',None)
        # departement = request.form['departement']

        if not username or not email or not password:
            return jsonify({'msg': "Tous les champs sont obligatoires"}), 400
        # if not allowed_file(file_image.filename):
        #     return jsonify({'msg': "Le fichier n'est pas autorisé"}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'msg': "L'email est déjà utilisé"}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({'msg': "Le nom d'utilisateur est déjà utilisé"}), 400
        
        user = User(username=username, email=email, password=hash_password(password))
        db.session.add(user)
        db.session.commit()

        return jsonify({'msg': "Utilisateur inscrit avec succès"}), 200
    return jsonify({'msg': "Méthode non autorisée"}), 405

# Login de l'utilisateur
@api.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'msg': "L'email ou le mot de passe n'existe pas"}), 400

    user = User.query.filter_by(email=data['email']).first()
    if user and check_password(data['password'], user.password):
        token = create_access_token(identity=user.id)
        return jsonify({'access_token': token}), 200
        # user_info = {
        #     'id': user.id,
        #     'email': user.email,
        #     'username': user.username,  # si tu as ce champ
        # }
        # return jsonify({
        #     'msg': "Utilisateur connecté avec succès",
        #     'user': user_info
        # }), 200
    return jsonify({'msg': "L'email ou le mot de passe n'existe pas"}), 401

# Modifier les informations de restaurants
@api.route('/update_user/<int:id>', methods=['PUT'])
def restaurant_update(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'Utilisateur non trouvé'}), 404

    # Extraire et mettre à jour les champs texte
    if request.form.get('nom'):
        user.username = request.form.get('username')
    if request.form.get('email'):
        user.email = request.form.get('email')
    if request.form.get('password'):
        user.password = request.form.get('password')
    

    # --- Vérification et hash du mot de passe ---
    if request.form.get('password') or request.form.get('passwordConfir'):
        if request.form.get('password') != request.form.get('password'):
            return jsonify({'message': 'Les mots de passe ne correspondent pas'}), 400
        user.password = hash_password(request.form.get('password'))
    

    db.session.commit()

    return jsonify({
        'message': 'Restaurant mis à jour avec succès'}), 200


# @api.route('/uploads/<filename>', methods=['GET'])
# def uploaded_file(filename):
#     return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# # Liste tous les utilisateurs
# @api.route('/getAll', methods=['GET'])
# def getAll():
#     datas = User.query.all()
#     return jsonify("Liste des utilisateurs",
#         [
#         {
#         'id': data.id,
#         'username': data.username,
#         'email': data.email,
#         # 'telephone': data.telephone,
#         # 'roles': data.roles,
#         # 'photos': data.photos,
#         # 'departement': data.departement,
#         'created_at': data.created_at,
#         'updated_at': data.updated_at
#     } for data in datas]), 200

# # Obtenir un utilisateur par son ID
# @api.route('/getUserById/<int:id>', methods=['GET'])
# def getById(id):
#     user = User.query.get(id)
#     if not user:
#         return jsonify({'msg': "L'utilisateur n'existe pas"}), 404
#     return jsonify({
#         'id': user.id,
#         'username': user.username,
#         'email': user.email,
#         'telephone': user.telephone,
#         'roles': user.roles,
#         'photos': user.photos,
#         'departement': user.departement,
#         'created_at': user.created_at.isoformat() if user.created_at else None,
#         'updated_at': user.updated_at.isoformat() if user.updated_at else None
#     }), 200


# Lite des gérants
# @api.route('/getAllGerants', methods=['GET'])
# def getAllGerants():
#     gerants = User.query.filter(User.roles.contains('Gérant')).all()
#     return jsonify([{
#         'id': gerant.id,
#         'username': gerant.username,
#         'email': gerant.email,
#         'roles': gerant.roles,
#         'created_at': gerant.created_at.isoformat() if gerant.created_at else None,
#         'updated_at': gerant.updated_at.isoformat() if gerant.updated_at else None
#     } for gerant in gerants]), 200

# Nombre des utilisateurs
@api.route('/count_User', methods=['GET'])
def count_User():
    count = User.query.count()
    return jsonify({"count_User": count}), 200

# Le nombre d'utilisateurs par rôle
@api.route('/count_roles', methods=['GET'])
def count_roles():
    admin_count = User.query.filter(User.roles.contains('Admin')).count()
    manager_count = User.query.filter(User.roles.contains('Manager')).count()
    employee_count = User.query.filter(User.roles.contains('Employé')).count()
    return jsonify({
        'admin': admin_count,
        'manager': manager_count,
        'employes': employee_count,
    }), 200

