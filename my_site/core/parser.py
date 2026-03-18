from __future__ import annotations
from pypdf import PdfReader
import spacy
from typing import Dict, List, Any
import io


class ResumeParser:
    def __init__(self) -> None:
        self.nlp = spacy.load("en_core_web_sm")

        self.tech_skills: List[str] = [
            "python", "javascript", "typescript", "java", "cpp", "c++", "c#",
            "react", "vue", "angular", "node", "django", "fastapi", "flask",
            "pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy",
            "sql", "postgresql", "mysql", "mongodb", "redis",
            "docker", "kubernetes", "aws", "gcp", "azure",
            "git", "ci/cd", "linux", "bash"
        ]

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        try:
            pdf_reader = PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error parsing PDF: {str(e)}")

    def extract_skills(self, text: str) -> List[str]:
        text_lower = text.lower()
        found_skills: List[str] = []

        for skill in self.tech_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)

        return list(set(found_skills))

    def extract_experience_years(self, text: str) -> str:
        text_lower = text.lower()

        if any(word in text_lower for word in ["senior", "lead", "principal", "staff"]):
            return "5+"
        elif any(word in text_lower for word in ["junior", "intern", "entry"]):
            return "0-2"
        elif "middle" in text_lower or "mid" in text_lower:
            return "2-5"
        else:
            return "2-5"

    def parse(self, file_bytes: bytes) -> Dict[str, Any]:
        text = self.extract_text_from_pdf(file_bytes)

        return {
            "raw_text": text[:5000],
            "word_count": len(text.split()),
            "skills": self.extract_skills(text),
            "experience_years": self.extract_experience_years(text),
            "has_email": "@" in text,
            "has_phone": any(char.isdigit() for char in text) and len(text) > 50
        }