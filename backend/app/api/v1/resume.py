"""
简历相关 API 路由
"""
import base64
import json
import os
import tempfile

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.models.schemas import (
    UploadResponse,
    ResumeParseResponse,
    ResumeMatchRequest,
    ResumeMatchResponse,
    APIResponse,
)
from app.services.resume_service import get_resume_service
from app.services.matching_service import get_matching_service

router = APIRouter(prefix="/resume", tags=["简历分析"])


@router.post("/upload", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    上传 PDF 简历文件
    
    - **file**: PDF 格式简历文件（最大 10MB）
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持 PDF 格式文件")

    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE // 1024 // 1024}MB)")

    try:
        service = get_resume_service()
        result = await service.upload_resume(contents, file.filename)
        return UploadResponse(
            success=True,
            message="上传成功",
            resume_id=result["resume_id"],
            filename=result["filename"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/parse/{resume_id}", response_model=ResumeParseResponse)
async def parse_resume(resume_id: str):
    """
    解析简历，提取关键信息
    
    - **resume_id**: 上传接口返回的简历ID
    """
    try:
        service = get_resume_service()
        result = await service.parse_resume(resume_id)
        return ResumeParseResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")


@router.post("/match", response_model=ResumeMatchResponse)
async def match_resume(request: ResumeMatchRequest):
    """
    简历与岗位需求匹配评分
    
    - **resume_id**: 简历ID
    - **job_description**: 岗位需求描述
    """
    if not request.job_description or len(request.job_description.strip()) < 10:
        raise HTTPException(status_code=400, detail="岗位描述过短，请提供详细描述")

    try:
        service = get_matching_service()
        result = await service.match_resume_with_job(
            request.resume_id,
            request.job_description.strip()
        )
        return ResumeMatchResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")


@router.post("/upload-and-match", response_model=ResumeMatchResponse)
async def upload_and_match(
    request: Request,
    file: UploadFile = File(None),
    job_description: str = Form(None),
):
    """
    上传简历并立即进行匹配评分（一步到位）
    
    支持两种请求格式：
    - **multipart/form-data**: 传统文件上传（file + job_description）
    - **text/plain**: Base64 JSON 上传（避免 CORS OPTIONS 预检）
    
    JSON 格式：{"filename": "xxx.pdf", "content": "base64字符串", "job_description": "..."}
    """
    contents = None
    filename = None
    jd = None

    content_type = request.headers.get("content-type", "").lower()

    if "text/plain" in content_type or "application/json" in content_type:
        # Base64 JSON 模式（用于避免 CORS 预检）
        try:
            body = await request.body()
            data = json.loads(body.decode("utf-8"))
            filename = data.get("filename", "resume.pdf")
            base64_content = data.get("content", "")
            jd = data.get("job_description", "")
            contents = base64.b64decode(base64_content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"JSON/Base64 解析失败: {str(e)}")
    else:
        # multipart/form-data 模式（传统上传）
        if file is None:
            raise HTTPException(status_code=400, detail="缺少文件")
        contents = await file.read()
        filename = file.filename
        jd = job_description or ""

    if not filename or not filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持 PDF 格式文件")

    # Base64 会增加约 33% 大小，放宽限制到 15MB
    max_size = max(settings.MAX_FILE_SIZE, 15 * 1024 * 1024)
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制 ({max_size // 1024 // 1024}MB)")

    if not jd or len(jd.strip()) < 10:
        raise HTTPException(status_code=400, detail="岗位描述过短，请提供详细描述")

    try:
        resume_service = get_resume_service()
        matching_service = get_matching_service()

        # 上传
        upload_result = await resume_service.upload_resume(contents, filename)
        resume_id = upload_result["resume_id"]

        # 匹配
        result = await matching_service.match_resume_with_job(
            resume_id,
            jd.strip()
        )
        return ResumeMatchResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

