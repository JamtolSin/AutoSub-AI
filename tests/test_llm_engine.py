from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.core.llm_engine import LLMEngine


def test_correction_preserves_timestamps_and_original(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    engine = LLMEngine(api_key="test-only")
    assert engine.prompt_path.is_file()
    original = [{"start": 1.0, "end": 2.0, "text": "원문", "confidence": -0.5}]
    model = Mock()
    model.generate_content.return_value = SimpleNamespace(
        text='```json\n[{"start":99,"end":100,"text":"교정문"}]\n```'
    )
    assert engine._process_batch(original, model) == [{**original[0], "text": "교정문"}]
    assert original[0]["text"] == "원문"


@pytest.mark.parametrize("payload", ['{}', '[null]', '[{"text":null}]', '[{"text":""}]'])
def test_invalid_response_retried_then_raises(payload, monkeypatch):
    monkeypatch.setattr("src.core.llm_engine.time.sleep", lambda _: None)
    model = Mock()
    model.generate_content.return_value = SimpleNamespace(text=payload)
    with pytest.raises(ValueError):
        LLMEngine()._process_batch([{"start": 0, "end": 1, "text": "original"}], model)
    assert model.generate_content.call_count == 3


def test_count_mismatch_retains_original():
    original = [{"start": 0, "end": 1, "text": "original"}]
    model = Mock()
    model.generate_content.return_value = SimpleNamespace(text="[]")
    assert LLMEngine()._process_batch(original, model) == original


def test_missing_key_and_invalid_batch_size(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    engine = LLMEngine()
    original = [{"start": 0, "end": 1, "text": "original"}]
    assert engine.correct_subtitles(original) == original
    with pytest.raises(ValueError):
        engine.correct_subtitles(original, batch_size=0)
