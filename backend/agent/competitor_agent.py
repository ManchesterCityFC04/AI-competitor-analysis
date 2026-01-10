# -*- coding: utf-8 -*-
import json, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from loguru import logger
from backend.llm.client import chat_completion
from backend.tools.anspire_search import AnspireSearch
from backend.tools.web_reader import WebReader
from backend.agent.feature_extractor import FeatureExtractor

class CompetitorAnalysisAgent:
    def __init__(self, anspire_search):
        self.anspire_search = anspire_search
        self.web_reader = WebReader()
        self.feature_extractor = FeatureExtractor(anspire_search, self.web_reader)
        logger.info("竞品分析Agent初始化成功")

    def generate_search_queries(self, domain, features, product_name, llm_client, model):
        if not domain and not features: return []
        user_content = f"产品名称：{product_name}\n"
        if domain: user_content += f"领域：{domain}\n"
        if features: user_content += f"功能：{features}\n"
        messages = [{"role": "system", "content": "你是搜索专家。生成3个挖掘竞品列表的查询。返回JSON"}, {"role": "user", "content": user_content}]
        try:
            response = chat_completion(llm_client, messages, model)
            if "```" in response:
                m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response, re.DOTALL)
                if m: response = m.group(1).strip()
            queries = json.loads(response).get("queries", [])
            # 标准化格式：确保每个查询都是包含 "query" 键的字典
            normalized = []
            for q in queries:
                if isinstance(q, str):
                    normalized.append({"query": q})
                elif isinstance(q, dict) and "query" in q:
                    normalized.append(q)
                elif isinstance(q, dict):
                    query_str = q.get("text") or q.get("search") or q.get("q") or str(q)
                    normalized.append({"query": query_str})
            return normalized if normalized else [{"query": f"{product_name} 竞品 排名 Top10"}]
        except Exception as e:
            logger.warning(f"Query生成降级: {e}")
            return [{"query": f"{product_name} 竞品 排名 Top10"}]

    def search_all_parallel(self, queries, max_results=10):
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.anspire_search.comprehensive_search, q["query"], max_results) for q in queries]
            for f in as_completed(futures):
                try:
                    for item in f.result().get("webpages", []):
                        results.append({"title": item.get("name", ""), "url": item.get("url", ""), "snippet": item.get("snippet", "")})
                except Exception as e: logger.error(f"搜索出错: {e}")
        return results

    def _extract_from_single_source(self, source_text, source_url, user_domain, user_features, llm_client, model):
        safe_text = source_text[:50000]
        user_req = f"目标领域：{user_domain}\n目标功能：{user_features}\n" if user_domain or user_features else ""
        prompt = f"你是竞品分析助手。用户需求：\n{user_req}\n提取竞品并评分(1-10)。9-10分直接竞品，7-8分间接竞品，5-6分领域相关，1-4分不相关。返回JSON格式"
        messages = [{"role": "system", "content": prompt}, {"role": "user", "content": f"URL: {source_url}\n内容:\n{safe_text}"}]
        try:
            response = chat_completion(llm_client, messages, model)
            json_str = response.strip()
            if "```" in json_str:
                m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", json_str, re.DOTALL)
                if m: json_str = m.group(1).strip()
            comps = json.loads(json_str).get("competitors", [])
            if comps: logger.info(f"从 {source_url[-20:]} 提取到 {len(comps)} 个竞品")
            return comps
        except Exception as e:
            logger.warning(f"提取失败: {e}")
            return []

    def extract_competitor_info(self, competitor_data, web_contents, user_domain, user_features, llm_client, model):
        all_comps = []
        web_map = {c.url: c.content for c in web_contents if c.success}
        seen, items = set(), []
        for item in competitor_data:
            if item["url"] in web_map and item["url"] not in seen:
                items.append(item); seen.add(item["url"])
        for item in competitor_data:
            if item["url"] not in seen:
                items.append(item); seen.add(item["url"])
        logger.info(f"准备对 {len(items)} 个来源进行并行提取...")
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(self._extract_from_single_source, re.sub(r"\s+", " ", web_map.get(item["url"], item["snippet"])), item["url"], user_domain, user_features, llm_client, model): item["url"] for item in items}
            for f in as_completed(futures):
                try: all_comps.extend(f.result())
                except Exception as e: logger.error(f"提取异常: {e}")
        return [{"name": str(c["name"]), "features": c.get("features", []), "score": c.get("score", 5), "reason": c.get("reason", "")} for c in all_comps if isinstance(c, dict) and "name" in c]

    def merge_and_deduplicate_competitors(self, all_competitors):
        merged, blocklist = {}, ["首页", "产品", "解决方案", "关于我们", "登录", "注册", "下载", "平台"]
        for comp in all_competitors:
            name = re.sub(r"[\(\（].*?[\)\）]", "", comp.get("name", "").strip()).strip()
            if not name or len(name) < 2 or name in blocklist: continue
            key, score = name.lower(), comp.get("score", 5)
            if key in merged:
                merged[key]["features"] = list(set(merged[key]["features"]) | set(comp.get("features", [])))
                if score > merged[key].get("score", 0):
                    merged[key]["score"], merged[key]["reason"] = score, comp.get("reason", "")
            else:
                merged[key] = {"name": name, "features": comp.get("features", []), "score": score, "reason": comp.get("reason", "")}
        return list(merged.values())

    def validate_competitors(self, competitors, user_domain, user_features, llm_client, model, min_score=6):
        if not competitors: return []
        filtered = [c for c in competitors if c.get("score", 0) >= min_score]
        logger.info(f"过滤：{len(competitors)} -> {len(filtered)} (移除评分<{min_score})")
        if not filtered: filtered = sorted(competitors, key=lambda x: x.get("score", 0), reverse=True)[:5]
        filtered.sort(key=lambda x: x.get("score", 0), reverse=True)
        return filtered

    def run(self, domain, features, product_name, llm_client, model, max_results=10):
        logger.info("=== 开始竞品分析 (带相关性过滤) ===")
        queries_data = self.generate_search_queries(domain, features, product_name, llm_client, model)
        query_strings = [q["query"] for q in queries_data]
        logger.info(f"生成查询: {query_strings}")
        raw_results = self.search_all_parallel(queries_data, max_results)
        search_results = list({r["url"]: r for r in raw_results}.values())
        logger.info(f"搜索到 {len(search_results)} 个唯一网页")
        rank_fn = lambda item: (10 if any(k in (item["title"]+item["snippet"]).lower() for k in ["排名","top","十大"]) else 0) + (5 if any(k in (item["title"]+item["snippet"]).lower() for k in ["有哪些","盘点"]) else 0)
        sorted_results = sorted(search_results, key=rank_fn, reverse=True)
        web_contents = self.web_reader.read_urls([r["url"] for r in sorted_results]) if sorted_results else []
        extracted = self.extract_competitor_info(search_results, web_contents, domain or "", features or "", llm_client, model)
        merged = self.merge_and_deduplicate_competitors(extracted)
        logger.info(f"合并去重后获得 {len(merged)} 个竞品")
        validated = self.validate_competitors(merged, domain or "", features or "", llm_client, model, min_score=6)
        logger.info(f"验证过滤后保留 {len(validated)} 个竞品")
        logger.info("=== 开始二次深度搜索 ===")
        enriched = self.feature_extractor.enrich_competitors(competitors=validated, domain=domain or "", llm_client=llm_client, model=model, max_workers=4)
        logger.info(f"分析结束，最终获得 {len(enriched)} 个竞品")
        return {"domain": domain, "features": features, "product_name": product_name, "queries": query_strings, "competitors": enriched, "total_count": len(enriched)}
