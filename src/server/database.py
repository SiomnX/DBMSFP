import os
import psycopg2
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor
import redis

class Database:
    def __init__(self):
        try:
            # 從環境變數獲取 DATABASE_URL
            database_url = os.getenv("DATABASE_URL")
            self.connection = psycopg2.connect(database_url)
            print("init: Connected to the database successfully!")
        except OperationalError as e:
            print(f"init: Error connecting to database: {e}")
            self.connection = None
            
        self.redis_client = None  # 添加 Redis 連線變數

    def connect(self):
        """建立資料庫連線"""
        if self.connection is None:
            try:
                self.connection = psycopg2.connect(
                    dbname="mydatabase",       # 資料庫名稱
                    user="postgres",          # 使用者名稱
                    password="postgres",      # 使用者密碼
                    host="db",                # 主機名稱（Docker 服務名稱）
                    port="5432"               # 資料庫端口
                )
                self.connection.autocommit = True
                print("connect: Connected to the database successfully!")
            except Exception as e:
                print(f"Error connecting to database: {e}")
                
        """建立redis連線"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.StrictRedis(
                    host="redis",  # Redis 主機名稱（Docker 服務名稱）
                    port=6379,     # Redis 預設端口
                    decode_responses=True  # 自動解碼字串
                )
                print("Connected to database and Redis successfully", flush = True)
            except Exception as e:
                print(f"Error connecting to Redis: {e}",  flush = True)
                self.connection.autocommit = True

    def execute_query(self, query, params=None):
        """執行 SQL 查詢"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                self.connection.commit();
                if cursor.description:  # 如果是查詢語句
                   return cursor.fetchall()  # 返回結果
                return None  # 非查詢語句 (如 INSERT, UPDATE)
        except Exception as e:
            print(f"Error executing query: {e}")
            return None

    def close(self):
        """關閉資料庫連線"""
        if self.connection:
            self.connection.close()
            self.connection = None

    # ------------------ User 表相關操作 ------------------
    #新增使用者
    def add_user(self, name, email, pwd_hash):
        """新增用戶"""
        # 檢查使用者是否已存在
        query = "SELECT * FROM \"User\" WHERE name = %s"
        existing_user = self.execute_query(query, (name,))
        if existing_user:
            return None  # 使用者已存在，返回 None

        query = """
        INSERT INTO "User" (name, email, pwd_hash, credit_score)
        VALUES (%s, %s, %s, 0)
        RETURNING user_ID
        """
        result = self.execute_query(query, (name, email, pwd_hash))
        return result[0]["user_id"] if result else None

    #刪除使用者
    def delete_user(self, user_id):
        """刪除用戶"""
        query = "DELETE FROM \"User\" WHERE user_ID = %s"
        self.execute_query(query, (user_id,))

    #用ID獲得使用者資料
    def get_user_by_id(self, user_id):
        """根據用戶 ID 查詢用戶資料"""
        query = """
        SELECT * FROM "User" WHERE user_ID = %s
        """
        result = self.execute_query(query, (user_id,))
        if result:
            return result[0]  # 返回第一條結果
        return None  # 如果找不到用戶，返回 None

    #更新用戶信用積分
    def update_credit_score(self, user_id, new_score):
        """更新用戶信用分數"""
        query = "UPDATE \"User\" SET credit_score = %s WHERE user_ID = %s"
        self.execute_query(query, (new_score, user_id))

    # ------------------ Friend_List 表相關操作 ------------------
    #新增好友
    def create_friend(self, user_id, friend_id, nickname):
        """新增好友關係"""
        query = """
        INSERT INTO Friend_List (user_ID, friend_ID, nickname)
        VALUES (%s, %s, %s)
        RETURNING list_ID
        """
        result = self.execute_query(query, (user_id, friend_id, nickname))
        return result[0]["list_id"] if result else None
    #刪除好友
    def delete_friend(self, list_id):
        """刪除好友關係"""
        query = "DELETE FROM Friend_List WHERE list_ID = %s"
        self.execute_query(query, (list_id,))
    #查詢好友列表
    def get_friends_by_user_id(self, user_id):
        """根據用戶 ID 查詢該用戶的所有好友資料"""
        query = """
        SELECT * FROM Friend_List WHERE user_ID = %s
        """
        result = self.execute_query(query, (user_id,))
        if result:
            return result  # 返回所有好友資料
        return None  # 如果找不到朋友資料，返回 None

    # ------------------ Category 表相關操作 ------------------
    def create_category(self, category_name):
        """新增交易類別"""
        query = """
        INSERT INTO Category (category_name)
        VALUES (%s)
        RETURNING category_ID
        """
        result = self.execute_query(query, (category_name,))
        return result[0]["category_id"] if result else None

    def delete_category(self, category_id):
        """刪除交易類別"""
        query = "DELETE FROM Category WHERE category_ID = %s"
        self.execute_query(query, (category_id,))

    def get_category_by_id(self, category_id):
        """根據交易類別 ID 查詢類別資訊"""
        query = """
        SELECT * FROM Category WHERE category_ID = %s
        """
        result = self.execute_query(query, (category_id,))
        logger.info(f"Category ID type: {type(category_id)} - Value: {category_id}")
        if result:
            return result[0]  # 返回查詢結果的第一條資料（該類別的資訊）
        return None  # 如果找不到該類別，返回 None


    # ------------------ Transaction 表相關操作 ------------------
    def create_transaction(self, item, amount, description, transaction_date, category_id, payer_id, split_count):
        """新增交易"""
        query = """
        INSERT INTO Transaction (item, amount, description, transaction_date, category_ID, payer_ID, split_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING transaction_ID
        """
        result = self.execute_query(query, (item, amount, description, transaction_date, category_id, payer_id, split_count))
        return result[0]["transaction_id"] if result else None

    def delete_transaction(self, transaction_id):
        """刪除交易"""
        query = "DELETE FROM Transaction WHERE transaction_ID = %s"
        self.execute_query(query, (transaction_id,))

    def get_transaction_by_id(self, transaction_id):
        """根據交易 ID 查詢交易資料"""
        query = """
        SELECT * FROM Transaction WHERE transaction_ID = %s
        """
        result = self.execute_query(query, (transaction_id,))
        if result:
            return result[0]  # 返回交易的第一條結果，即該交易的詳細資料
        return None  # 如果找不到交易資料，返回 None


    def get_all_transactions(self):
        query = "SELECT * FROM Transaction"
        return self.execute_query(query)

