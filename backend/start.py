"""
快捷启动脚本（本地开发使用）
"""
import sys
import os

# 解决 backend 目录下旧版依赖与 venv 冲突的问题
# 优先加载 venv 的 site-packages，再加载项目代码
backend_dir = os.path.dirname(os.path.abspath(__file__))
venv_path = os.path.join(backend_dir, "venv", "Lib", "site-packages")

for p in ("", backend_dir, os.getcwd()):
    while p in sys.path:
        sys.path.remove(p)

if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

if backend_dir not in sys.path:
    sys.path.append(backend_dir)

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print("=" * 50)
    print("AI 赋能的智能简历分析系统")
    print("=" * 50)
    print(f"文档地址: http://{settings.APP_HOST}:{settings.APP_PORT}/docs")
    print(f"前端页面: http://{settings.APP_HOST}:{settings.APP_PORT}/")
    print(f"AI 模型: {'已启用 (' + settings.ai_model + ')' if settings.ai_enabled else '未启用，使用规则提取'}")
    print(f"缓存: {'Redis' if settings.redis_enabled else '内存缓存'}")
    print("=" * 50)
    print()

    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
