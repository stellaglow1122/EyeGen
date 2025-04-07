# pages/dialogue_comment.py
import gradio as gr
import json
import os
import re
from copy import deepcopy
from pymongo import MongoClient
import threading
from collections import defaultdict
import unicodedata
from db_utils_report import init_db

# 互斥鎖確保資料庫操作安全
db_lock = threading.Lock()

global map_intention
map_intention = {
    "intraocular_lens_decisions": "推薦水晶體", 
    "ask_cataract_len": "眼科科普", 
    "patient_doctor": "診間對話",
    "ask_lensx": "飛秒雷射", #"推薦水晶體", # "眼科科普", 
    "": ""
}

global scenario_description
scenario_description = {

        "推薦水晶體": [
                "情境一: 使用者提到了眼睛不適症狀，判斷可能是白內障",
                "情境二: 使用者提到了眼睛不適症狀，判斷不太像白內障",
                "情境三: 使用者沒有提到任何眼睛不適症狀",
        ],
    
        "眼科科普": [
            "是: 判斷可能患有白內障",
            "否: 判斷應該不是白內障"
        ],
    
        "診間對話": [
            "是: 判斷可能患有白內障",
            "否: 判斷應該不是白內障"
        ],

        "": []
        
        # "推薦水晶體": {
        #     "情境一": "使用者提到了眼睛不適症狀，判斷可能是白內障",
        #     "情境二": "使用者提到了眼睛不適症狀，判斷不太像白內障",
        #     "情境三": "使用者沒有提到任何眼睛不適症狀",
        # },
        # "眼科科普": {
        #     "是": "判斷可能患有白內障",
        #     "否": "判斷應該不是白內障"
        # },
        # "診間對話": {
        #     "是": "判斷可能患有白內障",
        #     "否": "判斷應該不是白內障"
        # }
}

global fix_option_choice
fix_option_choice = {
    'scenario_judge': [ '情境分類', '系統回應' ],
    'iol_recommend_judge': [ 'IOL判斷過程', '最終總結推薦' ]
}

# connect with conversation DB
def connect_to_chat_db():

    db = init_db()  # using init_db from db_utils_report

    # create table(collection)
    user_inter_data_table = db['user_inter_data_info']

    # create conversation rate table
    # new_json_user_conv_data_rate_table = db['phase2_doctor_eval_v2_rate_table']
    new_json_user_conv_data_rate_table = db['synthesis_json_user_conv_data_rate_v2']
  
    return user_inter_data_table, new_json_user_conv_data_rate_table

# check already label or not
def check_label_or_not(conversation_data):

    if ( 
                ( conversation_data['system_response_rate'] == 5) or 
                ( (conversation_data['system_response_rate'] > 0 and conversation_data['doctor_edit_response'] != "")  and
                  (
                      (conversation_data['doctor_edit_option_checkbox'] == '情境分類' and conversation_data['doctor_scenario_cls_error'] != "") or 
                      (conversation_data['doctor_edit_option_checkbox'] == 'IOL判斷過程' and conversation_data['iol_sop_error_step'] != "") or 
                      conversation_data['doctor_edit_option_checkbox'] in [ '系統回應', '最終總結推薦' ]
                  )
                )
            
        ):

        return True

    else:
        return False


# read and handle doctor eval conversation datas
def read_and_set_conv_data_rate_table(new_json_user_conv_data_rate_table):

    rate_conversation_datas = []
    already_rate_conversation_datas = []
    not_rate_conversation_datas = []

    all_rows = list(new_json_user_conv_data_rate_table.find())
    print(f"-- 84 len(all_rows): {len(all_rows)}\n")

    # iterate each conversation_datas
    for all_row in all_rows:

        if "test_gpt_synthesis_v2" not in all_row['uid']:
            continue

        # no need doctor label
        if all_row['mark_need_label'] != True:
            continue

        if all_row['system_intent'] == 'ask_lensx' and (all_row['user_response'] == '否我不需要' or all_row['user_response'] == '飛秒雷射的簡介與價錢'): 
            continue
            # print(f"-- 106 all_row['user_response']:\n {all_row['user_response']}\n")
            # print(f"-- 107 all_row['system_response']:\n {all_row['system_response']}\n")
            # raise

        elif all_row['tags'] == ['ask_lensx']:
            all_row['tags'] =  [ 'ask_cataract_len' ]
            # print(f"--113 all_row['system_intent']: {all_row['system_intent']}\n")



        # all_row['system_response_rate'] = int(all_row['system_response_rate'])
        # print(f"-- 97 all_row['system_response_rate']: {all_row['system_response_rate']}\n")
        # print(f"-- 98 type(all_row['system_response_rate']): {type(all_row['system_response_rate'])}\n")
        # print(f"-- 99 all_row['doctor_edit_response']: {all_row['doctor_edit_response']}\n")
        # print(f"-- 100 type(all_row['doctor_edit_response']): {type(all_row['doctor_edit_response'])}\n")
        # print(f"-- 100 type(all_row['doctor_edit_response']): {type(all_row['doctor_edit_response'])}\n")
        
        # check data already in DB or not
        if check_label_or_not(conversation_data = all_row):


            already_rate_conversation_datas.append(deepcopy({

                ### conversation dialogue info
                "group_id": all_row['group_id'],
                "uid": all_row['uid'],
                "tags": all_row['tags'],
                "group_id": all_row['group_id'],
                "iter_idx": all_row['iter_idx'],  # which dialogue index in conversation
                "origin_intent": all_row['origin_intent'],
                "system_judge_scenario": all_row['system_judge_scenario'],
                # "has_iol_recommend": all_row['has_iol_recommend'],
    
                #### for our systems
                "prev_step_str": all_row['prev_step_str'],
                "user_response": all_row['user_response'],
                "system_response": all_row['system_response'],
                "system_intent": all_row['system_intent'] ,
                "current_subtask": all_row['current_subtask'],
                "system_retrieve_doc_paths": all_row["system_retrieve_doc_paths"],
                "state": all_row["state"],
                "subtasks": all_row["subtasks"],
                # "current_state": all_row['current_state'],

            
                #### for llama3.1 405b GT
                "gt_prev_step_str": all_row['gt_prev_step_str'],
                "ground_truth_answer": all_row['ground_truth_answer'], 


                #### for auto evaluation (llama3.1-405B & gpt-4o-mini)
                "intention_cls_error": all_row['intention_cls_error'],
                "scenario_cls_error": all_row['scenario_cls_error'],

                "gpt_4o_mini_score": all_row['gpt_4o_mini_score'],
                "gpt_4o_mini_feedback": all_row['gpt_4o_mini_feedback'],
            
                "llama405b_score": all_row['llama405b_score'],
                "llama405b_feedback": all_row['llama405b_feedback'],

                "show_model_score": all_row['show_model_score'],
                "show_model_feedback": all_row['show_model_feedback'],

            
                #### for doctor eval ui
                'mark_need_label': all_row['mark_need_label'],
                'mark_show_scenario_label': all_row['mark_show_scenario_label'],
    
    
                #### for doctor label
                "system_response_rate": all_row['system_response_rate'],
                "doctor_edit_response": all_row['doctor_edit_response'],
                "doctor_intention_cls_error": all_row['doctor_intention_cls_error'],
                "doctor_scenario_cls_error": all_row['doctor_scenario_cls_error'],
                "iol_sop_error_step": all_row['iol_sop_error_step'],
                "doctor_edit_option_checkbox": all_row.get('doctor_edit_option_checkbox', ''),
            }))

        else:
            
             not_rate_conversation_datas.append(deepcopy({

                ### conversation dialogue info
                "group_id": all_row['group_id'],
                "uid": all_row['uid'],
                "tags": all_row['tags'],
                "group_id": all_row['group_id'],
                "iter_idx": all_row['iter_idx'],  # which dialogue index in conversation
                "origin_intent": all_row['origin_intent'],
                "system_judge_scenario": all_row['system_judge_scenario'],
                # "has_iol_recommend": all_row['has_iol_recommend'],
    
                #### for our systems
                "prev_step_str": all_row['prev_step_str'],
                "user_response": all_row['user_response'],
                "system_response": all_row['system_response'],
                "system_intent": all_row['system_intent'],
                "current_subtask": all_row['current_subtask'],
                "system_retrieve_doc_paths": all_row["system_retrieve_doc_paths"],
                "state": all_row["state"],
                "subtasks": all_row["subtasks"],
                # "current_state": all_row['current_state'],

            
                #### for llama3.1 405b GT
                "gt_prev_step_str": all_row['gt_prev_step_str'],
                "ground_truth_answer": all_row['ground_truth_answer'], 


                #### for auto evaluation (llama3.1-405B & gpt-4o-mini)
                "intention_cls_error": all_row['intention_cls_error'],
                "scenario_cls_error": all_row['scenario_cls_error'],

                "gpt_4o_mini_score": all_row['gpt_4o_mini_score'],
                "gpt_4o_mini_feedback": all_row['gpt_4o_mini_feedback'],
            
                "llama405b_score": all_row['llama405b_score'],
                "llama405b_feedback": all_row['llama405b_feedback'],

                "show_model_score": all_row['show_model_score'],
                "show_model_feedback": all_row['show_model_feedback'],

            
                #### for doctor eval ui
                'mark_need_label': all_row['mark_need_label'],
                'mark_show_scenario_label': all_row['mark_show_scenario_label'],
    
    
                #### for doctor label
                "system_response_rate": all_row['system_response_rate'],
                "doctor_edit_response": all_row['doctor_edit_response'],
                "doctor_intention_cls_error": all_row['doctor_intention_cls_error'],
                "doctor_scenario_cls_error": all_row['doctor_scenario_cls_error'],
                "iol_sop_error_step": all_row['iol_sop_error_step'],
                "doctor_edit_option_checkbox": all_row.get('doctor_edit_option_checkbox', ''),
            }))

    
    rate_conversation_datas = already_rate_conversation_datas + not_rate_conversation_datas
    conversations_len = len(rate_conversation_datas)

    # print(f"-- 236 len(rate_conversation_datas): {len(rate_conversation_datas)}\n")
    # print(f"-- 237 len(already_rate_conversation_datas): {len(already_rate_conversation_datas)}\n")
    # print(f"-- 238 len(not_rate_conversation_datas): {len(not_rate_conversation_datas)}\n")
    
    return already_rate_conversation_datas, not_rate_conversation_datas, rate_conversation_datas

