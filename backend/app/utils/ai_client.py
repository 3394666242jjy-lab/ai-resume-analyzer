"""
AI 模型客户端模块
支持 OpenAI API 调用，同时提供本地规则引擎作为降级方案
"""
import json
import re
from typing import Optional, Dict, Any

from app.core.config import settings


class RuleBasedExtractor:
    """基于规则的简历信息提取器（AI 不可用时的降级方案）"""

    def extract(self, text: str) -> Dict[str, Any]:
        """从文本中提取关键信息"""
        result = {
            "basic_info": {
                "name": self._extract_name(text),
                "phone": self._extract_phone(text),
                "email": self._extract_email(text),
                "address": self._extract_address(text),
            },
            "job_intention": {
                "position": self._extract_job_position(text),
                "expected_salary": self._extract_salary(text),
                "expected_city": self._extract_city(text),
            },
            "work_years": self._extract_work_years(text),
            "education_background": self._extract_education(text),
            "work_experience": self._extract_work_experience(text),
            "project_experience": self._extract_projects(text),
            "skills": self._extract_skills(text),
            "self_evaluation": None,
        }
        return result

    def _extract_name(self, text: str) -> Optional[str]:
        lines = text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            if 2 <= len(line) <= 6 and not any(c in line for c in '0123456789@'):
                return line
        return None

    def _extract_phone(self, text: str) -> Optional[str]:
        pattern = r'1[3-9]\d{9}'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _extract_email(self, text: str) -> Optional[str]:
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _extract_address(self, text: str) -> Optional[str]:
        pattern = r'(现居|居住地|地址)[:：\s]*([^\n]{2,30})'
        match = re.search(pattern, text)
        return match.group(2).strip() if match else None

    def _extract_job_position(self, text: str) -> Optional[str]:
        pattern = r'(求职意向|期望职位|应聘岗位)[:：\s]*([^\n]{1,20})'
        match = re.search(pattern, text)
        return match.group(2).strip() if match else None

    def _extract_salary(self, text: str) -> Optional[str]:
        pattern = r'(期望薪资|薪资要求|薪水)[:：\s]*([^\n]{1,30})'
        match = re.search(pattern, text)
        return match.group(2).strip() if match else None

    def _extract_city(self, text: str) -> Optional[str]:
        pattern = r'(期望城市|意向城市|工作地点)[:：\s]*([^\n]{1,20})'
        match = re.search(pattern, text)
        return match.group(2).strip() if match else None

    def _extract_work_years(self, text: str) -> Optional[str]:
        pattern = r'(\d+)[\s]*年[\s]*(工作|相关|开发|经验)'
        match = re.search(pattern, text)
        if match:
            return f"{match.group(1)}年"
        pattern2 = r'(工作经验|工作年限)[:：\s]*(\d+)[\s]*年'
        match2 = re.search(pattern2, text)
        if match2:
            return f"{match2.group(2)}年"
        return None

    def _extract_education(self, text: str) -> list:
        educations = []
        pattern = r'(本科|硕士|博士|专科|大专|研究生|MBA)(.*?)(\d{4}[\./年]\d{1,2}|至今)'
        matches = re.findall(pattern, text)
        for match in matches[:3]:
            educations.append({
                "school": None,
                "degree": match[0],
                "major": match[1].strip(' |，,、') if match[1] else None,
                "duration": match[2] if len(match) > 2 else None,
            })
        return educations

    def _extract_work_experience(self, text: str) -> list:
        experiences = []
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(kw in line for kw in ['有限公司', '科技公司', '互联网公司', '集团']):
                company = line.strip()
                position = lines[i + 1].strip() if i + 1 < len(lines) else None
                if position and len(position) < 30:
                    experiences.append({
                        "company": company,
                        "position": position,
                        "duration": None,
                        "description": None,
                    })
        return experiences[:5]

    def _extract_projects(self, text: str) -> list:
        projects = []
        lines = text.split('\n')
        in_project = False
        current_project = {}
        for i, line in enumerate(lines):
            if '项目' in line and len(line) < 30 and not in_project:
                in_project = True
                current_project = {"name": line.strip(), "role": None, "duration": None, "description": None}
            elif in_project and current_project.get("description") is None:
                if len(line) > 20:
                    current_project["description"] = line.strip()
                    projects.append(current_project)
                    in_project = False
            if len(projects) >= 5:
                break
        return projects

    def _extract_skills(self, text: str) -> list:
        tech_keywords = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'C++', 'C#', 'PHP', 'Ruby',
            'React', 'Vue', 'Angular', 'Node.js', 'Django', 'Flask', 'Spring', 'SpringBoot',
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch', 'Kafka', 'RabbitMQ',
            'Docker', 'Kubernetes', 'AWS', '阿里云', 'Linux', 'Git', 'CI/CD',
            'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn', 'OpenAI',
            'HTML', 'CSS', 'jQuery', 'Bootstrap', 'Tailwind',
            'RESTful', 'GraphQL', 'gRPC', 'Microservices',
            'Nginx', 'Tomcat', 'Apache',
            'Hadoop', 'Spark', 'Flink', 'Hive',
        ]
        found_skills = []
        for skill in tech_keywords:
            if skill in text:
                found_skills.append(skill)
        return found_skills


