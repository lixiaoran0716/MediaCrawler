from sqlalchemy.orm import Session
from typing import Dict, Optional

from database.models import NytimesNews, NytimesComment
from database.db_session import get_session
from tools.utils import generate_unique_id


async def update_nytimes_news(news_info: Dict) -> Optional[NytimesNews]:
    """更新或创建纽约时报新闻记录"""
    if not news_info or not news_info.get('url'):
        return None

    async with get_session() as session:
        try:
                # 尝试通过URL查找现有记录
                existing_news = await session.query(NytimesNews).filter(NytimesNews.url == news_info['url']).first()

                if existing_news:
                    # 更新现有记录
                    for key, value in news_info.items():
                        if hasattr(existing_news, key) and value is not None:
                            setattr(existing_news, key, value)
                    news_item = existing_news
                else:
                    # 创建新记录
                    # 生成唯一ID（可以使用URL的哈希值或其他唯一标识）
                    news_id = generate_unique_id(news_info['url'])
                    news_item = NytimesNews(
                        id=news_id,
                        **news_info
                    )
                    session.add(news_item)

                await session.commit()
                await session.refresh(news_item)
                return news_item
        except Exception as e:
            await session.rollback()
            from tools import utils
            utils.logger.error(f"[update_nytimes_news] Database error: {str(e)}")
            return None
  


async def update_nytimes_comment(comment_info: Dict) -> Optional[NytimesComment]:
    """更新或创建纽约时报新闻评论记录"""
    if not comment_info or not comment_info.get('id'):
        return None

    async with get_session() as session:
        try:
                # 尝试通过ID查找现有记录
                existing_comment = await session.query(NytimesComment).filter(NytimesComment.id == comment_info['id']).first()

                if existing_comment:
                    # 更新现有记录
                    for key, value in comment_info.items():
                        if hasattr(existing_comment, key) and value is not None:
                            setattr(existing_comment, key, value)
                    comment_item = existing_comment
                else:
                    # 创建新记录
                    comment_item = NytimesComment(
                        **comment_info
                    )
                    session.add(comment_item)

                await session.commit()
                await session.refresh(comment_item)
                return comment_item
        except Exception as e:
            await session.rollback()
            from tools import utils
            utils.logger.error(f"[update_nytimes_comment] Database error: {str(e)}")
            return None
  


async def get_nytimes_news_by_url(url: str) -> Optional[NytimesNews]:
    """根据URL获取新闻记录"""
    async with get_session() as session:
        try:
            return await session.query(NytimesNews).filter(NytimesNews.url == url).first()
        except Exception as e:
            from tools import utils
            utils.logger.error(f"[get_nytimes_news_by_url] Database error: {str(e)}")
            return None
  


async def get_unprocessed_news() -> list[NytimesNews]:
    """获取未处理的新闻记录"""
    async with get_session() as session:
        try:
            return await session.query(NytimesNews).filter(NytimesNews.is_processed == False).all()
        except Exception as e:
            from tools import utils
            utils.logger.error(f"[get_unprocessed_news] Database error: {str(e)}")
            return []