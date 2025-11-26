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
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

from database import db
from media_platform.bilibili import BilibiliCrawler
from media_platform.douyin import DouYinCrawler
from media_platform.kuaishou import KuaishouCrawler
from media_platform.tieba import TieBaCrawler
from media_platform.weibo import WeiboCrawler
from media_platform.xhs import XiaoHongShuCrawler
from media_platform.zhihu import ZhihuCrawler
from media_platform.nytimes.core import NYTimesCrawler
from media_platform.qqnews.core import QQNewsCrawler

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MediaCrawlerAPI")

# 支持的媒体平台
SUPPORTED_PLATFORMS = [
    "xhs", "dy", "ks", "bili", "wb", "tieba", "zhihu", "nytimes", "qqnews"
]

# 爬虫工厂类
class CrawlerFactory:
    CRAWLERS = {
        "xhs": XiaoHongShuCrawler,
        "dy": DouYinCrawler,
        "ks": KuaishouCrawler,
        "bili": BilibiliCrawler,
        "wb": WeiboCrawler,
        "tieba": TieBaCrawler,
        "zhihu": ZhihuCrawler,
        "nytimes": NYTimesCrawler,
        "qqnews": QQNewsCrawler,
    }

    @staticmethod
    def create_crawler(platform: str, config: Dict) -> Union[BilibiliCrawler, DouYinCrawler, KuaishouCrawler, 
                                                           TieBaCrawler, WeiboCrawler, XiaoHongShuCrawler, 
                                                           ZhihuCrawler, NYTimesCrawler, QQNewsCrawler]:
        crawler_class = CrawlerFactory.CRAWLERS.get(platform)
        if not crawler_class:
            raise ValueError(f"不支持的媒体平台: {platform}")
        # 确保所有平台配置为字典并包含必要键
        if not isinstance(config, dict):
            config = vars(config) if hasattr(config, '__dict__') else {}
        # 所有平台统一使用字典参数传递配置
        # 小红书爬虫特殊处理：不传递配置参数
        if platform.lower() == 'xhs':
            return crawler_class()
        # QQNews爬虫需要特殊处理配置
        if platform.lower() == 'qqnews':
            # 创建一个简单的配置对象来满足QQNewsCrawler的要求
            class SimpleConfig:
                def __init__(self, **entries):
                    self.__dict__.update(entries)
            
            config_obj = SimpleConfig(**config)
            # 确保SAVE_DATA_OPTION设置为db以启用数据库存储
            if not hasattr(config_obj, 'SAVE_DATA_OPTION'):
                config_obj.SAVE_DATA_OPTION = 'db'
            # 确保其他必要配置也存在
            if not hasattr(config_obj, 'CRAWLER_TYPE'):
                config_obj.CRAWLER_TYPE = 'search'
            return crawler_class(config_obj)
        return crawler_class(config)

# 请求参数模型
class CrawlRequest(BaseModel):
    platform: str = Field(..., description="媒体平台", example="xhs")
    type: str = Field(default="search", description="爬取类型: search(搜索) | detail(详情) | creator(创作者)")
    keywords: Optional[str] = Field(default=None, description="搜索关键词，多个关键词用逗号分隔")
    start_page: int = Field(default=1, ge=1, description="起始页码")
    get_comment: bool = Field(default=False, description="是否爬取评论")
    get_sub_comment: bool = Field(default=False, description="是否爬取二级评论")
    save_data_option: str = Field(default="json", description="数据保存方式: csv | db | json | sqlite")
    cookies: Optional[str] = Field(default=None, description="Cookie 登录方式使用的 Cookie 值")
    login_type: str = Field(default="qrcode", description="登录方式: qrcode | phone | cookie")
    # QQ新闻专用参数
    specified_notes: Optional[List[str]] = Field(default=None, description="指定新闻URL列表（仅用于QQ新闻detail类型）")

    @validator('platform')
    def validate_platform(cls, v):
        if v not in SUPPORTED_PLATFORMS:
            raise ValueError(f"不支持的媒体平台: {v}，支持的平台有: {', '.join(SUPPORTED_PLATFORMS)}")
        return v

    @validator('type')
    def validate_type(cls, v):
        if v not in ['search', 'detail', 'creator']:
            raise ValueError("爬取类型必须是: search, detail 或 creator")
        return v

    @validator('save_data_option')
    def validate_save_option(cls, v):
        if v not in ['csv', 'db', 'json', 'sqlite']:
            raise ValueError("数据保存方式必须是: csv, db, json 或 sqlite")
        return v

    @validator('login_type')
    def validate_login_type(cls, v):
        if v not in ['qrcode', 'phone', 'cookie']:
            raise ValueError("登录方式必须是: qrcode, phone 或 cookie")
        return v

# 响应模型
class CrawlResponse(BaseModel):
    task_id: str
    status: str
    message: str
    platform: str
    crawl_type: str
    created_at: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: Optional[Dict] = None
    result: Optional[Dict] = None

# 活跃任务管理
active_tasks = {}

# 应用启动和关闭事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库连接
    logger.info("启动MediaCrawler API服务...")
    yield
    # 关闭时清理资源
    logger.info("关闭MediaCrawler API服务...")
    if 'db' in locals():
        await db.close()

