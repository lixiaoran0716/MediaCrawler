import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from media_platform.qqnews.core import QQNewsCrawler

class SimpleConfig:
    def __init__(self):
        self.REQUEST_TIMEOUT = 30
        self.HEADLESS = True
        self.CDP_HEADLESS = True
        self.ENABLE_CDP_MODE = False
        self.ENABLE_IP_PROXY = False
        self.BROWSER_LAUNCH_TIMEOUT = 60

async def test_updated_crawler():
    """测试更新后的QQNews爬虫"""
    config = SimpleConfig()
    crawler = QQNewsCrawler(config)
    
    try:
        print("开始测试更新后的QQNews爬虫...")
        news_list = await crawler.get_news_list()
        
        print(f"\n成功获取到 {len(news_list)} 条新闻:")
        for i, news in enumerate(news_list[:5], 1):  # 只显示前5条
            print(f"{i}. 标题: {news['title']}")
            print(f"   链接: {news['url']}\n")
            
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_updated_crawler())