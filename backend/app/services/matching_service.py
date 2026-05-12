"""
简历匹配服务层
"""
from typing import Optional, Dict, Any

from app.core.cache import cache
from app.utils.ai_client import get_ai_client
from app.services.resume_service import get_resume_service


class MatchingService:
    """匹配服务"""

    def __init__(self):
        self.ai_client = get_ai_client()
        self.resume_service = get_resume_service()

    async def match_resume_with_job(
        self,
        resume_id: str,
        job_description: str
    ) -> Dict[str, Any]:
        """
        将简历与岗位需求进行匹配评分
        
        Args:
            resume_id: 简历ID
            job_description: 岗位需求描述
            
        Returns:
            匹配评分结果
        """
        # 检查缓存
        cache_key = f"match:{resume_id}:{hash(job_description) % 10000000}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 获取简历文本
        resume_text = await self.resume_service.get_resume_text(resume_id)

        # 解析简历信息（用于返回）
        parse_result = await self.resume_service.parse_resume(resume_id)
        resume_info = parse_result.get("data", {})

        # AI 匹配评分
        match_result = await self.ai_client.match_resume(resume_text, job_description)

        # 构建响应
        result = {
            "success": True,
            "message": "匹配完成",
            "resume_info": resume_info,
            "match_score": match_result,
        }

        # 缓存匹配结果
        cache.set(cache_key, result, ttl=86400)
        return result


# 全局服务实例
_matching_service: Optional[MatchingService] = None


def get_matching_service() -> MatchingService:
    """获取匹配服务实例"""
    global _matching_service
    if _matching_service is None:
        _matching_service = MatchingService()
    return _matching_service
