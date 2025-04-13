import os
import re
import json
import requests
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import services.report_prompts as Prompts

# Load environment variables
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

class EvalCitation:
    def __init__(self, openai_key=None, twcc_key=None):
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")
        self.twcc_key = twcc_key or os.getenv("TWCC_API_KEY")
        self.openai_client = OpenAI(api_key=self.openai_key) if self.openai_key else None

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

    def _extract_citations(self, text: str) -> list[int]:
        return list(set(map(int, re.findall(r"\[(\d+)\]", text))))

    def _filter_indexed_dialogue(self, indexed_dialogue: str, citation_indices: list[int]) -> str:
        indexed_dialogue_lines = indexed_dialogue.split("\n")
        index_map = {
            int(match.group(1)): i
            for i, line in enumerate(indexed_dialogue_lines)
            if (match := re.match(r"\[(\d+)\]", line.strip()))
        }
        blocks = []
        for idx in citation_indices:
            start = index_map.get(idx)
            end = index_map.get(idx + 1, len(indexed_dialogue_lines))
            if start is not None:
                blocks.append("\n".join(indexed_dialogue_lines[start:end]))
        return "\n".join(blocks)

    def _extract_sentences(self, report_content: str) -> list[str]:
        return [
            line.strip()
            for line in report_content.splitlines()
            if re.search(r"\[\d+\]", line)
        ]

    async def _evaluate_sentence(self, sent: str, citations: list[int], indexed_dialogue: str, eval_model: str) -> dict:
        if not citations:
            return {
                "output": sent,
                "citations": citations,
                "warning": "No citations found"
            }

        relevant_indexed_dialogue = self._filter_indexed_dialogue(indexed_dialogue, citations)
        system_prompt = Prompts.gen_citation_system_context
        user_prompt = f"""
### **Relevant indexed_dialogue**
{relevant_indexed_dialogue}

### **Report Sentence for Validation**
{sent}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            if "gpt" in eval_model.lower():
                response = await self._call_openai(messages, eval_model)
            else:
                response = await self._call_nchc(messages, eval_model)

            json_block = re.search(r'\{.*?\}', response, re.DOTALL)
            if not json_block:
                raise ValueError("No valid JSON block found in response.")
            result = json.loads(json_block.group(0))
            return {
                "output": sent,
                "citations": citations,
                "provenance": result.get("provenance", []),
                "entailment_prediction": result.get("entailment_prediction", 0)
            }
        except Exception as e:
            return {
                "output": sent,
                "citations": citations,
                "error": str(e)
            }

    async def evaluate(self, report_content: str, indexed_dialogue: str, eval_model: str) -> list[dict]:
        print("[DEBUG] EvalCitation.py & Eval model received:", eval_model)
        sentences = self._extract_sentences(report_content)
        tasks = [
            self._evaluate_sentence(sent, self._extract_citations(sent), indexed_dialogue, eval_model)
            for sent in sentences
        ]
        return await asyncio.gather(*tasks)