## handle iol recommend process label, handle sop step option for doctor ui  build_sop_steps_map_dict
def build_sop_steps_map_dict():


    global user_task_sops
    user_task_sops = {}
    user_tasks_folder_path = "./SOP_module/user_task_SOPs"

    for user_task_path in os.listdir(user_tasks_folder_path):
            
        # get user task name
        intent = user_task_path.replace('_SOP.json', '')

        if 'test' in user_task_path or '.ipynb_checkpoints' in user_task_path or 'prev_' in user_task_path:
            continue

        with open(os.path.join(user_tasks_folder_path, user_task_path), 'r', encoding = 'utf-8') as json_file:    
            user_task_info = json.load(json_file)
            user_task_sops[intent] = user_task_info['subtask_descriptions'][0]


def handle_doctor_ui_sop_steps(
    prev_step_str,
    subtasks,
    current_subtask,
    current_intent,
    state
):
    
    global user_task_sops

    # print(f"-- 287 subtasks: {subtasks}\n")
    # print(f"-- 288 current_subtask: {current_subtask}\n")

    # handle sop step options
    step_options = []
    step_idx = 1
    step_step_idx = 1
    system_response_cnt = 1
    mark_prev_subtask = ""
    
    # user_responses = re.findall(r'使用者問題/回覆\d+: (.*?)\n', prev_step_str, re.DOTALL)
    # system_responses = re.findall(r"系統回覆\d+:\s*(.*?可能回覆選項:\s*\[.*?\])", prev_step_str, re.DOTALL)

    # 定義正則表達式
    user_pattern = re.compile(r"使用者問題/回覆\d+: (.+?)(?=(?:\n系統回覆\d+:)|$)", re.DOTALL)
    system_pattern = re.compile(r"系統回覆\d+: (.+?)(?=(?:\n使用者問題/回覆\d+:)|$)", re.DOTALL)
    
    # 提取使用者與系統回應
    user_responses = user_pattern.findall(prev_step_str)
    system_responses = system_pattern.findall(prev_step_str)
    
    # 移除前後多餘空格
    user_responses = [text.strip() for text in user_responses]
    system_responses = [text.strip() for text in system_responses]

    # print(f"-- 331 system_responses: \n{system_responses}\n")
    # print(f"-- 331 len(system_responses): \n{len(system_responses)}\n")
    # print(f"-- 332 len(user_responses): \n{len(user_responses)}\n")
    
    
    # print(f"system_responses[0]: \n{system_responses[0]}\n")
    # raise


    def normalize_text(text):
        text = text.strip()  # 移除首尾空格與換行
        text = re.sub(r"\s+", " ", text)  # 將多個空格轉換為單一空格
        text = unicodedata.normalize("NFKC", text)  # 標準化 Unicode
        return text


    def add_subnumbers(steps):
        
        step_count = defaultdict(int)  # 記錄每個 step 出現的次數
        step_occurrences = defaultdict(int)  # 記錄每個 step 最終出現的次數
        updated_steps = []
    
        # 先統計每個 stepX 出現的總次數
        for step in steps:
            match = re.match(r"(step\d+):", step)  # 匹配 step 數字
            if match:
                step_key = match.group(1)  # 取得 "stepN"
                step_occurrences[step_key] += 1  # 計算 stepN 出現的總次數
    
        # 再根據出現次數來決定是否加上 .1, .2
        for step in steps:
            match = re.match(r"(step\d+):", step)
            if match:
                step_key = match.group(1)
                step_count[step_key] += 1  # 記錄該 stepX 已處理的次數
                
                # 只有當 stepX 在清單中出現超過 1 次時，才加上 .1, .2
                if step_occurrences[step_key] > 1:
                    suffix = f".{step_count[step_key]}"
                    updated_steps.append(step.replace(step_key + ":", f"{step_key}{suffix}:"))
                else:
                    updated_steps.append(step)  # 只出現一次則不加數字
            else:
                updated_steps.append(step)  # 沒有匹配到 stepN: 則不變
    
        return updated_steps

    prev_subtask = ""
    
    # iterate handle each step content
    for subtask in subtasks:

        if subtask == current_subtask:
            break

        if user_task_sops[current_intent][subtask]['import_subtask_module'] in [  'output_msg_module']: 
            continue

        # elif user_task_sops[current_intent][subtask]['import_subtask_module'] in [  'condition_judge_module'] and current_intent == 'patient_doctor': 

        #     # scenario judge pass
        #     if subtask == 'check_cataract_case' and subtask == 'check_has_cataract_or_not':
        #         continue

        #     decision_field = list(user_task_sops[current_intent][subtask]['user_define_info']['output_infos'].keys())[0]

        #     print(f"-- 110 prev_subtask: {prev_subtask}\n")
        #     print(f"-- 111 prev_subtask: {prev_subtask}\n")
        #     print(f"-- 112 prev_subtask: {prev_subtask}\n")

        #     # has request 
        #     if user_task_sops[current_intent][subtask]['user_define_info']['next_subtask'][prev_subtask]['否'] in subtasks:
                
        #         for idx in range(system_response_cnt - 1, len(system_responses)):
    
        #             if req_info_msg in system_responses[idx]:
    
        #                 system_response_cnt = idx + 1
        #                 step_step_idx = 1
        #                 break

        
        elif user_task_sops[current_intent][subtask]['import_subtask_module'] in [ 'request_info_module', 'output_wait_msg_module'  ]:

            # scenario judge pass
            if subtask == 'check_cataract_case' and subtask == 'check_has_cataract_or_not':
                continue


            
            # for request_info_module
            if user_task_sops[current_intent][subtask]['import_subtask_module'] == 'request_info_module':

                if subtask not in user_task_sops['intraocular_lens_decisions'].keys():
                    continue
                
                req_info_field = list(user_task_sops[current_intent][subtask]['user_define_info']['require_infos'].keys())[0]
                req_info_msg = user_task_sops[current_intent][subtask]['user_define_info']['require_infos'][req_info_field]
                
                req_info_msg = re.sub(r"(?:請注意|注意)[:：]?\s*(.+)", "",  user_task_sops[current_intent][subtask]['user_define_info']['require_infos'][req_info_field], flags=re.DOTALL | re.IGNORECASE).replace('\n', '')
                req_info_msg = re.sub(r'，欄位名稱".*?"', '', req_info_msg) 
    
    
    
                decision_field = list(user_task_sops[current_intent][subtask]['user_define_info']['output_infos'].keys())[0]
                
                for idx in range(system_response_cnt - 1, len(system_responses)):
    
                    if req_info_msg in system_responses[idx]:
    
                        system_response_cnt = idx + 1
                        step_step_idx = 1
                        break


                # if subtask == 'opt_request_one_or_two_eye':
                #     print(f"-- 168 system_response_cnt: {system_response_cnt}\n")
                #     raise


                if decision_field == '推薦意願':

                    if f"step{system_response_cnt}: {decision_field}" not in step_options:
                        step_options.append(f"step{system_response_cnt}: {decision_field}")
    
                else:
                    # step_options.append(f"step{system_response_cnt}: {decision_field}-{state[decision_field]}")
    
                    # fix_info = re.sub(r'[:].*|\(.*?\)', '', state[req_info_field].replace('：', ':').replace('（', '(').replace('）', ')'))
                    # step_options.append(f"step{system_response_cnt}: {decision_field}-{fix_info}")
    
                    if req_info_field == '提及是否使用藥物' and f"step{system_response_cnt}: {decision_field}-{state['提及使用藥物']}" not in step_options:
                        step_options.append(f"step{system_response_cnt}: {decision_field}-{state['提及使用藥物']}")
    
                    else:
                        fix_info = re.sub(r'[:].*|\(.*?\)', '', state[req_info_field].replace('：', ':').replace('（', '(').replace('）', ')'))
                        fix_info = re.sub(r",.*", "", fix_info.replace('，', ','))

                        if f"step{system_response_cnt}: {decision_field}-{fix_info}" not in step_options:
                            step_options.append(f"step{system_response_cnt}: {decision_field}-{fix_info}")
            
                step_options = deepcopy(step_options)


            # for output_wait_msg_module
            elif user_task_sops[current_intent][subtask]['import_subtask_module'] == 'output_wait_msg_module':

                # print(f"-- 186 subtask: {subtask}\n")

                # output_msg_info = user_task_sops[current_intent][subtask]['user_define_info']['output_msg_info']
                output_msg_info = re.sub(r'，欄位名稱".*?"', '', user_task_sops[current_intent][subtask]['user_define_info']['output_msg_info'])

                # print(f"-- 187 output_msg_info: {output_msg_info}\n")
                # print(f"-- 188 system_responses[1]: {system_responses[1]}\n")

                # if subtask == 'opt_request_know_eye_disease':
                #     print(f"-- 195 output_msg_info in system_responses[1]: {normalize_text(text = output_msg_info) in normalize_text(text = system_responses[1])}\n")
                #     raise

                for idx in range(system_response_cnt, len(system_responses)):
    
                    if normalize_text(text = output_msg_info) in normalize_text(text = system_responses[idx]):
    
                        system_response_cnt = idx + 1
                        step_step_idx = 1
                        break

        prev_subtask = subtask

    
    final_step_options = add_subnumbers(step_options)
    print(f"-- 400 final_step_options:\n{final_step_options}\n")

    return final_step_options


