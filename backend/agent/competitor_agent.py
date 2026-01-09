# -*- coding: utf-8 -*-
"""
竞品分析Agent - 分布式提取版 (Map-Reduce)
解决超长上下文导致输出截断的问题
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from loguru import logger

from backend.llm.client import chat_completion
from backend.tools.anspire_search import AnspireSearch
from backend.tools.web_reader import WebReader
from backend.agent.feature_extractor import FeatureExtractor


class CompetitorAnalysisAgent:
    def __init__(self, anspire_search: AnspireSearch):
        self.anspire_search = anspire_search
        self.web_reader = WebReader()
        self.feature_extractor = FeatureExtractor(anspire_search, self.web_reader)
        logger.info(f"竞品分析Agent初始化成功")

    def generate_search_queries(self, domain: Optional[str], features: Optional[str], product_name: str, llm_client: Any, model: str) -> List[Dict[str, str]]:
        """生成搜索查询 (保持不变)"""
        if not domain and not features:
            return []

        user_content = f"产品名称：{product_name}\n"
        if domain: user_content += f"领域：{domain}\n"
        if features: user_content += f"功能：{features}\n"

        messages = [
            {
                "role": "system",
                "content": """你是一个搜索专家。生成3个能挖掘"竞品列表"的查询。
要求：包含"排名"、"Top"、"有哪些"、"好用"等词。
返回JSON: {"queries": [{"type": "feature", "name": "关键词", "query": "..."}]}"""
            },
            {"role": "user", "content": user_content}
        ]

        try:
            response = chat_completion(llm_client, messages, model)
            if "```" in response:
                match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response, re.DOTALL)
                if match: response = match.group(1).strip()
            
            result = json.loads(response)
            return result.get("queries", [])
        except Exception as e:
            logger.warning(f"Query生成降级: {e}")
            return [{"type": "auto", "name": "auto", "query": f"{product_name} 竞品 排名 Top10"}]

    def search_all_parallel(self, queries, max_results=10):
        """并行搜索 (保持不变)"""
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for q in queries:
                futures.append(executor.submit(self.anspire_search.comprehensive_search, q['query'], max_results))
            
            for f in as_completed(futures):
                try:
                    res = f.result()
                    for item in res.get("webpages", []):
                        results.append({
                            "title": item.get("name", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("snippet", "")
                        })
                except Exception as e:
                    logger.error(f"搜索出错: {e}")
        return results

    def _extract_from_single_source(self, source_text: str, source_url: str, llm_client: Any, model: str) -> List[Dict[str, Any]]:
        """
        原子操作：从单个文本块中提取竞品
        """
        # 限制单次输入长度，防止甚至单个网页也过长（比如超过3万字）
        # 30000字符对于单次提取足够了
        safe_text = source_text[:50000] 
        
        messages = [
            {
                "role": "system",
                "content": """你是一个数据提取助手。从给定的网页内容中提取所有提到的**竞品软件/产品名称**。

