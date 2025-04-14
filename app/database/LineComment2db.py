from datetime import datetime
import pytz
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError, DuplicateKeyError

client = MongoClient("mongodb://mongo:27017/", serverSelectionTimeoutMS=5000)  # 5秒超時
db = client["ophthalmology_db"]
line_dialogue_report_coll = db["line_dialogue_report"]  # 用於儲存對話和報告
line_comment_coll = db["line_comment"]  # 用於儲存評論
users_coll  = db["users"] # 用於儲存user的帳號與密碼

# 確保 idx 欄位有唯一索引（僅對 line_dialogue_report）
try:
    line_dialogue_report_coll.create_index("idx", unique=True)
    # 檢查並移除 line_comment 的 idx 唯一索引（如果存在）
    indexes = line_comment_coll.index_information()
    if "idx_1" in indexes:
        line_comment_coll.drop_index("idx_1")
        print("Dropped idx_1 index from line_comment collection")
    else:
        print("idx_1 index not found in line_comment collection, no action needed")
except OperationFailure as e:
    print(f"Error managing indexes: {e}")

def get_line_list(refresh=False):
    print("Fetching line list from MongoDB (line_dialogue_report)")
    try:
        return list(line_dialogue_report_coll.find({}, {"_id": 0}))
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error fetching line list: {e}")
        raise

def get_line_by_idx(idx):
    print(f"Fetching line by idx: {idx} from line_dialogue_report")
    try:
        doc = line_dialogue_report_coll.find_one({"idx": idx}, {"_id": 0})
        return doc
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error fetching line by idx {idx}: {e}")
        raise

def get_comments_by_idx(idx):
    print(f"Fetching comments by idx: {idx} from line_comment")
    try:
        comments = list(line_comment_coll.find({"idx": idx}, {"_id": 0}))
        return comments
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error fetching comments by idx {idx}: {e}")
        raise

def submit_comment(idx, comment_content, comment_score, comment_time, user_name):
    print(f"Submitting comment for idx: {idx} by user: {user_name}")
    try:
        # 檢查 comment_content 非空且 comment_score 不為 0
        if not comment_content.strip() or comment_score == 0:
            print(f"Comment submission skipped: empty content or zero score")
            return False

        # 準備資料並插入
        data = {
            "idx": idx,
            "user_name": user_name,
            "comment_content": comment_content,
            "comment_score": comment_score,
            "comment_time": comment_time
        }
        import_line_comment_to_mongo(data)
        return True
    except Exception as e:
        print(f"Error submitting comment for idx {idx}: {e}")
        raise

def import_line_dialogue_report_to_mongo(data, request_id=None):
    """
    Import a line dialogue report into MongoDB (line_dialogue_report collection), preventing duplicate idx.
    """
    idx = data.get("idx")
    print(f"Importing data for idx: {idx} into line_dialogue_report")
    try:
        if "idx" not in data:
            raise ValueError("Data must contain 'idx' field")

        # 檢查 idx 是否已存在
        existing_doc = line_dialogue_report_coll.find_one({"idx": idx})
        if existing_doc:
            print(f"[{idx}] already exists in line_dialogue_report")
            return False

        # 添加必要的欄位（如果不存在）
        taipei_tz = pytz.timezone("Asia/Taipei")
        data["upload_time"] = data.get("upload_time", datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S"))
        # 移除不需要的欄位
        for field in ["comment_content", "comment_score", "comment_state", "comment_time", "username", "comments"]:
            data.pop(field, None)

        # 插入新資料
        line_dialogue_report_coll.insert_one(data)
        print(f"Successfully inserted idx: {idx} into line_dialogue_report")
        return True
    except DuplicateKeyError as e:
        print(f"[{idx}] already exists in line_dialogue_report (DuplicateKeyError: {e})")
        return False
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error importing data for idx {idx} into line_dialogue_report: {e}")
        raise

def import_line_comment_to_mongo(data):
    """
    Import a comment into MongoDB (line_comment collection).
    Always insert a new row for each comment submission.
    """
    idx = data.get("idx")
    user_name = data.get("user_name")
    print(f"Importing comment for idx: {idx} by user: {user_name} into line_comment")
    try:
        if "idx" not in data or "user_name" not in data:
            raise ValueError("Data must contain 'idx' and 'user_name' fields")

        # 直接插入新記錄，不檢查唯一性
        line_comment_coll.insert_one(data)
        print(f"Inserted new comment for idx: {idx} by user: {user_name}")
        return True
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error importing comment for idx {idx}: {e}")
        raise

# 清除集合
def clear_line_dialogue_report_collection(confirm=False):
    if not confirm:
        print("Clear operation aborted: confirm parameter must be True")
        return False

    print("Clearing line_dialogue_report collection")
    try:
        result = line_dialogue_report_coll.delete_many({})
        print(f"Successfully cleared {result.deleted_count} documents from line_dialogue_report collection")
        return True
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error clearing line_dialogue_report collection: {e}")
        raise

def clear_line_comment_collection(confirm=False):
    if not confirm:
        print("Clear operation aborted: confirm parameter must be True")
        return False

    print("Clearing line_comment collection")
    try:
        result = line_comment_coll.delete_many({})
        print(f"Successfully cleared {result.deleted_count} documents from line_comment collection")
        return True
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error clearing line_comment collection: {e}")
        raise

def clear_users_collection(confirm=False):
    if not confirm:
        print("Clear operation aborted: confirm parameter must be True")
        return False

    print("Clearing users collection")
    try:
        result = users_coll.delete_many({})
        print(f"Successfully cleared {result.deleted_count} documents from users collection")
        return True
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error clearing users collection: {e}")
        raise

# 列印前 5 筆資料和總長度
def print_top_5_and_len(collection_name="line_dialogue_report"):
    coll = line_dialogue_report_coll if collection_name == "line_dialogue_report" else line_comment_coll
    print(f"Fetching top 5 documents from {collection_name} collection")
    try:
        total_length = coll.count_documents({})
        print(f"Total documents in {collection_name} collection: {total_length}")
        top_5 = list(coll.find({}, {"_id": 0}).sort("upload_time", -1).limit(5))
        print(f"Top 5 documents (sorted by upload_time, descending) from {collection_name}:")
        for i, doc in enumerate(top_5, 1):
            print(f"{i}. {doc}")
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error printing top 5 documents from {collection_name}: {e}")
        raise