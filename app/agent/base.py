import os
from abc import ABC
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class BaseAgent(ABC):
    def __init__(self, default_model: str):
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        if openrouter_api_key:
            self.client = OpenAI(
                base_url=os.getenv(
                    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
                ),
                api_key=openrouter_api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/Truong99zvc/ai-newsletter-agent",
                    "X-Title": "AI News Aggregator",
                },
            )
            # Allow model override, otherwise map standard names to OpenRouter format
            model_override = os.getenv("OPENROUTER_MODEL") or os.getenv("LLM_MODEL")
            if model_override:
                self.model = model_override
            else:
                if default_model == "gpt-4o-mini":
                    self.model = "openai/gpt-4o-mini"
                elif default_model == "gpt-4.1":
                    self.model = "openai/gpt-4"
                else:
                    self.model = default_model
        else:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = os.getenv("LLM_MODEL") or default_model
