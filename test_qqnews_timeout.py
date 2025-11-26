import asyncio
import config
from media_platform.qqnews.core import QQNewsCrawler

async def main():
    # 设置配置参数以匹配错误报告中的参数
    config.PLATFORM = "qqnews"
    config.CRAWLER_TYPE = "detail"
    config.KEYWORDS = ""
    config.START_PAGE = 1
    config.ENABLE_GET_COMMENTS = False
    config.ENABLE_GET_SUB_COMMENTS = False
    config.SAVE_DATA_OPTION = "db"
    config.COOKIES = None
    config.LOGIN_TYPE = "qrcode"
    
    # 创建爬虫实例
    crawler = QQNewsCrawler(config)
    
    # 尝试运行爬虫
    try:
        await crawler.start()
        print("爬虫执行完成")
    except Exception as e:
        print(f"爬虫执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())