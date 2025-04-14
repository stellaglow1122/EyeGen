from pymongo import MongoClient

# 連接到 MongoDB
client = MongoClient("mongodb://ophthalmology_db_container:27017/")
db = client["ophthalmology_db"]
users_collection = db["users"]

# 準備 user1 到 user50 的使用者資料
users = [
    {"username": f"user{i}", "password": f"user{i}"}
    for i in range(1, 50)
]

# 插入資料
def insert_users():
    try:
        # 清空現有 users 集合（可選）
        users_collection.delete_many({})
        # 插入新資料
        users_collection.insert_many(users)
        print(f"Successfully inserted {len(users)} users.")
    except Exception as e:
        print(f"Error inserting users: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    insert_users()