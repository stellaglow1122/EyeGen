import json
from pymongo import MongoClient
from copy import deepcopy
from db_utils_report import init_db
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
doctor_eval_data_v2_30_path = BASE_DIR / "json_dialogue" / "hole_qa_v2_doctor_eval_data_30.json"

def connect_to_db():
    db = init_db()
    collection = db['synthesis_json_user_conv_data_rate_v2']
    print(f"Connected to database: {db.name}")
    return collection

def insert_indexed_dialogue_to_mongo(json_path=doctor_eval_data_v2_30_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as json_file:
            doctor_eval_datas = json.load(json_file)
    except FileNotFoundError as e:
        print(f"Error: JSON file not found at {json_path}")
        return
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return
    
    print(f"len(doctor_eval_datas): {len(doctor_eval_datas)}\n")
    
    collection = connect_to_db()
    
    insert_cnt = 0
    skip_cnt = 0
    # iterate each indexed_dialogue datas
    for doctor_eval_data in doctor_eval_datas:
        update_fields = deepcopy({

            #### indexed_dialogue info
            'group_id': doctor_eval_data['group_id'],
            'uid': doctor_eval_data['uid'],
            'iter_idx': doctor_eval_data['iter_idx'],
            'origin_intent': doctor_eval_data['origin_intent'],
            'system_intent': doctor_eval_data['system_intent'],
            'current_subtask': doctor_eval_data['current_subtask'],
            'tags': doctor_eval_data['tags'],
            'system_judge_scenario': doctor_eval_data['system_judge_scenario'],

            #### for our systems
            'prev_step_str': doctor_eval_data['prev_step_str'],
            'user_response': doctor_eval_data['user_response'],
            'system_response': doctor_eval_data['system_response'],
            'system_retrieve_doc_paths': doctor_eval_data['system_retrieve_doc_paths'],
            'state': doctor_eval_data['state'],
            'subtasks': doctor_eval_data['subtasks'],

            #### for llama3.1-405B GT
            'gt_prev_step_str': doctor_eval_data['gt_prev_step_str'],
            'ground_truth_answer': doctor_eval_data['ground_truth_answer'],

            #### for auto evaluation (llama3.1-405B & gpt-4o-mini)
            'intention_cls_error': doctor_eval_data['intention_cls_error'],
            'scenario_cls_error': doctor_eval_data['scenario_cls_error'],
            'gpt_4o_mini_score': doctor_eval_data['gpt_4o_mini_score'],
            'gpt_4o_mini_feedback': doctor_eval_data['gpt_4o_mini_feedback'],
            'llama405b_score': doctor_eval_data['llama405b_score'],
            'llama405b_feedback': doctor_eval_data['llama405b_feedback'],
            'show_eval_model_score': doctor_eval_data.get('show_eval_model_score'),
            'show_eval_model_feedback': doctor_eval_data.get('show_eval_model_feedback'),

            #### for doctor eval ui
            'mark_need_label': doctor_eval_data['mark_need_label'],
            'mark_show_scenario_label': doctor_eval_data['mark_show_scenario_label'],

            #### for doctor
            "system_response_rate": doctor_eval_data['system_response_rate'],
            "doctor_edit_response": doctor_eval_data['doctor_edit_response'],
            "iol_sop_error_step": doctor_eval_data['iol_sop_error_step'],
            "doctor_intention_cls_error": doctor_eval_data['doctor_intention_cls_error'],
            "doctor_scenario_cls_error": doctor_eval_data['doctor_scenario_cls_error'],
            "doctor_edit_option_checkbox": doctor_eval_data['doctor_edit_option_checkbox']
        })
        
        # 定義唯一性條件
        filter_query = {
            'uid': doctor_eval_data['uid'],
            'prev_step_str': doctor_eval_data['prev_step_str'],
            'user_response': doctor_eval_data['user_response']
        }
        
        # insert corresponding data to doctor eval db
        # already insert in DB
        existing_data = collection.find_one(filter_query)
        if existing_data:
            skip_cnt += 1
            print(f"Skipped document {skip_cnt}: UID {doctor_eval_data['uid']} already exists.")
            continue
        
        # not in db yet -> insert
        try:
            result = collection.insert_one(update_fields)
            insert_cnt += 1
            print(f"Inserted document {insert_cnt} with _id: {result.inserted_id}")
        except Exception as e:
            print(f"Error inserting document: {e}")
    
    print(f"Successfully inserted {insert_cnt} new datas, skipped {skip_cnt} existing datas into db synthesis_json_user_conv_data_rate_v2 table !!!\n")

if __name__ == "__main__":
    insert_indexed_dialogue_to_mongo()