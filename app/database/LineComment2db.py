from datetime import datetime, timedelta
import pytz
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError, DuplicateKeyError

client = MongoClient("mongodb://mongo:27017/", serverSelectionTimeoutMS=5000)  # 5秒超時
db = client["ophthalmology_db"]
collection = db["line_comment"]

# 確保 idx 欄位有唯一索引
try:
    collection.create_index("idx", unique=True)
except OperationFailure as e:
    print(f"Error creating index on idx: {e}")

def get_line_list(refresh=False):
    print("Fetching line list from MongoDB")
    try:
        return list(collection.find({}, {"_id": 0}))
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error fetching line list: {e}")
        raise

def get_line_by_idx(idx, refresh=False):
    print(f"Fetching line by idx: {idx}")
    try:
        return collection.find_one({"idx": idx}, {"_id": 0})
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error fetching line by idx {idx}: {e}")
        raise

def lock_report(idx, session_id):
    print(f"Attempting to lock idx: {idx} for session: {session_id}")
    try:
        doc = collection.find_one({"idx": idx}, {"_id": 0})
        lock_info = doc.get("lock_info", {"locked": False, "session_id": "", "lock_time": 0})

        # 檢查鎖定時間是否超過 300 秒
        if lock_info.get("locked", False) and lock_info.get("lock_time", 0) > 0:
            current_time = datetime.now().timestamp()  # UTC 時間戳（秒）
            time_diff = current_time - lock_info["lock_time"]
            if time_diff > 300:  # 300 秒
                print(f"Lock on idx {idx} has expired (locked for {time_diff:.1f} seconds). Releasing lock.")
                # 自動解鎖
                collection.update_one(
                    {"idx": idx},
                    {"$set": {"lock_info": {"locked": False, "session_id": "", "lock_time": 0}}}
                )
                lock_info = {"locked": False, "session_id": "", "lock_time": 0}

        # 如果已鎖定，檢查是否是當前 session
        if lock_info.get("locked", False):
            if lock_info.get("session_id") == session_id:
                print(f"idx {idx} is already locked by this session: {session_id}")
                return True  # 允許繼續操作
            else:
                print(f"idx {idx} is already locked by another session: {lock_info.get('session_id')}")
                return False  # 不允許鎖定

        # 如果未鎖定，設置鎖定並記錄鎖定時間
        current_time = datetime.now().timestamp()  # UTC 時間戳（秒）
        result = collection.update_one(
            {"idx": idx, "lock_info.locked": {"$ne": True}},  # 確保未被鎖定
            {"$set": {"lock_info": {"locked": True, "session_id": session_id, "lock_time": current_time}}}
        )
        if result.modified_count == 0:
            print(f"Failed to lock idx {idx}: already locked by another process")
            return False
        print(f"Locked idx: {idx} for session: {session_id} at timestamp {current_time}")
        return True
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error locking idx {idx}: {e}")
        raise

def unlock_report(idx):
    print(f"Unlocking idx: {idx}")
    try:
        collection.update_one(
            {"idx": idx},
            {"$set": {"lock_info": {"locked": False, "session_id": "", "lock_time": 0}}}
        )
        print(f"Unlocked idx: {idx}")
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error unlocking idx {idx}: {e}")
        raise

def submit_comment(idx, comment_content, comment_score, comment_state, comment_time):
    print(f"Submitting comment for idx: {idx}")
    try:
        collection.update_one(
            {"idx": idx},
            {
                "$set": {
                    "comment_content": comment_content,
                    "comment_score": comment_score,
                    "comment_state": comment_state,
                    "comment_time": comment_time
                }
            }
        )
        print(f"Comment submitted for idx: {idx}")
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error submitting comment for idx {idx}: {e}")
        raise
    finally:
        unlock_report(idx)

# 匯入資料到 MongoDB
def import_line_comment_to_mongo(data):
    """
    Import a line comment data into MongoDB, preventing duplicate idx.

    Parameters:
    - data (dict): The data to import (e.g., {"idx": ..., "user_type": ..., ...})

    Returns:
    - bool: True if successful, False if idx already exists, raises an exception on other failures
    """
    print(f"Importing data for idx: {data.get('idx')}")
    try:
        # 檢查必要欄位
        if "idx" not in data:
            raise ValueError("Data must contain 'idx' field")

        # 檢查 idx 是否已存在
        existing_doc = collection.find_one({"idx": data["idx"]})
        if existing_doc:
            print(f"[{data['idx']}] already exists")
            return False

        # 添加必要的欄位（如果不存在）
        taipei_tz = pytz.timezone("Asia/Taipei")
        data["upload_time"] = data.get("upload_time", datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S"))
        data["comment_content"] = data.get("comment_content", "")
        data["comment_score"] = data.get("comment_score", 0)
        data["comment_state"] = data.get("comment_state", "N")
        data["comment_time"] = data.get("comment_time", "")
        data["lock_info"] = data.get("lock_info", {"locked": False, "session_id": "", "lock_time": 0})

        # 插入新資料
        collection.insert_one(data)
        print(f"Successfully inserted idx: {data['idx']}")
        return True
    except DuplicateKeyError as e:
        print(f"[{data.get('idx')}] already exists (DuplicateKeyError: {e})")
        return False
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error importing data for idx {data.get('idx')}: {e}")
        raise

# 清除集合
def clear_line_comment_collection(confirm=False):
    """
    Clear all documents in the line_comment collection.

    Parameters:
    - confirm (bool): Must be True to proceed with clearing the collection

    Returns:
    - bool: True if successful, raises an exception on failure
    """
    if not confirm:
        print("Clear operation aborted: confirm parameter must be True")
        return False

    print("Clearing line_comment collection")
    try:
        result = collection.delete_many({})
        print(f"Successfully cleared {result.deleted_count} documents from line_comment collection")
        return True
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error clearing line_comment collection: {e}")
        raise

# 列印前 5 筆資料和總長度
def print_top_5_and_len():
    """
    Print the top 5 documents (sorted by upload_time) and the total length of the line_comment collection.
    """
    print("Fetching top 5 documents from line_comment collection")
    try:
        # 獲取總長度
        total_length = collection.count_documents({})
        print(f"Total documents in line_comment collection: {total_length}")

        # 獲取前 5 筆資料，按 upload_time 降序排序
        top_5 = list(collection.find({}, {"_id": 0}).sort("upload_time", -1).limit(5))
        print("Top 5 documents (sorted by upload_time, descending):")
        for i, doc in enumerate(top_5, 1):
            print(f"{i}. {doc}")
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error printing top 5 documents: {e}")
        raise