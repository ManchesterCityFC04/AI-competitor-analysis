# -*- coding: utf-8 -*-
"""
测试竞品信息提取功能
主要用于验证messages格式和解析逻辑
"""

import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 模拟chat_completion函数，返回一个模拟的大模型响应
def mock_chat_completion(llm_client, messages, model):
    """模拟大模型响应"""
    print("\n=== 发送给大模型的messages ===")
    print(json.dumps(messages, ensure_ascii=False, indent=2))
    print("\n=== 大模型的模拟响应 ===")
    
    # 模拟一个标准的大模型响应，包含JSON代码块
    mock_response = '''
```json
{
  "competitors": [
    {
      "name": "竞品A",
      "features": ["核心功能1", "核心功能2", "核心功能3"]
    },
    {
      "name": "竞品B",
      "features": ["功能X", "功能Y"]
    }
  ]
}
```
    '''
    print(mock_response)
    return mock_response

# 模拟一个带额外文本的响应
def mock_chat_completion_with_extra_text(llm_client, messages, model):
    """模拟带有额外文本的大模型响应"""
    print("\n=== 发送给大模型的messages ===")
    print(json.dumps(messages, ensure_ascii=False, indent=2))
    print("\n=== 大模型的模拟响应（带额外文本）===")
    
    mock_response = '''
以下是提取的竞品信息：
```json
{
  "competitors": [
    {
      "name": "竞品C",
      "features": ["功能A", "功能B"]
    }
  ]
}
```
请参考以上信息。
    '''
    print(mock_response)
    return mock_response

