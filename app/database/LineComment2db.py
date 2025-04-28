from datetime import datetime
import pytz
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError, DuplicateKeyError

client = MongoClient("mongodb://mongo:27017/", serverSelectionTimeoutMS=5000)
db = client["ophthalmology_db"]
line_dialogue_report_coll = db["line_dialogue_report"]
line_dialogue_comment_coll = db["line_dialogue_comment"]
line_report_comment_coll = db["line_report_comment"]
users_coll = db["users"]

try:
    line_dialogue_report_coll.create_index("idx", unique=True)
    # 為新集合設置索引（非唯一）
    line_dialogue_comment_coll.create_index("idx")
    line_report_comment_coll.create_index("idx")
    # print("Indexes created for line_dialogue_comment and line_report_comment")
except OperationFailure as e:
    print(f"Error managing indexes: {e}")

def get_line_list(refresh=False):
    # print("Fetching line list from MongoDB (line_dialogue_report)")
    try:
        return list(line_dialogue_report_coll.find({}, {"_id": 0}))
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error fetching line list: {e}")
        raise

def get_line_by_idx(idx):
    # print(f"Fetching line by idx: {idx} from line_dialogue_report")
    try:
        doc = line_dialogue_report_coll.find_one({"idx": idx}, {"_id": 0})
        return doc
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error fetching line by idx {idx}: {e}")
        raise

def get_dialogue_comments_by_idx(idx):
    # print(f"Fetching dialogue comments by idx: {idx} from line_dialogue_comment")
    try:
        comments = list(line_dialogue_comment_coll.find({"idx": idx}, {"_id": 0}))
        return comments
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error fetching dialogue comments by idx {idx}: {e}")
        raise

def get_report_comments_by_idx(idx):
    # print(f"Fetching report comments by idx: {idx} from line_report_comment")
    try:
        comments = list(line_report_comment_coll.find({"idx": idx}, {"_id": 0}))
        return comments
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error fetching report comments by idx {idx}: {e}")
        raise

def submit_dialogue_comment(idx, dialogue_comment_content, dialogue_comment_score, dialogue_comment_time, user_name):
    # print(f"Submitting dialogue comment for idx: {idx} by user: {user_name}")
    try:
        if not idx or idx.strip() == "":
            print("Invalid idx provided")
            return False
        if not user_name or user_name.strip() == "":
            print("Invalid user_name provided")
            return False
        if not dialogue_comment_content.strip() or dialogue_comment_score == 0:
            print(f"Dialogue comment submission skipped: empty content or zero score")
            return False
        data = {
            "idx": idx,
            "user_name": user_name,
            "dialogue_comment_content": dialogue_comment_content.strip(),
            "dialogue_comment_score": dialogue_comment_score,
            "dialogue_comment_time": dialogue_comment_time
        }
        line_dialogue_comment_coll.insert_one(data)
        # print(f"Inserted dialogue comment for idx: {idx} by user: {user_name}")
        return True
    except Exception as e:
        print(f"Error submitting dialogue comment for idx {idx}: {e}")
        raise

def submit_report_comment(idx, report_comment_content, report_comment_score, report_comment_time, user_name):
    # print(f"Submitting report comment for idx: {idx} by user: {user_name}")
    try:
        if not idx or idx.strip() == "":
            print("Invalid idx provided")
            return False
        if not user_name or user_name.strip() == "":
            print("Invalid user_name provided")
            return False
        if not report_comment_content.strip() or report_comment_score == 0:
            print(f"Report comment submission skipped: empty content or zero score")
            return False
        data = {
            "idx": idx,
            "user_name": user_name,
            "report_comment_content": report_comment_content.strip(),
            "report_comment_score": report_comment_score,
            "report_comment_time": report_comment_time
        }
        line_report_comment_coll.insert_one(data)
        # print(f"Inserted report comment for idx: {idx} by user: {user_name}")
        return True
    except Exception as e:
        print(f"Error submitting report comment for idx {idx}: {e}")
        raise

def import_line_dialogue_report_to_mongo(data, request_id=None):
    idx = data.get("idx")
    # print(f"Importing data for idx: {idx} into line_dialogue_report")
    try:
        if "idx" not in data:
            raise ValueError("Data must contain 'idx' field")
        existing_doc = line_dialogue_report_coll.find_one({"idx": idx})
        if existing_doc:
            print(f"[{idx}] already exists in line_dialogue_report")
            return False
        line_dialogue_report_coll.insert_one(data)
        # print(f"Successfully inserted idx: {idx} into line_dialogue_report")
        return True
    except DuplicateKeyError as e:
        print(f"[{idx}] already exists in line_dialogue_report (DuplicateKeyError: {e})")
        return False
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error importing data for idx {idx} into line_dialogue_report: {e}")
        raise

def clear_line_dialogue_comment_collection(confirm=False):
    if not confirm:
        print("Clear operation aborted: confirm parameter must be True")
        return False
    print("Clearing line_dialogue_comment collection")
    try:
        result = line_dialogue_comment_coll.delete_many({})
        print(f"Successfully cleared {result.deleted_count} documents from line_dialogue_comment collection")
        return True
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error clearing line_dialogue_comment collection: {e}")
        raise

def clear_line_report_comment_collection(confirm=False):
    if not confirm:
        print("Clear operation aborted: confirm parameter must be True")
        return False
    print("Clearing line_report_comment collection")
    try:
        result = line_report_comment_coll.delete_many({})
        print(f"Successfully cleared {result.deleted_count} documents from line_report_comment collection")
        return True
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error clearing line_report_comment collection: {e}")
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

def print_top_5_and_len(collection_name="line_dialogue_report"):
    coll = {
        "line_dialogue_report": line_dialogue_report_coll,
        "line_dialogue_comment": line_dialogue_comment_coll,
        "line_report_comment": line_report_comment_coll
    }.get(collection_name, line_dialogue_report_coll)
    print(f"Fetching top 5 documents from {collection_name} collection")
    try:
        total_length = coll.count_documents({})
        print(f"Total documents in {collection_name} collection: {total_length}")
        sort_field = "upload_time" if collection_name == "line_dialogue_report" else "dialogue_comment_time" if collection_name == "line_dialogue_comment" else "report_comment_time"
        top_5 = list(coll.find({}, {"_id": 0}).sort(sort_field, -1).limit(5))
        print(f"Top 5 documents (sorted by {sort_field}, descending) from {collection_name}:")
        for i, doc in enumerate(top_5, 1):
            print(f"{i}. {doc}")
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error printing top 5 documents from {collection_name}: {e}")
        raise