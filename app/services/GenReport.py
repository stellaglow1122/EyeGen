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

    async def _call_openai(self, messages, model_name):
        if not self.openai_client:
            raise ValueError("OpenAI API key not found or client not initialized.")
        try:
            print(f"[OpenAI] Calling model: {model_name}")
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=model_name,
                messages=messages,
                max_tokens=2000,
                n=1,
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"[OpenAI Error] {e}")

    async def _call_nchc(self, messages, model_name):
        if not self.twcc_key:
            raise ValueError("TWCC API key not found.")

        url = "https://medusa-poc.genai.nchc.org.tw/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.twcc_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model_name,
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0,
            "top_p": 0.92
        }

        try:
            print(f"[🔁 NCHC] Calling model: {model_name}")
            response = await asyncio.to_thread(requests.post, url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            raise RuntimeError(f"[NCHC Error] {response.status_code}: {response.text}")
        except Exception as e:
            raise RuntimeError(f"[NCHC API Error] {e}")

    async def summary_report(self, dialogue: str, model_name: str, user_type: str) -> str:
        """
        Generate report content using the specified LLM model.

        Args:
            dialogue (str): Indexed dialogue with citation [1], [2], ...
            model_name (str): The name of the LLM model.
            user_type (str): 'doctor' or 'patient'

        Returns:
            str: Raw report content (can be JSON or plain text)
        """
        if user_type == "doctor":
            system_prompt = Prompts.gen_report_doctor_system_prompt
            user_prompt = Prompts.gen_report_doctor_user_prompt.replace("{dialogue}", dialogue)
        else:
            system_prompt = Prompts.gen_report_patient_system_prompt
            user_prompt = Prompts.gen_report_patient_user_prompt.replace("{dialogue}", dialogue)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        if "gpt" in model_name.lower():
            return await self._call_openai(messages, model_name)
        else:
            return await self._call_nchc(messages, model_name)
