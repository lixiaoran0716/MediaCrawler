import asyncio
import httpx
from typing import Dict, Optional, Any

from tools import utils
from tools.cookies import CookiesManager


class NYTimesClient:
    def __init__(
        self,
        proxy: Optional[str] = None,
        timeout: int = 10,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None
    ):
        self.proxy = proxy
        self.timeout = timeout
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.cookies_manager = CookiesManager()
        self.client = self._create_client()

    def _create_client(self) -> httpx.AsyncClient:
        """创建HTTP客户端"""
        client_kwargs = {
            'timeout': httpx.Timeout(self.timeout),
            'headers': self.headers,
            'follow_redirects': True,
            'verify': False
        }

        if self.proxy:
            client_kwargs['proxy'] = self.proxy

        if self.cookies:
            client_kwargs['cookies'] = self.cookies

        return httpx.AsyncClient(**client_kwargs)

    async def update_cookies(self, browser_context=None) -> None:
        """从浏览器上下文更新cookies"""
        if browser_context:
            cookies = await self.cookies_manager.extract_cookies_from_browser(browser_context)
            self.cookies = cookies
            # 更新客户端cookies
            self.client.cookies = cookies

    async def pong(self) -> bool:
        """测试与服务器的连接"""
        try:
            # 使用更真实的移动端请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            }
            
            # 合并现有头信息
            request_headers = {**self.headers, **headers}
            
            utils.logger.debug(f"[NYTimesClient.pong] Testing connection with headers: {request_headers}")
            response = await self.client.get('https://m.cn.nytimes.com/china', headers=request_headers, timeout=30)
            
            utils.logger.debug(f"[NYTimesClient.pong] Response status: {response.status_code}")
            utils.logger.debug(f"[NYTimesClient.pong] Response headers: {response.headers}")
            
            return response.status_code == 200
        except Exception as e:
            utils.logger.error(f"[NYTimesClient.pong] Connection test failed: {str(e)}", exc_info=True)
            return False

    async def get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        """发送GET请求"""
        try:
            response = await self.client.get(url, params=params,** kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            utils.logger.error(f"[NYTimesClient.get] HTTP error occurred: {str(e)}")
            raise
        except Exception as e:
            utils.logger.error(f"[NYTimesClient.get] Error occurred: {str(e)}")
            raise

    async def close(self) -> None:
        """关闭HTTP客户端"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()