"""
Novel2Script - AI 小说转结构化剧本工具
FastAPI 后端入口
"""
import os
import sys

print(f"[Main] Python 版本: {sys.version}")

# 先加载环境变量
env_file = os.path.join(os.path.dirname(__file__), ".env")
if not os.path.exists(env_file):
    env_file = os.path.join(os.path.dirname(__file__), "..", ".env")

if os.path.exists(env_file):
    print(f"[Main] 加载环境变量文件: {env_file}")
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()
else:
    print(f"[Main] 警告: 未找到 .env 文件: {env_file}")

print(f"[Main] 环境变量加载完成:")
print(f"  - LLM_PROVIDER: {os.getenv('LLM_PROVIDER', '未设置')}")
print(f"  - OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', '')[:10] if os.getenv('OPENAI_API_KEY') else '未设置'}...")
print(f"  - OPENAI_API_BASE: {os.getenv('OPENAI_API_BASE', '未设置')}")
print(f"  - LLM_MODEL: {os.getenv('LLM_MODEL', '未设置')}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import api

app = FastAPI(
    title="Novel2Script API",
    description="AI 小说转结构化剧本工具 API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api.router)


@app.get("/")
async def root():
    return {"message": "Novel2Script API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
