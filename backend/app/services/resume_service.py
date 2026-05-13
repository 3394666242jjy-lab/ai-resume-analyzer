"""
简历服务层
"""
import os
import uuid
import time
from typing import Optional, Dict, Any

from app.core.config import settings
from app.core.cache import cache
from app.utils.parser import resume_parser
from app.utils.ai_client import get_ai_client
from app.models.schemas import ResumeInfo, BasicInfo, JobIntention, Education, WorkExperience, ProjectExperience


class ResumeService:
    """简历服务"""

    def __init__(self):
        self.ai_client = get_ai_client()
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    async def upload_resume(self, file_bytes: bytes, filename: str) -> Dict[str, str]:
        """
        上传简历文件
        
        Args:
            file_bytes: 文件字节内容
            filename: 原始文件名
            
        Returns:
            包含 resume_id 和 filename 的字典
        """
        resume_id = f"resume_{uuid.uuid4().hex[:16]}"
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext != '.pdf':
            raise ValueError("仅支持 PDF 格式文件")

        file_path = os.path.join(self.upload_dir, f"{resume_id}{file_ext}")
        with open(file_path, 'wb') as f:
            f.write(file_bytes)

        # 缓存文件路径
        cache.set(f"file:{resume_id}", {"path": file_path, "filename": filename, "upload_time": time.time()})
        return {"resume_id": resume_id, "filename": filename}

    async def parse_resume(self, resume_id: str) -> Dict[str, Any]:
        """
        解析简历
        
        Args:
            resume_id: 简历ID
            
        Returns:
            解析结果
        """
        # 检查缓存
        cache_key = f"parse:{resume_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 获取文件信息
        file_info = cache.get(f"file:{resume_id}")
        if not file_info:
            # 尝试从本地文件查找
            possible_path = os.path.join(self.upload_dir, f"{resume_id}.pdf")
            if not os.path.exists(possible_path):
                raise ValueError(f"未找到简历文件: {resume_id}")
            file_info = {"path": possible_path, "filename": os.path.basename(possible_path)}

        file_path = file_info["path"]

        # 解析 PDF
        raw_text = resume_parser.parse_pdf(file_path)

        # AI 提取信息
        extracted_data = await self.ai_client.extract_resume_info(raw_text)
        self._patch_basic_info_from_text(extracted_data, raw_text)

        # 构建响应
        result = {
            "success": True,
            "message": "解析成功",
            "data": extracted_data,
            "raw_text": raw_text[:2000],  # 只返回前2000字符作为预览
        }

        # 缓存解析结果
        cache.set(cache_key, result, ttl=86400)
        return result

    def _patch_basic_info_from_text(self, data: Dict[str, Any], raw_text: str) -> None:
        """Fill high-confidence fields that are often distorted by PDF extraction."""
        basic_info = data.setdefault("basic_info", {})

        detected_phone = resume_parser.extract_phone(raw_text)
        current_phone = basic_info.get("phone")
        current_detected_phone = resume_parser.extract_phone(str(current_phone)) if current_phone else None
        if detected_phone and current_detected_phone != detected_phone:
            basic_info["phone"] = detected_phone

        detected_email = resume_parser.extract_email(raw_text)
        current_email = basic_info.get("email")
        current_detected = resume_parser.extract_email(str(current_email)) if current_email else None
        if detected_email and current_detected != detected_email:
            basic_info["email"] = detected_email

    async def get_resume_text(self, resume_id: str) -> str:
        """获取简历原始文本"""
        file_info = cache.get(f"file:{resume_id}")
        if not file_info:
            possible_path = os.path.join(self.upload_dir, f"{resume_id}.pdf")
            if os.path.exists(possible_path):
                file_path = possible_path
            else:
                raise ValueError(f"未找到简历文件: {resume_id}")
        else:
            file_path = file_info["path"]

        return resume_parser.parse_pdf(file_path)


# 全局服务实例
_resume_service: Optional[ResumeService] = None


def get_resume_service() -> ResumeService:
    """获取简历服务实例"""
    global _resume_service
    if _resume_service is None:
        _resume_service = ResumeService()
    return _resume_service
