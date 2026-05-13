"""
应用配置模块

安全规范：
- API Key 严禁硬编码在代码中，必须通过环境变量注入。
- 生产环境建议使用密钥管理服务（如阿里云 KMS、AWS Secrets Manager）。
"""
import os
from typing import Optional

import os

# 手动加载 .env 文件（不依赖 python-dotenv，兼容 FC 环境）
_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
if os.path.exists(_ENV_PATH):
    with open(_ENV_PATH, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("#"):
                continue
            if "=" in _line:
                _key, _value = _line.split("=", 1)
                os.environ.setdefault(_key.strip(), _value.strip())


class Settings:
    """应用配置"""

    # ================== 通义千问 (Qwen) AI 模型配置 ==================
    # 请从阿里云百炼/灵积控制台 (https://bailian.console.aliyun.com) 获取 API Key
    # 本地开发推荐在 .env 文件或系统环境变量中设置，切勿直接写死在代码里！
    QWEN_API_KEY: Optional[str] = os.getenv("QWEN_API_KEY", "")
    # 通义千问 OpenAI 兼容接口地址
    QWEN_BASE_URL: Optional[str] = os.getenv(
        "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    # 默认模型：qwen-plus（性价比高，支持 128K 上下文）
    # 可选：qwen-max（最强效果）、qwen-turbo（轻量快速）
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "qwen-plus")

    # ================== 阿里云标准环境变量兼容 ==================
    # 如果你习惯用阿里云官方文档推荐的 DASHSCOPE_API_KEY，也支持自动读取
    DASHSCOPE_API_KEY: Optional[str] = os.getenv("DASHSCOPE_API_KEY", "")

    # ================== 阿里云 FC 控制台兼容（极简命名） ==================
    # 阿里云 FC 控制台输入环境变量时可能有隐藏限制，
    # 因此提供极简命名作为兜底。优先级：标准名 > 驼峰名 > 极简名
    QWEN_API_KEY_CAMEL: Optional[str] = os.getenv("QwenApiKey", "")
    QWEN_BASE_URL_CAMEL: Optional[str] = os.getenv("QwenBaseUrl", "")
    QWEN_MODEL_CAMEL: Optional[str] = os.getenv("QwenModel", "")
    # 极简命名（纯字母，无大小写混合，最不容易触发控制台 bug）
    API_KEY_SIMPLE: Optional[str] = os.getenv("ApiKey", "")
    BASE_URL_SIMPLE: Optional[str] = os.getenv("BaseUrl", "") or os.getenv("BASE_URL", "")
    MODEL_SIMPLE: Optional[str] = os.getenv("AiModel", "") or os.getenv("AI_MODEL", "")

    # ================== 小米 MiMo 兼容配置（可选） ==================
    MIMO_API_KEY: Optional[str] = os.getenv("MIMO_API_KEY", "")
    MIMO_BASE_URL: Optional[str] = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
    MIMO_MODEL: str = os.getenv("MIMO_MODEL", "mimo-v2-flash")

    # ================== 通用 OpenAI 兼容配置（可选） ==================
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # ================== Redis 缓存配置 ==================
    REDIS_HOST: str = os.getenv("REDIS_HOST", "")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # ================== 应用基础配置 ==================
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "15728640"))  # 15MB，兼容 Base64 编码

    # 上传目录
    UPLOAD_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads"
    )

    @property
    def redis_enabled(self) -> bool:
        """是否启用 Redis 缓存"""
        return bool(self.REDIS_HOST)

    @property
    def ai_enabled(self) -> bool:
        """是否已配置 AI 模型"""
        return bool(self.qwen_api_key or self.MIMO_API_KEY or self.OPENAI_API_KEY)

    @property
    def qwen_api_key(self) -> str:
        """获取千问 API Key（优先级：标准名 > DASHSCOPE > 驼峰 > 极简）"""
        return (
            self.QWEN_API_KEY
            or self.DASHSCOPE_API_KEY
            or self.QWEN_API_KEY_CAMEL
            or self.API_KEY_SIMPLE
            or ""
        )

    @property
    def ai_api_key(self) -> str:
        """获取当前生效的 AI API Key（优先级：千问 > MiMo > OpenAI）"""
        if self.qwen_api_key:
            return self.qwen_api_key
        if self.MIMO_API_KEY:
            return self.MIMO_API_KEY
        return self.OPENAI_API_KEY or ""

    @property
    def ai_base_url(self) -> str:
        """获取当前生效的 AI Base URL"""
        if self.qwen_api_key:
            url = (
                self.QWEN_BASE_URL
                or self.QWEN_BASE_URL_CAMEL
                or self.BASE_URL_SIMPLE
                or "https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            return url.strip()
        if self.MIMO_API_KEY:
            return self.MIMO_BASE_URL
        return self.OPENAI_BASE_URL or "https://api.openai.com/v1"

    @property
    def ai_model(self) -> str:
        """获取当前生效的 AI 模型名"""
        if self.qwen_api_key:
            return self.QWEN_MODEL or self.QWEN_MODEL_CAMEL or self.MODEL_SIMPLE or "qwen-plus"
        if self.MIMO_API_KEY:
            return self.MIMO_MODEL
        return self.OPENAI_MODEL


settings = Settings()
