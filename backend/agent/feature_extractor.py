# -*- coding: utf-8 -*-
"""
竞品功能深度提取器
负责对已发现的竞品进行二次搜索，获取详细功能信息
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from loguru import logger

from backend.llm.client import chat_completion


class FeatureExtractor:
    """竞品功能深度提取器"""

    def __init__(self, anspire_search, web_reader):
        self.anspire_search = anspire_search
        self.web_reader = web_reader

    # ========== 1. 查询生成 ==========

    def generate_feature_query(self, competitor_name: str, domain: str = None) -> str:
        """
        为单个竞品生成功能搜索查询

        Args:
            competitor_name: 竞品名称
            domain: 所属领域（可选，用于提高搜索准确性）

        Returns:
            搜索查询字符串
        """
        if domain:
            return f"{competitor_name} {domain} 功能介绍 核心能力"
        return f"{competitor_name} 产品功能 特点 核心能力"

    # ========== 2. 搜索执行 ==========

    def search_single_competitor(self, competitor_name: str, domain: str = None, max_results: int = 5) -> List[Dict]:
        """
        搜索单个竞品的功能信息

        Args:
            competitor_name: 竞品名称
            domain: 所属领域
            max_results: 最大结果数

        Returns:
            搜索结果列表
        """
        query = self.generate_feature_query(competitor_name, domain)

        try:
            result = self.anspire_search.comprehensive_search(query, max_results)
            webpages = result.get("webpages", [])

            return [{
                "title": item.get("name", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", "")
            } for item in webpages]

        except Exception as e:
            logger.warning(f"搜索竞品 '{competitor_name}' 功能失败: {e}")
            return []

    def search_competitors_parallel(
        self,
        competitor_names: List[str],
        domain: str = None,
        max_results_per_competitor: int = 3,
        max_workers: int = 4
    ) -> Dict[str, List[Dict]]:
        """
        并行搜索多个竞品的功能信息

        Args:
            competitor_names: 竞品名称列表
            domain: 所属领域
            max_results_per_competitor: 每个竞品的最大搜索结果数
            max_workers: 并行工作线程数

        Returns:
            {竞品名: [搜索结果]} 的字典
        """
        results = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_name = {
                executor.submit(
                    self.search_single_competitor,
                    name,
                    domain,
                    max_results_per_competitor
                ): name
                for name in competitor_names
            }

            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    logger.error(f"搜索竞品 '{name}' 时出错: {e}")
                    results[name] = []

        return results

    # ========== 3. 功能提取 ==========

    def extract_features_from_content(
        self,
        competitor_name: str,
        content: str,
        llm_client: Any,
        model: str
    ) -> List[str]:
        """
        从文本内容中提取竞品的详细功能

        Args:
            competitor_name: 竞品名称
            content: 网页内容
            llm_client: LLM客户端
            model: 模型名称

        Returns:
            功能列表
        """
        # 限制内容长度
        safe_content = content[:30000]

        messages = [
            {
                "role": "system",
                "content": f"""你是一个产品分析专家。从给定内容中提取 "{competitor_name}" 的具体功能。

