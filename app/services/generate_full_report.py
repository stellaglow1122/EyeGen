import os
import json
import uuid
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from services.GenReport import GenReport
from services.EvalCitation import EvalCitation
from services.EvalMetrics import EvalMetrics

# Load environment variables
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

SAVE_DIR = Path(__file__).resolve().parents[1] / "json_report"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# Add index in front of dialogue lines for citation
def add_index_to_dialogue(dialogue: str) -> str:
    lines = dialogue.splitlines(keepends=True)
    indexed_lines = []
    index = 1
    for line in lines:
        if line.startswith('使用者問題/回覆') or line.startswith('系統回覆'):
            indexed_lines.append(f'[{index}] {line}')
            index += 1
        else:
            indexed_lines.append(line)
    return ''.join(indexed_lines)

# Format JSON report into Markdown
def report_format_from_json(report_json: dict) -> str:
    def format_section(section_list):
        return '\n'.join(section_list) if section_list else "No information available"

    return f"""### Intelligent Ophthalmology Professional Medical Agent Summary Report

#### **1. Patient Complaint**

{format_section(report_json.get("PatientComplaint", []))}

#### **2. Diagnosis**

{format_section(report_json.get("Diagnosis", []))}

#### **3. Recommended Medical Unit**

{format_section(report_json.get("RecommendedMedicalUnit", []))}

#### **4. Recommended Intraocular Lens (IOL)**

{format_section(report_json.get("RecommendedIntraocularLens (IOL)", []))}
""".strip()

# Generate report pipeline
async def generate_full_report(dialogue: str, gen_model: str, user_type: str, eval_model: str):
    print("[DEBUG] Running generate_full_report")

    # Generate unique IDs
    dialogue_id = f"dialogue_{uuid.uuid4().hex[:8]}"
    report_id = f"report_{dialogue_id}"

    # Preprocess dialogue
    indexed_dialogue = add_index_to_dialogue(dialogue)

    # Generate report using GenReport
    reporter = GenReport()
    report_content = await reporter.summary_report(indexed_dialogue, gen_model, user_type)

    # Attempt to parse JSON regardless of user_type
    if user_type == "doctor":
        
        try:
            cleaned_content = report_content.strip("```json").strip("```")
            report_json = json.loads(cleaned_content)
            formatted_report = report_format_from_json(report_json) 
        except Exception as e:
            raise ValueError(f"Failed to parse generated report: {e}\nContent: {report_content}")
    else:
        formatted_report = report_content 

    return formatted_report, "Coming soon", "Coming soon"

    # # Evaluate citations
    # evaluator = EvalCitation()
    # citation_result = evaluator.evaluate(report_json, indexed_dialogue, eval_model)

    # # Compute metrics
    # metrics = EvalMetrics.compute_citation_metrics({report_id: citation_result})
    # metrics_summary = {
    #     "citation_recall": metrics.get("citation_recall", 0.0),
    #     "citation_precision": metrics.get("citation_precision", 0.0),
    #     "total_entailed": metrics.get("total_entailed", 0),
    #     "total_of_sent": metrics.get("total_of_sent", 0),
    #     "total_matched_citations": metrics.get("total_matched_citations", 0),
    #     "total_citations": metrics.get("total_citations", 0),
    # }

    # formatted_report = report_format_from_json(report_json) if user_type == "doctor" else report_content 

    # full_report_json = {
    #         "report_id": report_id,
    #         "dialogue_id": dialogue_id,
    #         "user_type": user_type,
    #         "gen_model": gen_model,
    #         "eval_model": eval_model,
    #         **metrics_summary,
    #         "report_content": formatted_report,
    #         "report_json": report_json,
    #         "citation_result": citation_result,
    #         "dialogue_content": indexed_dialogue,
    #         "action": "add"
    #     }


    # save_path = SAVE_DIR / f"{report_id}.json"
    # with open(save_path, "w", encoding="utf-8") as f:
    #     json.dump(full_report_json, f, ensure_ascii=False, indent=2)
    # print(f"[✔] Report generated and evaluated. Saved to {save_path}")

    # return formatted_report, metrics_summary["citation_recall"], metrics_summary["citation_precision"]

