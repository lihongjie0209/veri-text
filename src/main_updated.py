"""
更新后的主应用入口
集成新的检测服务和管理界面
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path

from .core import get_settings, get_logger
from .api.main_api import router as main_router
from .api.wordlist_api import router as wordlist_router
from .utils.init_app import init_application

# 获取配置和日志
settings = get_settings()
logger = get_logger()


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    
    # 创建FastAPI实例
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="基于多规则引擎的敏感词检测服务",
        docs_url=settings.docs_url if settings.debug else None,
        openapi_url=settings.openapi_url if settings.debug else None,
    )
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 静态文件服务
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # 注册路由
    app.include_router(main_router)
    app.include_router(wordlist_router)
    
    # 应用启动事件
    @app.on_event("startup")
    async def startup_event():
        """应用启动时执行"""
        logger.info(f"启动 {settings.app_name} v{settings.app_version}")
        logger.info(f"服务地址: http://{settings.host}:{settings.port}")
        logger.info(f"管理界面: http://{settings.host}:{settings.port}/api/")
        if settings.debug:
            logger.info(f"API文档: http://{settings.host}:{settings.port}{settings.docs_url}")
        
        # 初始化应用数据（仅在首次启动时）
        try:
            init_application()
        except Exception as e:
            logger.warning(f"应用初始化出现问题（可能已初始化过）: {e}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时执行"""
        logger.info("应用正在关闭...")
    
    return app


def main():
    """主函数"""
    try:
        # 创建应用
        app = create_app()
        
        # 启动服务
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            workers=settings.workers if not settings.debug else 1,
            reload=settings.debug,
            log_level=settings.log_level.lower(),
            access_log=settings.debug
        )
        
    except Exception as e:
        logger.error(f"启动应用失败: {e}")
        raise


if __name__ == "__main__":
    main()
