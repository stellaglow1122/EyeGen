from datetime import datetime
import pytz
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError, DuplicateKeyError

client = MongoClient("mongodb://mongo:27017/", serverSelectionTimeoutMS=5000)
db = client["ophthalmology_db"]
line_dialogue_report_coll = db["line_dialogue_report"]
line_comment_coll = db["line_comment"]
users_coll = db["users"]

try:
    line_dialogue_report_coll.create_index("idx", unique=True)
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
        if not idx or idx.strip() == "":
            print("Invalid idx provided")
            return False
        if not user_name or user_name.strip() == "":
            print("Invalid user_name provided")
            return False
        if not comment_content.strip() or comment_score == 0:
            print(f"Comment submission skipped: empty content or zero score")
            return False
        data = {
            "idx": idx,
            "user_name": user_name,
            "comment_content": comment_content.strip(),
            "comment_score": comment_score,
            "comment_time": comment_time
        }
        import_line_comment_to_mongo(data)
        return True
    except Exception as e:
        print(f"Error submitting comment for idx {idx}: {e}")
        raise

def import_line_dialogue_report_to_mongo(data, request_id=None):
    idx = data.get("idx")
    print(f"Importing data for idx: {idx} into line_dialogue_report")
    try:
        if "idx" not in data:
            raise ValueError("Data must contain 'idx' field")
        existing_doc = line_dialogue_report_coll.find_one({"idx": idx})
        if existing_doc:
            print(f"[{idx}] already exists in line_dialogue_report")
            return False
        taipei_tz = pytz.timezone("Asia/Taipei")
        data["upload_time"] = data.get("upload_time", datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S"))
        for field in ["comment_content", "comment_score", "comment_state", "comment_time", "username", "comments"]:
            data.pop(field, None)
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
    idx = data.get("idx")
    user_name = data.get("user_name")
    print(f"Importing comment for idx: {idx} by user: {user_name} into line_comment")
    try:
        if "idx" not in data or not data["idx"]:
            raise ValueError("Data must contain a valid 'idx' field")
        if "user_name" not in data or not data["user_name"]:
            raise ValueError("Data must contain a valid 'user_name' field")
        line_comment_coll.insert_one(data)
        print(f"Inserted new comment for idx: {idx} by user: {user_name}")
        return True
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error importing comment for idx {idx}: {e}")
        raise

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