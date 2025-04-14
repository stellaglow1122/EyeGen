import asyncio
from services.line_dialogue_report_db import line_dialogue_report_db
from database.LineComment2db import clear_line_comment_collection

# 定義 10 組測試資料
test_data = [
    # idx: "idx1" (重複 3 次)
    {
        "idx": "idx1",
        "object_type": "Doctor",
        "object_name": "NTU",
        "dialogue": """
使用者問題/回覆1: 我的右眼最近很模糊，之前有做過白內障手術。
系統回覆1: 您好，您的症狀可能需要進一步檢查，建議到醫療中心的門診部。
"""
    },
    {
        "idx": "idx1",
        "object_type": "Patient",
        "object_name": "NYCU",
        "dialogue": """
使用者問題/回覆1: 我的左眼有點乾，會不會是乾眼症？
系統回覆1: 可能是乾眼症，建議使用人工淚液並減少螢幕時間。
"""
    },
    {
        "idx": "idx1",
        "object_type": "Doctor",
        "object_name": "John",
        "dialogue": """
使用者問題/回覆1: 我的視力最近下降很快。
系統回覆1: 建議進行眼底檢查，可能是視網膜問題。
"""
    },
    # idx: "idx2" (不重複)
    {
        "idx": "idx2",
        "object_type": "Patient",
        "object_name": "Mary",
        "dialogue": """
使用者問題/回覆1: 我的眼睛常常覺得累。
系統回覆1: 可能是用眼過度，建議每小時休息 5 分鐘。
"""
    },
    # idx: "idx3" (不重複)
    {
        "idx": "idx3",
        "object_type": "Doctor",
        "object_name": "NTU",
        "dialogue": """
使用者問題/回覆1: 我有青光眼病史，最近眼壓好像升高了。
系統回覆1: 建議立即到眼科檢查，可能需要調整藥物。
"""
    },
    # idx: "idx4" (不重複)
    {
        "idx": "idx4",
        "object_type": "Patient",
        "object_name": "NYCU",
        "dialogue": """
使用者問題/回覆1: 我的右眼紅腫，會不會是結膜炎？
系統回覆1: 可能是結膜炎，建議避免揉眼並就醫。
"""
    },
    # idx: "idx5" (不重複)
    {
        "idx": "idx5",
        "object_type": "Doctor",
        "object_name": "John",
        "dialogue": """
使用者問題/回覆1: 我的視野有黑點。
系統回覆1: 可能是飛蚊症，但需檢查是否有視網膜脫落。
"""
    },
    # idx: "idx6" (不重複)
    {
        "idx": "idx6",
        "object_type": "Doctor",
        "object_name": "Mary",
        "dialogue": """
使用者問題/回覆1: 我的眼睛對光很敏感。
系統回覆1: 可能是光敏感，建議佩戴太陽眼鏡。
"""
    },
    # idx: "idx7" (不重複)
    {
        "idx": "idx7",
        "object_type": "Doctor",
        "object_name": "NTU",
        "dialogue": """
使用者問題/回覆1: 我的眼瞼一直跳。
系統回覆1: 可能是疲勞或壓力，建議多休息。
"""
    },
    # idx: "idx8" (不重複)
    {
        "idx": "idx8",
        "object_type": "Doctor",
        "object_name": "NYCU",
        "dialogue": """
使用者問題/回覆1: 我的眼睛有異物感。
系統回覆1: 可能是異物進入，建議用清水沖洗並就醫。
"""
    }
]

if __name__ == "__main__":

    # import 10 dialogue to generate as report and save to db
    for i, data in enumerate(test_data, 1):
        print(f"\nProcessing test case {i}/{len(test_data)}: idx={data['idx']}")
        status_message, returned_data = asyncio.run(line_dialogue_report_db(
            idx=data["idx"],
            object_type=data["object_type"],
            object_name=data["object_name"],
            dialogue=data["dialogue"]
        ))
        print(f"Result for idx {data['idx']}: {status_message}")
        if returned_data:
            print(f"Data for idx {data['idx']}: {returned_data}")
        