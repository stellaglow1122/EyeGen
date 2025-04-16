import asyncio
import logging
import uuid
import secrets
import string
from datetime import datetime
import pytz
from services.GenReport import GenReport
from database.LineComment2db import import_line_dialogue_report_to_mongo, get_line_by_idx

# 設置日誌記錄
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_random_suffix(length=8):
    """
    Generate a random alphanumeric suffix of specified length.
    
    Parameters:
    - length (int): Length of the random suffix (default: 8)
    
    Returns:
    - str: Random alphanumeric string
    """
    characters = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
    return ''.join(secrets.choice(characters) for _ in range(length))

async def line_dialogue_report_db(object_idx, object_type, object_name, dialogue, gen_model="Llama-3.1-Nemotron-70B-Instruct"):
    """
    Generate a summary report for a given dialogue and insert it into MongoDB.

    Parameters:
    - object_idx (str): Unique identifier for the dialogue report
    - object_type (str): Role of the user, either "Doctor" or "Patient"
    - object_name (str): Name of the user submitting the dialogue
    - dialogue (str): Raw text of the dialogue that needs summarization
    - gen_model (str, optional): LLM model used to generate the report (default: Llama-3.1-Nemotron-70B-Instruct)

    Returns:
    - tuple: (status_message, data)
        - status_message (str): Status message indicating success or failure
        - data (dict or None): The data prepared for MongoDB insertion, or None if failed
    """
    request_id = str(uuid.uuid4())  # 生成唯一的請求 ID

    # 生成時間
    taipei_tz = pytz.timezone("Asia/Taipei")
    upload_time =datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")

    # 製作unique key id
    random_suffix = generate_random_suffix(8) # 為 idx 附加 8 位亂碼
    time_id = upload_time.replace("-", "").replace(" ", "").replace(":", "")
    idx = f"{time_id}-{random_suffix}"  # 例如 Eric-abcdef12
    logger.info(f"Processing idx: {idx}, user: {object_name} ({object_type}), request_id: {request_id}")

    # 先檢查 idx 是否已存在
    existing_doc = get_line_by_idx(idx)
    if existing_doc and not existing_doc.get("is_temp", False):
        logger.info(f"[{idx}] already exists in MongoDB, skipping report generation")
        return f"[{idx}] already exists", None

    try:
        # 生成報告
        logger.info(f"Calling model: {gen_model}")
        reporter = GenReport()
        indexed_dialogue = reporter.add_index_to_indexed_dialogue(dialogue)
        report_content = await reporter.summary_report(indexed_dialogue, gen_model, object_type)
        report_content = report_content.partition('---')[0]
    except Exception as e:
        logger.error(f"Failed to generate report for idx {idx}: {e}")
        return f"Failed to generate report for idx {idx}: {str(e)}", None
    finally:
        # 確保在生成報告後解鎖
        logger.info(f"Unlocking idx: {idx}")

    # 準備資料
    data = {
        "idx": idx,
        "upload_time": upload_time,
        "object_idx":object_idx,
        "object_type": object_type,
        "object_name": object_name,
        "dialogue_content": indexed_dialogue,
        "report_content": report_content,
        "gen_model": gen_model
    }

    # 匯入資料庫
    try:
        logger.info(f"[{idx}] Ready to import...")
        result = import_line_dialogue_report_to_mongo(data, request_id=request_id)
        if result:
            logger.info(f"[{idx}] imported successfully")
            return f"[{idx}] imported successfully", data
        else:
            logger.info(f"[{idx}] import skipped (already exists)")
            return f"[{idx}] import skipped (already exists)", data
    except Exception as e:
        logger.error(f"Failed to import idx {idx} to MongoDB: {e}")
        return f"Failed to import idx {idx}: {str(e)}", None