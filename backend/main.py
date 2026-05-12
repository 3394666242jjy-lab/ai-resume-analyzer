"""
AI 赋能的智能简历分析系统 - FastAPI 主入口
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.v1.resume import router as resume_router
from app.core.config import settings

# 创建应用
app = FastAPI(
    title="AI 赋能的智能简历分析系统",
    description="基于 AI 的简历解析、关键信息提取与岗位匹配评分系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(resume_router, prefix="/api/v1")

# 前端静态文件
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    # 如果前端是构建后的静态文件
    if os.path.exists(os.path.join(frontend_dir, "index.html")):
        app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def root():
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "AI 赋能的智能简历分析系统 API 服务运行中"}


@app.get("/api/health")
async def api_health():
    """API 健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "ai_enabled": settings.ai_enabled,
        "redis_enabled": settings.redis_enabled,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
