from flask import Blueprint, jsonify, request
from database import Database

leaderboard_bp = Blueprint("leaderboard", __name__)

@leaderboard_bp.route("/top", methods=["GET"])
def get_leaderboard():
    """返回排行榜數據"""
    limit = request.args.get("limit", 10, type=int)
    db = Database()
    db.connect()
    leaderboard = db.get_leaderboard_from_redis(limit)
    db.close()

    data = []
    for index, (entry, score) in enumerate(leaderboard):
        name, user_id = entry.split("|")
        data.append({"rank": index + 1, "name": name, "user_ID": user_id, "credit_score": score})

    return jsonify({"success": True, "data": data})

@leaderboard_bp.route("/update", methods=["POST"])
def update_leaderboard():
    """手動更新排行榜數據"""
    db = Database()
    db.connect()
    db.update_leaderboard_in_redis()
    db.close()
    return jsonify({"success": True, "message": "Leaderboard updated"})


@leaderboard_bp.route("/score/<int:user_id>", methods=["GET"])
def get_user_score(user_id):
    """返回指定用戶的積分"""
    db = Database()
    db.connect()
    
    try:
        query = """
        SELECT name, credit_score
        FROM "User"
        WHERE user_ID = %s;
        """
        result = db.execute_query(query, (user_id,))
        if result:
            user_data = result[0]  # 假設只會有一筆資料
            return jsonify({
                "success": True,
                "data": {
                    "user_ID": user_id,
                    "name": user_data["name"],
                    "credit_score": user_data["credit_score"]
                }
            })
        else:
            return jsonify({"success": False, "message": "User not found"}), 404
    except Exception as e:
        print(f"Error fetching user score: {e}")
        return jsonify({"success": False, "message": "Error fetching user score"}), 500
    finally:
        db.close()
        


@leaderboard_bp.route("/creditEvaluation", methods=["POST"])
def credit_evaluation():
    """評分好友"""
    data = request.json

    # 檢查請求中的必要參數
    if not all(k in data for k in ("user_id", "friend_id", "score")):
        return jsonify({"success": False, "message": "缺少必要參數"}), 400

    user_id = data["user_id"]
    friend_id = data["friend_id"]
    score = data["score"]

    # 驗證分數是否合法
    if not (-20 <= score <= 20):
        return jsonify({"success": False, "message": "分數應在 1 到 5 之間"}), 400

    try:
        db = Database()
        db.connect()

        # 檢查好友是否存在於好友列表
        query_check = """
        SELECT COUNT(*) FROM friend_list
        WHERE user_id = %s AND friend_id = %s;
        """
        result = db.execute_query(query_check, (user_id, friend_id))
        if result[0]["count"] == 0:
            return jsonify({"success": False, "message": "好友不存在"}), 404

        # 更新好友的信用分數
        query_update = """
        UPDATE "User"
        SET credit_score = COALESCE(credit_score, 0) + %s
        WHERE user_ID = %s;
        """
        db.execute_query(query_update, (score, friend_id))

        # 更新 Redis 排行榜
        db.update_leaderboard_in_redis()

        return jsonify({"success": True, "message": "評分成功！"})

    except Exception as e:
        print(f"Error during credit evaluation: {e}")
        return jsonify({"success": False, "message": "伺服器錯誤"}), 500
    finally:
        db.close()






