from sqlalchemy.exc import IntegrityError
from database.db_session import get_session
from database.models import QQNewsModel
from tools.utils import logger

class QQNewsStore:
    def __init__(self, config):
        self.config = config

    async def save_news(self, news_data: QQNewsModel):
        """
        Save news data to the database if SAVE_DATA_OPTION is set to 'db'
        """
        # 检查是否启用了数据库存储，默认为'db'
        save_option = getattr(self.config, 'SAVE_DATA_OPTION', 'db')
        if save_option != 'db':
            return

        # 注意：get_session会自动处理commit/rollback，所以我们不需要手动调用
        async with get_session(save_option) as session:
            # 检查session是否有效
            if session is None:
                logger.error("数据库会话无效，无法保存新闻数据")
                return
                
            try:
                # 检查新闻是否已存在（通过URL）
                from sqlalchemy import select
                stmt = select(QQNewsModel).where(QQNewsModel.url == news_data.url)
                result = await session.execute(stmt)
                existing_news = result.scalar_one_or_none()
                
                if existing_news:
                    logger.info(f"新闻已存在: {news_data.title[:20]}...")
                    # 即使新闻已存在，也要确保会话能正确关闭
                    return

                session.add(news_data)
                # 不需要手动调用commit，get_session会自动处理
                logger.info(f"成功保存新闻: {news_data.title[:20]}...")
            except IntegrityError as e:
                logger.error(f"保存新闻失败(数据冲突): {str(e)}")
            except Exception as e:
                logger.error(f"保存新闻失败: {str(e)}")