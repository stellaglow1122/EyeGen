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

    # Add index in front of dialogue lines for citation
    def add_index_to_dialogue(self, dialogue: str) -> str:
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
    def report_format_from_json(self, report_json: dict) -> str:
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

    async def _call_openai(self, messages, gen_model):
        if not self.openai_client:
            raise ValueError("OpenAI API key not found or client not initialized.")
        try:
            print(f"[OpenAI] Calling model: {gen_model}")
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=gen_model,
                messages=messages,
                max_tokens=2000,
                n=1,
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"[OpenAI Error] {e}")

    async def _call_nchc(self, messages, gen_model):
        if not self.twcc_key:
            raise ValueError("TWCC API key not found.")

        url = "https://medusa-poc.genai.nchc.org.tw/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.twcc_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": gen_model,
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0,
            "top_p": 0.92
        }

        try:
            print(f"[🔁 NCHC] Calling model: {gen_model}")
            response = await asyncio.to_thread(requests.post, url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            raise RuntimeError(f"[NCHC Error] {response.status_code}: {response.text}")
        except Exception as e:
            raise RuntimeError(f"[NCHC API Error] {e}")

    async def summary_report(self, dialogue: str, gen_model: str, user_type: str) -> str:
        """
        Generate report content using the specified LLM model.

        Args:
            dialogue (str): Indexed dialogue with citation [1], [2], ...
            gen_model (str): The name of the LLM model.
            user_type (str): 'doctor' or 'patient'

        Returns:
            str: Raw report content (can be JSON or plain text)
        """

        # Preprocess dialogue
        indexed_dialogue = self.add_index_to_dialogue(dialogue)

        if user_type == "Doctor":
            system_prompt = Prompts.gen_report_doctor_system_prompt
            user_prompt = Prompts.gen_report_doctor_user_prompt.replace("{dialogue}", dialogue)
        else:
            system_prompt = Prompts.gen_report_patient_system_prompt
            user_prompt = Prompts.gen_report_patient_user_prompt.replace("{dialogue}", dialogue)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        if "gpt" in gen_model.lower():
            report_content =  await self._call_openai(messages, gen_model)
        else:
            report_content = await self._call_nchc(messages, gen_model)
        
        # Attempt to parse JSON regardless of user_type
        if user_type == "Doctor":
            
            try:
                cleaned_content = report_content.strip("```json").strip("```")
                report_json = json.loads(cleaned_content)
                formatted_report = self.report_format_from_json(report_json) 
            except Exception as e:
                raise ValueError(f"Failed to parse generated report: {e}\nContent: {report_content}")
        else:
            formatted_report = report_content

        # Add LLM information at the bottom
        formatted_report += f"""\n\n ---
                            \n\n**Generate LLM summary report:** {gen_model}\n\n
                             \n\n**User Type:** {user_type}\n\n"""
        
        # Add dialogue with citation at the bottom 
        formatted_report += f"""**Dialogue with index:** \n\n{indexed_dialogue}"""

        return formatted_report
