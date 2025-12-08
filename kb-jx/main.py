from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.v1.endpoints import router as v1_router
from pathlib import Path
from config import config
from utils.logger import setup_logger, get_logger
from utils.cleaner import StorageCleaner

# 初始化日志
logger = setup_logger()
logger.info("="*60)
logger.info("文档检测与批量处理系统启动中...")
logger.info("="*60)

# 验证配置
if not config.validate():
    logger.error("配置验证失败，系统退出")
    exit(1)
logger.info("配置验证通过")

# 打印配置（调试模式）
if config.App.DEBUG:
    config.print_config()

# 创建 FastAPI 应用
app = FastAPI(
    title="文档检测与批量处理系统",
    description="检测文档是否为纯文本，并支持批量转换为 DOCX 格式",
    version="1.0.0"
)

logger.info("FastAPI 应用创建成功")

# 添加 CORS 中间件（从配置读取）
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.App.ALLOW_ORIGINS,
    allow_credentials=config.App.ALLOW_CREDENTIALS,
    allow_methods=config.App.ALLOW_METHODS,
    allow_headers=config.App.ALLOW_HEADERS,
)
logger.info("CORS 中间件配置完成")

# 注册路由（从配置读取前缀）
app.include_router(v1_router, prefix=config.App.API_PREFIX, tags=["documents"])
logger.info("API 路由注册完成")

# 挂载静态文件目录
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
logger.info(f"静态文件目录挂载成功: {static_dir.absolute()}")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "文档检测与批量处理系统",
        "version": "1.0.0",
        "web_upload": "http://localhost:8000/upload",
        "endpoints": {
            "单文件分析": "POST /api/v1/document/analyze",
            "批量上传": "POST /api/v1/documents/batch-upload",
            "查询任务状态": "GET /api/v1/batch/status/{task_id}",
            "下载纯文字转换": "GET /api/v1/batch/download/pure-converted/{task_id}",
            "下载富媒体原文件": "GET /api/v1/batch/download/rich-original/{task_id}",
            "下载所有文件": "GET /api/v1/batch/download/all/{task_id}"
        }
    }


@app.get("/upload")
async def upload_page():
    """文件夹上传页面"""
    upload_file = Path("static/upload.html")
    if upload_file.exists():
        logger.debug("返回上传页面")
        return FileResponse(upload_file)
    else:
        logger.warning("上传页面不存在")
        return {"error": "上传页面不存在"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_clean():
    """启动时执行清理任务"""
    logger.info("执行启动清理任务...")
    
    try:
        cleaner = StorageCleaner()
        # 从配置读取保留天数
        days = config.Storage.CLEAN_KEEP_DAYS
        result = cleaner.clean_old_batch_tasks(days=days)
        
        if result['deleted'] > 0:
            logger.info(
                f"启动清理完成: 删除 {result['deleted']} 个旧任务, "
                f"释放 {result['total_size_mb']} MB 空间"
            )
        else:
            logger.info("启动清理: 无需清理的文件")
    except Exception as e:
        logger.error(f"启动清理失败: {e}", exc_info=True)
    
    # 清理临时文件夹
    try:
        temp_dir = Path("storage/temp")
        if temp_dir.exists():
            import time
            current_time = time.time()
            deleted_count = 0
            freed_size = 0
            
            for temp_file in temp_dir.glob("*"):
                try:
                    # 删除1小时以上的临时文件
                    if temp_file.is_file():
                        file_age = current_time - temp_file.stat().st_mtime
                        if file_age > 3600:  # 1小时 = 3600秒
                            file_size = temp_file.stat().st_size
                            temp_file.unlink()
                            deleted_count += 1
                            freed_size += file_size
                            logger.debug(f"删除临时文件: {temp_file.name}")
                except Exception as e:
                    logger.debug(f"删除临时文件失败: {temp_file}, {e}")
            
            if deleted_count > 0:
                logger.info(f"临时文件清理完成: 删除 {deleted_count} 个文件, 释放 {freed_size / 1024 / 1024:.2f} MB 空间")
    except Exception as e:
        logger.error(f"临时文件清理失败: {e}", exc_info=True)


if __name__ == "__main__":
    import uvicorn
    import asyncio
    import sys
    
    # Windows 下抑制 ProactorEventLoop 的连接关闭异常
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        logger.info("Windows 事件循环策略配置完成")
    
    logger.info("="*60)
    logger.info("文档检测与批量处理系统")
    logger.info("="*60)
    logger.info(f"服务地址: http://{config.App.HOST}:{config.App.PORT}")
    logger.info(f"Web上传页面: http://localhost:{config.App.PORT}/upload")
    logger.info(f"API 文档: http://localhost:{config.App.PORT}/docs")
    logger.info(f"Redis: {config.Redis.HOST}:{config.Redis.PORT}/{config.Redis.DB}")
    logger.info("="*60)
    
    uvicorn.run(
        app,
        host=config.App.HOST,
        port=config.App.PORT,
        log_level=config.Log.LOG_LEVEL.lower()
    )
