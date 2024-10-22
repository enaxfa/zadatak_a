from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from os import environ
from jsonschema import validate, ValidationError
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DB_URL')
db = SQLAlchemy(app)

# JSON Schema for user validation
user_schema = {
    "type": "object",
    "properties": {
        "username": {"type": "string"},
        "email": {"type": "string", "format": "email", "pattern":"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"}
    },
    "required": ["username", "email"]
}

email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def json(self):
        return {'id': self.id,'username': self.username, 'email': self.email}

db.create_all()


# create a user
@app.route('/users/create', methods=['POST'])
def create_user():
  try:
    data = request.get_json()
    
    try:
        validate(instance=data, schema=user_schema)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    
    new_user = User(username=data['username'], email=data['email'])
    user = User.query.filter((User.username==new_user.username) | (User.email==new_user.email)).first()
    if user:
        return make_response(jsonify({'message': 'username or email already exist'}), 404)
    db.session.add(new_user)
    db.session.commit()
    return make_response(jsonify({'message': 'user created'}), 201)
  except e:
    return make_response(jsonify({'message': 'error creating user'}), 500)


# get all users
@app.route('/users/getAll', methods=['GET'])
def get_all_users():
  try:
    users = User.query.all()
    return make_response(jsonify([user.json() for user in users]), 200)
  except e:
    return make_response(jsonify({'message': 'error getting users'}), 500)


# get a user by id
@app.route('/users/get/<int:id>', methods=['GET'])
def get_user_by_id(id):
  try:
    user = User.query.filter_by(id=id).first()
    if user:
      return make_response(jsonify({'user': user.json()}), 200)
    return make_response(jsonify({'message': 'user not found'}), 404)
  except e:
    return make_response(jsonify({'message': 'error getting user'}), 500)


# update a user
@app.route('/users/update/<int:id>', methods=['PUT'])
def update_user(id):
  try:
    user = User.query.filter_by(id=id).first()
    if not user:
      return make_response(jsonify({'message': 'user not found'}), 404)
    
    data = request.get_json()
    if not data.get('username') and not data.get('email'):
      return jsonify({"error": "username or email are required"}), 400

    if data.get('username'):
      user_exist = User.query.filter_by(username=data.get('username')).first()
      if user_exist and user_exist.id != id:
        return make_response(jsonify({'message': 'username already exist'}), 400)
      user.username = data['username']
      
    if data.get('email'):
      if not re.match(email_regex, data['email']):
        return make_response(jsonify({'message': 'Invalid email format'}), 400)

      user_exist = User.query.filter_by(email=data.get('email')).first()
      if user_exist and user_exist.id != id:
        return make_response(jsonify({'message': 'email already exist'}), 400)
      user.email = data['email']
    
    db.session.commit()
    return make_response(jsonify({'message': 'user updated'}), 200)
  except Exception as e:
        return make_response(jsonify({'message': 'error updating user', 'error': str(e)}), 500)


# delete a user
@app.route('/users/deleteById/<int:id>', methods=['DELETE'])
def delete_user(id):
  try:
    user = User.query.filter_by(id=id).first()
    if user:
      db.session.delete(user)
      db.session.commit()
      return make_response(jsonify({'message': 'user deleted'}), 200)
    return make_response(jsonify({'message': 'user not found'}), 404)
  except e:
    return make_response(jsonify({'message': 'error deleting user'}), 500)