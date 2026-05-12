"""
API 接口测试
"""
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_upload_invalid_format():
    """测试上传非 PDF 文件"""
    files = {"file": ("test.txt", b"not a pdf", "text/plain")}
    response = client.post("/api/v1/resume/upload", files=files)
    assert response.status_code == 400
    assert "仅支持 PDF" in response.json()["detail"]


def test_match_without_resume():
    """测试匹配不存在的简历"""
    payload = {
        "resume_id": "non_existent_id",
        "job_description": "需要 Python 开发工程师，3年以上经验"
    }
    response = client.post("/api/v1/resume/match", json=payload)
    assert response.status_code == 404


def test_match_short_description():
    """测试岗位描述过短"""
    payload = {
        "resume_id": "test_id",
        "job_description": "太短"
    }
    response = client.post("/api/v1/resume/match", json=payload)
    assert response.status_code == 400
    assert "岗位描述过短" in response.json()["detail"]
