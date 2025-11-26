# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

import aiosqlite
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Database")

# 创建基类
Base = declarative_base()

# 数据库表模型
class NewsContent(Base):
    __tablename__ = "news_content"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False, index=True)
    url = Column(String(500), nullable=False, unique=True)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    author = Column(String(200), nullable=True)
    publish_time = Column(DateTime, nullable=True)
    crawled_time = Column(DateTime, default=datetime.now)
    image_urls = Column(Text, nullable=True)  # 存储为JSON字符串
    video_urls = Column(Text, nullable=True)  # 存储为JSON字符串
    metadata = Column(Text, nullable=True)    # 存储其他元数据为JSON字符串

class NewsComment(Base):
    __tablename__ = "news_comments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey("news_content.id"), nullable=False)
    comment_id = Column(String(200), nullable=True)  # 平台原始评论ID
    author = Column(String(200), nullable=True)
    content = Column(Text, nullable=True)
    publish_time = Column(DateTime, nullable=True)
    likes = Column(Integer, default=0)
    parent_id = Column(String(200), nullable=True)  # 用于回复评论
    platform = Column(String(50), nullable=False)
    crawled_time = Column(DateTime, default=datetime.now)

class CreatorInfo(Base):
    __tablename__ = "creator_info"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False)
    creator_id = Column(String(200), nullable=False, unique=True)
    name = Column(String(200), nullable=True)
    avatar = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    follower_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    post_count = Column(Integer, default=0)
    metadata = Column(Text, nullable=True)
    crawled_time = Column(DateTime, default=datetime.now)

# 数据库管理器类
class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
        self.db_type = None
        self.db_path = None
        self.initialized = False
    
    async def init_db(self, db_type: str = "sqlite"):
        """
        初始化数据库连接
        
        Args:
            db_type: 数据库类型，支持 'sqlite' 或 'mysql'
        """
        self.db_type = db_type
        
        try:
            if db_type == "sqlite":
                # SQLite 数据库配置
                self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media_crawler.db")
                
                # 同步引擎 (用于创建表)
                self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
                
                # 异步引擎 (用于操作)
                self.async_engine = create_async_engine(
                    f"sqlite+aiosqlite:///{self.db_path}",
                    echo=False,
                    future=True
                )
                
                self.AsyncSessionLocal = async_sessionmaker(
                    self.async_engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )
                
            elif db_type == "mysql":
                # MySQL 数据库配置 (示例，需要根据实际情况修改)
                # 注意：在生产环境中，这些配置应该通过环境变量或配置文件提供
                DB_USER = os.getenv("DB_USER", "root")
                DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
                DB_HOST = os.getenv("DB_HOST", "localhost")
                DB_PORT = os.getenv("DB_PORT", "3306")
                DB_NAME = os.getenv("DB_NAME", "media_crawler")
                
                # 同步引擎 (用于创建表)
                self.engine = create_engine(
                    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
                    echo=False
                )
                
                # 异步引擎 (用于操作)
                self.async_engine = create_async_engine(
                    f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
                    echo=False,
                    future=True
                )
                
                self.AsyncSessionLocal = async_sessionmaker(
                    self.async_engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )
            
            # 创建所有表
            Base.metadata.create_all(bind=self.engine)
            
            self.initialized = True
            logger.info(f"数据库 {db_type} 初始化成功")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise
    
    async def get_db(self):
        """
        获取数据库会话
        """
        if not self.initialized:
            await self.init_db()
        
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
    
    async def save_content(self, data: Dict[str, Any]) -> NewsContent:
        """
        保存内容数据
        """
        if not self.initialized:
            await self.init_db()
        
        async with self.AsyncSessionLocal() as session:
            try:
                # 检查URL是否已存在
                existing = await session.execute(
                    NewsContent.__table__.select().where(NewsContent.url == data.get("url"))
                )
                existing_content = existing.scalar_one_or_none()
                
                if existing_content:
                    # 更新现有记录
                    for key, value in data.items():
                        if hasattr(existing_content, key):
                            setattr(existing_content, key, value)
                    existing_content.crawled_time = datetime.now()
                    content = existing_content
                else:
                    # 创建新记录
                    content = NewsContent(**data)
                    session.add(content)
                
                await session.commit()
                await session.refresh(content)
                logger.info(f"内容保存成功: {content.id} - {content.title}")
                return content
            except Exception as e:
                await session.rollback()
                logger.error(f"内容保存失败: {str(e)}")
                raise
    
    async def save_comment(self, data: Dict[str, Any]) -> NewsComment:
        """
        保存评论数据
        """
        if not self.initialized:
            await self.init_db()
        
        async with self.AsyncSessionLocal() as session:
            try:
                comment = NewsComment(**data)
                session.add(comment)
                await session.commit()
                await session.refresh(comment)
                logger.info(f"评论保存成功: {comment.id}")
                return comment
            except Exception as e:
                await session.rollback()
                logger.error(f"评论保存失败: {str(e)}")
                raise
    
    async def save_creator(self, data: Dict[str, Any]) -> CreatorInfo:
        """
        保存创作者信息
        """
        if not self.initialized:
            await self.init_db()
        
        async with self.AsyncSessionLocal() as session:
            try:
                # 检查创作者ID是否已存在
                existing = await session.execute(
                    CreatorInfo.__table__.select().where(
                        (CreatorInfo.platform == data.get("platform")) & 
                        (CreatorInfo.creator_id == data.get("creator_id"))
                    )
                )
                existing_creator = existing.scalar_one_or_none()
                
                if existing_creator:
                    # 更新现有记录
                    for key, value in data.items():
                        if hasattr(existing_creator, key):
                            setattr(existing_creator, key, value)
                    existing_creator.crawled_time = datetime.now()
                    creator = existing_creator
                else:
                    # 创建新记录
                    creator = CreatorInfo(**data)
                    session.add(creator)
                
                await session.commit()
                await session.refresh(creator)
                logger.info(f"创作者信息保存成功: {creator.id} - {creator.name}")
                return creator
            except Exception as e:
                await session.rollback()
                logger.error(f"创作者信息保存失败: {str(e)}")
                raise
    
    async def get_content_by_platform(self, platform: str, limit: int = 10, offset: int = 0) -> List[NewsContent]:
        """
        根据平台获取内容列表
        """
        if not self.initialized:
            await self.init_db()
        
        async with self.AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    NewsContent.__table__.select()
                    .where(NewsContent.platform == platform)
                    .order_by(NewsContent.crawled_time.desc())
                    .limit(limit)
                    .offset(offset)
                )
                return result.scalars().all()
            except Exception as e:
                logger.error(f"获取内容失败: {str(e)}")
                raise
    
    async def close(self):
        """
        关闭数据库连接
        """
        if self.async_engine:
            await self.async_engine.dispose()
            logger.info("数据库连接已关闭")

# 创建数据库管理器实例
db = DatabaseManager()