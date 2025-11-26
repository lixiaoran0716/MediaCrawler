#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试QQNews爬虫获取新闻列表功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from media_platform.qqnews.core import QQNewsCrawler
from config.qqnews_config import qq_news_config

async def test_get_news_list():
    """测试获取新闻列表功能"""
    print("开始测试QQNews新闻列表获取...")
    
    # 创建爬虫实例
    crawler = QQNewsCrawler(qq_news_config)
    
    try:
        # 获取新闻列表
        news_list = await crawler.get_news_list()
        
        print(f"\n成功获取到 {len(news_list)} 条新闻:")
        print("=" * 50)
        
        for i, news in enumerate(news_list, 1):
            print(f"{i}. 标题: {news['title']}")
            print(f"   链接: {news['url']}")
            print("-" * 50)
            
        # 检查是否获取到了足够的新闻
        if len(news_list) >= 5:
            print(f"✅ 成功获取到 {len(news_list)} 条新闻，满足基本需求")
        else:
            print(f"⚠️  只获取到 {len(news_list)} 条新闻，少于预期的5条")
            
        return news_list
        
    except Exception as e:
        print(f"❌ 获取新闻列表时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    # 运行测试
    news_list = asyncio.run(test_get_news_list())
    
    print("\nQQNews新闻列表获取测试完成")