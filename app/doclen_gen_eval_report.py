import asyncio
import os
import json
import pytz
import random
import string
from datetime import datetime
from tqdm import tqdm
from services.GenReport import GenReport
from services.EvalCitation import EvalCitation
from services.EvalMetrics import EvalMetrics

SAVE_DIR = "./json_metrics"
os.makedirs(SAVE_DIR, exist_ok=True)

def generate_random_suffix(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def gen_eval_report(dialogue: str, gen_model: str, eval_model: str, object_type: str):
    # Step 0: add index in dialogue
    reporter = GenReport()
    indexed_dialogue = reporter.add_index_to_indexed_dialogue(dialogue)
    # Step 1: gen report
    report_content = await reporter.summary_report(indexed_dialogue, gen_model, object_type)
    # Step 2: eval report
    citation_evaluator = EvalCitation()
    citation_result = await citation_evaluator.evaluate(report_content, indexed_dialogue, eval_model)
    # Step 3: compute citation
    metrics_computer = EvalMetrics()
    metrics = await metrics_computer.compute(citation_result)
    return indexed_dialogue, report_content, citation_result, metrics

SEMAPHORE = asyncio.Semaphore(20)  # 控制最大並行任務數

async def process_single_model(dialogue, dialogue_idx, gen_model, eval_model, object_type, progress: tqdm):
    async with SEMAPHORE:
        task_name = f"dialogue_{dialogue_idx} | {gen_model}"
        try:
            progress.set_description(f"🧠 Processing {task_name}")
            indexed_dialogue, report_content, citation_result, metrics = await gen_eval_report(
                dialogue, gen_model, eval_model, object_type
            )

            taipei_tz = pytz.timezone("Asia/Taipei")
            upload_time = datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
            time_id = upload_time.replace("-", "").replace(" ", "").replace(":", "")
            random_suffix = generate_random_suffix(8)
            idx = f"{time_id}-{random_suffix}"

            object_idx = f"dialogue-{dialogue_idx}"
            output_data = {
                "idx": idx,
                "upload_time": upload_time,
                "object_idx": object_idx,
                "object_name": "test",
                "object_type": object_type,
                "gen_model": gen_model,
                "eval_model": eval_model,
                "dialogue_content": indexed_dialogue,
                "report_content": report_content,
                "citation_result": citation_result,
                "metrics": metrics
            }

            # Creat sub-folder：./json_metrics/gen_model/
            sub_dir = os.path.join(SAVE_DIR, gen_model)
            os.makedirs(sub_dir, exist_ok=True)

            filename = f"{object_idx}_{gen_model}_{eval_model}.json"
            save_path = os.path.join(sub_dir, filename)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"[INFO] ✅ Saved: {save_path}")
        except Exception as e:
            print(f"[ERROR] ❌ Failed: {task_name} | {str(e)}")
        finally:
            progress.update(1)

async def main():
    dialogue_path = "./json_dialogue/hole_qa_conversation_process_patient_doctor_v3.json"
    eval_model = "Llama-3.1-405B-Instruct-FP8"
    object_type = "Doctor"
    gen_models = [
        "gpt-4o-mini",
        "Llama-3.3-70B-Instruct",
        "Llama3-TAIDE-LX-70B-Chat",
        "Mistral-Small-24B-Instruct-2501",
        "Llama-3.1-8B-Instruct"
    ]

    with open(dialogue_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_tasks = len(data) * len(gen_models)
    print(f"[INFO] 🚀 Launching {total_tasks} async tasks...")

    progress = tqdm(total=total_tasks, ncols=100)

    tasks = [
        process_single_model(dialogue, i, gen_model, eval_model, object_type, progress)
        for i, dialogue in enumerate(data)
        for gen_model in gen_models
    ]

    await asyncio.gather(*tasks)
    # for task in tasks:
    #     await task
    progress.close()
    print(f"[INFO] ✅ All tasks completed.")

if __name__ == "__main__":
    asyncio.run(main())
