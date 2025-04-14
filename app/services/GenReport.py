import os
import json
import requests
import asyncio
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import services.report_prompts as Prompts

# Load .env for keys
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

class GenReport:
    def __init__(self, openai_key=None, twcc_key=None):
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")
        self.twcc_key = twcc_key or os.getenv("TWCC_API_KEY")
        self.openai_client = OpenAI(api_key=self.openai_key) if self.openai_key else None

    # Add index in front of indexed_dialogue lines for citation
    def add_index_to_indexed_dialogue(self, indexed_dialogue: str) -> str:
        lines = indexed_dialogue.splitlines(keepends=True)
        indexed_lines = []
        index = 1
        for line in lines:
            if line.startswith('使用者問題/回覆') or line.startswith('系統回覆'):
                indexed_lines.append(f'\n\n [{index}] {line}')
                index += 1
            else:
                indexed_lines.append(line)
        return ''.join(indexed_lines)

    # Format JSON report into Markdown
    def report_format_from_json(self, report_content: dict) -> str:
        def format_section(section_list):
            return '\n'.join(section_list) if section_list else "No information available"

        return f"""
#### **1. Patient Complaint**

{format_section(report_content.get("PatientComplaint", []))}

#### **2. Diagnosis**

{format_section(report_content.get("Diagnosis", []))}

#### **3. Recommended Medical Unit**

{format_section(report_content.get("RecommendedMedicalUnit", []))}

#### **4. Recommended Treatment**

{format_section(report_content.get("RecommendedTreatment", []))}
""".strip()

    async def _call_openai(self, messages, eval_model):
        if not self.openai_client:
            raise ValueError("OpenAI API key not found or client not initialized.")
        try:
            print(f"[OpenAI] Calling model: {eval_model}")
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=eval_model,
                messages=messages,
                max_tokens=2000,
                n=1,
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"[OpenAI Error] {e}")

    async def _call_nchc(self, messages, eval_model):
        if not self.twcc_key:
            raise ValueError("TWCC API key not found.")

        url = "https://medusa-poc.genai.nchc.org.tw/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.twcc_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": eval_model,
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0,
            "top_p": 0.92
        }

        try:
            print(f"[NCHC] Calling model: {eval_model}")
            response = await asyncio.to_thread(requests.post, url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            raise RuntimeError(f"[NCHC Error] {response.status_code}: {response.text}")
        except Exception as e:
            raise RuntimeError(f"[NCHC API Error] {e}")

    async def summary_report(self, indexed_dialogue: str, eval_model: str, object_type: str) -> str:
        """
        Generate report content using the specified LLM model.

        Args:
            indexed_dialogue (str): Indexed dialogue with citation [1], [2], ...
            eval_model (str): The name of the LLM model.
            object_type (str): 'Doctor' or 'Patient'

        Returns:
            str: Formatted report content as a Markdown string
        """
        # Preprocess indexed_dialogue
        # indexed_dialogue = self.add_index_to_indexed_dialogue(indexed_dialogue)

        if object_type == "Doctor":
            system_prompt = Prompts.gen_report_doctor_system_prompt
            user_prompt = Prompts.gen_report_doctor_user_prompt.replace("{dialogue}", indexed_dialogue)
        else:
            system_prompt = Prompts.gen_report_patient_system_prompt
            user_prompt = Prompts.gen_report_patient_user_prompt.replace("{dialogue}", indexed_dialogue)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        if "gpt" in eval_model.lower():
            report_content = await self._call_openai(messages, eval_model)
        else:
            report_content = await self._call_nchc(messages, eval_model)
        
        # Attempt to parse JSON regardless of object_type
        if object_type == "Doctor":
            try:
                # 提取有效的 JSON 部分
                start_marker = "```json\n"
                end_marker = "\n```"
                start_idx = report_content.find(start_marker)
                end_idx = report_content.rfind(end_marker)
                
                if start_idx == -1 or end_idx == -1:
                    raise ValueError(f"Invalid JSON format: ```json markers not found.\nContent: {report_content}")
                
                json_str = report_content[start_idx + len(start_marker):end_idx]
                report_content = json.loads(json_str)
                formatted_report = self.report_format_from_json(report_content)
            except Exception as e:
                raise ValueError(f"Failed to parse generated report: {e}\nContent: {report_content}")
        else:
            formatted_report = report_content

        return formatted_report