import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class LLM:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")

        if not self.api_key:
            raise ValueError("❌ OPENROUTER_API_KEY missing in .env")

        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        # Session client for re-use (faster)
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "http://localhost",
                "X-Title": "Appointment Scheduler Agent"
            }
        )

    async def respond(self, system_prompt: str, user_message: str, stream: bool = False):
        """
        Send a message to OpenRouter with retries, optional streaming.
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        }

        # ---- Optional: enable streaming ----
        if stream:
            payload["stream"] = True

        # ---- Retry logic ----
        for attempt in range(3):  # 3 retries
            try:
                response = await self.client.post(self.base_url, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]

                else:
                    print(f"⚠️ OpenRouter error {response.status_code}: {response.text}")

            except Exception as e:
                print(f"⚠️ Attempt {attempt+1} failed: {e}")

        raise RuntimeError("❌ LLM request failed after 3 retries")

    async def stream_reply(self, system_prompt: str, user_message: str):
        """
        Return a streaming generator for real-time tokens.
        """
        payload = {
            "model": self.model,
            "stream": True,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", self.base_url, json=payload) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            chunk = line.removeprefix("data: ")
                            if chunk != "[DONE]":
                                yield chunk
                        except:
                            continue