## handle ui current show conversation
def get_current_conversation(current_index, conversations_len, prev_data_type, data_type, prev_str = "", user_response = "", uid = ""):

    # raise
    # print(f"-- 144 current_index: {current_index}\n")
    # print(f"-- 145 prev_data_type:\n {prev_data_type}\n")
    # print(f"-- 145 data_type:\n {data_type}\n")

    global scenario_description
    global map_intention

    # connect to chat mongo DB
    user_inter_data_table, new_json_user_conv_data_rate_table = connect_to_chat_db()

    conversation_datas = []
    save_status = ""

    # get rate conversation data as json
    already_rate_conversation_datas, not_rate_conversation_datas, rate_conversation_datas = read_and_set_conv_data_rate_table(new_json_user_conv_data_rate_table = new_json_user_conv_data_rate_table)

    # print(f"-- 197 len(already_rate_conversation_datas): {len(already_rate_conversation_datas)}\n")
    # print(f"-- 198 len(not_rate_conversation_datas): {len(not_rate_conversation_datas)}\n")
    # print(f"-- 199 len(rate_conversation_datas): {len(rate_conversation_datas)}\n")

    
    ## map intention type 
    # map_intent = {
    #         "推薦水晶體": 'intraocular_lens_decisions',
    #         "眼科科普": 'ask_cataract_len',
    #         # "飛秒雷射": 'ask_lensx',
    #         "診間對話": 'patient_doctor',
    #         "其他": 'give_up'
    #     }


    """獲取當前對話內容""" 
    
    # filter user select data type
    if len(data_type['select_data_cls']) == 3 and len(data_type['eval_data_type']) == 2:

        # has change filter data type
        if prev_data_type != data_type:
            current_index = 0
        
        # original
        rate_conversation_data = rate_conversation_datas[current_index]
    
        if check_label_or_not(conversation_data = rate_conversation_data):
            save_status = "評分已儲存!"
    
        else:
            save_status = "尚未評分"
    
        conversations_len = len(rate_conversation_datas)
        processed_count = f"{len(already_rate_conversation_datas)}/{len(rate_conversation_datas)}"
        # unprocessed_count = f"{len(not_rate_conversation_datas)}/{len(rate_conversation_datas)}"   
    
    # no select data type 
    elif len(data_type['select_data_cls']) == 0 or len(data_type['eval_data_type']) == 0:

        processed_count = f"0/0"

        current_index = 0
        conversations_len = 0
        
        rate_conversation_data = {
                "group_id": "",
                "uid": "",
                "tags": [],
                "group_id": "",
                "iter_idx": "",  # which dialogue index in conversation
                "origin_intent": "",
                "system_judge_scenario": "",
                # "has_iol_recommend": all_row['has_iol_recommend'],
    
                #### for our systems
                "prev_step_str": "",
                "user_response": "",
                "system_response": "",
                "system_intent": "", 
                "current_subtask": "",
                "system_retrieve_doc_paths": "",
                # "current_state": all_row['current_state'],

            
                #### for llama3.1 405b GT
                "gt_prev_step_str": "",
                "ground_truth_answer": "", 


                #### for auto evaluation (llama3.1-405B & gpt-4o-mini)
                "intention_cls_error": "",
                "scenario_cls_error": "",

                "gpt_4o_mini_score": "",
                "gpt_4o_mini_feedback": "",
            
                "llama405b_score": "",
                "llama405b_feedback": "",

                "show_model_score": "",
                "show_model_feedback": "",

            
                #### for doctor eval ui
                'mark_need_label': "",
                'mark_show_scenario_label': "",
    
    
                #### for doctor label
                "system_response_rate": 0,
                "doctor_edit_response": "",
                "doctor_intention_cls_error": "",
                "doctor_scenario_cls_error": "",
                "iol_sop_error_step": "",
                "doctor_edit_option_checkbox": "",
            }
    
    else:

        filter_already_rate_conversation_datas = []
        filter_not_rate_conversation_datas = []
        
        # has change filter data type (intention)
        if prev_data_type != data_type:
            current_index = 0


        # map_data_type = [ map_intent[data] for data in data_type['select_data_cls'] if data in map_intent.keys() ]


        if len(already_rate_conversation_datas):
            # print(f"-- 309 already_rate_conversation_datas[0]['tags'][0]: {already_rate_conversation_datas[0]['tags'][0]}\n")
            # print(f"-- 310 data_type['select_data_cls']: {data_type['select_data_cls']}\n")
            
            filter_already_rate_conversation_datas = [deepcopy(data) for data in already_rate_conversation_datas if map_intention[data['tags'][0]] in data_type['select_data_cls']] if any(map_intention[data['tags'][0]] in data_type['select_data_cls'] for data in already_rate_conversation_datas) else []

        if len(not_rate_conversation_datas):
            # print(f"-- 315 not_rate_conversation_datas[0]['tags'][0]: {not_rate_conversation_datas[0]['tags'][0]}\n")
            # print(f"-- 316 data_type['select_data_cls']: {data_type['select_data_cls']}\n")
            
            filter_not_rate_conversation_datas = [deepcopy(data) for data in not_rate_conversation_datas if map_intention[data['tags'][0]] in data_type['select_data_cls']] if any(map_intention[data['tags'][0]] in data_type['select_data_cls'] for data in not_rate_conversation_datas) else []

        
        # has change filter data type
        if prev_data_type != data_type:
            # current_index = len(filter_already_rate_conversation_datas) - 1
            current_index = 0

        
        if len(data_type['eval_data_type']) == 2:

            filter_rate_conversation_datas = filter_already_rate_conversation_datas + filter_not_rate_conversation_datas
            

        elif len(data_type['eval_data_type']) == 1 and data_type['eval_data_type'][0] == '已評分':
            filter_rate_conversation_datas = filter_already_rate_conversation_datas

        elif len(data_type['eval_data_type']) == 1 and data_type['eval_data_type'][0] == '未評分':
            filter_rate_conversation_datas = filter_not_rate_conversation_datas


        # no select
        else:
            print(f"-- error occur !!! no select eval_data_type !!!\n")
            filter_rate_conversation_datas = []
            # raise

        # print(f"-- 647 len(filter_already_rate_conversation_datas): {len(filter_already_rate_conversation_datas)}\n")
        # print(f"-- 648 len(filter_not_rate_conversation_datas): {len(filter_not_rate_conversation_datas)}\n")
        # print(f"-- 649 len(filter_rate_conversation_datas): {len(filter_rate_conversation_datas)}\n")
        
        conversations_len = len(filter_rate_conversation_datas)
        processed_count = f"{len(filter_already_rate_conversation_datas)}/{len(filter_already_rate_conversation_datas + filter_not_rate_conversation_datas)}"

        # print(f"-- 654 processed_count: {processed_count}\n")

        if len(filter_rate_conversation_datas):

            # out of index range
            try:
                rate_conversation_data = filter_rate_conversation_datas[current_index]
            except:
                current_index = 0
                rate_conversation_data = filter_rate_conversation_datas[current_index]

        else:

            rate_conversation_data = {
                    "group_id": "",
                    "uid": "",
                    "tags": [],
                    "group_id": "",
                    "iter_idx": "",  # which dialogue index in conversation
                    "origin_intent": "",
                    "system_judge_scenario": "",
                    # "has_iol_recommend": all_row['has_iol_recommend'],
        
                    #### for our systems
                    "prev_step_str": "",
                    "user_response": "",
                    "system_response": "",
                    "system_intent": "", 
                    "current_subtask": "",
                    "system_retrieve_doc_paths": "",
                    # "current_state": all_row['current_state'],
    
                
                    #### for llama3.1 405b GT
                    "gt_prev_step_str": "",
                    "ground_truth_answer": "", 
    
    
                    #### for auto evaluation (llama3.1-405B & gpt-4o-mini)
                    "intention_cls_error": "",
                    "scenario_cls_error": "",
    
                    "gpt_4o_mini_score": "",
                    "gpt_4o_mini_feedback": "",
                
                    "llama405b_score": "",
                    "llama405b_feedback": "",
    
                    "show_model_score": "",
                    "show_model_feedback": "",
    
                
                    #### for doctor eval ui
                    'mark_need_label': "",
                    'mark_show_scenario_label': "",
        
        
                    #### for doctor label
                    "system_response_rate": 0,
                    "doctor_edit_response": "",
                    "doctor_intention_cls_error": "",
                    "doctor_scenario_cls_error": "",
                    "iol_sop_error_step": "",
                    "doctor_edit_option_checkbox": "",
                }

        processed_count = f"{len(filter_already_rate_conversation_datas)}/{len(filter_already_rate_conversation_datas + filter_not_rate_conversation_datas)}"


    print(f"!!!!!!!!!!!!!!!!!! -- 742 uid: {uid}\n")
    print(f"!!!!!!!!!!!!!!!!!! -- 743 prev_str: {prev_str}\n")
    print(f"!!!!!!!!!!!!!!!!!! -- 744 uid: {user_response}\n")

    ## get specific data
    if user_response != "" and uid != "":
        
        # tmp_rate_conversation_datas = filter_already_rate_conversation_datas + filter_not_rate_conversation_datas

        print(f"!!!!!!!!!!!!!!!!!! -- 747 uid: {uid}\n")
        print(f"!!!!!!!!!!!!!!!!!! -- 748 prev_str: {prev_str}\n")
        print(f"!!!!!!!!!!!!!!!!!! -- 749 uid: {user_response}\n")

        rate_conversation_data = deepcopy(new_json_user_conv_data_rate_table.find_one({
            "uid": uid,
            "prev_step_str": prev_str,
            "user_response": user_response,
        }))
        
        if rate_conversation_data is None:
            # 若查無資料則給定預設值
            rate_conversation_data = {
                "group_id": "",
                "uid": "",
                "tags": [],
                "iter_idx": "",
                "origin_intent": "",
                "system_judge_scenario": "",
                "prev_step_str": "",
                "user_response": "",
                "system_response": "",
                "system_intent": "",
                "current_subtask": "",
                "system_retrieve_doc_paths": "",
                "gt_prev_step_str": "",
                "ground_truth_answer": "",
                "intention_cls_error": "",
                "scenario_cls_error": "",
                "gpt_4o_mini_score": "",
                "gpt_4o_mini_feedback": "",
                "llama405b_score": "",
                "llama405b_feedback": "",
                "show_model_score": "",
                "show_model_feedback": "",
                "mark_need_label": "",
                "mark_show_scenario_label": "",
                "system_response_rate": 0,
                "doctor_edit_response": "",
                "doctor_intention_cls_error": "",
                "doctor_scenario_cls_error": "",
                "iol_sop_error_step": "",
                "doctor_edit_option_checkbox": "",
            }

        print(f"!!!!!!!!!!!!!!!!!! -- 792 rate_conversation_data: {rate_conversation_data}\n")

    
    
    if conversations_len > 0 and check_label_or_not(conversation_data = rate_conversation_data):
        save_status = "評分已儲存!"
    
    elif conversations_len > 0 :
        save_status = "尚未評分"

    else:
        save_status = "無"

    # print(f"-- 474 rate_conversation_data['system_judge_scenario']: {rate_conversation_data['system_judge_scenario']}\n")


    ## for doctor label scenario cls error
    doctor_edit_option = rate_conversation_data.get('doctor_edit_option_checkbox', '')

    if doctor_edit_option == '情境分類' and conversations_len:
        # print(f"-- 503 rate_conversation_data['doctor_scenario_cls_error']: {rate_conversation_data.get('doctor_scenario_cls_error')}\n")
        
        system_intent_key = rate_conversation_data.get('system_intent', '')
        mapped_intention = map_intention.get(system_intent_key, '')
        scenario_choices = scenario_description.get(mapped_intention, [])
    
        # print(f"-- 504 scenario_description[{mapped_intention}]: {scenario_choices}\n")
    
        fix_scenario_choices = deepcopy(scenario_choices)
    
        # 確保要移除的值存在於列表中
        system_judge_scenario = rate_conversation_data.get('system_judge_scenario', '')
        if system_judge_scenario in fix_scenario_choices:
            fix_scenario_choices.remove(system_judge_scenario)
    
        # print(f"-- 511 fix_scenario_choices: {fix_scenario_choices}\n")
    
        # 檢查 doctor_scenario_cls_error 是否在 fix_scenario_choices 內
        doctor_scenario_cls_error = rate_conversation_data.get('doctor_scenario_cls_error', None)
        
        if doctor_scenario_cls_error and doctor_scenario_cls_error in fix_scenario_choices:
            scenario_cls_error_checkbox = gr.update(visible=True, choices = fix_scenario_choices, value=doctor_scenario_cls_error)
        else:
            scenario_cls_error_checkbox = gr.update(visible=True, choices = fix_scenario_choices, value = None)
    
    else:
        scenario_cls_error_checkbox = gr.update(visible=False, choices=[], value=None)


    # check answer or iol recommend
    # 根據條件決定 fix_option_key
    fix_option_key = 'iol_recommend_judge' if rate_conversation_data.get('mark_show_scenario_label', False) == False else 'scenario_judge'

    
    # 獲取目前應該使用的 choices
    valid_choices = fix_option_choice[fix_option_key]
    # print(f"-- 830 fix_option_key: {fix_option_key}\n")
    # print(f"-- 830 valid_choices: {valid_choices}\n")
    
    
    # 初始化 doctor_edit_option
    if conversations_len == 0:
        doctor_edit_option = gr.update(visible = False, choices=[], value = None)
    
    else:
        # 確保 doctor_edit_option_checkbox 存在於 valid_choices
        current_value = rate_conversation_data.get('doctor_edit_option_checkbox', None)
        
        if current_value not in valid_choices:
            doctor_edit_option = gr.update(visible = True, choices = valid_choices, value = None)
        else:
            doctor_edit_option = gr.update(visible = True, choices = valid_choices, value = current_value)


    # print(f"-- 498 doctor_edit_option: {doctor_edit_option}\n")
    # print(f"-- 498 doctor_edit_option: {doctor_edit_option}\n")

    
    ## for scenarion CLS
    # show origin system classification scenario
    ## rate_conversation_data['system_intent'] == 'ask_lensx' or
    if rate_conversation_data['mark_show_scenario_label'] != True and fix_option_key != 'scenario_judge' or conversations_len == 0:
        scenario_cls_output_checkbox = gr.update(visible = False, choices = [], value = None)


    else:
        scenario_cls_output_checkbox = gr.update(visible = True, choices = scenario_description[map_intention[rate_conversation_data['system_intent']]], value = rate_conversation_data['system_judge_scenario']) 



    
    


    # print(f"-- 790 rate_conversation_data['doctor_edit_option_checkbox']: {rate_conversation_data['doctor_edit_option_checkbox']}\n")
    # print(f"-- 791 rate_conversation_data['iol_sop_error_step']: {rate_conversation_data['iol_sop_error_step']}\n")

    
    ## check sop error step already mark by doctor or not
    # already select label step
    # and rate_conversation_data['current_subtask'] == 'ask_understand_or_not'
    if rate_conversation_data['iol_sop_error_step'] != ""  and rate_conversation_data['doctor_edit_option_checkbox'] == 'IOL判斷過程':

        if rate_conversation_data['system_intent'] == 'ask_lensx':
            current_intent = rate_conversation_data['origin_intent']

        else:
            current_intent = rate_conversation_data['system_intent']


        sop_step_checkbox = gr.update(choices = handle_doctor_ui_sop_steps(prev_step_str = rate_conversation_data['prev_step_str'], subtasks = rate_conversation_data['subtasks'], current_subtask = rate_conversation_data['current_subtask'], current_intent = current_intent, state = rate_conversation_data['state']), visible = True, interactive = True, value = rate_conversation_data['iol_sop_error_step'])

    # not select label step yet
    elif rate_conversation_data['doctor_edit_option_checkbox'] == 'IOL判斷過程':

        if rate_conversation_data['system_intent'] == 'ask_lensx':
            current_intent = rate_conversation_data['origin_intent']

        else:
            current_intent = rate_conversation_data['system_intent']
        
        sop_step_checkbox = gr.update(choices = handle_doctor_ui_sop_steps(prev_step_str = rate_conversation_data['prev_step_str'], subtasks = rate_conversation_data['subtasks'], current_subtask = rate_conversation_data['current_subtask'], current_intent = current_intent, state = rate_conversation_data['state']), visible = True, interactive = True, value = None)


    # no need show iol sop step
    else:

        sop_step_checkbox = gr.update(choices = [], visible = False, interactive = True, value = None)
    

    
    
    # print(f"-- 826 map_intention[rate_conversation_data['system_intent']]: {map_intention[rate_conversation_data['system_intent']]}\n")
    # print(f"-- 827 rate_conversation_data['user_response']: {rate_conversation_data['user_response']}\n")
    # print(f"-- 828 rate_conversation_data['system_response']: {rate_conversation_data['system_response']}\n")
    # print(f"-- 829 scenario_cls_output_checkbox: {scenario_cls_output_checkbox}\n")
    # print(f"-- 830 doctor_edit_option: {doctor_edit_option}\n")
    # print(f"-- 831 scenario_cls_error_checkbox: {scenario_cls_error_checkbox}\n")
    # print(f"-- 832 sop_step_checkbox: {sop_step_checkbox}\n")

    return (
        current_index, 
        conversations_len,
        rate_conversation_data["uid"],
        rate_conversation_data["prev_step_str"],
        rate_conversation_data["user_response"],
        rate_conversation_data["system_response"],
        rate_conversation_data["doctor_edit_response"],
        rate_conversation_data["system_response_rate"],
        save_status,
        str(rate_conversation_data['show_model_score']),
        rate_conversation_data['show_model_feedback'],
        rate_conversation_data['ground_truth_answer'],
        processed_count,
        prev_data_type, 
        data_type,
        map_intention[rate_conversation_data['system_intent']],
        scenario_cls_output_checkbox,
        doctor_edit_option,
        scenario_cls_error_checkbox, 
        sop_step_checkbox
        # intention_cls_error_checkbox,
        # sop_step_checkbox,
        # cls_step1_error_checkbox
    )


