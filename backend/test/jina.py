import sys
import os

# 添加当前目录到Python搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.tools.web_reader import WebReader
from backend.tools.anspire_search import AnspireSearch
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))


def test_web_reader_with_search():
    """
    测试WebReader结合搜索功能
    """
    print("=== 测试3：结合搜索功能 ===")
    
    # 初始化搜索工具
    api_key = os.getenv("ANSPIRE_API_KEY")
    if not api_key:
        print("未找到ANSPIRE_API_KEY环境变量，跳过搜索测试")
        return
    
    search = AnspireSearch(api_key)
    reader = WebReader()
    
    # 搜索AI教育产品，max_results=1
    query = "AI批阅功能的产品有什么"
    max_results = 1
    print(f"搜索查询: {query}, 最大结果数: {max_results}")
    
    # 执行搜索
    search_results = search.comprehensive_search(query, max_results)
    webpages = search_results.get("webpages", [])
    
    if not webpages:
        print("搜索结果为空")
        return
    
    print(f"搜索到 {len(webpages)} 个结果")
    for webpage in webpages:
        print(f"\n搜索结果：")
        print(f"标题: {webpage.get('name', '')}")
        print(f"URL: {webpage.get('url', '')}")
        print(f"摘要: {webpage.get('snippet', '')[:200]}...")
        
        # 使用WebReader获取完整内容
        url = webpage.get('url', '')
        if url:
            print(f"\n使用Jina Reader获取完整内容：")
            content = reader.read_url(url)
            print(f"状态: {'成功' if content.success else '失败'}")
            if content.success:
                print(f"内容长度: {len(content.content)} 字符")
                print(f"内容预览: {content.content[:5000]}...")
            else:
                print(f"错误: {content.error}")
    print()


if __name__ == "__main__":
    # 运行所有测试
    test_web_reader_with_search()
