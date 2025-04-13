import asyncio
import logging
import uuid
from datetime import datetime
from services.GenReport import GenReport

# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.LineComment2db import import_line_comment_to_mongo, get_line_by_idx, lock_idx, unlock_idx

# 設置日誌記錄
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def line_dialogue_report_db(idx, user_type, user_name, dialogue, gen_model="Llama-3.1-Nemotron-70B-Instruct"):
    """
    Generate a summary report for a given dialogue and insert it into MongoDB.

    Parameters:
    - idx (str): Unique identifier for the dialogue report (used as DB key)
    - user_type (str): Role of the user, either "Doctor" or "Patient"
    - user_name (str): Name of the user submitting the dialogue
    - dialogue (str): Raw text of the dialogue that needs summarization
    - gen_model (str, optional): LLM model used to generate the report (default: Llama-3.1-Nemotron-70B-Instruct)

    Returns:
    - str: Status message indicating success or failure
    """
    request_id = str(uuid.uuid4())  # 生成唯一的請求 ID
    logger.info(f"Processing idx: {idx}, user: {user_name} ({user_type}), request_id: {request_id}")

    # 先檢查 idx 是否已存在
    existing_doc = get_line_by_idx(idx)
    if existing_doc and not existing_doc.get("is_temp", False):
        logger.info(f"[{idx}] already exists in MongoDB, skipping report generation")
        return f"[{idx}] already exists"

    # 在調用 LLM 之前嘗試鎖定 idx，重試 3 次，每次間隔 2 秒
    max_retries = 3
    retry_delay = 2  # 秒
    for attempt in range(max_retries):
        logger.info(f"Attempting to lock idx: {idx} for request: {request_id} (Attempt {attempt + 1}/{max_retries})")
        if lock_idx(idx, request_id):
            break
        if attempt < max_retries - 1:
            logger.info(f"[{idx}] is currently locked, retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
    else:
        logger.info(f"[{idx}] is currently locked by another process after {max_retries} attempts, skipping report generation")
        return f"[{idx}] is currently locked by another process"

    try:
        # 生成報告
        logger.info(f"Calling model: {gen_model}")
        reporter = GenReport()
        indexed_dialogue = reporter.add_index_to_indexed_dialogue(dialogue)
        report_content = await reporter.summary_report(indexed_dialogue, gen_model, user_type)
        report_content = report_content.partition('---')[0]
    except Exception as e:
        logger.error(f"Failed to generate report for idx {idx}: {e}")
        return f"Failed to generate report for idx {idx}: {str(e)}"
    finally:
        # 確保在生成報告後解鎖
        logger.info(f"Unlocking idx: {idx}")
        unlock_idx(idx)

    # 準備資料
    data = {
        "idx": idx,
        "user_type": user_type,
        "user_name": user_name,
        "dialogue_content": indexed_dialogue,
        "report_content": report_content,
        "gen_model": gen_model
    }


    # 匯入資料庫
    try:
        logger.info(f"[{idx}] Ready to import...")
        result = import_line_comment_to_mongo(data, request_id=request_id)
        if result:
            logger.info(f"[{idx}] imported successfully")
            return f"[{idx}] imported successfully"
        else:
            logger.info(f"[{idx}] import skipped (already exists)")
            return f"[{idx}] import skipped (already exists)"
    except Exception as e:
        logger.error(f"Failed to import idx {idx} to MongoDB: {e}")
        return f"Failed to import idx {idx}: {str(e)}"