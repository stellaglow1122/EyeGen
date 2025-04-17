import asyncio
import json
import random
import secrets
import string
from datetime import datetime
import pytz
from services.GenReport import GenReport
from database.LineComment2db import import_line_dialogue_report_to_mongo

# JSON 檔案路徑
path = "./json_dialogue/hole_qa_conversation_process_patient_doctor_v3(1).json"

# 輸出 JSON 檔案路徑
output_path = "./json_report/dialogue_reports.json"

# 機構列表，用於隨機選擇 object_name
institutions = ["Emily", "Bob", "Eric", "Mary", "John", "Emma", "James", "Sophia", "Jennifer", "David"]

# 讀取 JSON 檔案
def json_load(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from {file_path}: {e}")
        return []
    except Exception as e:
        print(f"Error: Failed to read file {file_path}: {e}")
        return []

# 生成 8 位亂碼
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

def add_newlines_to_dialogue(dialogue_content):
    # 按行分割對話內容
    lines = dialogue_content.strip().splitlines()
    
    # 用來儲存處理後的行
    processed_lines = []
    
    for line in lines:
        # 檢查是否為對話條目（以 [數字] 開頭）
        if re.match(r'^\[\d+\]', line.strip()):
            # 在對話條目之前添加兩行換行
            processed_lines.append("\n\n" + line)
        else:
            processed_lines.append(line)
    
    # 組合處理後的內容，並移除開頭多餘的 \n\n（如果有）
    result = "".join(processed_lines).lstrip("\n\n")
    return result

# 處理資料：添加 idx, object_type, object_name
def process_data(raw_data):
    processed_data = []
    for i, item in enumerate(raw_data, 1):


        # 確保 item 是字串（對話內容）
        if not isinstance(item, str):
            print(f"Warning: Skipping item {i} due to invalid dialogue format (not a string).")
            continue
        
        # 隨機選擇 object_name
        object_name = random.choice(institutions)
        
        # 生成基礎 idx，並附加 8 位亂碼
        random_suffix = generate_random_suffix(8)
        
        taipei_tz = pytz.timezone("Asia/Taipei")
        upload_time =datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")

        time_id = upload_time.replace("-", "").replace(" ", "").replace(":", "")
        idx = f"{time_id}-{random_suffix}"  # 例如 Eric-abcdef12
        
        # 組合資料
        processed_item = {
            "idx": idx,
            "upload_time": upload_time,
            "object_idx": random_suffix,
            "object_type": "Doctor",
            "object_name": object_name,
            "dialogue_content": item
        }
        processed_data.append(processed_item)
    
    return processed_data[:1]

# 儲存資料到 JSON 檔案
def save_as_json(data_list, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=4, ensure_ascii=False)
        print(f"Data successfully saved to {file_path}")
    except Exception as e:
        print(f"Error: Failed to save data to {file_path}: {e}")

# 異步函數：生成報告
async def generate_report(data, gen_model="Llama-3.1-Nemotron-70B-Instruct"):
    try:
        object_type = data["object_type"]
        dialogue = data["dialogue_content"]
        
        # 生成報告
        reporter = GenReport()
        indexed_dialogue = reporter.add_index_to_indexed_dialogue(dialogue)
        report_content = await reporter.summary_report(indexed_dialogue, gen_model, object_type)
        report_content = report_content.partition('---')[0]

        # 更新資料
        data["dialogue_content"] = indexed_dialogue
        data["report_content"] = report_content
        data["gen_model"] = gen_model

        return data
    except Exception as e:
        print(f"Error generating report for idx {data['idx']}: {e}")
        return None

# Ready report from dialogue
def ready_report_from_dialogue():
     # 讀取並處理資料
    raw_data = json_load(path)
    if not raw_data:
        print("No data to process. Exiting.")
        exit(1)
    
    test_data = process_data(raw_data)
    if not test_data:
        print("No valid data to process after filtering. Exiting.")
        exit(1)

    data_ls = []

    # 生成報告
    for i, data in enumerate(test_data, 1):
        print(f"\nProcessing test case {i}/{len(test_data)}: idx={data['idx']}")
        
        # 異步生成報告
        processed_data = asyncio.run(generate_report(data))
        
        if processed_data:
            print(f"Report generated for idx {data['idx']}: {processed_data['report_content'][:100]}...")  # 打印報告前 100 字元
            data_ls.append(processed_data)
        else:
            print(f"Skipping idx {data['idx']} due to report generation failure.")

    # 儲存到 JSON 檔案
    if data_ls:
        save_as_json(data_ls, output_path)
    else:
        print("No data to save. Exiting.")

def import_completed_data_to_db():
    # Read completed preprocess dialogues and reports
    json_data = json_load(output_path)

    for i, data in enumerate(json_data, 1):
        
        # # 生成基礎 idx，並附加 8 位亂碼
        # random_suffix = generate_random_suffix(8)
        
        # taipei_tz = pytz.timezone("Asia/Taipei")
        # upload_time =datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")

        # time_id = upload_time.replace("-", "").replace(" ", "").replace(":", "")
        # idx = f"{time_id}-{random_suffix}"  # 例如 Eric-abcdef12
        
        # data["idx"] = idx
        # data["upload_time"] = upload_time
        # data["object_idx"] = random_suffix
        # data_ls.append(data)

        import_line_dialogue_report_to_mongo(data)
        print("[Import] FINISH.", data["idx"])
    
    # save_as_json(data_ls, output_path)

if __name__ == "__main__":

    # Ready report from dialogue
    # ready_report_from_dialogue()
   
    # Import completed preprocess dialogues and reports with JSON to db (line_dialogue_report)
    import_completed_data_to_db()
