from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Message

message_bp = Blueprint('messages', __name__)

# send message
@message_bp.route('/send', methods=["POST"])
@jwt_required()
def send_message():
    data = request.get_json(silent=True) or {}
    receiver_id = data.get('receiver_id')
    content = data.get('content')

    sender_id = get_jwt_identity()

    if not receiver_id or not content:
        return jsonify({"error":"receiver_id and content are required"}), 400

    if sender_id == receiver_id:
        return jsonify({"error":"you cannot send messages to yourself"}), 400

    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({"error":"Receiver not found"}), 404

    new_message = Message(sender_id = sender_id, receiver_id = receiver_id, content=content)
    db.session.add(new_message)
    db.session.commit()

    return jsonify({
        "message" : "Message sent successfully",
        "data": {
            "id" : new_message.id,
            "sender_id": new_message.sender_id,
            "receiver_id": new_message.receiver_id,
            "content": new_message.content,
            "timestamp": new_message.timestamp,
            "status": new_message.status
        }
    }), 201


# get messages between sender and receiver
@message_bp.route('/chat/<int:user_id>', methods=['GET'])
@jwt_required()
def get_message(user_id):
    current_user_id = get_jwt_identity()

    other_user = User.query.get(user_id)
    if not other_user:
        return jsonify({"error": "User not found"}), 404

    # Pagination parameters
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
    except ValueError:
        return jsonify({"error": "page and limit must be integers"}), 400

    if page < 1 or limit < 1:
        return jsonify({"error": "page and limit must be positive numbers"}), 400

    # Order: 'desc' (newest first) by default, or 'asc' (oldest first)
    order = request.args.get('order', 'desc').lower()

    query = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
    )

    if order == 'asc':
        query = query.order_by(Message.timestamp.asc())
    else:
        query = query.order_by(Message.timestamp.desc())

    total_messages = query.count()
    total_pages = (total_messages + limit - 1) // limit

    messages = query.offset((page - 1) * limit).limit(limit).all()

    # If descending, reverse in-memory to maintain chronological UI order
    if order == 'desc':
        messages.reverse()

    message_list = [
        {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "content": msg.content,
            "timestamp": msg.timestamp,
            "status": msg.status
        } for msg in messages
    ]

    return jsonify({
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "total_messages": total_messages,
        "order": order,
        "messages": message_list
    }), 200

@message_bp.route('/chats', methods=['GET'])
@jwt_required()
def list_chats():
    curr_user_id = get_jwt_identity()

    sent_to = db.session.query(Message.receiver_id).filter_by(sender_id = curr_user_id)
    received_from = db.session.query(Message.sender_id).filter_by(receiver_id = curr_user_id)

    user_ids = set([uid for (uid,) in sent_to.union(received_from).all()])
    users = User.query.filter(User.id.in_(user_ids)).all()

    chat_list = [
        {
            "user_id": user.id,
            "username": user.username
        } for user in users
    ]

    return jsonify({"chats": chat_list}), 200


# Delete Messages
@message_bp.route('/<int:message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(message_id):
    curr_user_id = get_jwt_identity()
    message = Message.query.get(message_id)

    if not message:
        return jsonify({"error":"Message not found"}), 404

    if message.sender_id != curr_user_id:
        return jsonify({"error":"You can only delete your own message"}), 403
    
    db.session.delete(message)
    db.session.commit()

    return jsonify({"message":"Message was deleted"}), 200


# Mark as read
@message_bp.route('/<int:message_id>/read', methods=['PATCH'])
@jwt_required()
def mark_as_read(message_id):
    curr_user_id = get_jwt_identity()
    message = Message.query.get(message_id)

    if not message:
        return jsonify({"error":"Message not found"}), 404

    if message.receiver_id != curr_user_id:
        return jsonify({"error":"You can only mark messages sent to you as read"}), 403

    message.status = "read"
    db.session.commit()

    return jsonify({
        "message":"Message was marked read",
        "data": {
            "id": message.id,
            "status": message.status
        }
    }), 200
