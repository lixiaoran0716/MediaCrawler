import asyncio
import urllib.parse
from playwright.async_api import async_playwright, BrowserType, BrowserContext
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
from database.models import QQNewsModel
from tools.crawler_util import generate_random_id
from tools.time_util import parse_time
from store.qqnews._store_impl import QQNewsStore

class QQNewsCrawler:
    def __init__(self, config):
        self.config = config
        self.base_url = 'https://qq.com'  # 使用新闻域名作为基础URL
        self.news_list_url = 'https://news.qq.com/'  # 恢复到新闻首页，确保有新闻列表
        self.store = QQNewsStore(config)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.qq.com/',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        }

    async def start(self):
        """启动爬虫"""
        if hasattr(self.config, 'CRAWLER_TYPE') and self.config.CRAWLER_TYPE == 'detail':
            await self.get_specified_notes()
        elif hasattr(self.config, 'CRAWLER_TYPE') and self.config.CRAWLER_TYPE == 'search':
            await self.search()
        else:
            news_list = await self.get_news_list()
            for news in news_list:
                detail = await self.get_news_detail(news['url'])
                if detail:
                    news_data = self.parse_news_data(news, detail)
                    await self.store.save_news(news_data)
            print(f"爬取完成，共处理{len(news_list)}条新闻")

    async def get_specified_notes(self):
        """处理详情页爬取"""
        if not hasattr(self.config, 'SPECIFIED_NOTES'):
            print("未指定详情页URL列表")
            return
        
        specified_notes = self.config.SPECIFIED_NOTES
        print(f"开始处理详情页爬取，共{len(specified_notes)}条URL")
        
        if len(specified_notes) == 0:
            print("详情页URL列表为空，未找到需要处理的新闻")
            return
        
        processed_count = 0
        for i, url in enumerate(specified_notes, 1):
            print(f"[{i}/{len(specified_notes)}] 正在处理URL: {url}")
            try:
                detail = await self.get_news_detail(url)
                if detail:
                    news_data = self.parse_news_data({'url': url, 'title': ''}, detail)
                    await self.store.save_news(news_data)
                    processed_count += 1
                    print(f"[{i}/{len(specified_notes)}] 成功处理URL: {url}")
                else:
                    print(f"[{i}/{len(specified_notes)}] 处理URL失败(无详情数据): {url}")
            except Exception as e:
                print(f"[{i}/{len(specified_notes)}] 处理URL时发生错误: {url}, 错误: {str(e)}")
        
        print(f"详情页爬取完成，共{len(specified_notes)}条URL，成功处理{processed_count}条")

    async def search(self, keywords: str = "", page: int = 1) -> List[Dict[str, str]]:
        """搜索新闻"""
        # 获取关键词，如果没有指定则使用配置中的关键词
        if not keywords and hasattr(self.config, 'KEYWORDS'):
            keywords = self.config.KEYWORDS
        
        if not keywords:
            print("未指定搜索关键词")
            return []
        
        # 使用腾讯新闻搜索URL (根据用户提供的正确格式)
        encoded_keywords = urllib.parse.quote(keywords)
        search_url = f"https://news.qq.com/search?query={encoded_keywords}&page={page}"
        
        print(f"[QQNewsCrawler] 搜索URL: {search_url}")
        
        browser = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page_obj = await browser.new_page()
                
                # 设置请求头
                await page_obj.set_extra_http_headers(self.headers)
                
                # 导航到搜索页面并等待加载完成
                response = await page_obj.goto(search_url, wait_until='domcontentloaded', timeout=60000)
                
                # 等待页面主要内容加载完成
                try:
                    await page_obj.wait_for_selector('body', state='visible', timeout=15000)
                    # 给页面更多时间加载动态内容
                    await page_obj.wait_for_timeout(5000)
                except TimeoutError:
                    # 超时后捕获页面状态
                    await page_obj.screenshot(path='search_timeout_screenshot.png')
                    print("搜索页面加载超时，已保存截图到 search_timeout_screenshot.png")
                    raise
                
                # 获取渲染后的页面内容
                html_content = await page_obj.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 提取新闻列表
                news_items = []
                
                # 查找搜索结果项
                # 腾讯新闻搜索结果通常在特定的容器中
                result_containers = soup.find_all('div', class_='result-item')
                
                for container in result_containers:
                    # 查找标题和链接
                    title_tag = container.find('h3').find('a') if container.find('h3') else None
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        href = title_tag.get('href', '')
                        
                        if href and title:
                            # 处理相对URL
                            if href.startswith('/'):
                                href = f'https://news.qq.com{href}'
                            elif not href.startswith('http'):
                                # 对于搜索结果，链接可能是完整的URL
                                if not href.startswith('http'):
                                    # 保留原始链接，让后续处理决定
                                    pass
                                    
                            # 避免重复添加
                            if not any(item['url'] == href for item in news_items):
                                news_items.append({
                                    'title': title,
                                    'url': href
                                })
                
                # 如果没找到结果，尝试其他选择器
                if len(news_items) == 0:
                    # 尝试查找所有新闻链接
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        title = link.get_text(strip=True)
                        
                        # 过滤有效的新闻链接
                        if (href and title and 
                            (('news.qq.com' in href and '/a/' in href) or 
                             ('news.qq.com' in href and '/omn/' in href))):
                            
                            # 避免重复添加
                            if not any(item['url'] == href for item in news_items):
                                news_items.append({
                                    'title': title,
                                    'url': href
                                })
                
                print(f"[QQNewsCrawler] 搜索完成，共找到 {len(news_items)} 条新闻")
                
                # 如果是搜索模式，处理详情并保存
                if hasattr(self.config, 'CRAWLER_TYPE') and self.config.CRAWLER_TYPE == 'search':
                    for news in news_items:
                        # 对于搜索结果，需要确保URL是完整的
                        if news['url'].startswith('//'):
                            news['url'] = 'https:' + news['url']
                        elif news['url'].startswith('/'):
                            news['url'] = 'https://news.qq.com' + news['url']
                        
                        detail = await self.get_news_detail(news['url'])
                        if detail:
                            news_data = self.parse_news_data(news, detail)
                            await self.store.save_news(news_data)
                
                return news_items
        finally:
            pass

    async def get_news_list(self) -> List[Dict[str, str]]:
        """获取新闻列表"""
        browser = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # 设置请求头
                await page.set_extra_http_headers(self.headers)
                
                # 导航到新闻页面并等待加载完成
                print(f"正在获取新闻列表页: {self.news_list_url}")
                # 获取页面响应对象以获取状态码
                response = await page.goto(self.news_list_url, wait_until='domcontentloaded', timeout=60000)
                print(f"成功获取新闻列表页: {self.news_list_url}, 状态码: {response.status}")
                
                # 等待页面主要内容加载完成
                try:
                    # 等待页面主要内容区域加载完成
                    await page.wait_for_selector('body', state='visible', timeout=15000)
                    # 给页面更多时间加载动态内容
                    await page.wait_for_timeout(5000)
                except TimeoutError:
                    # 超时后捕获页面状态
                    await page.screenshot(path='timeout_screenshot.png')
                    print("页面加载超时，已保存截图到 timeout_screenshot.png")
                    raise
                
                # 获取渲染后的页面内容
                html_content = await page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 诊断信息打印
                print(f"\n=== 开始深度页面诊断 ===")
                print(f"请求URL: {self.news_list_url}")
                print(f"响应状态码: {response.status}")
                print(f"响应头部: {list(response.headers.items())[:5]}")
                
                news_items = []
                # 解析新闻列表项
                print("\n=== 开始深度页面诊断 ===")
                
                # 打印完整的响应状态和头部信息
                print(f"请求URL: {self.news_list_url}")
                print(f"响应状态码: {response.status}")
                print(f"响应头部: {list(response.headers.items())[:5]}")  # 打印前5个头部
                
                # 保存精简版HTML以便分析
                body_start = html_content.find('<body')
                body_end = html_content.find('</body>') + 7
                body_content = html_content[body_start:body_end] if body_start != -1 and body_end != -1 else html_content
                
                # 限制文件大小为20000字符
                trimmed_content = body_content[:20000] + '\n<!-- 内容已截断 -->' if len(body_content) > 20000 else body_content
                
                with open('debug_qqnews.html', 'w', encoding='utf-8') as f:
                    f.write(trimmed_content)
                print(f"精简版HTML已保存到 debug_qqnews.html (大小: {len(trimmed_content)}字符)")
                  
                # 根据HTML结构分析，使用新的选择器提取新闻
                # 查找所有新闻条目容器
                news_containers = soup.find_all('div', class_='channel-feed-item')
                
                for container in news_containers:
                    # 在每个容器中查找标题和链接
                    title_span = container.find('span', class_='article-title')
                    link_tag = container.find('a', href=True)
                    
                    if title_span and link_tag:
                        title = title_span.get_text(strip=True)
                        href = link_tag.get('href', '')
                        
                        if href and title:
                            # 处理相对URL
                            if href.startswith('/'):
                                href = f'https://news.qq.com{href}'
                            elif not href.startswith('http'):
                                href = f'https://news.qq.com{href}'
                                
                            # 避免重复添加
                            if not any(item['url'] == href for item in news_items):
                                news_items.append({
                                    'title': title,
                                    'url': href
                                })
                
                # 如果没找到足够的新闻链接，尝试备用选择器
                if len(news_items) < 5:
                    # 查找所有可能的新闻链接（备用方案）
                    potential_links = soup.find_all('a', href=True)
                    
                    for link in potential_links:
                        href = link.get('href', '')
                        title = link.get_text(strip=True)
                        
                        # 过滤有效的新闻链接
                        if (href and title and 
                            (('/a/' in href and len(href) > 10) or 
                             ('/omn/' in href) or 
                             (href.startswith('http') and 'qq.com' in href and '/a/' in href))):
                            # 处理相对URL
                            if href.startswith('/'):
                                href = f'https://news.qq.com{href}'
                            elif not href.startswith('http'):
                                href = f'https://news.qq.com{href}'
                                
                            # 避免重复添加
                            if not any(item['url'] == href for item in news_items):
                                news_items.append({
                                    'title': title,
                                    'url': href
                                })
                
                print(f"总共找到 {len(news_items)} 条新闻链接")
                
                print("\n=== 链接提取诊断结束 ===")
                return news_items
        finally:
            # 使用Playwright上下文自动管理浏览器生命周期
            pass

    async def launch_browser(self, chromium: BrowserType, playwright_proxy: Optional[Dict], user_agent: Optional[str], headless: bool = True) -> Optional[BrowserContext]:
        """实现基类AbstractCrawler的浏览器启动方法"""
        try:
            browser = await chromium.launch(headless=headless, proxy=playwright_proxy)
            context = await browser.new_context(user_agent=user_agent)
            return context
        except Exception as e:
            print(f"浏览器启动失败: {str(e)}")
            return None

    async def get_news_detail(self, url: str) -> Optional[Dict[str, str]]:
        """获取新闻详情页数据"""
        context = None
        try:
            async with async_playwright() as p:
                context = await self.launch_browser(p.chromium, None, self.headers.get('User-Agent'), headless=True)
                if not context:
                    print(f"浏览器上下文创建失败: {url}")
                    return None
                page = await context.new_page()
                await page.set_extra_http_headers(self.headers)

                # 导航到详情页并等待加载完成
                print(f"正在获取新闻详情页: {url}")
                response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                if response.status != 200:
                    print(f"获取详情页失败: {url}, 状态码: {response.status}")
                    return None
                print(f"成功获取新闻详情页: {url}, 状态码: {response.status}")

                # 获取页面内容
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')

                # 提取发布人信息
                author_tag = soup.select_one('a[href*="/omn/author/"] .media-name')
                author = author_tag.text.strip() if author_tag else ''
                author_url = soup.select_one('a[href*="/omn/author/"]').get('href', '').strip() if soup.select_one('a[href*="/omn/author/"]') else ''

                # 提取发布时间和地点
                publish_time_tag = soup.select_one('p.media-meta span:first-child')
                publish_time = publish_time_tag.text.strip() if publish_time_tag else ''
                if publish_time:
                    parsed_time = parse_time(publish_time)
                    publish_time = parsed_time.isoformat() if parsed_time else ''
                publish_location = ''
                media_account = ''

                # 增强内容提取
                content_paragraphs = soup.select('div.article-content p, div.rich_media_content p, #Cnt-Main-Article-QQ p')
                content = '\n'.join([p.text.strip() for p in content_paragraphs if p.text.strip()])

                result = {
                    'author': author,
                    'author_url': author_url,
                    'publish_time': publish_time,
                    'publish_location': publish_location,
                    'media_account': media_account,
                    'content': content
                }
                return result

        except Exception as e:
            print(f"获取新闻详情失败: {url}, 错误: {str(e)}")
            return None
        finally:
            # 确保context不为None且有效后再尝试关闭
            if context is not None:
                try:
                    # 再次检查context是否具有close方法
                    if hasattr(context, 'close'):
                        await context.close()
                except Exception as e:
                    print(f"关闭浏览器上下文时出错: {str(e)}")

    def parse_news_data(self, list_data: Dict[str, str], detail_data: Dict[str, str]) -> QQNewsModel:
        """解析新闻数据为模型对象"""
        # 从URL提取新闻ID（假设URL格式如https://news.qq.com/rain/a/20251111A023VI00）
        news_id = list_data['url'].split('/')[-1] if '/' in list_data['url'] else generate_random_id()

        return QQNewsModel(
            id=news_id,
            title=list_data['title'],
            url=list_data['url'],
            content=detail_data['content'],
            author=detail_data['author'],
            author_url=detail_data['author_url'],
            publish_time=parse_time(detail_data['publish_time']),
            publish_location=detail_data['publish_location'],
            media_account=detail_data['media_account']
        )