要求：
1. 只提取该产品的真实功能，不要编造
2. 功能描述要具体，如"智能试卷批改"而非"AI功能"
3. 每个功能用简短的一句话描述
4. 提取所有能找到的功能，不限数量
5. 返回JSON格式: {{"features": ["功能1", "功能2", ...]}}
6. 如果内容中没有该产品的功能信息，返回 {{"features": []}}"""
            },
            {
                "role": "user",
                "content": f"产品名称: {competitor_name}\n\n内容:\n{safe_content}"
            }
        ]

        try:
            response = chat_completion(llm_client, messages, model)

            # 提取JSON
            json_str = response.strip()
            if "```" in json_str:
                match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', json_str, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()

            data = json.loads(json_str)
            features = data.get("features", [])

            # 清洗：去除空字符串和过短的功能描述
            features = [f.strip() for f in features if f and len(f.strip()) >= 4]

            return features

        except Exception as e:
            logger.warning(f"提取 '{competitor_name}' 功能失败: {e}")
            return []

    def extract_features_for_competitor(
        self,
        competitor_name: str,
        search_results: List[Dict],
        llm_client: Any,
        model: str,
        max_pages: int = 2
    ) -> List[str]:
        """
        为单个竞品提取详细功能（读取网页 + LLM提取）

        Args:
            competitor_name: 竞品名称
            search_results: 该竞品的搜索结果
            llm_client: LLM客户端
            model: 模型名称
            max_pages: 最多读取的网页数

        Returns:
            功能列表
        """
        if not search_results:
            return []

        all_features = []

        # 取前N个搜索结果的URL
        urls = [r['url'] for r in search_results[:max_pages]]

        # 读取网页内容
        web_contents = self.web_reader.read_urls(urls)

        # 从每个网页提取功能
        for wc in web_contents:
            if wc.success and wc.content:
                features = self.extract_features_from_content(
                    competitor_name,
                    wc.content,
                    llm_client,
                    model
                )
                all_features.extend(features)

        # 如果网页抓取失败，尝试从snippet提取
        if not all_features:
            combined_snippets = "\n".join([r.get('snippet', '') for r in search_results])
            if combined_snippets:
                all_features = self.extract_features_from_content(
                    competitor_name,
                    combined_snippets,
                    llm_client,
                    model
                )

        # 去重
        unique_features = list(dict.fromkeys(all_features))

        return unique_features

    # ========== 4. 主入口 ==========

    def enrich_competitors(
        self,
        competitors: List[Dict[str, Any]],
        domain: str,
        llm_client: Any,
        model: str,
        max_workers: int = 4
    ) -> List[Dict[str, Any]]:
        """
        丰富竞品的功能信息（主入口方法）

        Args:
            competitors: 竞品列表，每个元素包含 name 和 features
            domain: 所属领域
            llm_client: LLM客户端
            model: 模型名称
            max_workers: 并行线程数

        Returns:
            丰富后的竞品列表
        """
        if not competitors:
            return []

        # 处理所有竞品，不限制数量
        to_process = competitors
        competitor_names = [c['name'] for c in to_process]

        logger.info(f"开始深度搜索 {len(competitor_names)} 个竞品的功能...")

        # 1. 并行搜索所有竞品
        search_results_map = self.search_competitors_parallel(
            competitor_names,
            domain,
            max_results_per_competitor=3,
            max_workers=max_workers
        )

        # 2. 并行提取功能
        enriched = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_competitor = {}

            for comp in to_process:
                name = comp['name']
                search_results = search_results_map.get(name, [])

                future = executor.submit(
                    self.extract_features_for_competitor,
                    name,
                    search_results,
                    llm_client,
                    model,
                    max_pages=2
                )
                future_to_competitor[future] = comp

            for future in as_completed(future_to_competitor):
                comp = future_to_competitor[future]
                try:
                    new_features = future.result()

                    # 合并新旧功能，去重
                    old_features = comp.get('features', [])
                    all_features = old_features + new_features
                    unique_features = list(dict.fromkeys(all_features))

                    enriched.append({
                        "name": comp['name'],
                        "features": unique_features
                    })

                    logger.info(f"竞品 '{comp['name']}' 功能: {len(old_features)} -> {len(unique_features)}")

                except Exception as e:
                    logger.error(f"丰富竞品 '{comp['name']}' 功能失败: {e}")
                    enriched.append(comp)

        # 补充未处理的竞品
        processed_names = {c['name'] for c in enriched}
        for comp in competitors:
            if comp['name'] not in processed_names:
                enriched.append(comp)

        logger.info(f"深度搜索完成，共处理 {len(to_process)} 个竞品")

        return enriched