class OpenAIClient:
    """OpenAI API 客户端"""

    def __init__(self):
        self.client = None
        self.model = settings.OPENAI_MODEL
        self.rule_extractor = RuleBasedExtractor()
        if settings.ai_enabled:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL,
                )
            except ImportError:
                pass

    async def extract_resume_info(self, text: str) -> Dict[str, Any]:
        """使用 AI 模型提取简历信息"""
        if self.client is None:
            return self.rule_extractor.extract(text)

        prompt = f"""
请从以下简历文本中提取关键信息，并以 JSON 格式返回。
注意：
1. 如果某项信息无法提取，使用 null
2. 工作年限请提取为 "X年" 的格式
3. 教育背景、工作经历、项目经历请提取为数组
4. 技能请提取为字符串数组

简历文本：
{text[:6000]}

请严格按照以下 JSON 格式返回：
{{
    "basic_info": {{
        "name": "姓名",
        "phone": "电话",
        "email": "邮箱",
        "address": "地址"
    }},
    "job_intention": {{
        "position": "求职岗位",
        "expected_salary": "期望薪资",
        "expected_city": "期望城市"
    }},
    "work_years": "工作年限",
    "education_background": [
        {{
            "school": "学校",
            "degree": "学历",
            "major": "专业",
            "duration": "就读时间"
        }}
    ],
    "work_experience": [
        {{
            "company": "公司",
            "position": "职位",
            "duration": "工作时间",
            "description": "工作内容"
        }}
    ],
    "project_experience": [
        {{
            "name": "项目名",
            "role": "角色",
            "duration": "项目时间",
            "description": "项目描述"
        }}
    ],
    "skills": ["技能1", "技能2"],
    "self_evaluation": "自我评价"
}}
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的简历信息提取助手，擅长从非结构化文本中提取结构化信息。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            result.setdefault("basic_info", {})
            result.setdefault("job_intention", {})
            result.setdefault("education_background", [])
            result.setdefault("work_experience", [])
            result.setdefault("project_experience", [])
            result.setdefault("skills", [])
            return result
        except Exception:
            return self.rule_extractor.extract(text)

    async def match_resume(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """使用 AI 模型对简历和岗位进行匹配评分"""
        if self.client is None:
            return self._rule_based_match(resume_text, job_description)

        prompt = f"""
请对以下简历和岗位需求进行匹配分析，并以 JSON 格式返回评分结果。

岗位需求：
{job_description[:3000]}

简历内容：
{resume_text[:4000]}

