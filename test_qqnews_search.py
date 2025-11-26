import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.qqnews_config import qq_news_config
from media_platform.qqnews.core import QQNewsCrawler

async def test_qqnews_search():
    """测试QQ新闻搜索功能"""
    # 设置爬虫类型为搜索
    qq_news_config.CRAWLER_TYPE = "search"
    qq_news_config.KEYWORDS = "科技"
    
    # 创建爬虫实例
    crawler = QQNewsCrawler(qq_news_config)
    
    # 启动爬虫
    print("开始测试QQ新闻搜索功能...")
    await crawler.start()
    print("QQ新闻搜索测试完成")

if __name__ == "__main__":
    asyncio.run(test_qqnews_search())