# get prev or last conversation
def navigate(direction, current_index, conversations_len, prev_data_type, data_type):

    # print(f"-- 1181 prev_data_type:\n {prev_data_type}\n")
    # print(f"-- 1182 data_type:\n {data_type}\n")
    
    """切換到上一個或下一個對話"""
    
    if direction == "next" and current_index < conversations_len - 1:
        current_index += 1
    
    elif direction == "prev" and current_index > 0:
        current_index -= 1
    
    # circuit
    elif direction == "next" and current_index >= conversations_len - 1:
        current_index = 0
    
    elif direction == "prev" and current_index <= 0:
        current_index = conversations_len - 1

    prev_data_type = deepcopy(data_type)
    
    return get_current_conversation(current_index, conversations_len, prev_data_type, data_type)


# change show conversation data type on UI
def change_conversation_data_type(prev_data_type, data_type, data_type_select, eval_data_type_select, current_index, conversations_len):

    # print(f"-- 1204 type(data_type_select): {type(data_type_select)}\n")
    # print(f"-- 1205 data_type_select: {data_type_select}\n")
    # print(f"-- 1206 type(eval_data_type_select): {type(eval_data_type_select)}\n")
    # print(f"-- 1207 eval_data_type_select: {eval_data_type_select}\n")

    # connect to chat mongo DB
    user_inter_data_table, new_json_user_conv_data_rate_table = connect_to_chat_db()
    conversation_datas = []

    
    # set previous and selected data type
    prev_data_type = deepcopy(data_type)
    
    select_data_type = {
        "select_data_cls": deepcopy(data_type_select),
        "eval_data_type": deepcopy(eval_data_type_select)
    }


    
    # get rate conversation data as json
    current_index, conversations_len, user_id_box, previous_conversations, user_input, system_output, modified_output, rating, save_status, model_score_box, model_feedback_box, gt_answer, processed_count, prev_data_type, select_data_type, system_cls_output, scenario_cls_output, doctor_edit_option_checkbox, scenario_cls_error_checkbox, sop_step_checkbox = get_current_conversation(current_index = current_index, conversations_len = conversations_len, prev_data_type = prev_data_type, data_type = select_data_type)

    
    prev_data_type = deepcopy(select_data_type)

    # print(f"-------------------------------------------------------------------------------\n")
    # print(f"-- 1204 scenario_cls_output: {scenario_cls_output}\n")
    # print(f"-- 1205 doctor_edit_option_checkbox: {doctor_edit_option_checkbox}\n")
    # print(f"-- 1206 sop_step_checkbox: {sop_step_checkbox}\n")
    # print(f"-- 1207 scenario_cls_error_checkbox: {scenario_cls_error_checkbox}\n")
    # print(f"-------------------------------------------------------------------------------\n")


    # prev_data_type, data_type
    return prev_data_type, select_data_type, current_index, conversations_len, user_id_box, previous_conversations, user_input, system_output, modified_output, rating, save_status, model_score_box, model_feedback_box, gt_answer, processed_count, prev_data_type, select_data_type, system_cls_output, scenario_cls_output, doctor_edit_option_checkbox, scenario_cls_error_checkbox, sop_step_checkbox


