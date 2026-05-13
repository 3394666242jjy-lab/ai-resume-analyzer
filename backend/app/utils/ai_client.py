"""
AI 模型客户端模块
使用通义千问 (Qwen) API 进行简历信息提取和岗位匹配分析。
直接基于 httpx 发送 HTTP 请求，不依赖 openai SDK，避免平台兼容性问题。
"""
import json
import os
import re
from typing import Optional, Dict, Any

import httpx

from app.core.config import settings


class QwenAIClient:
    """通义千问 (Qwen) AI API 客户端（基于 httpx）"""

    def __init__(self):
        self.api_key = settings.ai_api_key
        self.base_url = settings.ai_base_url.rstrip("/")
        self.model = settings.ai_model
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60.0,
        )

    def _clean_json_response(self, content: str) -> str:
        """清洗模型返回的内容，提取其中的 JSON 部分，兼容 markdown 代码块。"""
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
            content = re.sub(r"\s*```$", "", content)
        return content.strip()

    async def _chat_completion(self, messages: list, temperature: float = 0.1, max_tokens: int = 4096) -> str:
        """调用千问 Chat Completion API，返回模型生成的文本内容。"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"千问 API 请求失败 ({exc.response.status_code}): {exc.response.text[:500]}") from exc
        except Exception as exc:
            raise RuntimeError(f"千问 API 调用失败: {exc}") from exc

    async def extract_resume_info(self, text: str) -> Dict[str, Any]:
        """
        使用 Qwen AI 从简历文本中提取结构化信息。

        Args:
            text: 清洗后的简历全文。

        Returns:
            结构化的简历信息字典。
        """
        if not self.api_key:
            env_status = {
                "ApiKey": bool(os.getenv("ApiKey")),
                "BASE_URL": bool(os.getenv("BASE_URL")),
                "AI_MODEL": bool(os.getenv("AI_MODEL")),
                "QWEN_API_KEY": bool(os.getenv("QWEN_API_KEY")),
                "QwenApiKey": bool(os.getenv("QwenApiKey")),
                "DASHSCOPE_API_KEY": bool(os.getenv("DASHSCOPE_API_KEY")),
                ".env_exists": os.path.exists("/code/.env"),
            }
            raise RuntimeError(
                f"AI 客户端未初始化。环境变量检测: {env_status}。"
                f"当前生效 Key 前8位: {self.api_key[:8] if self.api_key else '空'}...。"
                "请确保 .env 文件中已配置 QWEN_API_KEY。"
            )

        max_chars = 15000
        truncated_text = text[:max_chars]
        if len(text) > max_chars:
            truncated_text += "\n...（后文已截断）"

        system_prompt = (
            "你是一名资深的简历解析专家。任务：从非结构化的简历文本中，"
            "精确提取关键字段，并以严格合法的 JSON 返回。\n\n"
            "提取规则：\n"
            "1. 基本信息(basic_info)：姓名、手机号、邮箱、所在城市/地址。\n"
            "2. 求职意向(job_intention)：应聘职位、期望薪资、期望城市。\n"
            "3. 工作年限(work_years)：如'3年经验'提取为'3年'；无法推断则 null。\n"
            "4. 教育背景(education_background)：学校、学历(本科/硕士/博士/专科等)、专业、时间段。\n"
            "5. 工作经历(work_experience)：公司名、职位、在职时间、工作内容描述。\n"
            "6. 项目经历(project_experience)：项目名、担任角色、项目时间、项目描述。\n"
            "7. 技能列表(skills)：提取所有专业技能，返回为字符串数组；不要遗漏，也不要合并成一句话。\n"
            "8. 自我评价(self_evaluation)：如有则提取完整内容，否则 null。\n\n"
            "输出要求：\n"
            "- 必须返回合法、可解析的 JSON，不要包含 markdown 标记或额外解释文字。\n"
            "- 不存在的字段使用 null；数组字段不存在则返回空数组 []。\n"
            "- 技能列表必须拆分为独立项，例如 [\"Python\", \"Spring Boot\", \"MySQL\"]。\n"
            "- 工作/项目经历的 description 保留原文核心信息，可适当精简。"
        )

        user_prompt = (
            f"请从以下简历文本中提取结构化信息：\n\n{truncated_text}\n\n"
            "请严格按照以下 JSON Schema 输出，不要添加任何额外说明：\n"
            "{\n"
            '  "basic_info": {\n'
            '    "name": "姓名或null",\n'
            '    "phone": "手机号或null",\n'
            '    "email": "邮箱或null",\n'
            '    "address": "地址或null"\n'
            "  },\n"
            '  "job_intention": {\n'
            '    "position": "应聘职位或null",\n'
            '    "expected_salary": "期望薪资或null",\n'
            '    "expected_city": "期望城市或null"\n'
            "  },\n"
            '  "work_years": "工作年限或null",\n'
            '  "education_background": [\n'
            "    {\n"
            '      "school": "学校名",\n'
            '      "degree": "学历",\n'
            '      "major": "专业",\n'
            '      "duration": "时间段"\n'
            "    }\n"
            "  ],\n"
            '  "work_experience": [\n'
            "    {\n"
            '      "company": "公司名",\n'
            '      "position": "职位",\n'
            '      "duration": "时间段",\n'
            '      "description": "工作内容"\n'
            "    }\n"
            "  ],\n"
            '  "project_experience": [\n'
            "    {\n"
            '      "name": "项目名",\n'
            '      "role": "角色",\n'
            '      "duration": "时间段",\n'
            '      "description": "项目描述"\n'
            "    }\n"
            "  ],\n"
            '  "skills": ["技能1", "技能2"],\n'
            '  "self_evaluation": "自我评价或null"\n'
            "}"
        )

        try:
            content = await self._chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=4096,
            )
            cleaned = self._clean_json_response(content)
            result = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"AI 返回内容 JSON 解析失败: {exc}。原始内容前 500 字: {content[:500]}"
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"AI 提取简历信息失败: {exc}") from exc

        result.setdefault("basic_info", {})
        result.setdefault("job_intention", {})
        result.setdefault("work_years", None)
        result.setdefault("education_background", [])
        result.setdefault("work_experience", [])
        result.setdefault("project_experience", [])
        result.setdefault("skills", [])
        result.setdefault("self_evaluation", None)
        return result

    async def match_resume(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """
        使用 Qwen AI 对简历与岗位描述进行深度语义匹配分析。

        Args:
            resume_text: 简历全文。
            job_description: 岗位描述（JD）。

        Returns:
            结构化的匹配评分结果。
        """
        if not self.api_key:
            env_status = {
                "ApiKey": bool(os.getenv("ApiKey")),
                "BASE_URL": bool(os.getenv("BASE_URL")),
                "AI_MODEL": bool(os.getenv("AI_MODEL")),
                "QWEN_API_KEY": bool(os.getenv("QWEN_API_KEY")),
                "QwenApiKey": bool(os.getenv("QwenApiKey")),
                "DASHSCOPE_API_KEY": bool(os.getenv("DASHSCOPE_API_KEY")),
                ".env_exists": os.path.exists("/code/.env"),
            }
            raise RuntimeError(
                f"AI 客户端未初始化。环境变量检测: {env_status}。"
                f"当前生效 Key 前8位: {self.api_key[:8] if self.api_key else '空'}...。"
                "请确保 .env 文件中已配置 QWEN_API_KEY。"
            )

        system_prompt = (
            "你是一名资深的技术招聘专家与 HR 总监。任务：对比候选人简历与招聘岗位要求，"
            "给出专业、客观的匹配评估，并以严格合法的 JSON 返回。\n\n"
            "评估维度：\n"
            "1. overall_score (综合匹配度, 0-100)：基于简历与 JD 的整体契合度打分。\n"
            "2. skill_match_rate (技能匹配度, 0-100)：技能栈的重合度与深度。\n"
            "3. experience_match_rate (经验匹配度, 0-100)：工作年限、行业背景、项目经验匹配度。\n"
            "4. education_match_rate (学历匹配度, 0-100)：学历层次与专业相关度。\n\n"
            "输出要求：\n"
            "- matched_keywords：简历中与岗位要求匹配的关键技能/优势（最多 10 个）。\n"
            "- missing_keywords：岗位要求但简历中明显缺失的关键点（最多 10 个）。\n"
            "- analysis：用 2-4 句话给出综合匹配分析，包括优势和潜在不足。\n"
            "- 必须返回合法 JSON，不要包含 markdown 标记或额外解释文字。"
        )

        user_prompt = (
            f"请对以下简历和岗位进行匹配分析：\n\n"
            f"【岗位描述】\n{job_description[:4000]}\n\n"
            f"【简历内容】\n{resume_text[:6000]}\n\n"
            "请严格按照以下 JSON 格式输出，不要添加任何额外说明：\n"
            "{\n"
            '  "overall_score": 85,\n'
            '  "skill_match_rate": 80,\n'
            '  "experience_match_rate": 90,\n'
            '  "education_match_rate": 85,\n'
            '  "matched_keywords": ["匹配关键词1", "匹配关键词2"],\n'
            '  "missing_keywords": ["缺失关键词1", "缺失关键词2"],\n'
            '  "analysis": "综合匹配分析文本"\n'
            "}"
        )

        try:
            content = await self._chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=2048,
            )
            cleaned = self._clean_json_response(content)
            result = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"AI 返回内容 JSON 解析失败: {exc}。原始内容前 500 字: {content[:500]}"
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"AI 匹配分析失败: {exc}") from exc

        for key in [
            "overall_score",
            "skill_match_rate",
            "experience_match_rate",
            "education_match_rate",
        ]:
            if key in result:
                try:
                    val = float(result[key])
                    result[key] = max(0.0, min(100.0, round(val, 1)))
                except (ValueError, TypeError):
                    result[key] = 0.0
            else:
                result[key] = 0.0

        result.setdefault("matched_keywords", [])
        result.setdefault("missing_keywords", [])
        result.setdefault("analysis", "暂无分析")
        return result


# 全局 AI 客户端单例
_ai_client: Optional[QwenAIClient] = None


def get_ai_client() -> QwenAIClient:
    """获取 AI 客户端实例"""
    global _ai_client
    if _ai_client is None:
        _ai_client = QwenAIClient()
    return _ai_client
