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

        # 从环境变量读取 .env 文件
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_file):
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
            self.api_key = os.getenv("OPENAI_API_KEY", self.api_key)
            self.base_url = os.getenv("OPENAI_API_BASE", self.base_url)
            if os.getenv("LLM_MODEL"):
                self.model = os.getenv("LLM_MODEL", self.model)

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

        print(f"[LLM Provider] 初始化 - 类型: {self.provider_type}")
        print(f"[LLM Provider] Base URL: {self.base_url}")
        print(f"[LLM Provider] Model: {self.model}")
        print(f"[LLM Provider] API Key: {self.api_key[:10]}...")

    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """统一的生成接口"""
        print(f"[LLM Provider] 开始生成请求...")

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

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                print(f"[LLM Provider] 发送请求到: {self.base_url}/chat/completions")
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                print(f"[LLM Provider] 响应状态码: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                result = data["choices"][0]["message"]["content"]
                print(f"[LLM Provider] 生成成功，长度: {len(result)}")
                return result
        except httpx.HTTPStatusError as e:
            print(f"[LLM Provider] HTTP 错误: {e.response.status_code}")
            print(f"[LLM Provider] 响应内容: {e.response.text}")
            raise Exception(f"API 请求失败: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"[LLM Provider] 错误: {e}")
            raise

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
