import os
import json
import requests
import asyncio
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import services.report_prompts as Prompts
import re

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

        # check the format tag in dialogue
        has_tags = any(
            line.startswith('使用者問題/回覆') or line.startswith('系統回覆')
            for line in lines
        )

        if has_tags:
            for line in lines:
                if line.startswith('使用者問題/回覆') or line.startswith('系統回覆'):
                    indexed_lines.append(f'\n\n [{index}] {line}')
                    index += 1
                else:
                    indexed_lines.append(line)
        else:
            for line in lines:
                # skip the empty line
                if line.strip():
                    indexed_lines.append(f' [{index}] {line}')
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
  
    def parse_json_from_llm_output(self, content: str) -> dict:
        # Step 1: Normalize special characters
        content = content.replace("“", '"').replace("”", '"')\
                        .replace("‘", "'").replace("’", "'")\
                        .replace("\u2028", "").replace("\u2029", "").strip()

        # Step 2: Remove ```json blocks
        content = re.sub(r"^```json\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

        # Step 3: Extract from first {
        match = re.search(r"{[\s\S]*", content)
        if not match:
            raise ValueError("❌ No valid JSON object found.")
        content = match.group(0)

        # Step 4: Process line-by-line and fix incomplete strings
        lines = content.splitlines()
        fixed_lines = []

        for line in lines:
            line = line.strip()

            # Remove any inner " inside strings
            quote_match = re.match(r'^"- .*"(.*?)$', line)
            if quote_match:
                line = line.replace('"', '')  # drop internal quote
                line = f'"{line}"'  # wrap again

            # Fix line with missing quote at end (truncate and close)
            if line.count('"') % 2 != 0:
                line = line + '"'  # close the quote if odd

            fixed_lines.append(line)

        # Step 5: Add commas between items if needed
        new_lines = []
        for i in range(len(fixed_lines)):
            current = fixed_lines[i].strip()
            next_line = fixed_lines[i+1].strip() if i < len(fixed_lines) - 1 else ""
            new_lines.append(fixed_lines[i])

            if (
                current.endswith('"') and not current.endswith(',') and
                (next_line.startswith('"') or next_line.startswith('- "') or next_line.startswith(']') or next_line.startswith('}'))
            ):
                new_lines[-1] = current + ','

        # Step 6: Remove trailing commas before ] or }
        for i in range(len(new_lines)-1):
            if new_lines[i+1].strip() in [']', '}', '],', '},']:
                new_lines[i] = re.sub(r',\s*$', '', new_lines[i])

        # Step 7: Join and fix brackets
        json_str = "\n".join(new_lines)
        json_str += ']' * max(0, json_str.count('[') - json_str.count(']'))
        json_str += '}' * max(0, json_str.count('{') - json_str.count('}'))

        # Final quote fix
        if json_str.count('"') % 2 != 0:
            json_str += '"'

        # Step 8: Try parse
        try:
            print("✅ JSONSuccessfuls:")
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print("❌ JSONDecodeError:", e)
            print("🧪 Final Attempt:\n", json_str[:1000])
            raise

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

        # For doctor-type reports, try to parse and format JSON response
        if object_type == "Doctor":
            try:
                parsed_json = self.parse_json_from_llm_output(report_content)
                formatted_report = self.report_format_from_json(parsed_json)
            except Exception as e:
                raise ValueError(f"❌ Failed to parse generated report: {e}\nOriginal Content:\n{report_content}")
        else:
            # For patient, keep the raw string output
            formatted_report = report_content

        return formatted_report
