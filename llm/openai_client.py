import os
import requests
from typing import Optional
from dotenv import load_dotenv
import logging
load_dotenv()

# Use variável de ambiente para a chave da API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-3.5-turbo"

logger = logging.getLogger(__name__)

class OpenAIClient:
    @staticmethod
    def generate(prompt: str) -> str:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY environment variable not set.")
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "Você é um assistente educacional. Responda apenas com JSON válido."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1024
        }
        try:
            response = requests.post(OPENAI_URL, headers=headers, json=payload, timeout=120)
        except requests.RequestException as exc:
            logger.exception("OpenAI request failed")
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc

        if not response.ok:
            error_body = response.text[:1000]
            logger.error(
                "OpenAI API error status=%s body=%s",
                response.status_code,
                error_body,
            )
            raise RuntimeError(
                f"OpenAI API error: {response.status_code} {response.reason} - {error_body}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            logger.error("OpenAI returned invalid JSON: %s", response.text[:1000])
            raise RuntimeError("OpenAI returned invalid JSON.") from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("OpenAI response missing expected content: %s", data)
            raise RuntimeError("OpenAI response missing expected content.") from exc
