from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# user table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default= datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Data {self.id} {self.username}, {self.created_at}>"

# message table (message_id, message_text, seneder_id, reciever_id, status)
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id= db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id= db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp= db.Column(db.DateTime, default= datetime.now)
    content= db.Column(db.Text, nullable=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy=True))
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref=db.backref('received_messages', lazy=True))

    def __repr__(self):
        return f"<Message {self.id} from {self.sender_id} to {self.receiver_id}: {self.content[:20]}>"
