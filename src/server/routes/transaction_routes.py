from flask import Flask, request, jsonify
from flask import Blueprint
from database import Database
from dotenv import load_dotenv
from flask_cors import CORS
from datetime import datetime
import logging

# 初始化应用与环境
load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3001"}})
db = Database()
db.connect()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 通用的 API 响应格式
def create_response(message="", data=None, error=None, status=200):
    return jsonify({"message": message, "data": data, "error": error}), status

transaction_bp = Blueprint("transaction_bp", __name__)

@transaction_bp.route("/", methods=["GET"])
def get_transactions():
    """获取所有交易记录
    """
    try:
        db.connect()
        query = '''
            SELECT
                t."transaction_id" AS transaction_id,
                t."item",
                t."amount",
                t."description",
                t."transaction_date",
                t."category_id" AS category_id,
                c."category_name",
                t."payer_id" AS payer_id,
                t."split_count"
            FROM "transaction" t
            LEFT JOIN "category" c
                ON t."category_id" = c."category_id"
        '''


        rows = db.execute_query(query)
        print("Query Result:", rows)  # 打印查询结果
        return create_response(data=rows, status=200)

    except Exception as e:
        print("Database connection error:", e)
        logger.exception("Error fetching transactions: %s", e)
        return create_response(error=str(e), status=500)

    finally:
        db.close()
