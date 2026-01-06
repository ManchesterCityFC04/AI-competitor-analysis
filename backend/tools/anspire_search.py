# -*- coding: utf-8 -*-
"""
Anspire搜索工具
用于执行网络搜索，获取竞品相关信息
"""

import os
import sys
import requests
from typing import List, Dict, Any, Optional
from loguru import logger


class AnspireSearch:
    """Anspire搜索工具类"""

    def __init__(self, api_key: str, base_url: str = "https://plugin.anspire.cn/api/ntsearch/search"):
        """
        初始化Anspire搜索工具

        Args:
            api_key: Anspire API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Connection": "keep-alive",
            "Accept": "*/*"
        }
        logger.info(f"Anspire搜索工具初始化成功")

    def comprehensive_search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        执行全面搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            搜索结果字典
        """
        try:
            # 使用 GET 请求，参数通过 params 传递
            params = {
                "query": query,
                "top_k": max_results,
                "Insite": "",
                "FromTime": "",
                "ToTime": ""
            }

            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=30
            )

            response.raise_for_status()

            result = response.json()

            # 转换 Anspire 返回格式为统一格式
            webpages = []
            for item in result.get("results", []):
                webpages.append({
                    "name": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", "")
                })

            logger.info(f"搜索成功，查询: {query}, 结果数: {len(webpages)}")
            return {"webpages": webpages}

        except requests.exceptions.RequestException as e:
            logger.error(f"搜索失败: {e}")
            return {
                "webpages": [],
                "error": str(e)
            }

    def search_competitors(self, domain: str, product_name: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        搜索竞品

        Args:
            domain: 领域
            product_name: 产品名称
            max_results: 最大结果数

        Returns:
            竞品信息列表
        """
        query = f"{domain} 竞品分析 {product_name}"
        results = self.comprehensive_search(query, max_results)

        competitors = []
        for webpage in results.get("webpages", []):
            competitors.append({
                "title": webpage.get("name", ""),
                "url": webpage.get("url", ""),
                "snippet": webpage.get("snippet", "")
            })

        return competitors
