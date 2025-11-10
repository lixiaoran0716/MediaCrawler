# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

import asyncio
import re
import os
from store import nytimes as nytimes_store
from typing import Dict, List, Optional
import urllib.parse

from playwright.async_api import BrowserContext, Page, async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup

import config
from base.base_crawler import AbstractCrawler
from proxy.proxy_ip_pool import IpInfoModel, create_ip_pool

from store import nytimes as nytimes_store
from tools import utils
from tools.cdp_browser import CDPBrowserManager
from var import crawler_type_var

from .client import NYTimesClient
from .exception import DataFetchError
from .help import parse_news_info


class NYTimesCrawler(AbstractCrawler):
    context_page: Page
    nyt_client: NYTimesClient
    browser_context: BrowserContext
    cdp_manager: Optional[CDPBrowserManager]

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.index_url = "https://m.cn.nytimes.com/china"
        self.user_agent = utils.get_user_agent()
        self.cdp_manager = None

    async def launch_browser(self, chromium, proxy, user_agent, headless=True):
        """启动浏览器"""
        browser = await chromium.launch(
            headless=headless,
            proxy=proxy,
            args=[
                f"--user-agent={user_agent}",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        return await browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1280, 'height': 720},
            ignore_https_errors=True
        )

    async def launch_browser_with_cdp(self, playwright, proxy, user_agent, headless=True):
        """使用CDP模式启动浏览器"""
        self.cdp_manager = CDPBrowserManager()
        return await self.cdp_manager.launch_and_connect(playwright, playwright_proxy=proxy, user_agent=user_agent, headless=headless, viewport={'width': 1280, 'height': 720})

    async def create_ny_client(self, proxy):
        """创建NYT客户端"""
        return NYTimesClient(
            proxy=proxy,
            timeout=config.REQUEST_TIMEOUT,
            headers={
                'User-Agent': self.user_agent,
                'Referer': 'https://m.cn.nytimes.com/china',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
            }
        )

    async def extract_news_list(self, page_content):
        """从页面内容中提取新闻列表"""
        soup = BeautifulSoup(page_content, 'html.parser')
        news_items = []
        # 查找所有常规新闻项 - 更新选择器以匹配纽约时报当前页面结构
        # 使用基础选择器匹配所有文章标签，并添加详细日志
        # 提取所有可能包含新闻的元素并记录完整页面结构
        # 根据页面结构分析，使用更精确的选择器匹配新闻容器
        # 根据页面内容分析，使用移动版搜索结果选择器
        # 使用基础选择器匹配所有链接元素，并记录完整内容结构
        # 使用更具体的新闻容器选择器并优化日志
        # 使用更通用的选择器匹配可能的新闻容器
        # 根据爬取类型使用不同的文章选择器
        # 更精确的首页新闻选择器
        # 扩展选择器以匹配更多新闻容器类型
        # 增强的首页新闻选择器，添加通用选择器作为备选
        # 全面的首页新闻选择器，覆盖更多可能的容器结构
        # 超全面的首页新闻选择器，覆盖更多可能的容器结构
        item_selector = 'article, div.story, section.article, div.card, div[class*="news"], div[class*="post"], div[class*="item"], .story-card, .news-article, .featured-story, #main-content article, #latest-news .story, .stream-item, .tile-item, .content-item, [data-testid="story"], [role="article"]' if self.config.CRAWLER_TYPE == 'detail' else 'div[class*="result"], article, div[class*="item"]'
        items = soup.select(item_selector)
        utils.logger.info(f"[NYTimesCrawler] 找到 {len(items)} 个潜在新闻项")
        # 调试信息：记录页面HTML以便分析选择器问题
        if self.config.CRAWLER_TYPE == 'detail' and len(items) == 0:
            page_html = await self.context_page.content()
            with open('nytimes_homepage_debug.html', 'w', encoding='utf-8') as f:
                f.write(page_html)
            utils.logger.warning("[NYTimesCrawler] 未找到新闻项，已保存页面HTML到 nytimes_homepage_debug.html")
        # 无结果时记录页面内容以便调试
        if len(items) == 0:
            utils.logger.warning(f"[NYTimesCrawler] 未找到新闻项，页面内容预览: {soup.prettify()[:2000]}")
        for item in items:
            news_info = parse_news_info(item)
            if news_info:
                news_items.append(news_info)
        return news_items

    async def search(self):
        """搜索新闻（实现抽象方法）"""
        try:
            # 获取页面内容
            # 使用默认关键词确保搜索有结果
            keywords = self.config.KEYWORDS.strip() if hasattr(self.config, 'KEYWORDS') and self.config.KEYWORDS else 'china'
            # 使用移动版搜索URL并优化关键词编码
            encoded_keywords = urllib.parse.quote(keywords)
            # 根据爬取类型确定URL
            if self.config.CRAWLER_TYPE == "detail":
                search_url = self.index_url
                utils.logger.info(f"[NYTimesCrawler] 详情模式 - 直接访问首页: {search_url}")
            else:
                search_url = f"https://m.cn.nytimes.com/search?query={encoded_keywords}"
                utils.logger.info(f"[NYTimesCrawler] 搜索URL: {search_url}")
            # 使用浏览器导航获取动态内容
            await self.context_page.goto(search_url)
            # 等待页面加载完成
            await self.context_page.wait_for_load_state('networkidle')
            # 等待新闻容器加载
            if self.config.CRAWLER_TYPE == 'detail':
                # 等待多种可能的新闻容器
                # 等待主要内容容器加载
                # 延长超时时间并增加更多可能的主内容容器
                # 延长超时时间并使用更通用的选择器
                try:
                    # 修复缩进并使用更全面的主内容选择器
                    await self.context_page.wait_for_selector('body > div, #root, .app-content, .page-container, main, #main, [id*="content"], [class*="main"]', timeout=30000)
                except TimeoutError:
                    # 超时后保存页面内容用于调试
                    page_html = await self.context_page.content()
                    with open('nytimes_timeout_debug.html', 'w', encoding='utf-8') as f:
                        f.write(page_html)
                    utils.logger.error("主内容容器加载超时，已保存页面内容到 nytimes_timeout_debug.html")
                    raise
                # 等待新闻项加载
                # 扩展新闻项选择器范围并延长超时
                await self.context_page.evaluate('window.scrollTo(0, 0)')  # 滚动到顶部触发可能的内容加载
                await self.context_page.wait_for_selector('article, div.story, section.article, div.story-item, .news-article, .story-card, [data-testid="story"]', timeout=20000)
                # 滚动页面加载更多内容
                await self.context_page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(2)
                await self.context_page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        except Exception as e:
            utils.logger.error(f"页面加载失败: {e}")
            raise
        # 处理Cookie同意弹窗
        try:
            consent_button = self.context_page.locator('button:has-text("Accept")')
            await consent_button.click(timeout=5000)
        except Exception as e:
            utils.logger.warning(f"处理Cookie时出错: {str(e)}")
            # 等待页面完全加载和网络空闲
            await self.context_page.wait_for_load_state('networkidle')
            # 记录搜索URL以便调试
            utils.logger.info(f"[NYTimesCrawler] 搜索URL: {search_url}")
            # 增加页面滚动以加载更多内容
            for _ in range(3):
                await self.context_page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(2)
            # 调整选择器以匹配移动版页面结构
            try:
                # 增加页面内容日志并调整选择器
                page_content = await self.context_page.content()
                utils.logger.info(f"页面内容: {page_content[:2000]}")
                await self.context_page.wait_for_selector('div, article', timeout=60000)
            except TimeoutError:
                utils.logger.warning("主内容区域加载超时，尝试继续提取内容")
            page_content = await self.context_page.content()

            # 提取新闻信息
            news_list = await self.extract_news_list(page_content)
            utils.logger.info(f"[NYTimesCrawler] Extracted {len(news_list)} news items")

            # 存储新闻列表
            for news in news_list:
                await nytimes_store.update_nytimes_news(news)

            return news_list

        except Exception as e:
            utils.logger.error(f"[NYTimesCrawler.search] Error: {str(e)}")
            raise DataFetchError(f"Failed to search news: {str(e)}")

    async def fetch_and_store_news_details(self):
        """爬取新闻详情并存储到数据库"""
        # 从首页提取新闻链接
        page_content = await self.context_page.content()
        news_list = await self.extract_news_list(page_content)
        utils.logger.info(f"[NYTimesCrawler] 发现 {len(news_list)} 条新闻，开始爬取详情")

        # 逐个处理新闻详情
        stored_count = 0
        for idx, news in enumerate(news_list, 1):
            try:
                # 访问新闻详情页
                await self.context_page.goto(news['link'], timeout=60000, wait_until='networkidle')
                detail_content = await self.context_page.content()

                # 提取详情页信息
                news_detail = await self.parse_news_detail(detail_content, news)
                if news_detail:
                    # 存储到数据库
                    # 在独立线程中执行同步数据库操作
                    result = await asyncio.to_thread(
                        nytimes_store.update_nytimes_news,
                        news_detail
                    )
                    if result:
                        stored_count += 1
                        utils.logger.info(f"[{idx}/{len(news_list)}] 新闻详情存储成功: {news['title']}")
                    else:
                        utils.logger.warning(f"[{idx}/{len(news_list)}] 新闻详情存储失败: {news['title']}")
                else:
                    utils.logger.warning(f"[{idx}/{len(news_list)}] 未能提取详情: {news['title']}")
            except Exception as e:
                utils.logger.error(f"[{idx}/{len(news_list)}] 处理新闻失败: {str(e)}", exc_info=True)

        utils.logger.info(f"详情页爬取完成，成功存储 {stored_count}/{len(news_list)} 条新闻")
        # 等待所有异步任务完成
        await asyncio.sleep(10)
        utils.logger.info("所有数据库操作已完成")

        return news_list

    async def parse_news_detail(self, page_content, base_info):
        """解析新闻详情页"""
        soup = BeautifulSoup(page_content, 'html.parser')

        # 提取正文内容
        content_tag = soup.select_one('div.css-53u6y8')
        content = '\n'.join([p.get_text(strip=True) for p in content_tag.select('p')]) if content_tag else ''

        # 提取作者信息
        author_tag = soup.select_one('span.css-1n7hynb')
        author = author_tag.get_text(strip=True) if author_tag else ''

        # 合并基础信息和详情信息
        return {
            **base_info,
            'content': content,
            'author': author,
            'crawl_time': utils.get_current_time_str()
        }

    async def get_news_list(self):
        """获取新闻列表（兼容旧方法）"""
        return await self.search()

    async def start(self):
        """启动爬虫"""
        playwright_proxy_format, httpx_proxy_format = None, None
        if config.ENABLE_IP_PROXY:
            ip_proxy_pool = await create_ip_pool(config.IP_PROXY_POOL_COUNT, enable_validate_ip=True)
            ip_proxy_info: IpInfoModel = await ip_proxy_pool.get_proxy()
            playwright_proxy_format, httpx_proxy_format = utils.format_proxy_info(ip_proxy_info)

        async with async_playwright() as playwright:
            # 根据配置选择启动模式
            if config.ENABLE_CDP_MODE:
                utils.logger.info("[NYTimesCrawler] 使用CDP模式启动浏览器")
                self.browser_context = await self.launch_browser_with_cdp(
                    playwright,
                    playwright_proxy_format,
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                    headless=config.CDP_HEADLESS,
                )
            else:
                utils.logger.info("[NYTimesCrawler] 使用标准模式启动浏览器")
                # Launch a browser context.
                chromium = playwright.chromium
                self.browser_context = await self.launch_browser(
                    chromium,
                    playwright_proxy_format,
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                    headless=config.HEADLESS
                )
            stealth = Stealth()
            await stealth.apply_stealth_async(self.browser_context)
            self.context_page = await self.browser_context.new_page()
            # 使用更宽松的页面加载策略，避免networkidle导致的超时
            utils.logger.debug(f"[NYTimesCrawler] 正在访问首页: {self.index_url}")
            try:
                await self.context_page.goto(self.index_url, timeout=30000, wait_until='domcontentloaded')
                utils.logger.debug("[NYTimesCrawler] 页面DOM加载完成")
                # 等待额外的时间确保主要内容加载
                await asyncio.sleep(3)
            except Exception as e:
                utils.logger.error(f"[NYTimesCrawler] 页面访问失败: {str(e)}")
                raise

            # 创建客户端
            self.nyt_client = await self.create_ny_client(httpx_proxy_format)
            if not await self.nyt_client.pong():
                utils.logger.warning("[NYTimesCrawler] 客户端连接失败，尝试刷新页面")
                await self.context_page.reload()
                await self.nyt_client.update_cookies(browser_context=self.browser_context)

            # 根据爬虫类型执行不同任务
            crawler_type_var.set(config.CRAWLER_TYPE)
            if config.CRAWLER_TYPE == "search":
                await self.search()
            elif config.CRAWLER_TYPE == "detail":
                # 先搜索获取新闻列表，再爬取详情
                await self.search()
                await self.fetch_and_store_news_details()
            else:
                await self.get_news_list()
            # 等待所有异步任务完成后再关闭浏览器
            await asyncio.sleep(3)

            utils.logger.info("[NYTimesCrawler.start] 纽约时报中文网爬虫完成")