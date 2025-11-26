import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from media_platform.qqnews.core import QQNewsCrawler

# 创建一个简单的配置对象
class SimpleConfig:
    def __init__(self):
        self.SAVE_DATA_OPTION = 'db'

async def test_qqnews_crawler():
    """直接测试QQNews爬虫"""
    print("开始测试QQNews爬虫...")
    
    # 创建配置对象
    config = SimpleConfig()
    
    # 创建爬虫实例
    crawler = QQNewsCrawler(config)
    
    try:
        # 获取新闻列表
        print("正在获取新闻列表...")
        news_list = await crawler.get_news_list()
        
        print(f"成功获取到 {len(news_list)} 条新闻:")
        for i, news in enumerate(news_list[:5], 1):  # 只显示前5条
            print(f"{i}. 标题: {news['title']}")
            print(f"   链接: {news['url']}")
            print()
            
        if len(news_list) > 0:
            print(f"✅ 成功获取到 {len(news_list)} 条新闻，满足基本需求")
        else:
            print("❌ 未能获取到任何新闻")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_qqnews_crawler())