import sys
import os

# 添加当前目录到Python搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.agent.competitor_agent import CompetitorAnalysisAgent
from backend.tools.anspire_search import AnspireSearch
from backend.llm.client import get_llm_client
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))

def test_refine_query_with_custom_prompt():
    """
    测试refine_query方法，使用自定义的system prompt
    """
    print("\n" + "=" * 60)
    print("测试refine_query方法（自定义prompt）")
    print("=" * 60)
    
    # 初始化组件
    api_key = os.getenv("ANSPIRE_API_KEY")
    llm_api_key = os.getenv("LLM_API_KEY")
    llm_base_url = os.getenv("LLM_BASE_URL")
    llm_model = os.getenv("LLM_MODEL", "gemini-3-flash-preview")
    
    if not api_key or not llm_api_key:
        print("未找到必要的环境变量")
        return
    
    anspire_search = AnspireSearch(api_key)
    llm_client = get_llm_client(llm_api_key, llm_base_url)
    agent = CompetitorAnalysisAgent(anspire_search)
    
    # 测试用例
    test_cases = [
        {"domain": "AI教育", "product_name": "Kimi"},
        {"domain": "在线办公", "product_name": "WPS"},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        domain = test_case["domain"]
        product_name = test_case["product_name"]
        
        print(f"\n测试用例 {i}:")
        print(f"  领域: {domain}")
        print(f"  产品名称: {product_name}")
        print("-" * 40)
        
        try:
            # 调用refine_query方法
            query = agent.refine_query(domain, product_name, llm_client, llm_model)
            
            print(f"  生成的查询: {query}")
            print(f"  查询长度: {len(query)} 字符")
            
        except Exception as e:
            print(f"  错误: {e}")
        
        print()
    
    print("=" * 60)




if __name__ == "__main__":
    # 运行所有测试
    test_refine_query_with_custom_prompt()

