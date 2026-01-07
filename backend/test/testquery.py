# -*- coding: utf-8 -*-
"""
测试生成查询功能
"""

import sys
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))

# 获取当前文件的目录结构
current_file_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_file_dir)
proto_dir = os.path.dirname(backend_dir)

# 将prototype目录添加到Python路径，这样可以从backend模块导入
if proto_dir not in sys.path:
    sys.path.insert(0, proto_dir)

from backend.agent.competitor_agent import CompetitorAnalysisAgent
from backend.tools.anspire_search import AnspireSearch
from backend.llm.client import get_llm_client

# 测试生成搜索查询功能
llm_client = get_llm_client(os.getenv("LLM_API_KEY"), os.getenv("LLM_BASE_URL"))
agent = CompetitorAnalysisAgent(AnspireSearch(api_key=os.getenv("ANSPIRE_API_KEY")))

# 测试用例
queries = agent.generate_search_queries("AI教育", "智能批改，AI组卷，题库", "学而思", llm_client, os.getenv("LLM_MODEL", "gemini-3-flash-preview"))

print("生成的查询:", queries)

# 测试并行搜索
if queries:
    results = agent.search_all_parallel(queries)
    print("\n搜索结果:", results)

queries = [r["query"] for r in search_results]
all_search_results = []
for r in search_results:
    all_search_results.extend(r["search_results"])