# ------------------ Transaction_Debtor 表相關操作 ------------------

    def create_transaction_debtor(self, transaction_id, debtor_id, amount):
        """新增交易債務關係"""
        query = """
        INSERT INTO Transaction_Debtor (transaction_ID, debtor_ID, amount)
        VALUES (%s, %s, %s)
        """
        self.execute_query(query, (transaction_id, debtor_id, amount))

    def delete_transaction_debtor(self, transaction_id, debtor_id):
        """刪除交易債務關係"""
        query = "DELETE FROM Transaction_Debtor WHERE transaction_ID = %s AND debtor_ID = %s"
        self.execute_query(query, (transaction_id, debtor_id))

    def get_debtors_by_transaction_id(self, transaction_id):
        """根據交易 ID 查詢該交易的所有債務人資訊"""
        query = """
        SELECT u.user_ID, u.name, u.email, td.amount
        FROM Transaction_Debtor td
        JOIN "User" u ON td.debtor_ID = u.user_ID
        WHERE td.transaction_ID = %s;
        """
        result = self.execute_query(query, (transaction_id,))
        if result:
            return result  # 返回所有債務人資訊
        return None  # 如果找不到債務人資料，返回 None

    def update_debt_amount(self, transaction_id, debtor_id, new_amount):
        """更新債務人的債務金額"""
        query = """
        UPDATE Transaction_Debtor
        SET amount = %s
        WHERE transaction_ID = %s AND debtor_ID = %s
        """
        self.execute_query(query, (new_amount, transaction_id, debtor_id))

# ------------------ Split 表相關操作 ------------------
    def create_split(self, transaction_id, debtor_id, payer_id, amount):
        """新增分帳資訊"""
        query = """
        INSERT INTO Split (transaction_ID, debtor_ID, payer_ID, amount)
        VALUES (%s, %s, %s, %s)
        RETURNING split_ID
        """
        result = self.execute_query(query, (transaction_id, debtor_id, payer_id, amount))
        return result[0]["split_id"] if result else None

    def delete_split(self, split_id):
        """刪除分帳資訊"""
        query = "DELETE FROM Split WHERE split_ID = %s"
        self.execute_query(query, (split_id,))

    def get_splits_by_transaction_id(self, transaction_id):
        """根據交易 ID 查詢該交易的所有分帳資訊"""
        query = """
        SELECT split_ID, transaction_ID, debtor_ID, payer_ID, amount
        FROM Split
        WHERE transaction_ID = %s;
        """
        result = self.execute_query(query, (transaction_id,))
        if result:
            return result  # 返回所有分帳資訊
        return None  # 如果找不到分帳資料，返回 None
    def update_split_amount(self, transaction_id, debtor_id, new_amount):
        """根據交易 ID 和債務人 ID 更新分帳金額"""
        query = """
        UPDATE Split
        SET amount = %s
        WHERE transaction_ID = %s AND debtor_ID = %s;
        """
        self.execute_query(query, (new_amount, transaction_id, debtor_id))
        
        
    # ------------------ LeaderBoard 表相關操作-----------------
    def update_leaderboard_in_redis(self):
        """從資料庫更新 Redis 排行榜數據"""
        # 定義 SQL 查詢語句，用於從 "User" 表中獲取前 100 名的用戶數據
        query = """
        SELECT user_id, name, credit_score
        FROM "User"
        ORDER BY credit_score DESC
        LIMIT 100;
        """
        try:
            result = self.execute_query(query) # 執行 SQL 查詢
            if result:          # 如果查詢有結果，則更新 Redis 中的排行榜數據
                if not self.redis_client: # 確保 Redis 連接已初始化
                    raise Exception("Redis client not initialized", flush = True)
            
                self.redis_client.delete("leaderboard") # 清空 Redis 中舊的排行榜數據
            
                for user in result: # 插入新的排行榜數據
                    self.redis_client.zadd(
                        "leaderboard", 
                        {f"{user['name']}|{user['user_id']}": user['credit_score']}
                    )
        except Exception as e: # 如果發生異常，印錯誤信息
            print(f"Error updating leaderboard in Redis: {e}", flush = True)
    
    def get_leaderboard_from_redis(self, limit=10):
        """從 Redis 查詢排行榜"""
        try:
            leaderboard = self.redis_client.zrevrange("leaderboard", 0, limit - 1, withscores=True) # 從 Redis 中以分數倒序獲取排行榜數據，返回前 limit 名
            print(f"Leaderboard from Redis: {leaderboard}")  # 印從 Redis 獲取的數據
            return leaderboard # 返回排行榜數據
        except Exception as e:
            print(f"Error fetching leaderboard from Redis: {e}")
            return []


db = Database()
