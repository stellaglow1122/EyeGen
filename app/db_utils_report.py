from pymongo import MongoClient
import threading

# 定義全局互斥鎖
db_lock = threading.Lock()

def init_db():
    client = MongoClient("mongodb://mongo:27017/")
    db = client["ophthalmology_db"]
    return db

def get_report_list():
    db = init_db()
    reports = list(db.reports.find().sort("report_id", 1))
    return reports

def get_report_by_id(report_id):
    db = init_db()
    return db.reports.find_one({"report_id": report_id})

def submit_comment(report_id, comment_content, comment_score, comment_state, comment_time):
    db = init_db()
    with db_lock:  # 使用互斥鎖保護寫入操作
        db.reports.update_one(
            {"report_id": report_id},
            {"$set": {
                "comment_content": comment_content,
                "comment_score": comment_score,
                "comment_state": comment_state,
                "comment_time": comment_time
            }},
            upsert=True
        )

def get_next_uncommented_report(current_id):
    db = init_db()
    query = {"comment_state": {"$ne": "Y"}}
    if current_id:
        query["report_id"] = {"$gt": current_id}
    return db.reports.find_one(query, sort=[("report_id", 1)])

def get_prev_uncommented_report(current_id):
    db = init_db()
    query = {"comment_state": {"$ne": "Y"}}
    if current_id:
        query["report_id"] = {"$lt": current_id}
    return db.reports.find_one(query, sort=[("report_id", -1)])