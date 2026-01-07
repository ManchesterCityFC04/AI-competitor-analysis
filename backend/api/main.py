# -*- coding: utf-8 -*-
"""
后端API入口
"""

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from loguru import logger

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.llm.client import get_llm_client
from backend.tools.anspire_search import AnspireSearch
from backend.agent.competitor_agent import CompetitorAnalysisAgent

# 配置日志
logger.add("backend.log", level="INFO", rotation="10 MB")

# 创建FastAPI应用
app = FastAPI(title="竞品分析API", debug=True)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，用于开发
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",  # 允许localhost和127.0.0.1的所有端口
)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 获取配置
ANSPIRE_API_KEY = os.getenv("ANSPIRE_API_KEY", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")

# 初始化工具实例
anspire_search = AnspireSearch(api_key=ANSPIRE_API_KEY)
competitor_agent = CompetitorAnalysisAgent(anspire_search)

# 请求模型
class AnalysisRequest(BaseModel):
    domain: Optional[str] = None  # 领域（可选）
    features: Optional[str] = None  # 功能描述（可选）
    product_name: str  # 产品名称

# 响应模型
class Competitor(BaseModel):
    name: str  # 竞品名称
    features: list[str]  # 核心功能

class AnalysisResponse(BaseModel):
    domain: Optional[str]
    features: Optional[str]
    product_name: str
    queries: list[str]  # 查询列表
    competitors: list[Competitor]
    total_count: int
    message: str

# API端点
@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """
    执行竞品分析（领域和功能同时并行搜索）
    """
    try:
        logger.info(f"收到分析请求：领域={request.domain}, 功能={request.features}, 产品={request.product_name}")

        # 验证至少有一个输入
        if not request.domain and not request.features:
            raise HTTPException(status_code=400, detail="请至少输入领域或功能")

        # 初始化LLM客户端
        llm_client = get_llm_client(LLM_API_KEY, LLM_BASE_URL)

        # 执行竞品分析
        result = competitor_agent.run(
            domain=request.domain,
            features=request.features,
            product_name=request.product_name,
            llm_client=llm_client,
            model=LLM_MODEL,
            max_results=5
        )

        # 生成消息
        parts = []
        if request.domain:
            parts.append(f"领域 '{request.domain}'")
        if request.features:
            parts.append(f"功能描述")
        message = f"成功分析 {' 和 '.join(parts)}，共 {len(result['queries'])} 个查询，发现 {result['total_count']} 个竞品"

        return AnalysisResponse(
            domain=result["domain"],
            features=result["features"],
            product_name=result["product_name"],
            queries=result["queries"],
            competitors=result["competitors"],
            total_count=result["total_count"],
            message=message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))

# 健康检查端点
@app.get("/health")
async def health_check():
    """
    健康检查
    """
    return {
        "status": "ok",
        "message": "竞品分析API运行正常",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
