"""
FastAPI应用主入口
"""
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import time
import uuid

from .core import get_settings, get_logger, VeriTextBaseException
from .api import detection_router, health_router, get_detection_service

# 获取配置和日志
settings = get_settings()
logger = get_logger()

# 设置路径
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# 模板引擎
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("正在启动敏感词检测服务...")
    
    try:
        # 预加载检测服务（触发词库和模型加载）
        detection_service = get_detection_service()
        logger.info("检测服务预加载完成")
        
        logger.info(f"敏感词检测服务启动成功，版本: {settings.app_version}")
        yield
        
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        raise
    finally:
        # 关闭时清理
        logger.info("敏感词检测服务正在关闭...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="高性能敏感词检测API服务，支持规则匹配和语义检测",
    docs_url=settings.docs_url if not settings.debug else settings.docs_url,
    openapi_url=settings.openapi_url,
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求ID中间件
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """为每个请求添加唯一ID"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    # 处理请求
    response = await call_next(request)
    
    # 添加响应头
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    # 记录请求日志
    logger.info(
        f"请求处理完成",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": process_time
        }
    )
    
    return response


# 全局异常处理器
@app.exception_handler(VeriTextBaseException)
async def veri_text_exception_handler(request: Request, exc: VeriTextBaseException):
    """处理自定义异常"""
    logger.error(
        f"业务异常: {exc.message}",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "error_code": exc.error_code,
            "details": exc.details
        }
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"未处理异常: {str(exc)}",
        extra={"request_id": request_id},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务内部错误",
            "request_id": request_id
        }
    )


# 注册路由
app.include_router(detection_router, prefix=settings.api_prefix)
app.include_router(health_router, prefix=settings.api_prefix)

# 引入主API路由（包含配置API）
from .api.main_api import router as main_api_router
app.include_router(main_api_router)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Web界面路由
@app.get("/", response_class=HTMLResponse, summary="敏感词检测界面")
async def web_interface(request: Request):
    """提供敏感词检测Web界面"""
    try:
        return templates.TemplateResponse("detector.html", {"request": request})
    except FileNotFoundError:
        logger.error("检测界面模板文件不存在")
        return HTMLResponse(
            content="""
            <html>
                <head><title>敏感词检测服务</title></head>
                <body>
                    <h1>敏感词检测服务</h1>
                    <p>Web界面暂不可用，请直接使用API接口。</p>
                    <p>API文档: <a href="/docs">/docs</a></p>
                </body>
            </html>
            """,
            status_code=200
        )


# API信息路由
@app.get("/api", summary="API服务信息")
async def api_info():
    """API服务信息"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs_url": settings.docs_url,
        "api_prefix": settings.api_prefix
    }


# 命令行启动
def main():
    """主函数"""
    settings = get_settings()
    
    print(f"启动 {settings.app_name} v{settings.app_version}")
    print(f"地址: http://{settings.host}:{settings.port}")
    print(f"API文档: http://{settings.host}:{settings.port}{settings.docs_url}")
    print(f"调试模式: {'开启' if settings.debug else '关闭'}")
    print("-" * 50)
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
