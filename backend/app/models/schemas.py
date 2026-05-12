"""
Pydantic 数据模型定义
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from enum import Enum


class BasicInfo(BaseModel):
    """基本信息"""
    name: Optional[str] = Field(None, description="姓名")
    phone: Optional[str] = Field(None, description="电话")
    email: Optional[str] = Field(None, description="邮箱")
    address: Optional[str] = Field(None, description="地址")


class JobIntention(BaseModel):
    """求职意向"""
    position: Optional[str] = Field(None, description="求职岗位")
    expected_salary: Optional[str] = Field(None, description="期望薪资")
    expected_city: Optional[str] = Field(None, description="期望城市")


class Education(BaseModel):
    """教育背景"""
    school: Optional[str] = Field(None, description="学校")
    degree: Optional[str] = Field(None, description="学历")
    major: Optional[str] = Field(None, description="专业")
    duration: Optional[str] = Field(None, description="就读时间")


class WorkExperience(BaseModel):
    """工作经历"""
    company: Optional[str] = Field(None, description="公司")
    position: Optional[str] = Field(None, description="职位")
    duration: Optional[str] = Field(None, description="工作时间")
    description: Optional[str] = Field(None, description="工作内容")


class ProjectExperience(BaseModel):
    """项目经历"""
    name: Optional[str] = Field(None, description="项目名称")
    role: Optional[str] = Field(None, description="项目角色")
    duration: Optional[str] = Field(None, description="项目时间")
    description: Optional[str] = Field(None, description="项目描述")


class ResumeInfo(BaseModel):
    """简历提取信息"""
    basic_info: BasicInfo = Field(default_factory=BasicInfo, description="基本信息")
    job_intention: JobIntention = Field(default_factory=JobIntention, description="求职意向")
    work_years: Optional[str] = Field(None, description="工作年限")
    education_background: List[Education] = Field(default_factory=list, description="教育背景")
    work_experience: List[WorkExperience] = Field(default_factory=list, description="工作经历")
    project_experience: List[ProjectExperience] = Field(default_factory=list, description="项目经历")
    skills: List[str] = Field(default_factory=list, description="技能列表")
    self_evaluation: Optional[str] = Field(None, description="自我评价")


class MatchScore(BaseModel):
    """匹配度评分"""
    overall_score: float = Field(0.0, ge=0, le=100, description="综合评分")
    skill_match_rate: float = Field(0.0, ge=0, le=100, description="技能匹配率")
    experience_match_rate: float = Field(0.0, ge=0, le=100, description="经验匹配率")
    education_match_rate: float = Field(0.0, ge=0, le=100, description="学历匹配率")
    matched_keywords: List[str] = Field(default_factory=list, description="匹配关键词")
    missing_keywords: List[str] = Field(default_factory=list, description="缺失关键词")
    analysis: Optional[str] = Field(None, description="匹配分析")


class ResumeParseResponse(BaseModel):
    """简历解析响应"""
    success: bool = Field(True, description="是否成功")
    message: str = Field("success", description="状态信息")
    data: Optional[ResumeInfo] = Field(None, description="解析结果")
    raw_text: Optional[str] = Field(None, description="原始文本")


class ResumeMatchRequest(BaseModel):
    """简历匹配请求"""
    resume_id: str = Field(..., description="简历ID")
    job_description: str = Field(..., description="岗位需求描述")


class ResumeMatchResponse(BaseModel):
    """简历匹配响应"""
    success: bool = Field(True, description="是否成功")
    message: str = Field("success", description="状态信息")
    resume_info: Optional[ResumeInfo] = Field(None, description="简历信息")
    match_score: Optional[MatchScore] = Field(None, description="匹配评分")


class UploadResponse(BaseModel):
    """文件上传响应"""
    success: bool = Field(True, description="是否成功")
    message: str = Field("success", description="状态信息")
    resume_id: Optional[str] = Field(None, description="简历ID")
    filename: Optional[str] = Field(None, description="文件名")


class APIResponse(BaseModel):
    """通用 API 响应"""
    success: bool = Field(True, description="是否成功")
    message: str = Field("success", description="状态信息")
    data: Optional[Any] = Field(None, description="响应数据")