# 创建FastAPI应用
app = FastAPI(
    title="MediaCrawler API",
    description="多平台媒体数据爬取API服务",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 临时允许所有来源用于调试
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
from fastapi import Request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"收到请求: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"返回响应: {response.status_code}")
    return response

# 异步任务处理
async def run_crawler_task(task_id: str, crawl_request: CrawlRequest):
    try:
        # 更新任务状态
        active_tasks[task_id] = {
            "status": "running",
            "progress": {"step": "initializing", "percentage": 0}
        }

        # 准备配置
        config_dict = {
            "PLATFORM": crawl_request.platform,
            "CRAWLER_TYPE": crawl_request.type,
            "START_PAGE": crawl_request.start_page,
            "KEYWORDS": crawl_request.keywords,
            "ENABLE_GET_COMMENTS": crawl_request.get_comment,
            "ENABLE_GET_SUB_COMMENTS": crawl_request.get_sub_comment,
            "SAVE_DATA_OPTION": crawl_request.save_data_option,
            "COOKIES": crawl_request.cookies,
            "LOGIN_TYPE": crawl_request.login_type
        }
        
        # 如果是QQ新闻且指定了新闻URL列表，则添加到配置中
        if crawl_request.platform.lower() == 'qqnews' and crawl_request.specified_notes:
            config_dict["SPECIFIED_NOTES"] = crawl_request.specified_notes

        active_tasks[task_id]["progress"] = {"step": "creating_crawler", "percentage": 10}

        # 创建爬虫实例
        crawler = CrawlerFactory.create_crawler(crawl_request.platform, config_dict)
        
        active_tasks[task_id]["progress"] = {"step": "starting_crawler", "percentage": 20}

        # 执行爬取
        await crawler.start()
        
        active_tasks[task_id]["status"] = "completed"
        active_tasks[task_id]["progress"] = {"step": "finished", "percentage": 100}
        active_tasks[task_id]["result"] = {"success": True, "message": "爬取完成"}
        
        logger.info(f"任务 {task_id} 完成: {crawl_request.platform} - {crawl_request.type}")
    
    except Exception as e:
        error_message = str(e)
        logger.error(f"任务 {task_id} 失败: {error_message}")
        active_tasks[task_id]["status"] = "failed"
        active_tasks[task_id]["result"] = {"success": False, "error": error_message}

# API端点
@app.get("/", tags=["health"])
async def root():
    return {
        "message": "Welcome to MediaCrawler API",
        "supported_platforms": SUPPORTED_PLATFORMS,
        "docs": "/docs"
    }

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}

@app.get("/test", tags=["test"])
async def test_endpoint():
    logger.info("测试接口被调用")
    return {"status": "success", "message": "测试接口调用成功"}

@app.post("/api/crawl", response_model=CrawlResponse, tags=["crawling"])
async def start_crawling(crawl_request: CrawlRequest, background_tasks: BackgroundTasks):
    logger.info("收到/api/crawl请求，开始处理...")
    logger.info("爬取接口被调用")
    logger.info(f"收到爬取请求: {crawl_request.dict()}")
    logger.info(f"平台: {crawl_request.platform}, 类型: {crawl_request.type}, 关键词: {crawl_request.keywords}")
    """
    开始爬取任务
    
    - **platform**: 媒体平台 (xhs, dy, ks, bili, wb, tieba, zhihu, nytimes, qqnews)
    - **type**: 爬取类型 (search, detail, creator)
    - **keywords**: 搜索关键词，多个关键词用逗号分隔
    - **start_page**: 起始页码
    - **get_comment**: 是否爬取评论
    - **get_sub_comment**: 是否爬取二级评论
    - **save_data_option**: 数据保存方式 (csv, db, json, sqlite)
    - **cookies**: Cookie登录方式使用的Cookie值
    - **login_type**: 登录方式 (qrcode, phone, cookie)
    """
    try:
        # 生成任务ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # 在后台启动爬取任务
        background_tasks.add_task(run_crawler_task, task_id, crawl_request)
        
        # 更新活跃任务列表
        active_tasks[task_id] = {
            "status": "queued",
            "request": crawl_request.dict()
        }
        
        # 返回任务信息
        return CrawlResponse(
            task_id=task_id,
            status="queued",
            message="爬取任务已创建，正在后台执行",
            platform=crawl_request.platform,
            crawl_type=crawl_request.type,
            created_at=str(asyncio.get_event_loop().time())
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tasks", tags=["tasks"])
async def list_tasks():
    """
    获取所有活跃任务列表
    """
    return {"tasks": active_tasks}

@app.get("/api/tasks/{task_id}", response_model=TaskStatus, tags=["tasks"])
async def get_task_status(task_id: str):
    """
    获取特定任务的状态
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = active_tasks[task_id]
    return TaskStatus(
        task_id=task_id,
        status=task["status"],
        progress=task.get("progress"),
        result=task.get("result")
    )

@app.post("/api/init-db", tags=["database"])
async def initialize_database(db_type: str = Query(..., description="数据库类型", regex="^(sqlite|mysql)$")):
    """
    初始化数据库表结构
    """
    try:
        await db.init_db(db_type)
        return {"status": "success", "message": f"数据库 {db_type} 初始化成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 启动API服务
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发环境启用热重载
        log_level="info"
    )