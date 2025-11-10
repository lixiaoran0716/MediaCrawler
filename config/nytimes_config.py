# -*- coding: utf-8 -*-
"""纽约时报中文网爬虫配置"""
import os
from typing import Optional

from pydantic import BaseSettings
from tools.utils import get_env_var


class NYTimesConfig(BaseSettings):
    """纽约时报中文网爬虫配置类"""
    # 基础URL
    BASE_URL: str = "https://m.cn.nytimes.com"
    # 新闻列表页URL
    NEWS_LIST_URL: str = "https://m.cn.nytimes.com/china"
    # 请求超时时间(秒)
    REQUEST_TIMEOUT: int = 60
    # 最大并发数
    MAX_CONCURRENCY: int = 5
    # 爬取间隔(秒)
    CRAWL_INTERVAL: int = 3
    # 是否启用代理
    ENABLE_PROXY: bool = True
    # 代理池大小
    PROXY_POOL_SIZE: int = 5
    # 重试次数
    RETRY_TIMES: int = 3
    # 页面加载等待时间(秒)
    PAGE_LOAD_WAIT: int = 2
    # 最大翻页数
    MAX_PAGE: int = 5
    # 数据保存方式(db/sqlite/file)
    SAVE_DATA_OPTION: str = "db"
    # 日志级别
    LOG_LEVEL: str = "INFO"

    class Config:
        """配置设置"""
        case_sensitive = True
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')


# 创建配置实例
nytimes_config = NYTimesConfig()


# 兼容旧版配置的导出变量
BASE_URL = nytimes_config.BASE_URL
NEWS_LIST_URL = nytimes_config.NEWS_LIST_URL
REQUEST_TIMEOUT = nytimes_config.REQUEST_TIMEOUT
MAX_CONCURRENCY = nytimes_config.MAX_CONCURRENCY
CRAWL_INTERVAL = nytimes_config.CRAWL_INTERVAL
ENABLE_PROXY = nytimes_config.ENABLE_PROXY
PROXY_POOL_SIZE = nytimes_config.PROXY_POOL_SIZE
RETRY_TIMES = nytimes_config.RETRY_TIMES
PAGE_LOAD_WAIT = nytimes_config.PAGE_LOAD_WAIT
MAX_PAGE = nytimes_config.MAX_PAGE
SAVE_DATA_OPTION = nytimes_config.SAVE_DATA_OPTION
LOG_LEVEL = nytimes_config.LOG_LEVEL