"""
LLM Provider - 统一的大模型调用接口
支持 OpenAI API、Qwen API、DeepSeek、本地 vLLM
"""
import os
import httpx
from typing import Optional


class LLMProvider:
    def __init__(
        self,
        provider_type: str = "openai",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-3.5-turbo"
    ):
        self.provider_type = provider_type
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model = model

        if provider_type == "qwen":
            self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
            self.model = model or "qwen-max"
        elif provider_type == "deepseek":
            self.base_url = base_url or "https://api.deepseek.com/v1"
            self.model = model or "deepseek-chat"
        elif provider_type == "deepseekv4pro":
            self.base_url = base_url or "https://api.deepseek.com/v1"
            self.model = model or "deepseek-chat"
        elif provider_type == "vllm":
            self.base_url = base_url or "http://localhost:8000/v1"
            self.model = model or "meta-llama/Llama-2-7b-chat-hf"

    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """统一的生成接口"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4000
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def generate_stream(self, prompt: str, system: Optional[str] = None):
        """流式生成接口"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4000,
            "stream": True
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        import json
                        chunk = json.loads(data)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]


def create_llm_provider() -> LLMProvider:
    """从环境变量创建 LLM Provider"""
    provider_type = os.getenv("LLM_PROVIDER", "openai")
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_API_BASE", "")
    model = os.getenv("LLM_MODEL", "")

    return LLMProvider(
        provider_type=provider_type,
        api_key=api_key,
        base_url=base_url if base_url else None,
        model=model if model else None
    )