提取规则：
1. **只提取产品名**：不要提取公司名、通用名词（如"CRM系统"）。
2. **提取功能**：简要总结该产品的 1-2 个核心功能。
3. **JSON格式**：{"competitors": [{"name": "产品A", "features": ["功能1"]}]}
4. 如果文中没有具体产品，返回 {"competitors": []}
5. 不要废话，直接返回JSON。"""
            },
            {
                "role": "user",
                "content": f"来源URL: {source_url}\n\n内容:\n{safe_text}"
            }
        ]

        try:
            # 这里是关键：单次输入变小了，Output Token 即使默认较小也足够写出 JSON
            response = chat_completion(llm_client, messages, model)
            
            # 极简清洗
            json_str = response.strip()
            if "```" in json_str:
                match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', json_str, re.DOTALL)
                if match: json_str = match.group(1).strip()
            
            # 尝试修复截断（虽然分片后截断概率很小）
            if not json_str.endswith("]}"):
                 # 暴力修复：寻找最后一个 } 或 ]
                 last_brace = json_str.rfind('}')
                 if last_brace != -1:
                     json_str = json_str[:last_brace+1]
                     if not json_str.endswith("]}") and json_str.endswith("}"):
                         # 假设是 {"comp": [...]} 结构
                         if json_str.count('{') > json_str.count('}'):
                            json_str += "]}"
            
            data = json.loads(json_str)
            comps = data.get("competitors", [])
            if comps:
                logger.info(f"从 {source_url[-20:]} 提取到 {len(comps)} 个竞品")
            return comps
            
        except Exception as e:
            # 单个失败不影响整体
            return []

    def extract_competitor_info(self, competitor_data: List[Dict[str, str]], web_contents: List[Any], llm_client: Any, model: str) -> List[Dict[str, Any]]:
        """
        Map-Reduce 模式提取：并行处理每个网页，然后汇总
        """
        all_extracted_competitors = []

        # 将网页内容映射回 URL
        web_map = {c.url: c.content for c in web_contents if c.success}
        
        # 选取高质量内容进行提取（优先有全文的，其次是Snippet）
        seen_urls = set()

        # 优先处理有全文的
        priority_items = []
        for item in competitor_data:
            if item['url'] in web_map and item['url'] not in seen_urls:
                priority_items.append(item)
                seen_urls.add(item['url'])

        # 如果全文不够，用 Snippet 凑
        for item in competitor_data:
            if item['url'] not in seen_urls:
                priority_items.append(item)
                seen_urls.add(item['url'])

        tasks_input = priority_items
        logger.info(f"准备对 {len(tasks_input)} 个来源进行并行提取...")

        # 2. 并行执行提取 (Map 阶段)
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_url = {}
            
            for item in tasks_input:
                url = item['url']
                # 如果有全文用全文，否则用 Snippet
                if url in web_map:
                    content_text = web_map[url]
                    # 清洗空白
                    content_text = re.sub(r'\s+', ' ', content_text)
                else:
                    content_text = item['snippet']
                
                # 提交任务
                future = executor.submit(self._extract_from_single_source, content_text, url, llm_client, model)
                future_to_url[future] = url

            # 收集结果
            for future in as_completed(future_to_url):
                try:
                    comps = future.result()
                    all_extracted_competitors.extend(comps)
                except Exception as e:
                    logger.error(f"提取任务异常: {e}")

        # 3. 结果清洗
        clean_results = []
        for c in all_extracted_competitors:
            if isinstance(c, dict) and "name" in c:
                clean_results.append({
                    "name": str(c["name"]),
                    "features": c.get("features", [])
                })
        
        return clean_results

    def merge_and_deduplicate_competitors(self, all_competitors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并并去重 (Reduce 阶段)
        """
        merged = {}
        # 过滤词
        blocklist = ["首页", "产品", "解决方案", "关于我们", "登录", "注册", "下载", "平台"]
        
        for comp in all_competitors:
            name = comp.get("name", "").strip()
            # 简单清洗
            name = re.sub(r'[\(\（].*?[\)\）]', '', name).strip() # 去除括号内容
            
            if not name or len(name) < 2 or name in blocklist:
                continue
                
            key = name.lower()
            if key in merged:
                # 合并功能
                old_feats = set(merged[key]["features"])
                new_feats = comp.get("features", [])
                if isinstance(new_feats, list):
                    old_feats.update(new_feats)
                merged[key]["features"] = list(old_feats)
            else:
                merged[key] = {
                    "name": name,
                    "features": comp.get("features", [])
                }
        
        return list(merged.values())

    def run(self, domain: Optional[str], features: Optional[str], product_name: str, llm_client: Any, model: str, max_results: int = 10) -> Dict[str, Any]:
        logger.info(f"=== 开始竞品分析 (Map-Reduce版) ===")
        
        # 1. 生成查询
        queries_data = self.generate_search_queries(domain, features, product_name, llm_client, model)
        # 提取纯文本查询列表，供返回使用
        query_strings = [q['query'] for q in queries_data]
        logger.info(f"生成查询: {query_strings}")
        
        # 2. 搜索
        raw_results = self.search_all_parallel(queries_data, max_results)
        
        # 去重 URL
        unique_results = {}
        for r in raw_results:
            if r['url'] not in unique_results:
                unique_results[r['url']] = r
        search_results = list(unique_results.values())
        logger.info(f"搜索到 {len(search_results)} 个唯一网页")

        # 3. 智能筛选 Top N 进行抓取
        def rank_score(item):
            score = 0
            txt = (item['title'] + item['snippet']).lower()
            if '排名' in txt or 'top' in txt or '十大' in txt: score += 10
            if '有哪些' in txt or '盘点' in txt: score += 5
            return score
            
        sorted_results = sorted(search_results, key=rank_score, reverse=True)
        top_urls = [r['url'] for r in sorted_results]
        
        # 4. 读取网页
        web_contents = []
        if top_urls:
            web_contents = self.web_reader.read_urls(top_urls)
            
        # 5. 分布式提取
        extracted = self.extract_competitor_info(search_results, web_contents, llm_client, model)
        
        # 6. 汇总去重
        final_competitors = self.merge_and_deduplicate_competitors(extracted)
        logger.info(f"初步分析完成，获得 {len(final_competitors)} 个竞品")

        # 7. 二次深度搜索：获取竞品详细功能
        logger.info("=== 开始二次深度搜索 ===")
        enriched_competitors = self.feature_extractor.enrich_competitors(
            competitors=final_competitors,
            domain=domain or "",
            llm_client=llm_client,
            model=model,
            max_workers=4
        )

        logger.info(f"分析结束，最终获得 {len(enriched_competitors)} 个竞品（含详细功能）")

        return {
            "domain": domain,
            "features": features,
            "product_name": product_name,
            "queries": query_strings,
            "competitors": enriched_competitors,
            "total_count": len(enriched_competitors)
        }