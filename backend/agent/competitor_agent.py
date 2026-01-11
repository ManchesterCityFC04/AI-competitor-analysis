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

    def generate_summary_and_recommendations(self, competitors, domain, features, product_name, llm_client, model):
        """生成竞品总结和产品发展建议"""
        if not competitors:
            return {"summary": "未发现足够的竞品信息", "recommendations": []}

        # 构建竞品信息摘要
        competitor_info = "\n".join([
            f"- {c['name']}（相关性：{c.get('score', 5)}/10）：{', '.join(c.get('features', [])[:8])}"
            for c in competitors[:10]
        ])

        # 收集所有功能用于分析
        all_features = []
        for c in competitors:
            all_features.extend(c.get('features', []))
        feature_freq = {}
        for f in all_features:
            feature_freq[f] = feature_freq.get(f, 0) + 1
        common_features = sorted(feature_freq.items(), key=lambda x: -x[1])[:15]
        common_features_str = ", ".join([f[0] for f in common_features])

        system_prompt = """你是一位资深的产品战略顾问和市场分析专家。请基于竞品分析结果，进行深度思考和战略建议。

## 你的分析框架

### 第一步：市场格局理解
- 这些竞品反映了怎样的市场需求？
- 市场处于什么发展阶段（萌芽期/成长期/成熟期/衰退期）？
- 主要玩家的定位有何差异？

### 第二步：功能维度分析
- 哪些是"必备功能"（大多数竞品都有）？
- 哪些是"差异化功能"（少数竞品独有）？
- 有哪些功能空白点（用户可能需要但竞品未覆盖）？

### 第三步：战略建议思考
- 如果是新进入者，应该采取什么策略？
- 如果要差异化竞争，切入点在哪里？
- 有哪些创新机会？

## 输出要求
请返回JSON格式，包含：
1. summary: 市场总结（200-300字，包含市场格局、竞争态势、关键洞察）
2. market_stage: 市场阶段（萌芽期/成长期/成熟期/衰退期）
3. must_have_features: 必备功能列表（用户期望的基础功能）
4. differentiators: 差异化机会列表（可以突破的点）
5. recommendations: 产品发展建议列表（3-5条具体可行的建议，每条包含 title 和 detail）
6. risks: 潜在风险提醒（1-2条）

请深入思考，给出有洞察力的分析，而不是泛泛而谈。"""

        user_content = f"""## 分析目标
- 用户产品名称：{product_name}
- 目标领域：{domain or '未指定'}
- 期望功能：{features or '未指定'}

## 竞品数据
共发现 {len(competitors)} 个竞品：

{competitor_info}

## 市场常见功能（按出现频率）
{common_features_str}

请基于以上信息，进行深度分析并给出战略建议。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        try:
            response = chat_completion(llm_client, messages, model)
            json_str = response.strip()
            if "```" in json_str:
                m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", json_str, re.DOTALL)
                if m: json_str = m.group(1).strip()

            result = json.loads(json_str)
            logger.info("成功生成竞品总结和建议")
            return {
                "summary": result.get("summary", ""),
                "market_stage": result.get("market_stage", ""),
                "must_have_features": result.get("must_have_features", []),
                "differentiators": result.get("differentiators", []),
                "recommendations": result.get("recommendations", []),
                "risks": result.get("risks", [])
            }
        except Exception as e:
            logger.warning(f"生成总结建议失败: {e}")
            return {
                "summary": "分析生成失败，请重试",
                "market_stage": "",
                "must_have_features": [],
                "differentiators": [],
                "recommendations": [],
                "risks": []
            }

    def run(self, domain, features, product_name, llm_client, model, max_results=10):
        logger.info("=== 开始竞品分析 (带相关性过滤) ===")
        queries_data = self.generate_search_queries(domain, features, product_name, llm_client, model)
        query_strings = [q["query"] for q in queries_data]
        logger.info(f"生成查询: {query_strings}")
        raw_results = self.search_all_parallel(queries_data, max_results)
        search_results = list({r["url"]: r for r in raw_results}.values())
        logger.info(f"搜索到 {len(search_results)} 个唯一网页")

        # 保存参考链接
        source_links = [{"title": r["title"], "url": r["url"]} for r in search_results[:15]]

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

        # 生成总结和建议
        logger.info("=== 生成市场总结和产品建议 ===")
        insights = self.generate_summary_and_recommendations(enriched, domain, features, product_name, llm_client, model)

        return {
            "domain": domain,
            "features": features,
            "product_name": product_name,
            "queries": query_strings,
            "competitors": enriched,
            "total_count": len(enriched),
            "source_links": source_links,
            "insights": insights
        }
