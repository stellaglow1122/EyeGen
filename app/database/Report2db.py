import json
import os
from datetime import datetime
from pymongo import MongoClient
from db_utils_report import init_db

def import_reports_to_mongo():
    db = init_db()
    collection = db["reports"]

    json_dir = "/app/json_report"
    for filename in os.listdir(json_dir):
        if filename.endswith(".json") and filename != "dialogue_reports.json":
            filepath = os.path.join(json_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # default columns for comment
                default_fields = {
                    "comment_state": "N",
                    "comment_content": "",
                    "comment_time": "",
                    "comment_score": 0
                }

                if isinstance(data, list):
                    for entry in data:
                        if "report_id" not in entry:
                            entry["report_id"] = filename.replace(".json", "")
                        entry["upload_time"] = upload_time
                        # add comment columns and keep original data
                        entry.update({k: v for k, v in default_fields.items() if k not in entry})
                        collection.update_one(
                            {"report_id": entry["report_id"]},
                            {"$set": entry},
                            upsert=True
                        )
                else:
                    if "report_id" not in data:
                        data["report_id"] = filename.replace(".json", "")
                    data["upload_time"] = upload_time
                    # add comment columns and keep original data
                    data.update({k: v for k, v in default_fields.items() if k not in data})
                    collection.update_one(
                        {"report_id": data["report_id"]},
                        {"$set": data},
                        upsert=True
                    )

            print(f"Imported (upserted) {filename} to MongoDB")

if __name__ == "__main__":
    import_reports_to_mongo()