# -*- coding: utf-8 -*-
"""
测试JSON解析逻辑
"""

import json
import re

# 测试不同格式的大模型响应
def test_json_parsing():
    """测试不同格式的大模型响应解析"""
    
    test_cases = [
        {
            "name": "标准JSON代码块",
            "response": '''
```json
{
  "competitors": [
    {
      "name": "竞品A",
      "features": ["核心功能1", "核心功能2"]
    }
  ]
}
```
            '''
        },
        {
            "name": "带json标记的代码块",
            "response": '''
```json
{
  "competitors": [
    {
      "name": "竞品B",
      "features": ["功能X", "功能Y"]
    }
  ]
}
```
            '''
        },
        {
            "name": "不带json标记的代码块",
            "response": '''
```
{
  "competitors": [
    {
      "name": "竞品C",
      "features": ["功能A", "功能B"]
    }
  ]
}
```
            '''
        },
        {
            "name": "带额外文本的响应",
            "response": '''
根据搜索结果，我提取了以下竞品信息：

```json
{
  "competitors": [
    {
      "name": "竞品D",
      "features": ["功能1", "功能2", "功能3"]
    }
  ]
}
```

以上是提取的竞品信息，请参考。
            '''
        },
        {
            "name": "纯JSON响应",
            "response": '''
{
  "competitors": [
    {
      "name": "竞品E",
      "features": ["核心功能A", "核心功能B"]
    }
  ]
}
            '''
        },
        {
            "name": "带多余逗号的JSON",
            "response": '''
```json
{
  "competitors": [
    {
      "name": "竞品F",
      "features": ["功能X", "功能Y",],
    },
  ],
}
```
            '''
        },
        {
            "name": "使用单引号的JSON",
            "response": '''
```json
{
  'competitors': [
    {
      'name': '竞品G',
      'features': ['功能A', '功能B']
    }
  ]
}
```
            '''
        }
    ]
    
    for test_case in test_cases:
        print(f"\n" + "="*60)
        print(f"测试：{test_case['name']}")
        print("="*60)
        
        response = test_case['response']
        print("=== 原始响应 ===")
        print(response)
        
        # 应用修复后的解析逻辑
        json_str = response.strip()
        
        # 处理代码块
        if "```" in json_str:
            code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
            matches = re.findall(code_block_pattern, json_str, re.DOTALL)
            
            if matches:
                json_str = matches[0].strip()
        
        # 预处理JSON字符串
        json_str = json_str.strip()
        
        # 查找JSON的开始和结束位置
        start_pos = -1
        end_pos = -1
        
        start_brace = json_str.find("{")
        start_bracket = json_str.find("[")
        
        if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
            start_pos = start_brace
        elif start_bracket != -1:
            start_pos = start_bracket
        
        if start_pos != -1:
            substr = json_str[start_pos:]
            end_brace = substr.rfind("}")
            end_bracket = substr.rfind("]")
            
            if end_brace != -1 and (end_bracket == -1 or end_brace > end_bracket):
                end_pos = start_pos + end_brace + 1
            elif end_bracket != -1:
                end_pos = start_pos + end_bracket + 1
        
        if start_pos != -1 and end_pos != -1:
            json_str = json_str[start_pos:end_pos]
        
        print("\n=== 提取后的JSON字符串 ===")
        print(json_str)
        
        # 尝试解析JSON
        result = None
        try:
            # 首次尝试
            result = json.loads(json_str)
        except json.JSONDecodeError:
            # 修复常见问题
            fixed_json_str = json_str
            # 移除多余的逗号
            fixed_json_str = re.sub(r',\s*([}\]])', r'\1', fixed_json_str)
            # 修复引号
            fixed_json_str = re.sub(r"'([^']+)'", r'"\1"', fixed_json_str)
            # 再次尝试
            result = json.loads(fixed_json_str)
        
        if result:
            print("\n=== 解析结果 ===")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print("✅ 解析成功")
        else:
            print("❌ 解析失败")

if __name__ == "__main__":
    test_json_parsing()
