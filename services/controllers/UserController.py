import jwt
from flask import Blueprint, jsonify, request
from repositories.UserRepository import UserRepository
from repositories.MessageRepository import MessageRepository
from repositories.ProfilRepository import ProfilRepository
from models.User import User
from models.Message import Message
from config import Config
from constants import constants

SECRET_KEY = Config.SECRET_KEY

userRepository = UserRepository()
messageRepository = MessageRepository()
profilRepository = ProfilRepository()

userBp = Blueprint('userBp', __name__, url_prefix='/users')

@userBp.route('/connect', methods=['POST'])
def connectUser():
    data = request.json
    user = userRepository.getUserByName(data['username'])
    if not user:
        return jsonify({'message': constants.USER_NOT_FOUND}), 404
    if user.password != data['password']:
        return jsonify({'message': constants.WRONG_PASSWORD}), 401
    token = jwt.encode(user.toDict(), SECRET_KEY, algorithm='HS256')
    return jsonify({'token': token}), 200

@userBp.route('/create', methods=['POST'])
def createAccount():
    data = request.json
    user = userRepository.getUserByName(data['username'])
    if user:
        return jsonify({'message': constants.USER_ALREADY_EXISTS}), 409
    user = User.fromJson(data)
    userRepository.addUser(user)
    message = Message("USERS", f"{user.name.title()} a crée son compte")
    messageRepository.addMessage(message)
    token = jwt.encode(user.toDict(), SECRET_KEY, algorithm='HS256')
    return jsonify({'token': token}), 200

@userBp.route('/<int:userId>/role', methods=['PUT'])
def updateRole(userId):
    user = userRepository.getUserById(userId)
    if not user:
        return jsonify({'message': constants.USER_NOT_FOUND}), 404
    newRole = int(request.json['newRole'])
    if newRole < user.profileValue or user.superAdmin == 1:
        if user.profileValue == 2:
            user = userRepository.updateProfile(userId, newRole, 1)
        else :
            user = userRepository.updateProfile(userId, newRole, user.superAdmin)
        token = jwt.encode(user.toDict(), SECRET_KEY, algorithm='HS256')
        return jsonify({'token': token}), 200
    return jsonify({'message': constants.CANNOT_CHANGE_ROLE}), 403

@userBp.route('/admin/connect', methods=['POST'])
def connectAdmin():
    data = request.json
    password = data['password']
    userId = int(data['userId'])
    newRole = int(data['newRole'])
    admin = userRepository.getAdminWithPassword(password)
    if not admin:
        return jsonify({'message': constants.INVALID_PASSWORD}), 401
    user = userRepository.updateProfile(userId, newRole, 0)
    token = jwt.encode(user.toDict(), SECRET_KEY, algorithm='HS256')
    return jsonify({'token': token}), 200

@userBp.route('/<int:userId>/access', methods=['POST'])
def askAccess(userId):
    data = request.json
    role = str(data['role'])
    user = userRepository.getUserById(userId)
    profil = profilRepository.getProfilByValue(role)
    if not user or not profil:
        return jsonify({'message': constants.USER_NOT_FOUND}), 404
    message = Message("ASK", f"{user.name.title()} a demandé des accès {profil.label}")
    messageRepository.addMessage(message)
    return jsonify({'message': 'Message sent!'}), 200

@userBp.route('/<int:userId>/changePassword', methods=['PUT'])
def changePassword(userId):
    data = request.json
    oldPassword = str(data['oldPassword'])
    password = str(data['password'])
    user = userRepository.getUserById(userId)
    if not user:
        return jsonify({'message': constants.USER_NOT_FOUND}), 404
    if user.password != oldPassword:
        return jsonify({'message': constants.INVALID_PASSWORD}), 401
    user.password = password
    userRepository.updatePassword(userId, password)
    return jsonify({'message': constants.PASSWORD_CHANGED}), 200

@userBp.route('/users', methods=['GET'])
def getUsers():
    users = userRepository.getAllUsers()
    return jsonify([user.toDict() for user in users]), 200

@userBp.route('/update', methods=['PUT'])
def updateUsers():
    users = request.json['users']
    for userId, userProfile in users.items():
        userRepository.updateProfile(userId, userProfile, 0)
    return jsonify({'message': constants.USERS_UPDATED}), 200