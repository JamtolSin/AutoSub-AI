import pytest
import os
from src.core.srt_generator import SRTGenerator

def test_format_timestamp():
    # Test cases: seconds -> 00:00:00,000
    assert SRTGenerator.format_timestamp(0) == "00:00:00,000"
    assert SRTGenerator.format_timestamp(1.5) == "00:00:01,500"
    assert SRTGenerator.format_timestamp(61.001) == "00:01:01,001"
    assert SRTGenerator.format_timestamp(3661.0) == "01:01:01,000"

def test_generate_srt(tmp_path):
    segments = [
        {"start": 0.0, "end": 2.0, "text": "Hello"},
        {"start": 2.5, "end": 4.0, "text": "World"}
    ]
    
    output_file = tmp_path / "test.srt"
    SRTGenerator.generate_srt(segments, str(output_file))
    
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    
    expected = (
        "1\n"
        "00:00:00,000 --> 00:00:02,000\n"
        "Hello\n\n"
        "2\n"
        "00:00:02,500 --> 00:00:04,000\n"
        "World\n\n"
    )
    
    # Normalize newlines for comparison
    assert content.replace("\r\n", "\n") == expected.replace("\r\n", "\n")

def test_generate_output_filename(tmp_path):
    source = "C:/video/movie.mp4"
    output_dir = tmp_path
    
    filename = SRTGenerator.generate_output_filename(source, str(output_dir))
    assert "movie_" in filename
    assert filename.endswith(".srt")


def test_millisecond_rounding_carries_into_next_minute():
    assert SRTGenerator.format_timestamp(59.9996) == "00:01:00,000"


@pytest.mark.parametrize("seconds", [-1, float("nan"), float("inf")])
def test_invalid_timestamp(seconds):
    with pytest.raises(ValueError):
        SRTGenerator.format_timestamp(seconds)


@pytest.mark.parametrize("bad_segment", [
    {"start": 2, "end": 1, "text": "reversed"},
    {"start": 0, "end": 1, "text": None},
])
def test_invalid_later_segment_does_not_truncate_output(tmp_path, bad_segment):
    output = tmp_path / "existing.srt"
    output.write_text("keep this", encoding="utf-8")
    with pytest.raises(ValueError):
        SRTGenerator.generate_srt(
            [{"start": 0, "end": 1, "text": "valid"}, bad_segment], str(output)
        )
    assert output.read_text(encoding="utf-8") == "keep this"
