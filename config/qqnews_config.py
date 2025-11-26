from config.base_config import Config


class QQNewsConfig(Config):
    # 爬虫名称
    CRAWLER_NAME = "qqnews"
    # 基础URL
    BASE_URL = "https://www.qq.com"
    # 新闻列表页URL
    NEWS_LIST_URL = "https://www.qq.com"
    # 搜索URL模板
    SEARCH_URL_TEMPLATE = "https://news.qq.com/search?query={keywords}&page=1"
    # 爬取间隔时间(秒)
    CRAWL_INTERVAL = 5
    # 最大并发数
    MAX_CONCURRENCY = 5
    # 超时时间(秒)
    TIMEOUT = 10
    # 是否启用IP代理
    ENABLE_IP_PROXY = False
    # IP代理池大小
    IP_PROXY_POOL_COUNT = 5
    # 重试次数
    RETRY_TIMES = 3
    # 新闻详情页超时时间(秒)
    DETAIL_PAGE_TIMEOUT = 15
    # 数据库存储相关配置
    SAVE_DATA_OPTION = "db"
    # 缓存类型
    CACHE_TYPE = "memory"
    # 缓存过期时间(秒)
    CACHE_EXPIRE_SECONDS = 3600
    # 指定新闻URL列表 (用于详情页爬取模式)
    SPECIFIED_NOTES = [
        # 示例URL，实际使用时需要替换为真实的腾讯新闻URL
        "https://news.qq.com/a/20241201/001234.htm",
        "https://news.qq.com/omn/20241201A05678.htm"
    ]


# 实例化配置对象
qq_news_config = QQNewsConfig()