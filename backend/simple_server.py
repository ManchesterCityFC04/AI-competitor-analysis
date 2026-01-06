# -*- coding: utf-8 -*-
"""
简单的后端服务器，用于测试
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 创建FastAPI应用
app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8888"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 简单的请求模型
class AnalysisRequest(BaseModel):
    domain: str
    product_name: str

# 健康检查端点
@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "Server is running"
    }

# 分析端点
@app.post("/api/analyze")
def analyze(request: AnalysisRequest):
    return {
        "domain": request.domain,
        "product_name": request.product_name,
        "query": f"{request.domain} 竞品分析 {request.product_name}",
        "competitors": [
            {"name": "竞品A", "features": ["功能1", "功能2", "功能3"]},
            {"name": "竞品B", "features": ["功能4", "功能5", "功能6"]},
            {"name": "竞品C", "features": ["功能7", "功能8", "功能9"]}
        ],
        "total_count": 3,
        "message": f"成功分析 {request.domain} 领域，发现 3 个竞品"
    }

# 根路径端点
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "竞品分析API",
        "endpoints": [
            "/health",
            "/api/analyze"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",  # 使用IPv4本地地址
        port=8001
    )
