from doc_shape_shifter.pipelines.ocr.engines import get_engine
from doc_shape_shifter.pipelines.ocr.engines.base import OCRPage, OCRWord
from doc_shape_shifter.pipelines.ocr.engines.tesseract import TesseractEngine


def test_get_engine_returns_tesseract():
    assert isinstance(get_engine("tesseract"), TesseractEngine)


def test_get_engine_unknown_raises():
    import pytest

    with pytest.raises(ValueError):
        get_engine("nope")


def test_ocr_dataclasses():
    page = OCRPage(text="hi", words=[OCRWord(text="hi", bbox=(0, 0, 1, 1))])
    assert page.text == "hi"
    assert page.words[0].bbox == (0, 0, 1, 1)


def test_tesseract_availability_requires_binary(monkeypatch):
    import doc_shape_shifter.pipelines.ocr.engines.tesseract as mod

    monkeypatch.setattr(mod.shutil, "which", lambda _: None)
    assert TesseractEngine().is_available() is False


def test_surya_engine_selectable_and_gated():
    from doc_shape_shifter.pipelines.ocr.engines import get_engine
    from doc_shape_shifter.pipelines.ocr.engines.surya import SuryaEngine

    eng = get_engine("surya")
    assert isinstance(eng, SuryaEngine)
    # is_available reflects whether surya is importable; must not raise either way.
    assert isinstance(eng.is_available(), bool)
