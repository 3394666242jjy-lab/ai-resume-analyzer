"""
简历相关 API 路由
"""
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
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
    file: UploadFile = File(...),
    job_description: str = Form(...),
):
    """
    上传简历并立即进行匹配评分（一步到位）
    
    - **file**: PDF 简历文件
    - **job_description**: 岗位需求描述
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持 PDF 格式文件")

    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE // 1024 // 1024}MB)")

    if not job_description or len(job_description.strip()) < 10:
        raise HTTPException(status_code=400, detail="岗位描述过短，请提供详细描述")

    try:
        resume_service = get_resume_service()
        matching_service = get_matching_service()

        # 上传
        upload_result = await resume_service.upload_resume(contents, file.filename)
        resume_id = upload_result["resume_id"]

        # 匹配
        result = await matching_service.match_resume_with_job(
            resume_id,
            job_description.strip()
        )
        return ResumeMatchResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "ai_enabled": settings.ai_enabled}
