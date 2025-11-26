import asyncio
import config
from media_platform.qqnews.core import QQNewsCrawler

# 设置QQNews平台配置
config.PLATFORM = "qqnews"
config.CRAWLER_TYPE = "search"  # 使用搜索模式而不是详情页模式
config.KEYWORDS = ""  # 清空关键词
config.HEADLESS = True  # 无头模式

async def main():
    try:
        # 创建QQNews爬虫实例
        crawler = QQNewsCrawler(config)
        print("开始执行QQNews爬虫...")
        
        # 启动爬虫
        await crawler.start()
        print("QQNews爬虫执行完成")
        
    except Exception as e:
        print(f"执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())