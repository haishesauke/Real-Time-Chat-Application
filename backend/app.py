from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from auth_routes import auth_bp
from message_routes import message_bp
from models import db, User, Message
from sqlalchemy import inspect
from datetime import timedelta

app = Flask(__name__)

#Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#JWT Config
app.config['JWT_SECRET_KEY'] = 'my_secret_key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

db.init_app(app)
jwt = JWTManager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(message_bp)

with app.app_context():
    try:
        db.create_all()
        inspector = inspect(db.engine)
        print("Tables in DB", inspector.get_table_names())
    except Exception as e:
        print("Tables were not created in DB:", e)



if __name__ == '__main__':
    app.run(debug=True)
