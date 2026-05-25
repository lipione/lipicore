from dataclasses import dataclass
from typing import Any

from PIL import Image

from ..core.config import settings


@dataclass(frozen=True)
class OcrResult:
    text: str
    confidence: float | None = None


def _confidence_from_data(data: dict[str, list[Any]]) -> float | None:
    values: list[float] = []
    for raw in data.get("conf", []):
        try:
            score = float(raw)
        except (TypeError, ValueError):
            continue
        if score >= 0:
            values.append(score / 100)
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _prepare_image(image: Image.Image) -> Image.Image:
    if image.mode not in {"RGB", "L"}:
        return image.convert("RGB")
    return image


def _run_tesseract(image: Image.Image, language: str) -> OcrResult:
    try:
        import pytesseract
        from pytesseract import Output
    except ImportError as exc:
        raise RuntimeError("pytesseract is not installed") from exc

    try:
        text = pytesseract.image_to_string(
            image,
            lang=language,
            config=settings.OCR_TESSERACT_CONFIG,
        ).strip()
        data = pytesseract.image_to_data(
            image,
            lang=language,
            config=settings.OCR_TESSERACT_CONFIG,
            output_type=Output.DICT,
        )
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError("Tesseract OCR binary is not installed or not on PATH") from exc
    except pytesseract.TesseractError as exc:
        raise RuntimeError(str(exc)) from exc

    return OcrResult(text=text, confidence=_confidence_from_data(data))


def ocr_pil_image_to_text(image: Image.Image) -> OcrResult:
    if settings.OCR_ENGINE.lower() != "tesseract":
        raise RuntimeError(f"Unsupported OCR_ENGINE: {settings.OCR_ENGINE}")

    prepared = _prepare_image(image)
    language = settings.OCR_LANGUAGES.strip() or "eng"
    try:
        return _run_tesseract(prepared, language)
    except RuntimeError:
        if language != "eng":
            return _run_tesseract(prepared, "eng")
        raise


def ocr_image_file(file_path: str) -> OcrResult:
    with Image.open(file_path) as image:
        return ocr_pil_image_to_text(image)


def convert_pdf_pages_to_images(file_path: str, *, first_page: int, last_page: int) -> list[Image.Image]:
    try:
        from pdf2image import convert_from_path
    except ImportError as exc:
        raise RuntimeError("pdf2image is not installed") from exc

    return convert_from_path(
        file_path,
        dpi=settings.OCR_IMAGE_DPI,
        first_page=first_page,
        last_page=last_page,
    )
