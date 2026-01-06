# -*- coding: utf-8 -*-
"""
竞品分析Agent
负责重构查询和搜索竞品
"""

import json
from typing import List, Dict, Any
from loguru import logger

from backend.llm.client import chat_completion
from backend.tools.anspire_search import AnspireSearch


class CompetitorAnalysisAgent:
    """
    竞品分析Agent
    """

    def __init__(self, anspire_search: AnspireSearch):
        """
        初始化竞品分析Agent

        Args:
            anspire_search: Anspire搜索工具实例
        """
        self.anspire_search = anspire_search
        logger.info(f"竞品分析Agent初始化成功")

    def refine_query(self, domain: str, product_name: str, llm_client: Any, model: str) -> str:
        """
        使用LLM重构查询

        Args:
            domain: 领域
            product_name: 产品名称
            llm_client: LLM客户端实例
            model: 模型名称

        Returns:
            重构后的查询
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个搜索查询优化专家。你的任务是生成一个简洁的搜索查询字符串。要求：1. 只返回查询字符串本身，不要任何解释或格式；2. 查询长度控制在20个字以内；3. 包含核心关键词，适合搜索引擎使用。"
            },
            {
                "role": "user",
                "content": f"领域：{domain}\n产品名称：{product_name}\n\n请直接返回一个简洁的搜索查询字符串（只要查询本身，不要其他内容）："
            }
        ]

        try:
            response = chat_completion(llm_client, messages, model)
            query = response.strip().strip('"').strip("'")
            logger.info(f"查询重构成功：{query}")
            return query
        except Exception as e:
            logger.error(f"查询重构失败：{e}")
            # 降级方案：使用简单的查询格式
            default_query = f"{domain} 竞品分析 {product_name}"
            logger.info(f"使用默认查询：{default_query}")
            return default_query

    def search_competitors(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        搜索竞品

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            竞品信息列表
        """
        try:
            results = self.anspire_search.comprehensive_search(query, max_results)
            competitors = []

            for webpage in results.get("webpages", []):
                competitors.append({
                    "title": webpage.get("name", ""),
                    "url": webpage.get("url", ""),
                    "snippet": webpage.get("snippet", "")
                })

            logger.info(f"竞品搜索成功，找到 {len(competitors)} 个结果")
            return competitors
        except Exception as e:
            logger.error(f"竞品搜索失败：{e}")
            return []

    def extract_competitor_info(self, competitor_data: List[Dict[str, str]], llm_client: Any, model: str) -> List[Dict[str, Any]]:
        """
        从搜索结果中提取竞品信息

        Args:
            competitor_data: 竞品搜索结果列表
            llm_client: LLM客户端实例
            model: 模型名称

        Returns:
            提取后的竞品信息列表
        """
        if not competitor_data:
            logger.warning("没有搜索结果可供提取")
            return []

        # 构建输入内容
        input_content = "\n\n".join([
            f"标题：{item['title']}\nURL：{item['url']}\n内容摘要：{item['snippet']}"
            for item in competitor_data
        ])

        messages = [
            {
                "role": "system",
                "content": "你是一个专业的竞品分析师。请从提供的搜索结果中提取竞品信息，包括竞品名称和核心功能。只返回JSON格式，不要其他文字。"
            },
            {
                "role": "user",
                "content": f"请从以下搜索结果中提取竞品信息，包括竞品名称和核心功能：\n\n{input_content}\n\n输出格式：{json.dumps({'competitors': [{'name': '竞品名称', 'features': ['功能1', '功能2', '功能3']}]}, ensure_ascii=False)}"
            }
        ]

        try:
            response = chat_completion(llm_client, messages, model)

            # 解析JSON响应
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            result = json.loads(response)
            competitors = result.get("competitors", [])
            logger.info(f"竞品信息提取成功，提取了 {len(competitors)} 个竞品")
            return competitors
        except Exception as e:
            logger.error(f"竞品信息提取失败：{e}")
            return []

    def run(self, domain: str, product_name: str, llm_client: Any, model: str, max_results: int = 10) -> Dict[str, Any]:
        """
        执行竞品分析流程

        Args:
            domain: 领域
            product_name: 产品名称
            llm_client: LLM客户端实例
            model: 模型名称
            max_results: 最大结果数

        Returns:
            竞品分析结果
        """
        logger.info(f"开始竞品分析，领域：{domain}，产品：{product_name}")

        # 1. 重构查询
        query = self.refine_query(domain, product_name, llm_client, model)

        # 2. 搜索竞品
        search_results = self.search_competitors(query, max_results)

        # 3. 提取竞品信息
        competitors = self.extract_competitor_info(search_results, llm_client, model)

        logger.info(f"竞品分析完成，共发现 {len(competitors)} 个竞品")

        return {
            "domain": domain,
            "product_name": product_name,
            "query": query,
            "competitors": competitors,
            "total_count": len(competitors)
        }
