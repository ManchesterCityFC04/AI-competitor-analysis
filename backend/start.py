# -*- coding: utf-8 -*-
"""
后端服务启动脚本
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

# 配置日志
logger.add("backend.log", level="INFO", rotation="10 MB")

# 创建FastAPI应用
app = FastAPI(title="竞品分析API", debug=True)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8888"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class AnalysisRequest(BaseModel):
    domain: str  # 分析领域
    product_name: str  # 产品名称

# 响应模型
class Competitor(BaseModel):
    name: str  # 竞品名称
    features: list[str]  # 核心功能

class AnalysisResponse(BaseModel):
    domain: str
    product_name: str
    query: str
    competitors: list[Competitor]
    total_count: int
    message: str

# 简单的健康检查端点
@app.get("/health")
def health_check():
    """
    健康检查
    """
    return {
        "status": "ok",
        "message": "竞品分析API运行正常",
        "version": "1.0.0"
    }

# 简单的分析端点（模拟数据）
@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze(request: AnalysisRequest):
    """
    执行竞品分析（模拟）
    """
    logger.info(f"收到分析请求：领域={request.domain}, 产品={request.product_name}")
    
    # 模拟数据
    mock_competitors = [
        {
            "name": "竞品A",
            "features": ["智能分析", "自动生成报告", "实时监控"]
        },
        {
            "name": "竞品B",
            "features": ["数据分析", "预测建模", "自然语言处理"]
        },
        {
            "name": "竞品C",
            "features": ["机器学习", "深度学习", "计算机视觉"]
        }
    ]
    
    return AnalysisResponse(
        domain=request.domain,
        product_name=request.product_name,
        query=f"{request.domain} 竞品分析 {request.product_name}",
        competitors=mock_competitors,
        total_count=len(mock_competitors),
        message=f"成功分析 {request.domain} 领域，发现 {len(mock_competitors)} 个竞品"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "start:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
