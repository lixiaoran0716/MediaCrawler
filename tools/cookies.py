import json
from pathlib import Path

class CookiesManager:
    """Cookie管理类，用于加载和保存cookies"""
    def __init__(self, cookies_path: str = 'cookies.json'):
        self.cookies_path = Path(cookies_path)
        self.cookies = self._load_cookies()

    def _load_cookies(self) -> dict:
        """加载保存的cookies"""
        if self.cookies_path.exists():
            try:
                with open(self.cookies_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_cookies(self, cookies: dict) -> None:
        """保存cookies到文件"""
        try:
            with open(self.cookies_path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            self.cookies = cookies
        except IOError as e:
            print(f"保存cookies失败: {e}")

    def get_cookies(self) -> dict:
        """获取当前cookies"""
        return self.cookies

    async def extract_cookies_from_browser(self, browser_context):
        """从浏览器上下文中提取cookies"""
        cookies = await browser_context.cookies()
        return {cookie['name']: cookie['value'] for cookie in cookies}

    def update_cookies(self, new_cookies: dict) -> None:
        """更新cookies"""
        self.cookies.update(new_cookies)
        self.save_cookies(self.cookies)