# 直接测试JSON解析逻辑
def test_json_parsing():
    """直接测试JSON解析逻辑"""
    from backend.agent.competitor_agent import CompetitorAnalysisAgent
    
    agent = CompetitorAnalysisAgent(None)
    
    # 测试1：标准JSON响应
    print("\n" + "="*60)
    print("测试1：标准JSON响应")
    print("="*60)
    
    mock_response = '''
```json
{
  "competitors": [
    {
      "name": "竞品A",
      "features": ["核心功能1", "核心功能2", "核心功能3"]
    },
    {
      "name": "竞品B",
      "features": ["功能X", "功能Y"]
    }
  ]
}
```
    '''
    
    print("=== 模拟大模型响应 ===")
    print(mock_response)
    
    # 直接测试解析逻辑
    json_str = mock_response.strip()
    
    # 复制agent.extract_competitor_info中的JSON解析逻辑
    if "```" in json_str:
        code_blocks = []
        start_idx = 0
        while start_idx < len(json_str):
            start = json_str.find("```", start_idx)
            if start == -1:
                break
            end = json_str.find("```", start + 3)
            if end == -1:
                break
            code_block = json_str[start + 3:end].strip()
            code_blocks.append(code_block)
            start_idx = end + 3
        
        for block in code_blocks:
            if block.startswith("json"):
                json_str = block[4:].strip()
                break
        else:
            if code_blocks:
                json_str = code_blocks[0]
    
    json_str = json_str.strip()
    
    if json_str and not (json_str.startswith("{") or json_str.startswith("[")):
        start_brace = json_str.find("{")
        start_bracket = json_str.find("[")
        
        if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
            json_str = json_str[start_brace:]
        elif start_bracket != -1:
            json_str = json_str[start_bracket:]
    
    if json_str and not (json_str.endswith("}") or json_str.endswith("]")):
        end_brace = json_str.rfind("}")
        end_bracket = json_str.rfind("]")
        
        if end_brace != -1 and (end_bracket == -1 or end_brace > end_bracket):
            json_str = json_str[:end_brace + 1]
        elif end_bracket != -1:
            json_str = json_str[:end_bracket + 1]
    
    print("\n=== 提取后的JSON字符串 ===")
    print(json_str)
    
    try:
        result = json.loads(json_str)
        print("\n=== 解析结果 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except json.JSONDecodeError as e:
        print(f"\n=== JSON解析失败 ===")
        print(f"错误：{e}")
    
    # 测试2：带额外文本的响应
    print("\n" + "="*60)
    print("测试2：带额外文本的响应")
    print("="*60)
    
    mock_response_with_text = '''
以下是提取的竞品信息：
```json
{
  "competitors": [
    {
      "name": "竞品C",
      "features": ["功能A", "功能B"]
    }
  ]
}
```
请参考以上信息。
    '''
    
    print("=== 模拟大模型响应（带额外文本）===")
    print(mock_response_with_text)
    
    # 直接测试解析逻辑
    json_str = mock_response_with_text.strip()
    
    # 复制agent.extract_competitor_info中的JSON解析逻辑
    if "```" in json_str:
        code_blocks = []
        start_idx = 0
        while start_idx < len(json_str):
            start = json_str.find("```", start_idx)
            if start == -1:
                break
            end = json_str.find("```", start + 3)
            if end == -1:
                break
            code_block = json_str[start + 3:end].strip()
            code_blocks.append(code_block)
            start_idx = end + 3
        
        for block in code_blocks:
            if block.startswith("json"):
                json_str = block[4:].strip()
                break
        else:
            if code_blocks:
                json_str = code_blocks[0]
    
    json_str = json_str.strip()
    
    if json_str and not (json_str.startswith("{") or json_str.startswith("[")):
        start_brace = json_str.find("{")
        start_bracket = json_str.find("[")
        
        if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
            json_str = json_str[start_brace:]
        elif start_bracket != -1:
            json_str = json_str[start_bracket:]
    
    if json_str and not (json_str.endswith("}") or json_str.endswith("]")):
        end_brace = json_str.rfind("}")
        end_bracket = json_str.rfind("]")
        
        if end_brace != -1 and (end_bracket == -1 or end_brace > end_bracket):
            json_str = json_str[:end_brace + 1]
        elif end_bracket != -1:
            json_str = json_str[:end_bracket + 1]
    
    print("\n=== 提取后的JSON字符串 ===")
    print(json_str)
    
    try:
        result = json.loads(json_str)
        print("\n=== 解析结果 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except json.JSONDecodeError as e:
        print(f"\n=== JSON解析失败 ===")
        print(f"错误：{e}")

# 测试input_content构建
def test_input_content_building():
    """测试input_content构建"""
    # 模拟搜索结果数据
    competitor_data = [
        {
            "title": "竞品A - 领先的产品",
            "url": "https://example.com/competitor-a",
            "snippet": "竞品A是一款功能强大的产品，具有核心功能1、核心功能2等特性。"
        },
        {
            "title": "竞品B官网",
            "url": "https://example.com/competitor-b",
            "snippet": "竞品B提供功能X和功能Y，满足用户需求。"
        }
    ]
    
    input_sections = []
    for item in competitor_data:
        url = item['url']
        title = item['title'].replace('"', '\"').replace('\n', ' ')
        snippet = item['snippet'].replace('"', '\"').replace('\n', ' ')
        section = f"标题：{title}\nURL：{url}\n内容摘要：{snippet}"
        
        # 模拟网页内容
        content = f"{item['title']}的完整内容，包含相关功能描述。"
        content = content.replace('"', '\"').replace('\n', ' ')
        section += f"\n完整内容：{content[:10000]}"
        
        input_sections.append(section)
    
    # 构建input_content
    input_content = "\n\n" + "="*50 + "\n\n" + "\n\n".join(input_sections)
    
    print("\n" + "="*60)
    print("测试3：input_content构建")
    print("="*60)
    print(input_content)
    
    # 生成messages
    messages = [
        {
            "role": "system",
            "content": "你是一个专业的竞品分析师。请从提供的搜索结果和网页内容中提取竞品信息，包括竞品名称和核心功能。只返回JSON格式，不要其他文字。"
        },
        {
            "role": "user",
            "content": f"请从以下搜索结果和网页内容中提取竞品信息，包括竞品名称和核心功能：\n\n{input_content}\n\n输出格式：" + json.dumps({'competitors': [{'name': '竞品名称', 'features': ['功能1', '功能2', '功能3']}]}, ensure_ascii=False)
        }
    ]
    
    print("\n" + "="*60)
    print("测试4：messages生成")
    print("="*60)
    print(json.dumps(messages, ensure_ascii=False, indent=2))
    

if __name__ == "__main__":
    test_json_parsing()
    test_input_content_building()
