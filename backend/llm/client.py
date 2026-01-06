# -*- coding: utf-8 -*-
"""
LLM客户端模块
提供统一的LLM调用接口
"""

from openai import OpenAI
from typing import Optional, Dict, Any, List
from loguru import logger


def get_llm_client(api_key: str, base_url: str, timeout: int = 60) -> OpenAI:
    """
    获取LLM客户端实例
    
    Args:
        api_key: API密钥
        base_url: API基础URL
        timeout: 超时时间（秒）
        
    Returns:
        OpenAI客户端实例
    """
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )
        logger.info(f"LLM客户端初始化成功")
        return client
    except Exception as e:
        logger.error(f"LLM客户端初始化失败: {e}")
        raise


def chat_completion(
    client: OpenAI,
    messages: List[Dict[str, str]],
    model: str,
    temperature: float = 0.3,
    max_tokens: int = 2000
) -> str:
    """
    调用LLM进行对话补全
    
    Args:
        client: OpenAI客户端实例
        messages: 对话消息列表
        model: 模型名称
        temperature: 温度参数
        max_tokens: 最大生成令牌数
        
    Returns:
        LLM返回的内容
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM调用失败: {e}")
        raise