def save_changes(change_obj, current_index, conversations_len, user_id_box, previous_conversations, user_input, system_output, modified_output, rating, processed_count, prev_data_type, select_data_type, doctor_edit_option_checkbox, scenario_cls_error_checkbox, sop_step_checkbox):

    # print(f"-- 1464 sop_step_checkbox: {sop_step_checkbox}\n")
    # print(f"-- 1465 type(sop_step_checkbox): {type(sop_step_checkbox)}\n")

    # print(f"-- 1467 cls_step1_error_checkbox: {cls_step1_error_checkbox}\n")
    # print(f"-- 1468 type(cls_step1_error_checkbox): {type(cls_step1_error_checkbox)}\n")
    # raise

    print(f"-- 1035 change_obj: {change_obj}\n")
    print(f"-- 1036 rating: {rating}\n")
    print(f"-- 1037 modified_output: {modified_output}\n")
    print(f"-- 1038 scenario_cls_error_checkbox: {scenario_cls_error_checkbox}\n")
    print(f"-- 1039 doctor_edit_option_checkbox: {doctor_edit_option_checkbox}\n")
    print(f"-- 1040 user_input: {user_input}\n")
    # raise

    

    with db_lock:
        
        # connect to chat mongo DB
        user_inter_data_table, new_json_user_conv_data_rate_table = connect_to_chat_db()
        
        """保存修改的系統輸出和評分"""
        
        # update modify data to user_conv_data_rate_table
        # 使用 update_one 更新一筆資料
        filter_query = { 
            "uid": user_id_box,
            "prev_step_str": previous_conversations ,
            "user_response": user_input,
            "system_response": system_output
        }  # 選擇條件


        origin_modified_output = modified_output
        origin_scenario_cls_error_checkbox = scenario_cls_error_checkbox
        origin_sop_step_checkbox = sop_step_checkbox
        origin_doctor_edit_option_checkbox = doctor_edit_option_checkbox
        

        # if modified_output == None:
        #     modified_output = ""

        # if scenario_cls_error_checkbox == None:
        #     scenario_cls_error_checkbox = ""

        # if doctor_edit_option_checkbox == None:
        #     doctor_edit_option_checkbox = ""

        # elif doctor_edit_option_checkbox == '系統回應修正':
        #     scenario_cls_error_checkbox = ""


        # if sop_step_checkbox == None:
        #     sop_step_checkbox = ""

        # elif doctor_edit_option_checkbox != 'IOL判斷過程':
        #     sop_step_checkbox = ""


        # not intention or doctor not select sop step
        # update_operation = {
        #             "$set": { 
        #                 "system_response_rate": rating, 
        #                 "doctor_edit_response": modified_output,
        #                 "doctor_scenario_cls_error": scenario_cls_error_checkbox,
        #                 "iol_sop_error_step": sop_step_checkbox,   # not yet
        #                 "doctor_edit_option_checkbox": doctor_edit_option_checkbox
        #             }
        # }  
        


        # 空的不用寫?? 
        set_fields = {}
        keep_fields = {
            "system_response_rate": rating, 
            "doctor_edit_response": modified_output,
            "doctor_scenario_cls_error": scenario_cls_error_checkbox,
            "iol_sop_error_step": sop_step_checkbox,   # not yet
            "doctor_edit_option_checkbox": doctor_edit_option_checkbox
        }
        
        for field in keep_fields.keys():

            if keep_fields[field] != None and keep_fields[field] != "":

                set_fields[field] = keep_fields[field]


        if doctor_edit_option_checkbox in [ '系統回應', '最終總結推薦' ]:
            set_fields["iol_sop_error_step"] = ""
            set_fields["doctor_scenario_cls_error"] = ""
        


        print(f"-- 656 save to db scenario_cls_error_checkbox: {scenario_cls_error_checkbox}\n")

        update_operation = {
                    "$set": set_fields
        } 

        print(f"-- 1150 save to db update_operation: {update_operation}\n")
            
        result = new_json_user_conv_data_rate_table.update_one(filter_query, update_operation)
        conversation_datas = []
    
        # get rate conversation data as json
        current_index, conversations_len, user_id_box, previous_conversations, get_user_input, system_output, modified_output, rating, save_status, model_score_box, model_feedback_box, gt_answer, processed_count, prev_data_type, select_data_type, system_cls_output, scenario_cls_output, doctor_edit_option_checkbox, scenario_cls_error_checkbox, sop_step_checkbox = get_current_conversation(current_index = current_index, conversations_len = conversations_len, prev_data_type = prev_data_type, data_type = select_data_type, prev_str = previous_conversations, user_response = user_input, uid = user_id_box)
        

        # print(f"-- 647 user_input: {user_input}\n")
        
        hole_qa_backend_data_path = "./json_dialogue/hole_qa_v2_doctor_eval_data.json"
        all_rows = list(new_json_user_conv_data_rate_table.find())

        for row in all_rows:
            row.pop('_id', None)
        
        # save as json file
        with open(hole_qa_backend_data_path, "w", encoding = "utf-8") as file:
            json.dump(all_rows, file, indent = 4, ensure_ascii = False)
        
        print("successfully update all conversation datas json file for DB！")
        # print(f"-- 1673 cls_step1_error_checkbox: {cls_step1_error_checkbox}\n")


        # sop_step_checkbox scenario_cls_error_checkbox doctor_edit_option_checkbox modified_output_box rating_slider
        
        if change_obj in [ 'sop_step_checkbox',  'doctor_edit_option_checkbox', 'scenario_cls_error_checkbox' ]:

            return current_index, conversations_len, "評分已儲存!", processed_count, scenario_cls_error_checkbox, sop_step_checkbox, doctor_edit_option_checkbox

        else:
            return current_index, conversations_len, "評分已儲存!", processed_count, origin_scenario_cls_error_checkbox, origin_sop_step_checkbox, origin_doctor_edit_option_checkbox
            
        
        # return current_index, conversations_len, "評分已儲存!", processed_count, unprocessed_count
        # return current_index, conversations_len, "評分已儲存!", processed_count, scenario_cls_error_checkbox, sop_step_checkbox, doctor_edit_option_checkbox
        # return current_index, conversations_len, "評分已儲存!", processed_count, scenario_cls_error_checkbox, sop_step_checkbox

