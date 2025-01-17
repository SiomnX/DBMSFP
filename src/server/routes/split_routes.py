from flask import Flask, request, jsonify
from flask import Blueprint
from database import Database
from dotenv import load_dotenv
from flask_cors import CORS
from datetime import datetime
import logging

load_dotenv()

db = Database()  # 你自己的 Database 類別
db.connect()

split_bp = Blueprint('split_routes', __name__)

@split_bp.route("/", methods=["GET"])
def get_splits():
    """
    從資料庫中獲取所有分帳紀錄。
    """
    try:
        db.connect()

        # SQL 查詢語句
        query = """
            SELECT
                s."split_id",
                s."transaction_id",
                s."debtor_id",
                s."payer_id",
                s."amount",
                t."item" AS "transaction_item",
                t."description" AS "transaction_description"
            FROM "split" s
            LEFT JOIN "transaction" t
                ON s."transaction_id" = t."transaction_id"
        """
        results = db.execute_query(query)
        print("Fetched results:", results)

        if not results:
            return jsonify({"message": "No data found", "data": []}), 200


        return jsonify({"data": results}), 200

    except Exception as e:
        logging.exception(f"無法取得分帳紀錄: {e}")
        return jsonify({"error": f"伺服器錯誤: {str(e)}"}), 500

    finally:
        db.close()


@split_bp.route("/splits/", methods=["POST"])
def create_splits():
    try:
        new_splits = request.json  # 預期是一個陣列

        db.connect()
        for line in new_splits:
            tx_id = line["transactionId"]
            debtor_id = line["debtorId"]
            payer_id = line["payerId"]
            amt = float(line["amount"])

            # ★ INSERT 時，同樣要對 "transaction_ID", "debtor_ID" 等加雙引號
            db.execute_query("""
                INSERT INTO "Split" ("transaction_ID", "debtor_ID", "payer_ID", "amount")
                VALUES (%s, %s, %s, %s)
            """, (tx_id, debtor_id, payer_id, amt))

        return jsonify({"message": "split lines inserted successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()
