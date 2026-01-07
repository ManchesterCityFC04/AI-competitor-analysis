# -*- coding: utf-8 -*-
"""
竞品分析Agent
负责重构查询和搜索竞品
支持领域和功能同时并行搜索
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from loguru import logger

from backend.llm.client import chat_completion
from backend.tools.anspire_search import AnspireSearch
from backend.tools.web_reader import WebReader


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
        self.web_reader = WebReader()
        logger.info(f"竞品分析Agent初始化成功")

    def generate_search_queries(self, domain: Optional[str], features: Optional[str], product_name: str, llm_client: Any, model: str) -> List[Dict[str, str]]:
        """
        使用LLM根据领域和功能生成搜索查询

        Args:
            domain: 领域（可选）
            features: 功能描述（可选）
            product_name: 产品名称
            llm_client: LLM客户端实例
            model: 模型名称

        Returns:
            查询列表，格式：[{"type": "domain"/"feature", "name": "名称", "query": "搜索查询"}, ...]
        """
        if not domain and not features:
            return []

        user_content = f"产品名称：{product_name}\n"
        if domain:
            user_content += f"领域：{domain}\n"
        if features:
            user_content += f"功能：{features}\n"

        messages = [
            {
                "role": "system",
                "content": """你是一个搜索查询生成专家。根据用户提供的领域和功能信息，生成最佳搜索查询。

要求：
1. 领域生成1个搜索查询，功能生成多个查询（每个功能点一个）
2. 每个查询长度控制在20字以内，适合搜索引擎
3. 只返回JSON格式，不要其他文字
4.比如的查询：AI教育的产品有什么？ AI批阅试卷的产品有什么？.....
**重点**：必须要落到产品上。
输出格式：
{
  "queries": [
    {"type": "domain", "name": "领域名称", "query": "搜索查询"},
    {"type": "feature", "name": "功能1", "query": "搜索查询"},
    {"type": "feature", "name": "功能2", "query": "搜索查询"}
  ]
}"""
            },
            {
                "role": "user",
                "content": user_content
            }
        ]

        try:
            response = chat_completion(llm_client, messages, model)

            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            result = json.loads(response)
            queries = result.get("queries", [])
            logger.info(f"LLM生成搜索查询成功：{queries}")
            return queries
        except Exception as e:
            logger.error(f"LLM生成查询失败：{e}，使用默认方案")
            queries = []
            if domain:
                queries.append({
                    "type": "domain",
                    "name": domain,
                    "query": f"{domain} {product_name} 竞品"
                })
            if features:
                features_list = re.split(r'[,，]', features)
                for f in features_list:
                    f = f.strip()
                    if f:
                        queries.append({
                            "type": "feature",
                            "name": f,
                            "query": f"{f} 功能的产品有哪些"
                        })
            return queries

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

            logger.info(f"搜索成功，查询：{query}，找到 {len(competitors)} 个结果")
            return competitors
        except Exception as e:
            logger.error(f"搜索失败：{e}")
            return []

    def search_single_query(self, query_info: Dict[str, str], max_results: int = 10) -> Dict[str, Any]:
        """
        执行单个查询搜索

        Args:
            query_info: 包含type, name, query的字典
            max_results: 最大结果数

        Returns:
            搜索结果
        """
        query = query_info["query"]
        search_results = self.search_competitors(query, max_results)
        return {
            "type": query_info["type"],
            "name": query_info["name"],
            "query": query,
            "search_results": search_results
        }

    def search_all_parallel(self, all_queries: List[Dict[str, str]], max_results: int = 10) -> List[Dict[str, Any]]:
        """
        并行搜索所有查询（领域+功能）

        Args:
            all_queries: 所有查询列表，格式：[{"type": "domain"/"feature", "name": "名称", "query": "查询"}, ...]
            max_results: 每个查询的最大结果数

        Returns:
            所有搜索结果列表
        """
        if not all_queries:
            return []

        results = []
        with ThreadPoolExecutor(max_workers=min(len(all_queries), 5)) as executor:
            future_to_query = {
                executor.submit(self.search_single_query, q, max_results): q
                for q in all_queries
            }
            for future in as_completed(future_to_query):
                q = future_to_query[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"{q['type']} '{q['name']}' 搜索完成")
                except Exception as e:
                    logger.error(f"{q['type']} '{q['name']}' 搜索失败: {e}")
                    results.append({
                        "type": q["type"],
                        "name": q["name"],
                        "query": q["query"],
                        "search_results": []
                    })
        return results

    def extract_competitor_info(self, competitor_data: List[Dict[str, str]], web_contents: List[Any], llm_client: Any, model: str) -> List[Dict[str, Any]]:
        """
        从搜索结果和网页内容中提取竞品信息
        """
        if not competitor_data:
            logger.warning("没有搜索结果可供提取")
            return []

        # ... (此处保持原本构建 input_content 的逻辑不变) ...
        # 构建 input_content 代码省略，保持原样
        # ... -------------------------------- ...
        
        # 重新构建 input_sections 和 input_content (为了完整性展示变量名)
        web_content_map = {content.url: content for content in web_contents if content.success}
        input_sections = []
        for item in competitor_data:
            url = item['url']
            title = item['title'].replace('"', '\"').replace('\n', ' ').strip()
            snippet = item['snippet'].replace('"', '\"').replace('\n', ' ').strip()
            section = f"标题：{title}\nURL：{url}\n内容摘要：{snippet}"
            if url in web_content_map:
                content = web_content_map[url].content.replace('"', '\"').replace('\n', ' ').strip()
                content = re.sub(r'\s+', ' ', content)
                section += f"\n完整内容：{content[:5000]}" # 缩减一下长度防止过长
            input_sections.append(section)
        
        input_content = "\n\n".join(input_sections)

        messages = [
            {
                "role": "system",
                "content": """你是一个专业的竞品分析师。请提取竞品名称和核心功能。
