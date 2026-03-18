from __future__ import annotations
import os
import json
import hashlib
from typing import Dict, Any, Optional, List
import google.generativeai as genai
import redis
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridAIRouter:
    def __init__(self, gemini_api_key: Optional[str] = None) -> None:
        # Настраиваем Gemini
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

        # Кэш (опционально)
        try:
            self.cache = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        except Exception:
            self.cache = None

    def _get_cache_key(self, task: str, content: str, company: str) -> str:
        raw = f"{task}:{content[:100]}:{company}"
        return f"resume:{hashlib.md5(raw.encode()).hexdigest()}"

    def analyze_resume(self, resume_text: str, company: str = "Google") -> Dict[str, Any]:
        cache_key = self._get_cache_key("analyze", resume_text, company)

        # Проверяем кэш
        if self.cache and self.cache.exists(cache_key):
            return json.loads(self.cache.get(cache_key))

        company_contexts: Dict[str, str] = {
            "Google": "Focus on impact, metrics, scale. Use X-Y-Z formula: 'Accomplished [X] as measured by [Y], by doing [Z]'.",
            "Amazon": "Evaluate against Leadership Principles: Customer Obsession, Ownership, Bias for Action. Look for STAR examples.",
            "Meta": "Focus on impact, speed, moving fast. Look for metrics and iteration.",
            "Tesla": "Value practicality, first-principles thinking, solving hard problems. No fluff."
        }

        context = company_contexts.get(company, company_contexts["Google"])

        if self.model:
            result = self._gemini_analysis(resume_text, context, company)
        else:
            result = self._mock_analysis(resume_text, company)

        # Кэшируем
        if self.cache:
            self.cache.setex(cache_key, 3600, json.dumps(result, ensure_ascii=False))

        return result

    def _gemini_analysis(self, text: str, context: str, company: str) -> Dict[str, Any]:
        """Анализ через Google Gemini"""

        prompt = f"""Ты — старший рекрутер в {company}. Проанализируй это резюме:

{text[:2000]}

Дай обратную связь в формате ТОЛЬКО JSON (без markdown, без пояснений):
{{
  "ats_score": 75,
  "strengths": ["...", "..."],
  "improvements": [
    {{"issue": "...", "suggestion": "...", "example": "..."}}
  ],
  "company_specific_advice": "..."
}}

Контекст для {company}: {context}

Отвечай ТОЛЬКО валидным JSON."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    response_mime_type="application/json"  # ✅ Gemini 1.5 поддерживает JSON output!
                )
            )

            # Парсим ответ
            result = json.loads(response.text)
            return result

        except Exception as e:
            print(f"Gemini API Error: {e}")
            return self._mock_analysis(text, company)

    def _mock_analysis(self, text: str, company: str) -> Dict[str, Any]:
        """Mock-ответ для демо без API"""
        return {
            "ats_score": 72,
            "strengths": ["Good technical skills", "Clear structure"],
            "improvements": [
                {
                    "issue": "Missing metrics",
                    "suggestion": "Add numbers to show impact",
                    "example": "Instead of 'improved performance', write 'improved API response time by 40%'"
                }
            ],
            "company_specific_advice": f"For {company}: emphasize measurable impact"
        }

    def get_embedding(self, text: str) -> List[float]:
        """Генерирует эмбеддинг через Gemini (упрощённо)"""
        # Для демо: простой хэш-вектор
        import hashlib
        hash_bytes = hashlib.md5(text.encode()).digest()
        vector = []
        for i in range(384):
            byte_idx = i % len(hash_bytes)
            vector.append((hash_bytes[byte_idx] - 128) / 128.0)
        return vector

    def fix_resume_bullet(self, original: str, company: str = "Google") -> str:
        """Исправляет один пункт резюме"""
        if not self.model:
            return f"✨ Fixed: {original} (demo mode)"

        prompt = f"""Ты — рекрутер {company}. Исправь этот пункт резюме, сделав его сильнее:

    Оригинал: "{original}"

    Правила:
    - Используй активный залог
    - Добавь метрики если возможно
    - Формула: "Сделал X, используя Y, что привело к Z"

    Верни ТОЛЬКО исправленный текст, без пояснений."""

        response = self.model.generate_content(prompt)
        return response.text.strip()