import os
import json
import requests
from openai import OpenAI
import asyncio
import services.report_prompts as Prompts
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

class GenReport:
    def __init__(self, openai_key=None, twcc_key=None):
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")
        self.twcc_key = twcc_key or os.getenv("TWCC_API_KEY")
        self.client = None

    async def llm_openai(self, user_context, system_context, model_name):
        if not self.openai_key:
            raise ValueError("OpenAI API key not found.")

        if self.client is None:
            self.client = OpenAI(api_key=self.openai_key)

        try:
            print(f"Calling OpenAI model: {model_name}")
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=model_name,
                messages=[
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": user_context}
                ],
                max_tokens=2000,
                n=1,
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}")

    async def llm_nchc(self, user_context, system_context, model_name):
        if not self.twcc_key:
            raise ValueError("TWCC API key not found.")

        url = "https://medusa-poc.genai.nchc.org.tw/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.twcc_key}",
            "Content-Type": "application/json"
        }
        data = {
            "max_tokens": 2000,
            "messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": user_context}
            ],
            "model": model_name,
            "temperature": 0,
            "top_p": 0.92
        }

        try:
            print(f"Calling NCHC model: {model_name}")
            response = await asyncio.to_thread(requests.post, url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            raise RuntimeError(f"NCHC API failed: {response.status_code} {response.text}")
        except Exception as e:
            raise RuntimeError(f"NCHC API call failed: {e}")

    def report_format_from_json(self, report_json):
        def format_section(section_list):
            return '\n'.join(section_list) if section_list else "No relevant information"

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

    async def summary_report(self, dialogue, model_name, user_type):
        if user_type == "doctor":
            system_context = Prompts.gen_report_doctor_system_prompt
            user_context = Prompts.gen_report_doctor_user_prompt.replace("{dialogue}", dialogue)
        else:
            system_context = Prompts.gen_report_patient_system_prompt
            user_context = Prompts.gen_report_patient_user_prompt.replace("{dialogue}", dialogue)

        if model_name == "gpt-4o-mini":
            report_content = await self.llm_openai(user_context, system_context, model_name)
        else:
            report_content = await self.llm_nchc(user_context, system_context, model_name)

        if user_type == "doctor":
            report_content = report_content.strip("```json\n").strip("```")
            try:
                report_json = json.loads(report_content)
                return self.report_format_from_json(report_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON response: {e}\nContent: {report_content}")
        else:
            return report_content.strip()