规则：
1. 必须返回标准JSON格式。
2. JSON结构：{"competitors":[{"name":"产品名","features":["功能1","功能2"]}]}
3. 如果内容很多，请确保JSON完整，不要用"..."省略，如果写不下可以少写几个竞品，但必须保证JSON语法闭合。
4. 不要返回任何Markdown标记，只返回纯JSON字符串。"""
            },
            {
                "role": "user",
                "content": f"请从以下内容提取竞品信息：\n\n{input_content[:15000]}" # 截断输入防止Token溢出
            }
        ]

        try:
            response = chat_completion(llm_client, messages, model)
            
            # 1. 提取 JSON 字符串 (移除 Markdown 和无关文本)
            json_str = response.strip()
            if "```" in json_str:
                pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
                match = re.search(pattern, json_str, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()
            
            # 移除可能的前后缀
            start_idx = json_str.find('{')
            if start_idx != -1:
                json_str = json_str[start_idx:]
            
            # 2. 尝试清洗常见的语法错误
            # 修复：对象之间缺失逗号 (e.g., } { -> }, {)
            json_str = re.sub(r'\}\s*\{', '}, {', json_str)
            # 修复：列表内字符串缺失逗号 (e.g., "a" "b" -> "a", "b")
            json_str = re.sub(r'\"\s*\"', '", "', json_str)
            # 修复：中文冒号
            json_str = json_str.replace('：', ':')
            # 移除末尾的 "..." (LLM常用来表示未完)
            if json_str.endswith("..."):
                json_str = json_str[:-3].strip()

            # 3. 解析与截断修复循环
            parsed_json = None
            
            # 尝试 1: 直接解析
            try:
                parsed_json = json.loads(json_str)
            except json.JSONDecodeError:
                pass

            # 尝试 2: 如果失败，尝试通过寻找最后一个有效的对象闭合来修复截断
            if parsed_json is None:
                try:
                    # 我们假设结构是 {"competitors": [ ... ]}
                    # 找到最后一个 "}]" 或者 "}"
                    # 如果是被截断的，我们尝试找到列表里最后一个完整的 "}"，然后手动闭合
                    
                    # 找到 "competitors" 的开始位置
                    comp_start = json_str.find('"competitors"')
                    if comp_start != -1:
                        # 找到列表的开始 '['
                        list_start = json_str.find('[', comp_start)
                        if list_start != -1:
                            # 从后往前找 '}'，这是最后一个完整对象的结束
                            last_obj_end = json_str.rfind('}')
                            
                            # 如果最后一个 '}' 是在最末尾（可能是根对象的结束），我们需要找倒数第二个
                            # 或者我们简单地不断尝试截断解析
                            
                            # 策略：从后往前遍历所有的 '}'，试图在那个位置闭合 JSON
                            valid_indices = [m.end() for m in re.finditer(r'\}', json_str)]
                            # 倒序尝试
                            for idx in reversed(valid_indices):
                                # 尝试构建：当前截断点 + ]} (补全列表和根对象)
                                temp_json = json_str[:idx] + ']}'
                                try:
                                    parsed_json = json.loads(temp_json)
                                    logger.info(f"JSON通过截断修复成功，保留至索引 {idx}")
                                    break
                                except json.JSONDecodeError:
                                    continue
                                    
                                # 另一种情况：也许根本就没有根对象的闭合，尝试只补全 ]}
                                # 上面的逻辑已经涵盖了大多数情况
                except Exception as e:
                    logger.warning(f"智能截断修复失败: {e}")

            # 4. 提取数据
            competitors = []
            if parsed_json and "competitors" in parsed_json:
                competitors = parsed_json["competitors"]
            
            # 5. 降级方案：如果JSON解析依然全军覆没，使用正则暴力提取
            if not competitors:
                logger.warning("JSON解析失败，启用正则暴力提取模式")
                # 匹配 {"name": "...", "features": [...]} 结构
                # 这种正则即使JSON不完整也能提取出完整的片段
                block_pattern = r'\{\s*"name"\s*:\s*"(.*?)"\s*,\s*"features"\s*:\s*\[(.*?)\]\s*\}'
                matches = re.findall(block_pattern, json_str, re.DOTALL)
                
                for name, features_str in matches:
                    # 清洗功能列表
                    feats = re.findall(r'"(.*?)"', features_str)
                    if not feats: # 尝试单引号
                        feats = re.findall(r"'(.*?)'", features_str)
                    
                    competitors.append({
                        "name": name,
                        "features": feats
                    })

            # 确保数据格式正确
            final_results = []
            for comp in competitors:
                if isinstance(comp, dict) and "name" in comp:
                    final_results.append({
                        "name": str(comp["name"]),
                        "features": comp.get("features", []) if isinstance(comp.get("features"), list) else []
                    })
            
            logger.info(f"竞品信息提取完成，共提取 {len(final_results)} 个")
            return final_results

        except Exception as e:
            logger.error(f"竞品提取发生未预期的错误: {e}")
            return []

    def merge_and_deduplicate_competitors(self, all_competitors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并并去重竞品列表
        """
        merged = {}
        for competitor in all_competitors:
            name = competitor.get("name", "").strip()
            if not name:
                continue

            name_lower = name.lower()
            if name_lower in merged:
                existing_features = set(merged[name_lower]["features"])
                new_features = competitor.get("features", [])
                existing_features.update(new_features)
                merged[name_lower]["features"] = list(existing_features)
            else:
                merged[name_lower] = {
                    "name": name,
                    "features": list(set(competitor.get("features", [])))
                }

        result = list(merged.values())
        logger.info(f"竞品去重完成，合并后共 {len(result)} 个竞品")
        return result

    def run(self, domain: Optional[str], features: Optional[str], product_name: str, llm_client: Any, model: str, max_results: int = 10) -> Dict[str, Any]:
        """
        执行竞品分析流程（领域和功能同时并行搜索）

        Args:
            domain: 领域（可选）
            features: 功能描述（可选）
            product_name: 产品名称
            llm_client: LLM客户端实例
            model: 模型名称
            max_results: 最大结果数

        Returns:
            竞品分析结果
        """
        logger.info(f"开始竞品分析，领域：{domain}，功能：{features}，产品：{product_name}")

        all_queries = self.generate_search_queries(domain, features, product_name, llm_client, model)

        if not all_queries:
            logger.warning("没有有效的查询")
            return {
                "domain": domain,
                "features": features,
                "product_name": product_name,
                "queries": [],
                "competitors": [],
                "total_count": 0
            }

        logger.info(f"共生成 {len(all_queries)} 个查询，开始并行搜索")

        # 3. 并行搜索所有查询
        search_results = self.search_all_parallel(all_queries, max_results)

        # 4. 收集所有搜索结果
        queries = [r["query"] for r in search_results]
        all_search_results = []
        for r in search_results:
            all_search_results.extend(r["search_results"])

        # 5. 获取网页内容
        web_contents = []
        if all_search_results:
            urls = list(set(result['url'] for result in all_search_results))[:5]
            web_contents = self.web_reader.read_urls(urls)
            logger.info(f"成功获取 {sum(1 for c in web_contents if c.success)} 个网页内容")

        # 6. 提取竞品信息
        extracted = self.extract_competitor_info(all_search_results, web_contents, llm_client, model)

        # 7. 合并去重
        all_competitors = self.merge_and_deduplicate_competitors(extracted)

        logger.info(f"竞品分析完成，共发现 {len(all_competitors)} 个竞品")

        return {
            "domain": domain,
            "features": features,
            "product_name": product_name,
            "queries": queries,
            "competitors": all_competitors,
            "total_count": len(all_competitors)
        }
