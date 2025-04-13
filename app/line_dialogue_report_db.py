from services.GenReport import GenReport
from database.LineComment2db import import_line_comment_to_mongo
import asyncio

def line_dialogue_report_db(idx, user_type, user_name, dialogue, gen_model="Llama-3.1-Nemotron-70B-Instruct"):
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

    reporter = GenReport()
    indexed_dialogue = reporter.add_index_to_indexed_dialogue(dialogue)
    report_content = asyncio.run(reporter.summary_report(indexed_dialogue, gen_model, user_type))
    report_content = report_content.partition('---')[0]
    data = {
        "idx": idx,
        "user_type": user_type,
        "user_name": user_name,
        "dialogue_content": indexed_dialogue,
        "report_content": report_content,
        "gen_model": gen_model
    }

    result = import_line_comment_to_mongo(data)
    if result:
        print(f"[{idx}] imported successfully")
    else:
        print(f"[{idx}] import skipped (already exists)")


# Simulated parameters
idx = 'TESTEID'
user_type = "Patient"
user_name = "Peter"
dialogue = """
使用者問題/回覆1: 明天我有醫生門診，過去我有做過青光眼的手術，這次門診前需要特別準備什麼文件嗎？
系統回覆1: 您好，最近您的眼睛有什麼不舒服的地方嗎？請盡可能詳細的告訴我，以便更好的幫助您找出原因，確保您的視力健康！

使用者問題/回覆2: 最近我的眼睛常常覺得模糊，看東西沒有那麼清楚，有時候近距離的字看起來會扭曲，好像變形了一樣。
系統回覆2: 您剛剛提到的眼睛不適的症狀，大約持續多久了呢？請您回想看看，大約是最近才發生，還是已經持續一陣子呢？

使用者問題/回覆3: 大約已經持續了三個月了。
系統回覆3: 系統詢問: 需要提供"您的眼睛不適症狀，是發生在一隻眼睛，還是兩隻眼睛都有呢？"資訊:
 
可能回覆選項: ['單眼(左眼)', '單眼(右眼)', '雙眼']


使用者問題/回覆4: 單眼(右眼)
系統回覆4: 請問您的家人當中，有人曾經被診斷過眼睛相關的疾病嗎？
有些眼睛疾病可能與遺傳有關，如果家族中有人曾經有眼疾(如青光眼、白內障、高度近等等)或視遺傳性眼疾(如色盲)，您的風險可能會比較高，我們可以提早注意。
"""

if __name__ == "__main__":
    line_dialogue_report_db(idx, user_type, user_name, dialogue)