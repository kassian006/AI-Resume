from __future__ import annotations
from typing import Dict, Any
import io
from PIL import Image
import pytesseract
import cv2
import numpy as np


class OCRParser:
    """Простой OCR для сканов резюме"""

    def __init__(self, lang: str = "eng+rus") -> None:
        # Tesseract должен быть установлен в системе
        self.lang = lang

    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """Предобработка изображения для лучшего распознавания"""
        # Конвертируем в numpy
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Grayscale + threshold (улучшает качество OCR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return thresh

    def extract_text(self, image_bytes: bytes) -> str:
        """Извлекает текст из изображения"""
        try:
            # Предобработка
            processed = self.preprocess_image(image_bytes)

            # Распознавание
            text = pytesseract.image_to_string(processed, lang=self.lang)
            return text.strip()

        except Exception as e:
            print(f"OCR Error: {e}")
            # Fallback: попробуем без предобработки
            img = Image.open(io.BytesIO(image_bytes))
            return pytesseract.image_to_string(img, lang=self.lang).strip()

    def is_scanned_resume(self, file_bytes: bytes, filename: str) -> bool:
        """Определяет, является ли файл сканом (изображением)"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
        return any(filename.lower().endswith(ext) for ext in image_extensions)