# dialogue_comment_page
# create_doctor_eval_ui
def dialogue_comment_page():

    build_sop_steps_map_dict()

    # connect to chat mongo DB
    user_inter_data_table, new_json_user_conv_data_rate_table = connect_to_chat_db()

    already_rate_conversation_datas = []
    not_rate_conversation_datas = []
    rate_conversation_datas = []
    

    # get rate conversation data as json
    already_rate_conversation_datas, not_rate_conversation_datas, rate_conversation_datas = read_and_set_conv_data_rate_table(new_json_user_conv_data_rate_table = new_json_user_conv_data_rate_table)

    with gr.Blocks(css="""
        #bold_label label, 
        #bold_label .block-title { font-weight: bold !important; } 
    
        footer { display: none !important; }
    
        #custom_textbox textarea { overflow: auto !important; }
    """) as demo:

        
        # each user has own current index and conversations_len
        current_index = gr.State(len(already_rate_conversation_datas))
        conversations_len = gr.State(len(rate_conversation_datas))

        
        # keep selecting show data type 
        data_type = gr.State({
            "select_data_cls": [ "推薦水晶體", "眼科科普", "診間對話" ],
            # "eval_data_type": [ "未評分", "只顯示經自動評分過濾資料" ]
            "eval_data_type": [ "未評分" ]
        })

        prev_data_type = gr.State({
            "select_data_cls": [ "推薦水晶體", "眼科科普", "診間對話" ],
            # "eval_data_type": [ "未評分", "只顯示經自動評分過濾資料" ]
            "eval_data_type": [ "未評分" ]
        })

        
        gr.Markdown("# 對話評分系統")
        
        gr.Markdown("### 資料篩選")
        with gr.Row():
            
            data_type_select = gr.CheckboxGroup(
                        choices = [ "推薦水晶體", "眼科科普", "診間對話"  ],
                        label = "按照類別(多選)",
                        value = [ "推薦水晶體", "眼科科普", "診間對話"  ],
                        scale = 50,
                        interactive = True,
                    )

            eval_data_type_select = gr.CheckboxGroup( # gr.Radio
                        # choices = [ "已評分", "未評分", "只顯示經自動評分過濾資料" ], #"只顯示經 gpt-4o 評分"
                        choices = [ "已評分", "未評分" ],
                        label = "按照評分與否(多選)",
                        # value = [ "未評分", "只顯示經自動評分過濾資料" ]
                        value = [ "未評分" ],
                        scale = 25,
                        interactive = True,
                    )

            processed_count = gr.Textbox(label = "已評分資料數量:", value = f"{len(already_rate_conversation_datas)}/{len(rate_conversation_datas)}", interactive = False, scale = 25)


        with gr.Row():

            with gr.Column():
                
                gr.Markdown("### 先前對話紀錄")
                previous_conversations = gr.Textbox(value = "", lines = 24, interactive = False, show_label = False, autoscroll = True)


            with gr.Column():
                
                gr.Markdown("### 目前對話")
                user_id_box = gr.Textbox(label = "使用者ID", interactive = False, visible = False)
                user_input_box = gr.Textbox(label = "使用者問題/回覆", interactive = False)
                
                system_cls_output_box = gr.Textbox(label = "系統問題分類", interactive = False, visible = False)
                scenario_cls_output = gr.Radio(
                    choices = [ "一", "二", "三"  ], 
                    label = "問題情境分類", 
                    visible = False
                )
                
                system_output_box = gr.Textbox(label = "系統回應", lines = 1, interactive = False, autoscroll = True, elem_id = "custom_textbox")


        with gr.Row():

            with gr.Column():
    
                # show llama3.1-405B evaluated score and feedback
                gr.Markdown("### 自動評分資訊")
                model_score_box = gr.Textbox(label = "模型評分", interactive = False)
                model_feedback_box = gr.Textbox(label = "模型 Feedback", lines = 8, interactive = False, autoscroll = True)
                model_answer_box = gr.Textbox(label = "ground truth 回答", lines = 8, interactive = False, autoscroll = True, visible = False)
                

            with gr.Column():
                
                gr.Markdown("### 醫生編輯")

                # intention classification error
                intention_cls_error_checkbox = gr.Radio(
                    choices = [ "推薦水晶體", "眼科科普", "診間對話"  ], 
                    label = "問題分類", 
                    visible = False
                )


                
                doctor_edit_option_checkbox = gr.Radio(
                    # choices = [ "情境分類", "系統回應"  ], 
                    choices = [],
                    label = "修正種類", 
                    visible = True
                )

                
                sop_step_checkbox = gr.Radio(
                    choices = [],
                    label = "SOP 流程最開始錯誤步驟",
                    visible = False
                )
                

                # scenario classification error
                scenario_cls_error_checkbox = gr.Radio(
                    choices = [ "一", "二", "三"  ], 
                    label = "問題情境分類", 
                    visible = False
                )
                
                modified_output_box = gr.Textbox(label = "修正內容", placeholder = "請修改系統輸出...", lines = 15, autoscroll = True)

                
                rating_slider = gr.Slider(1, 5, step = 1, label = "系統回應評分", value = 0)
                save_status = gr.Textbox(label = "評分保存狀態", interactive = False)
                

        
        with gr.Row():
            prev_btn = gr.Button("⬅️ 上一個")
            next_btn = gr.Button("下一個 ➡️")


        # 自動保存的函數
        sop_step_checkbox.change(save_changes, inputs = [ gr.State("sop_step_checkbox"), current_index, conversations_len, user_id_box, previous_conversations, user_input_box, system_output_box, modified_output_box, rating_slider, processed_count, prev_data_type, data_type, doctor_edit_option_checkbox, scenario_cls_error_checkbox, sop_step_checkbox ], outputs = [ current_index, conversations_len, save_status, processed_count, scenario_cls_error_checkbox, sop_step_checkbox, doctor_edit_option_checkbox ])

        
        scenario_cls_error_checkbox.change(save_changes, inputs = [ gr.State("scenario_cls_error_checkbox"), current_index, conversations_len, user_id_box, previous_conversations, user_input_box, system_output_box, modified_output_box, rating_slider, processed_count, prev_data_type, data_type, doctor_edit_option_checkbox, scenario_cls_error_checkbox, sop_step_checkbox ], outputs = [ current_index, conversations_len, save_status, processed_count, scenario_cls_error_checkbox, sop_step_checkbox, doctor_edit_option_checkbox ]) # , sop_step_checkbox, doctor_edit_option_checkbox

        
        doctor_edit_option_checkbox.change(save_changes, inputs = [gr.State("doctor_edit_option_checkbox"), current_index, conversations_len, user_id_box, previous_conversations, user_input_box, system_output_box, modified_output_box, rating_slider, processed_count, prev_data_type, data_type, doctor_edit_option_checkbox, scenario_cls_error_checkbox, sop_step_checkbox ], outputs = [ current_index, conversations_len, save_status, processed_count, scenario_cls_error_checkbox, sop_step_checkbox, doctor_edit_option_checkbox ])

        
        modified_output_box.change(save_changes, inputs = [ gr.State("modified_output_box"), current_index, conversations_len, user_id_box, previous_conversations, user_input_box, system_output_box, modified_output_box, rating_slider, processed_count, prev_data_type, data_type, doctor_edit_option_checkbox, scenario_cls_error_checkbox, sop_step_checkbox ], outputs = [ current_index, conversations_len, save_status, processed_count, scenario_cls_error_checkbox, sop_step_checkbox, doctor_edit_option_checkbox ])
        
        
        rating_slider.change(save_changes, inputs = [ gr.State("rating_slider"), current_index, conversations_len, user_id_box, previous_conversations, user_input_box, system_output_box, modified_output_box, rating_slider, processed_count, prev_data_type, data_type, doctor_edit_option_checkbox, scenario_cls_error_checkbox, sop_step_checkbox ], outputs = [ current_index, conversations_len, save_status, processed_count, scenario_cls_error_checkbox, sop_step_checkbox, doctor_edit_option_checkbox ])



        # change show conversation data type on UI
        data_type_select.change(
                    change_conversation_data_type,  
                    inputs = [ prev_data_type, data_type, data_type_select, eval_data_type_select, current_index, conversations_len ],  # input select intention type and eval data type
                    outputs = [ prev_data_type, data_type, current_index, conversations_len, user_id_box, previous_conversations, user_input_box, system_output_box, modified_output_box, rating_slider, save_status, model_score_box, model_feedback_box, model_answer_box, processed_count, prev_data_type, data_type, system_cls_output_box, scenario_cls_output, doctor_edit_option_checkbox, scenario_cls_error_checkbox, sop_step_checkbox ]          # update show conversation data result
                )
        
        eval_data_type_select.change(
                    change_conversation_data_type,  
                    inputs = [ prev_data_type, data_type, data_type_select, eval_data_type_select, current_index, conversations_len ],  # input select intention type and eval data type
                    outputs = [ prev_data_type, data_type, current_index, conversations_len, user_id_box, previous_conversations, user_input_box, system_output_box, modified_output_box, rating_slider, save_status, model_score_box, model_feedback_box, model_answer_box, processed_count, prev_data_type, data_type, system_cls_output_box, scenario_cls_output, doctor_edit_option_checkbox, scenario_cls_error_checkbox, sop_step_checkbox ]     
                )

        
        # 切換對話的按鈕
        prev_btn.click(navigate, inputs = [ gr.State("prev"), current_index, conversations_len, prev_data_type, data_type ], outputs = [current_index, conversations_len, user_id_box, previous_conversations, user_input_box, system_output_box, modified_output_box, rating_slider, save_status, model_score_box, model_feedback_box, model_answer_box, processed_count, prev_data_type, data_type, system_cls_output_box, scenario_cls_output, doctor_edit_option_checkbox, scenario_cls_error_checkbox, sop_step_checkbox ])
        
        next_btn.click(navigate, inputs = [ gr.State("next"), current_index, conversations_len, prev_data_type, data_type ], outputs = [ current_index, conversations_len, user_id_box, previous_conversations, user_input_box, system_output_box, modified_output_box, rating_slider, save_status, model_score_box, model_feedback_box, model_answer_box, processed_count, prev_data_type, data_type, system_cls_output_box, scenario_cls_output, doctor_edit_option_checkbox, scenario_cls_error_checkbox, sop_step_checkbox ]) # , model_feedback_box 



        # 使用 load事件：介面一載入就呼叫 get_current_conversation 函式
        demo.load(
            fn = get_current_conversation, 
            inputs = [
                current_index,
                conversations_len,
                prev_data_type,
                data_type
            ], 
            outputs = [
                current_index,
                conversations_len,
                user_id_box,
                previous_conversations,
                user_input_box,
                system_output_box,
                modified_output_box,
                rating_slider, 
                save_status,
                model_score_box,
                model_feedback_box,
                model_answer_box,
                processed_count,
                prev_data_type,
                data_type,
                system_cls_output_box,
                scenario_cls_output,
                doctor_edit_option_checkbox,
                scenario_cls_error_checkbox,
                sop_step_checkbox,
                # cls_step1_error_checkbox
            ]
        )
    
  
