"""
PDF resume parser.
"""
import re
from typing import Optional

from PyPDF2 import PdfReader


class ResumeParser:
    """Parse resume PDFs and extract high-confidence contact fields."""

    EMAIL_PATTERN = re.compile(
        r"(?<![A-Z0-9._%+\-])"
        r"[A-Z0-9._%+\-]+(?:\s*)@(?:\s*)"
        r"[A-Z0-9\-]+(?:\s*\.\s*[A-Z0-9\-]+)*"
        r"(?:\s*)\.(?:\s*)[A-Z]{2,}"
        r"(?![A-Z0-9._%+\-])",
        re.IGNORECASE,
    )
    PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?86[-\s]?)?1[3-9]\d{9}(?!\d)")

    def parse_pdf(self, file_path: str) -> str:
        text_parts = []
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        except Exception as e:
            raise ValueError(f"PDF parse failed: {str(e)}")

        if not text_parts:
            raise ValueError("No text could be extracted from the PDF")

        raw_text = "\n".join(text_parts)
        return self._clean_text(raw_text)

    def extract_email(self, text: str) -> Optional[str]:
        """Extract a likely email address, even if PDF text inserts spaces."""
        if not text:
            return None

        normalized = self._normalize_contact_text(text)
        match = self.EMAIL_PATTERN.search(normalized)
        if not match:
            return None

        email = re.sub(r"\s+", "", match.group(0)).strip(".,;:")
        domain = email.rsplit("@", 1)[-1] if "@" in email else ""
        return email.lower() if "." in domain else None

    def extract_phone(self, text: str) -> Optional[str]:
        """Extract a mainland China mobile number from free text."""
        if not text:
            return None

        normalized = self._normalize_contact_text(text)
        match = self.PHONE_PATTERN.search(normalized)
        if not match:
            compact = re.sub(r"[\s\-()\uff08\uff09]", "", normalized)
            match = self.PHONE_PATTERN.search(compact)
        if not match:
            return None

        phone = re.sub(r"\D", "", match.group(0))
        if phone.startswith("86") and len(phone) == 13:
            phone = phone[2:]
        return phone if len(phone) == 11 else None

    def _normalize_contact_text(self, text: str) -> str:
        replacements = {
            "\uff20": "@",
            "\ufe6b": "@",
            "\u3002": ".",
            "\uff0e": ".",
            "\ufe52": ".",
            "\uff0d": "-",
            "\u2010": "-",
            "\u2011": "-",
            "\u2012": "-",
            "\u2013": "-",
            "\u2014": "-",
            "\u2212": "-",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def _clean_text(self, text: str) -> str:
        text = self._normalize_contact_text(text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f]", "", text)
        return text.strip()

    def extract_sections(self, text: str) -> dict:
        lines = text.split("\n")
        sections = {
            "header": [],
            "education": [],
            "experience": [],
            "projects": [],
            "skills": [],
            "others": [],
        }
        current_section = "header"
        section_keywords = {
            "education": [
                "education", "school", "degree",
                "\u6559\u80b2", "\u5b66\u5386", "\u5b66\u6821", "\u5b66\u4f4d",
                "\u672c\u79d1", "\u7855\u58eb", "\u535a\u58eb", "\u6bd5\u4e1a",
            ],
            "experience": [
                "experience", "work", "internship",
                "\u5de5\u4f5c", "\u5b9e\u4e60", "\u7ecf\u9a8c", "\u7ecf\u5386",
                "\u4efb\u804c", "\u5c31\u804c", "\u804c\u4e1a",
            ],
            "projects": ["project", "\u9879\u76ee", "\u8bfe\u9898", "\u7814\u53d1"],
            "skills": [
                "skills", "technical",
                "\u6280\u80fd", "\u6280\u672f", "\u80fd\u529b", "\u719f\u6089",
                "\u638c\u63e1", "\u7cbe\u901a", "\u4e86\u89e3",
            ],
        }

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            lowered = line_stripped.lower()
            for section, keywords in section_keywords.items():
                if any(kw in lowered for kw in keywords) and len(line_stripped) < 40:
                    current_section = section
                    break

            sections[current_section].append(line_stripped)

        return sections


resume_parser = ResumeParser()