@transaction_bp.route("/split", methods=["POST"])
def split_transaction():
    """处理分账请求
    """
    try:
        logger.info("Connecting to database...")
        db.connect()

        logger.info("Parsing request data...")
        data = request.json
        logger.info(f"Request data: {data}")

        # 数据验证
        required_fields = ["item", "amount", "description", "transaction_date","category_id", "payer_id", "splitters"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.error(f"Missing fields: {missing_fields}")
            return create_response(error=f"Missing fields: {missing_fields}", status=400)

        # 验证 category_id 是否有效
        category = db.execute_query("SELECT * FROM Category WHERE category_ID = %s", (data["category_id"],))
        logger.info("%s",data["category_id"]),
        if not category:
            logger.error(f"Invalid category_id: {data['category_id']}")
            return create_response(error="Invalid category ID.", status=400)

        transaction_date = datetime.strptime(data["transaction_date"], "%Y-%m-%d").date()

        logger.info("Creating transaction..."),
        logger.info("Inserting transaction with data: item=%s, amount=%s, description=%s, transaction_date=%s, category_id=%s, payer_id=%s, split_count=%s",
            data["item"], data["amount"], data["description"], transaction_date, data["category_id"], data["payer_id"], len(data["splitters"]))
        transaction_id = db.create_transaction(
            item=data["item"],
            amount=data["amount"],
            description=data["description"],
            transaction_date=transaction_date,
            category_id=data["category_id"],
            payer_id=data["payer_id"],
            split_count=len(data["splitters"]),

            )
        logger.info(f"Transaction creation result: {transaction_id}")
        if not transaction_id:
            logger.error("Transaction creation failed: No transaction ID returned.")
            return create_response(error="Transaction creation failed.", status=500)

        logger.info("Creating split and debtor records...")
        split_amount = round(data["amount"] / len(data["splitters"]), 2)
        for debtor_id in data["splitters"]:
            # 将每笔分账信息写入 Split 表
            logger.info(f"Inserting split record for debtor_id={debtor_id}")
            db.execute_query(
                '''
                INSERT INTO split (transaction_ID, debtor_ID, payer_ID, amount)
                VALUES (%s, %s, %s, %s)
                ''',
                (transaction_id, debtor_id, data["payer_id"], split_amount)
            )

            # 将每笔债务信息写入 Transaction_Debtor 表
            logger.info(f"Inserting debtor record for transaction_id={transaction_id}, debtor_id={debtor_id}")
            db.execute_query(
                '''
                INSERT INTO transaction_debtor (transaction_ID, debtor_ID, amount)
                VALUES (%s, %s, %s)
                ''',
                (transaction_id, debtor_id, split_amount)
            )

        logger.info(f"Transaction {transaction_id} created successfully.")
        return create_response(
            message="Transaction created successfully.",
            data={"transaction_id": transaction_id},
            status=201,
        )

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return create_response(error=f"An unexpected error occurred: {str(e)}", status=500)
    finally:
        db.close()

@transaction_bp.route("/users", methods=["GET"])
def get_users():
    """返回测试用的用户列表
    """
    try:
        db.connect()
        users = [
            {"id": "6", "name": "testuser"},
            {"id": "13", "name": "monkey"},
            {"id": "14", "name": "monkey"},
        ]
        logger.info(f"Fetched users: {users}")
        return create_response(data=users, status=200)
    except Exception as e:
        logger.exception(f"Error fetching users: {e}")
        return create_response(error="Failed to fetch users.", status=500)
    finally:
        db.close()

@transaction_bp.route("/friends/<int:user_id>", methods=["GET"])
def get_friends(user_id):
    """返回用户的好友列表
    """
    try:
        db.connect()
        friends = db.get_friends_by_user_id(user_id)
        logger.info(f"Fetched friends for user {user_id}: {friends}")
        return create_response(data=friends, status=200)
    except Exception as e:
        logger.exception(f"Error fetching friends for user {user_id}: {e}")
        return create_response(error="Failed to fetch friends.", status=500)
    finally:
        db.close()

@transaction_bp.route("/categories", methods=["GET"])
def get_categories():
    """取得所有交易类别
    """
    try:
        db.connect()
        categories = db.execute_query("SELECT * FROM Category")
        if not categories:
            return create_response(message="No categories found.", status=404)
        return create_response(data=categories, status=200)
    except Exception as e:
        logger.exception(f"Error fetching categories: {e}")
        return create_response(error="Failed to fetch categories.", status=500)
    finally:
        db.close()


@transaction_bp.route("/transaction/", methods=["POST"])
def add_transaction():
    """
    新增交易 (例如在 /accounting 頁面用),
    預設付款人 payer_id = 使用者自己。
    排除自己在 splitters 裡面 (防止自己欠自己)。
    """
    try:
        db.connect()
        data = request.json
        # 檢查必填欄位
        required = ["item", "amount", "description", "transaction_date", "category_id", "payer_id", "splitters"]
        missing = [f for f in required if f not in data]
        if missing:
            return create_response(error=f"Missing fields: {missing}", status=400)

        payer_id = data["payer_id"]
        # 排除自己
        filtered_splitters = [d for d in data["splitters"] if d != payer_id]

        # 建立交易
        tx_id = db.create_transaction(
            item=data["item"],
            amount=data["amount"],
            description=data["description"],
            transaction_date=data["transaction_date"],
            category_id=data["category_id"],
            payer_id=payer_id,
            split_count=len(filtered_splitters)
        )

        if filtered_splitters:
            split_amount = round(float(data["amount"]) / len(filtered_splitters), 2)
            for debtor_id in filtered_splitters:
                db.create_transaction_debtor(tx_id, debtor_id, split_amount)

        return create_response(message="Transaction added successfully.", data={"transaction_id": tx_id}, status=201)
    except Exception as e:
        logger.exception("Error adding transaction: %s", e)
        return create_response(error="Failed to add transaction.", status=500)
    finally:
        db.close()

# ★ 修改點 (2)：分帳 (save_splits_for_existing_transactions)
@transaction_bp.route("/split/", methods=["POST"])
def save_splits_for_existing_transactions():
    """
    前端送來：
    {
      "splits": {
        "3": {"2": 25},
        "5": {"2": 25}
      },
      "transaction_ids": [10, 11]
    }
    預設只用 transaction_ids[0]，一筆筆插入 transaction_debtor & Split。
    """
    try:
        db.connect()
        data = request.json or {}

        splits = data.get("split")
        if not splits:
            return create_response(error="缺少 splits", status=400)

        tx_ids = data.get("transaction_ids", [])
        if not tx_ids:
            return create_response(error="缺少 transaction_ids", status=400)

        transaction_id = tx_ids[0]  # 全部都插到第一筆交易

        for debtorIdStr, creditorsDict in splits.items():
            debtor_id = int(debtorIdStr)
            for payerIdStr, amountVal in creditorsDict.items():
                payer_id = int(payerIdStr)

                # 寫入 transaction_debtor
                db.execute_query(
                    """
                    INSERT INTO transaction_debtor ("transaction_id", "debtor_id", "amount")
                    VALUES (%s, %s, %s)
                    """,
                    (transaction_id, debtor_id, float(amountVal))
                )

                # 同步插入 split (若想留更完整紀錄)
                db.execute_query(
                    """
                    INSERT INTO "split" ("transaction_id", "debtor_id", "payer_id", "amount")
                    VALUES (%s, %s, %s, %s)
                    """,
                    (transaction_id, debtor_id, payer_id, float(amountVal))
                )

        return create_response(message="split saved successfully.", status=201)

    except Exception as e:
        logger.exception(f"Error saving splits: {e}")
        return create_response(error=f"儲存 splits 失敗: {str(e)}", status=500)

    finally:
        db.close()

@transaction_bp.route("/split-bulk/", methods=["POST"])
def save_split_lines():
    """
    前端傳來:
    {
      "lines": [
        { "transactionId": 10, "debtorId": 3, "payerId": 2, "amount": 100 },
        { "transactionId": 11, "debtorId": 5, "payerId": 2, "amount": 25 },
        ...
      ]
    }
    逐筆 INSERT 到 transaction_debtor + split
    """
    try:
        db.connect()
        data = request.json or {}
        lines = data.get("lines", [])

        if not lines:
            return create_response(error="No split lines provided", status=400)

        for line in lines:
            tx_id = line["transactionId"]
            debtor_id = line["debtorId"]
            payer_id = line["payerId"]
            amt = float(line["amount"])

            # (1) transaction_debtor
            db.execute_query(
                """
                INSERT INTO transaction_debtor ("transaction_id", "debtor_id", "amount")
                VALUES (%s, %s, %s)
                """,
                (tx_id, debtor_id, amt)
            )

            # (2) split (小寫 s，確保和 schema.sql 裡的表名一致)
            db.execute_query(
                """
                INSERT INTO split ("transaction_id", "debtor_id", "payer_id", "amount")
                VALUES (%s, %s, %s, %s)
                """,
                (tx_id, debtor_id, payer_id, amt)
            )

        return create_response(message="Split lines saved successfully!", status=201)

    except Exception as e:
        logging.exception(f"Error saving split lines: {e}")
        return create_response(error=f"Split lines save failed: {str(e)}", status=500)
    finally:
        db.close()

if __name__ == "__main__":
    app.run(debug=True)

