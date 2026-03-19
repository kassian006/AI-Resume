# test_ocr.py
import pytesseract
from PIL import Image

# ✅ Укажи путь к tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 1. Проверка версии
print("✅ Tesseract version:", pytesseract.get_tesseract_version())

# 2. Проверка языков
langs = pytesseract.get_languages(config='')
print(f"✅ Available languages: {len(langs)} total")
print("   eng:", 'eng' in langs)
print("   rus:", 'rus' in langs)
print("   kir:", 'kir' in langs)

# 3. Тест на простом тексте (если есть изображение)
# Создай тестовое изображение или используй своё
try:
    # Для теста создадим простое изображение с текстом
    from PIL import ImageDraw, ImageFont

    img = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Hello World\nПривет Мир\nСалам дүйнө", fill='black')

    text = pytesseract.image_to_string(img, lang='eng+rus+kir')
    print("\n✅ OCR Test Result:")
    print(text)
except Exception as e:
    print(f"\n⚠️  Test error (это нормально): {e}")

print("\n🎉 Tesseract готов к работе!")


def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
    """Улучшенная предобработка для кириллицы"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 1. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Увеличение контраста
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 3. Threshold
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 4. Denoising
    denoised = cv2.fastNlMeansDenoising(thresh, h=30)

    # 5. Увеличение размера (для лучшего распознавания)
    scaled = cv2.resize(denoised, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    return scaled