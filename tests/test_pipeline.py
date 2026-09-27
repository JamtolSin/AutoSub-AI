from pathlib import Path
from unittest.mock import Mock

import pytest

from src.core.pipeline import generate_subtitles


@pytest.mark.parametrize("failure", [None, "audio", "stt", "llm", "empty"])
def test_pipeline_output_and_cleanup(tmp_path, failure):
    source = tmp_path / "video.mp4"
    source.write_bytes(b"input remains untouched")
    created_dirs = []

    def audio_factory(temp_dir):
        folder = Path(temp_dir)
        created_dirs.append(folder)
        audio = folder / "audio.mp3"
        audio.write_bytes(b"fake audio")
        processor = Mock()
        processor.extract_audio.return_value = str(audio)
        if failure == "audio":
            processor.extract_audio.side_effect = RuntimeError("extraction failed")
        return processor

    segment = {"start": 61.001, "end": 62.5, "text": "original"}
    stt = Mock()
    stt.transcribe.return_value = [] if failure == "empty" else [segment]
    llm = Mock()
    llm.correct_subtitles.return_value = [{**segment, "text": "corrected"}]
    if failure == "stt":
        stt.transcribe.side_effect = RuntimeError("recognition failed")
    if failure == "llm":
        llm.correct_subtitles.side_effect = RuntimeError("correction failed")
    progress = Mock()
    kwargs = dict(
        api_key="test-only", audio_factory=audio_factory,
        stt_factory=Mock(return_value=stt), llm_factory=Mock(return_value=llm),
        progress=progress,
    )
    output_dir = tmp_path / "output"
    if failure:
        with pytest.raises((RuntimeError, ValueError)):
            generate_subtitles(str(source), str(output_dir), **kwargs)
        assert not output_dir.exists()
    else:
        result = generate_subtitles(str(source), str(output_dir), **kwargs)
        assert result.read_text(encoding="utf-8") == (
            "1\n00:01:01,001 --> 00:01:02,500\ncorrected\n\n"
        )
        assert llm.correct_subtitles.call_args.args[0] == [segment]
        assert progress.call_args.args[0] == 100
    assert created_dirs and all(not path.exists() for path in created_dirs)
    assert source.read_bytes() == b"input remains untouched"
