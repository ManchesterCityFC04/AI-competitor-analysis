"""
网页内容获取工具

使用 Jina Reader 将网页转换为 Markdown 格式，提取网页的主要内容。
Jina Reader 是免费服务，无需 API Key。
"""

import requests
from typing import Optional, Dict, Any, List, Callable, Generator
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger


@dataclass
class WebContent:
    """网页内容结果"""
    url: str
    title: str = ""
    content: str = ""
    success: bool = False
    error: Optional[str] = None


class WebReader:
    """
    网页内容读取器

    使用 Jina Reader (r.jina.ai) 将网页转换为 Markdown 格式。
    特点：
    - 免费使用，无需 API Key
    - 自动提取网页主要内容
    - 返回干净的 Markdown 格式
    - 自动去除广告和导航等噪音
    """

    JINA_READER_URL = "https://r.jina.ai/"

    def __init__(self, timeout: int = 30):
        """
        初始化 WebReader

        Args:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout
        self._headers = {
            'Accept': 'text/markdown',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def _fetch_content(self, url: str) -> WebContent:
        """内部方法：获取网页内容"""
        result = WebContent(url=url)

        try:
            # 使用 Jina Reader 获取内容
            jina_url = f"{self.JINA_READER_URL}{url}"
            response = requests.get(jina_url, headers=self._headers, timeout=self.timeout)
            response.raise_for_status()

            content = response.text

            # 提取标题（Jina 返回的第一行通常是标题）
            lines = content.split('\n')
            title = ""
            for line in lines:
                line = line.strip()
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
                elif line and not line.startswith('http'):
                    title = line
                    break

            result.title = title
            result.content = content
            result.success = True

            logger.info(f"成功获取网页内容: {url[:50]}... ({len(content)} 字符)")

        except requests.exceptions.Timeout:
            result.error = "请求超时"
            logger.warning(f"获取网页超时: {url}")
        except requests.exceptions.RequestException as e:
            result.error = f"网络错误: {str(e)}"
            logger.error(f"获取网页失败: {url}, 错误: {e}")
        except Exception as e:
            result.error = f"未知错误: {str(e)}"
            logger.exception(f"获取网页时发生未知错误: {url}")

        return result

    def read_url(self, url: str) -> WebContent:
        """
        读取指定 URL 的网页内容

        Args:
            url: 要读取的网页 URL

        Returns:
            WebContent: 包含网页内容的对象
        """
        logger.info(f"--- 读取网页内容: {url[:60]}... ---")
        return self._fetch_content(url)

    def read_urls(self, urls: list, max_workers: int = 8) -> list:
        """
        并行批量读取多个 URL 的内容

        Args:
            urls: URL 列表
            max_workers: 并行线程数

        Returns:
            List[WebContent]: 网页内容列表
        """
        if not urls:
            return []

        logger.info(f"开始并行抓取 {len(urls)} 个网页（{max_workers} 线程）...")

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self._fetch_content, url): url for url in urls}

            for future in as_completed(future_to_url):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    url = future_to_url[future]
                    logger.error(f"抓取失败: {url}, 错误: {e}")
                    results.append(WebContent(url=url, error=str(e)))

        success_count = sum(1 for r in results if r.success)
        logger.info(f"抓取完成: {success_count}/{len(urls)} 成功")

        return results

    def read_urls_with_progress(
        self,
        urls: List[str],
        on_progress: Callable[[int, int, str, bool], None] = None
    ) -> List[WebContent]:
        """
        批量读取 URL 并报告进度

        Args:
            urls: URL 列表
            on_progress: 进度回调函数 (current, total, url, success)

        Returns:
            List[WebContent]: 网页内容列表
        """
        results = []
        total = len(urls)

        logger.info(f"开始批量获取 {total} 个网页内容...")

        for idx, url in enumerate(urls):
            result = self.read_url(url)
            results.append(result)

            if on_progress:
                on_progress(idx + 1, total, url, result.success)

        success_count = sum(1 for r in results if r.success)
        logger.info(f"批量获取完成: {success_count}/{total} 成功")

        return results

    def fetch_from_search_results(
        self,
        search_results,
        max_count: int = 10
    ) -> List[WebContent]:
        """
        从搜索结果中获取网页完整内容

        Args:
            search_results: 搜索结果字典，包含 webpages 字段
            max_count: 最多获取多少个网页

        Returns:
            List[WebContent]: 网页内容列表
        """
        webpages = search_results.get("webpages", [])
        urls = [wp.get("url", "") for wp in webpages[:max_count] if wp.get("url")]
        logger.info(f"从搜索结果获取 {len(urls)} 个网页内容...")

        return self.read_urls(urls)

    def read_url_simple(self, url: str) -> str:
        """
        简化版：直接返回网页内容字符串

        Args:
            url: 要读取的网页 URL

        Returns:
            str: 网页内容，失败时返回空字符串
        """
        result = self.read_url(url)
        return result.content if result.success else ""
