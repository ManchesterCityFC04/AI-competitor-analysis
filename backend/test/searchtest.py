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

from typing import List, Dict, Any
import time
test_queries = [
    {"type": "domain", "name": "AI教育", "query": "AI教育的产品都有什么"},
    {"type": "domain", "name": "AI批阅试卷", "query": "AI批阅试卷的产品有什么"},

]

agent = CompetitorAnalysisAgent(AnspireSearch(api_key=os.getenv("ANSPIRE_API_KEY")))
a = agent.search_all_parallel(test_queries)

print(a)
