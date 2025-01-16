from flask_bcrypt import Bcrypt
from database import Database  # 從 database 資料夾引入資料庫模組

bcrypt = Bcrypt()

# def create_account(username, password, email):
#     try:
#         # 密碼加密
#         hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

#         db = Database()
#         # 建立資料庫連線
#         # conn = db.connect()

#         if conn is None:
#             print("Failed to connect to the database.")
#         else:
#             cursor = conn.cursor()

#             # 建立使用者資料表（如果不存在的話）
#             cursor.execute('''
#             CREATE TABLE IF NOT EXISTS User (
#                 user_id INTEGER PRIMARY KEY,
#                 name TEXT UNIQUE,
#                 email TEXT UNIQUE,
#                 pwd_hash TEXT,
#                 credit_score INTEGER
#             )
#             ''')
            
#             # 確認使用者是否已存在
#             cursor.execute('SELECT * FROM User WHERE name = ?', (username,))
#             existing_user = cursor.fetchone()

#             if existing_user:
#                 conn.close()
#                 return {'error': 'Username already exists'}

#             # 新增帳號到資料庫
#             db.add_user(username, hashed_password, email)
            
#             # 提交變更
#             conn.commit()

#             # 關閉連線
#             conn.close()
#             return {'message': 'Account created'}
#     except Exception as e:
#         return {'error': f'An error occurred: {str(e)}'}

def create_account(username, password, email):
    try:
        db = Database()
        conn = db.connect()

        if conn is None:
            return {'error': 'Failed to connect to the database'}
        
        # 密碼加密
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # 新增帳號到資料庫
        user_id = db.add_user(username, email, hashed_password)
        
        if user_id is None:
            return {'error': 'Username already exists or failed to create account'}
        
        # 關閉資料庫連線
        db.close()
        return {'message': 'Account created successfully'}

    except Exception as e:
        return {'error': f'An error occurred: {str(e)}'}
