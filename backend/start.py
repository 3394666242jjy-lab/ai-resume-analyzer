"""
快捷启动脚本
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print("=" * 50)
    print("AI 赋能的智能简历分析系统")
    print("=" * 50)
    print(f"文档地址: http://{settings.APP_HOST}:{settings.APP_PORT}/docs")
    print(f"前端页面: http://{settings.APP_HOST}:{settings.APP_PORT}/")
    print(f"AI 模型: {'已启用 (' + settings.OPENAI_MODEL + ')' if settings.ai_enabled else '未启用（使用规则引擎）'}")
    print(f"缓存: {'Redis' if settings.redis_enabled else '内存缓存'}")
    print("=" * 50)
    print()
    
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