请严格按照以下 JSON 格式返回：
{{
    "overall_score": 85,
    "skill_match_rate": 80,
    "experience_match_rate": 90,
    "education_match_rate": 85,
    "matched_keywords": ["匹配的关键词1", "匹配的关键词2"],
    "missing_keywords": ["缺失的关键词1", "缺失的关键词2"],
    "analysis": "详细的匹配分析说明"
}}

评分标准：
- overall_score: 综合评分 (0-100)
- skill_match_rate: 技能匹配率 (0-100)
- experience_match_rate: 经验匹配率 (0-100)
- education_match_rate: 学历匹配率 (0-100)
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的招聘顾问，擅长分析简历与岗位的匹配度。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            for key in ["overall_score", "skill_match_rate", "experience_match_rate", "education_match_rate"]:
                if key in result:
                    result[key] = max(0, min(100, float(result[key])))
            result.setdefault("matched_keywords", [])
            result.setdefault("missing_keywords", [])
            result.setdefault("analysis", "")
            return result
        except Exception:
            return self._rule_based_match(resume_text, job_description)

    def _rule_based_match(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """基于规则的匹配评分（无需 jieba）"""
        resume_lower = resume_text.lower()
        job_lower = job_description.lower()

        # 常见技术关键词
        tech_keywords = [
            'python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++', 'c#', 'php',
            'react', 'vue', 'angular', 'nodejs', 'node.js', 'django', 'flask', 'spring',
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'kafka',
            'docker', 'kubernetes', 'aws', 'linux', 'git',
            'tensorflow', 'pytorch', '机器学习', '深度学习', 'ai',
            'html', 'css', 'jquery', 'bootstrap',
            'restful', 'graphql', 'grpc', 'microservices',
            'nginx', 'tomcat', 'apache',
        ]

        job_tech = [w for w in tech_keywords if w in job_lower]
        resume_tech = [w for w in tech_keywords if w in resume_lower]

        matched = [w for w in job_tech if w in resume_tech]
        missing = [w for w in job_tech if w not in resume_tech]

        if job_tech:
            skill_rate = len(matched) / len(job_tech) * 100
        else:
            # 非技术岗位，计算通用匹配度
            job_words = set(job_lower.split())
            resume_words = set(resume_lower.split())
            common_words = job_words & resume_words
            stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', 'the', 'a', 'an', 'is', 'are', 'was', 'were', 'and', 'or', 'of', 'to', 'in', 'for', 'with', 'on', 'at'}
            common_words -= stop_words
            job_words -= stop_words
            skill_rate = len(common_words) / max(len(job_words), 1) * 100
            matched = list(common_words)[:10]
            missing = list(job_words - resume_words)[:10]

        # 经验匹配
        years_match = re.search(r'(\d+)[\s]*年[\s]*(?:工作|经验|相关)', resume_text)
        req_years_match = re.search(r'(\d+)[\s]*年[\s]*(?:工作|经验|相关)', job_description)
        exp_rate = 70
        if years_match and req_years_match:
            y = int(years_match.group(1))
            ry = int(req_years_match.group(1))
            if y >= ry:
                exp_rate = 95
            else:
                exp_rate = 50 + (y / ry) * 45

        overall = (skill_rate * 0.5 + exp_rate * 0.3 + 70 * 0.2)

        return {
            "overall_score": round(overall, 1),
            "skill_match_rate": round(skill_rate, 1),
            "experience_match_rate": round(exp_rate, 1),
            "education_match_rate": 70.0,
            "matched_keywords": matched[:15],
            "missing_keywords": missing[:15],
            "analysis": f"技能匹配率 {round(skill_rate, 1)}%，经验匹配率 {round(exp_rate, 1)}%。{'高度匹配' if overall >= 80 else '基本匹配' if overall >= 60 else '匹配度较低'}",
        }


# 全局 AI 客户端
_ai_client: Optional[OpenAIClient] = None


def get_ai_client() -> OpenAIClient:
    """获取 AI 客户端实例"""
    global _ai_client
    if _ai_client is None:
        _ai_client = OpenAIClient()
    return _ai_client
