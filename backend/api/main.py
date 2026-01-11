# -*- coding: utf-8 -*-
"""
后端API入口
"""

import os
import sys
import json
import asyncio
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Any
from loguru import logger
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.llm.client import get_llm_client
from backend.tools.anspire_search import AnspireSearch
from backend.agent.competitor_agent import CompetitorAnalysisAgent

# 配置日志
logger.add("backend.log", level="INFO", rotation="10 MB")

# 创建FastAPI应用
app = FastAPI(title="竞品分析API", debug=True)

# 配置CORS - 开发环境允许所有localhost端口
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    score: int = 5  # 相关性评分
    reason: str = ""  # 评分理由
    name: str  # 竞品名称
    features: list[str]  # 核心功能

class SourceLink(BaseModel):
    title: str
    url: str

class Recommendation(BaseModel):
    title: str = ""
    detail: str = ""

class Insights(BaseModel):
    summary: str = ""
    market_stage: str = ""
    must_have_features: List[str] = []
    differentiators: List[str] = []
    recommendations: List[Any] = []
    risks: List[str] = []

class AnalysisResponse(BaseModel):
    domain: Optional[str]
    features: Optional[str]
    product_name: str
    queries: list[str]  # 查询列表
    competitors: list[Competitor]
    total_count: int
    message: str
    source_links: List[SourceLink] = []
    insights: Optional[Insights] = None

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
            message=message,
            source_links=result.get("source_links", []),
            insights=result.get("insights")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))

# 线程池用于运行同步任务
executor = ThreadPoolExecutor(max_workers=2)

# SSE流式分析端点
@app.get("/api/analyze/stream")
async def analyze_stream(
    domain: Optional[str] = Query(None),
    features: Optional[str] = Query(None),
    product_name: str = Query(...)
):
    """
    流式竞品分析，通过SSE推送进度
    """
    async def event_generator():
        try:
            # 验证输入
            if not domain and not features:
                yield f"data: {json.dumps({'type': 'error', 'message': '请至少输入领域或功能'})}\n\n"
                return

            logger.info(f"[SSE] 开始流式分析：领域={domain}, 功能={features}, 产品={product_name}")

            # 发送初始化进度
            yield f"data: {json.dumps({'type': 'progress', 'stage': 'init', 'progress': 5, 'detail': '正在初始化分析...'})}\n\n"
            await asyncio.sleep(0.1)

            # 发送查询生成进度
            yield f"data: {json.dumps({'type': 'progress', 'stage': 'query', 'progress': 10, 'detail': '正在生成搜索查询...'})}\n\n"
            await asyncio.sleep(0.1)

            # 初始化LLM客户端
            llm_client = get_llm_client(LLM_API_KEY, LLM_BASE_URL)

            # 发送搜索进度
            yield f"data: {json.dumps({'type': 'progress', 'stage': 'search', 'progress': 25, 'detail': '正在搜索竞品信息...'})}\n\n"

            # 在线程池中运行同步任务
            loop = asyncio.get_event_loop()

            # 分阶段执行并发送进度
            # 阶段1: 生成查询
            queries_data = await loop.run_in_executor(
                executor,
                lambda: competitor_agent.generate_search_queries(domain, features, product_name, llm_client, LLM_MODEL)
            )
            query_strings = [q["query"] for q in queries_data]

            yield f"data: {json.dumps({'type': 'progress', 'stage': 'search', 'progress': 35, 'detail': f'生成了 {len(query_strings)} 个搜索查询，开始搜索...'})}\n\n"
            await asyncio.sleep(0.1)

            # 阶段2: 并行搜索
            raw_results = await loop.run_in_executor(
                executor,
                lambda: competitor_agent.search_all_parallel(queries_data, 5)
            )
            search_results = list({r["url"]: r for r in raw_results}.values())

            # 保存参考链接
            source_links = [{"title": r["title"], "url": r["url"]} for r in search_results[:15]]

            yield f"data: {json.dumps({'type': 'progress', 'stage': 'read', 'progress': 45, 'detail': f'搜索到 {len(search_results)} 个网页，正在读取内容...'})}\n\n"
            await asyncio.sleep(0.1)

            # 阶段3: 读取网页
            web_contents = await loop.run_in_executor(
                executor,
                lambda: competitor_agent.web_reader.read_urls([r["url"] for r in search_results]) if search_results else []
            )

            yield f"data: {json.dumps({'type': 'progress', 'stage': 'extract', 'progress': 55, 'detail': '正在提取竞品数据...'})}\n\n"
            await asyncio.sleep(0.1)

            # 阶段4: 提取竞品
            extracted = await loop.run_in_executor(
                executor,
                lambda: competitor_agent.extract_competitor_info(search_results, web_contents, domain or "", features or "", llm_client, LLM_MODEL)
            )

            yield f"data: {json.dumps({'type': 'progress', 'stage': 'merge', 'progress': 65, 'detail': f'提取到 {len(extracted)} 个竞品，正在合并去重...'})}\n\n"
            await asyncio.sleep(0.1)

            # 阶段5: 合并去重
            merged = competitor_agent.merge_and_deduplicate_competitors(extracted)
            validated = competitor_agent.validate_competitors(merged, domain or "", features or "", llm_client, LLM_MODEL, min_score=6)

            yield f"data: {json.dumps({'type': 'progress', 'stage': 'enrich', 'progress': 75, 'detail': f'筛选出 {len(validated)} 个竞品，正在深度分析...'})}\n\n"
            await asyncio.sleep(0.1)

            # 阶段6: 深度分析
            enriched = await loop.run_in_executor(
                executor,
                lambda: competitor_agent.feature_extractor.enrich_competitors(
                    competitors=validated,
                    domain=domain or "",
                    llm_client=llm_client,
                    model=LLM_MODEL,
                    max_workers=4
                )
            )

            yield f"data: {json.dumps({'type': 'progress', 'stage': 'insights', 'progress': 90, 'detail': '正在生成市场总结和产品建议...'})}\n\n"
            await asyncio.sleep(0.1)

            # 阶段7: 生成总结和建议
            insights = await loop.run_in_executor(
                executor,
                lambda: competitor_agent.generate_summary_and_recommendations(
                    enriched, domain, features, product_name, llm_client, LLM_MODEL
                )
            )

            yield f"data: {json.dumps({'type': 'progress', 'stage': 'complete', 'progress': 100, 'detail': '分析完成！'})}\n\n"
            await asyncio.sleep(0.1)

            # 构建结果
            result = {
                "domain": domain,
                "features": features,
                "product_name": product_name,
                "queries": query_strings,
                "competitors": enriched,
                "total_count": len(enriched),
                "source_links": source_links,
                "insights": insights,
                "message": f"成功分析，发现 {len(enriched)} 个竞品"
            }

            # 发送最终结果
            yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
            logger.info(f"[SSE] 分析完成，发现 {len(enriched)} 个竞品")

        except Exception as e:
            logger.error(f"[SSE] 分析失败：{e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

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
        port=8001,
        reload=True,
        reload_dirs=[".", "../agent", "../tools", "../llm"]
    )
