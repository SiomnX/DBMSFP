from flask import Blueprint, request, jsonify
from database import Database
import psycopg2
from psycopg2.extras import RealDictCursor

#define blueprint
friendlist_bp = Blueprint('friendList', __name__)
db = Database()
db.connect() # connect to db

#get friends(看user_id)
@friendlist_bp.route('/', methods=['GET'])
def get_friends():
    user_id = request.args.get('user_id')  # get user ID from query param

    if not user_id:
        # dynamically fetch first available user ID
        result = db.execute_query("SELECT user_ID FROM \"User\" LIMIT 1")
        if not result:
            return jsonify({'error': 'No users found in the database!'}), 404
        user_id = result[0]['user_ID']

    try:
        friends = db.get_friends_by_user_id(user_id) #fetch friends from db
        return jsonify(friends)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


#add a freind (add friend) ok
@friendlist_bp.route('/', methods=['POST'])
def add_friend():
    data = request.json  # Extract JSON payload
    user_id = data.get('user_id')
    friend_id = data.get('friend_id')
    nickname = data.get('nickname')

    if not (user_id and friend_id and nickname):
        return jsonify({'error': 'Missing required fields'}), 400

    # 確保 user_id & friend_id 存在(in database)
    try:
        user_exists = db.execute_query(
            "SELECT COUNT(*) FROM \"User\" WHERE user_ID = %s", (user_id,))

        friend_exists = db.execute_query(
            "SELECT COUNT(*) FROM \"User\" WHERE user_ID = %s", (friend_id,))

        if user_exists[0]['count'] == 0 or friend_exists[0]['count'] == 0:
            return jsonify({'error': 'Invalid user_id or friend_id'}), 400

    except Exception as e:
        return jsonify({'error': f'Database validation error: {e}'}), 500

    try:
        # attempt to create a few friend
        list_id = db.create_friend(user_id, friend_id, nickname)
        return jsonify({'list_id': list_id, 'message': 'Friend added successfully!'}), 201

    except psycopg2.errors.UniqueViolation:  # Catch unique constraint violation
        return jsonify({'error': '你們已經是朋友！'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


#delete a friend（用list_id刪除好友）
@friendlist_bp.route('/<int:list_id>', methods=['DELETE'])
def delete_friend(list_id):
    try:
        db.delete_friend(list_id)
        return jsonify({'message': 'Friend deleted successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

