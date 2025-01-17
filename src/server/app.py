from flask import Flask, jsonify
from database import Database
from dotenv import load_dotenv
from flask_cors import CORS
from routes import transaction_bp, user_bp

# Import Blueprints
from routes.user_routes import user_bp
from routes.friend_routes import friend_bp
from routes.friendlist import friendlist_bp
from routes.transaction_routes import transaction_bp
from routes.leaderboard_routes import leaderboard_bp
from routes.split_routes import split_bp
from routes.category_routes import category_bp
# 加載環境變數
load_dotenv()

# 創建 Flask 應用
app = Flask(__name__)

#session加的東西
app.config['SECRET_KEY'] = 'your_secret_key'  # 替換為更安全的密鑰
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/mydatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, resources={r"/api/*": {"origins": "http://localhost:3001"}})
db = Database()  # 初始化資料庫

# 註冊 Blueprint
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(friend_bp, url_prefix='/api/friends')
app.register_blueprint(friendlist_bp, url_prefix='/api/friendslist')
app.register_blueprint(transaction_bp, url_prefix='/api/transaction')
app.register_blueprint(leaderboard_bp, url_prefix="/api/leaderboard")
app.register_blueprint(split_bp, url_prefix="/api/split")
app.register_blueprint(category_bp, url_prefix="/api/category")
# 測試路由
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to the Flask API"})

@app.route("/test-db", methods=["GET"])
def test_db():
    db.connect()
    user_id = db.add_user("Monkey", "monkey@example.com", "hashed_password")
    db.close()
    return jsonify({"message": "Database test complete", "user_id": user_id})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

