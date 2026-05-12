"""
PDF 简历解析模块
"""
import os
import re
from typing import Optional
from PyPDF2 import PdfReader


class ResumeParser:
    """简历解析器"""

    def __init__(self):
        pass

    def parse_pdf(self, file_path: str) -> str:
        """
        解析 PDF 文件，提取文本内容
        
        Args:
            file_path: PDF 文件路径
            
        Returns:
            提取的文本内容
        """
        text_parts = []
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        except Exception as e:
            raise ValueError(f"PDF 解析失败: {str(e)}")

        if not text_parts:
            raise ValueError("无法从 PDF 中提取文本内容")

        raw_text = "\n".join(text_parts)
        return self._clean_text(raw_text)

    def _clean_text(self, text: str) -> str:
        """
        清洗和格式化文本
        
        Args:
            text: 原始文本
            
        Returns:
            清洗后的文本
        """
        # 去除多余空白字符
        text = re.sub(r'[ \t]+', ' ', text)
        # 去除多余空行，但保留段落结构
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 去除页眉页脚常见的重复数字
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        # 去除特殊控制字符
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)
        return text.strip()

    def extract_sections(self, text: str) -> dict:
        """
        将简历文本按段落分割
        
        Args:
            text: 清洗后的文本
            
        Returns:
            段落字典
        """
        lines = text.split('\n')
        sections = {
            'header': [],
            'education': [],
            'experience': [],
            'projects': [],
            'skills': [],
            'others': []
        }
        
        current_section = 'header'
        section_keywords = {
            'education': ['教育', '学历', '学校', '学位', '本科', '硕士', '博士', '毕业'],
            'experience': ['工作', '实习', '经验', '经历', '任职', '就职', '职业'],
            'projects': ['项目', '课题', '研发'],
            'skills': ['技能', '技术', '能力', '熟悉', '掌握', '精通', '了解']
        }
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            # 检测段落切换
            for section, keywords in section_keywords.items():
                if any(kw in line_stripped for kw in keywords) and len(line_stripped) < 20:
                    current_section = section
                    break
            
            sections[current_section].append(line_stripped)
        
        return sections


# 全局解析器实例
resume_parser = ResumeParser()
