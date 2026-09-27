"""Render fixed sample segments; does not run speech recognition or an LLM."""

from pathlib import Path

from src.core.srt_generator import SRTGenerator


if __name__ == "__main__":
    output = Path("output/demo.srt")
    SRTGenerator.generate_srt(
        [
            {"start": 0.0, "end": 2.5, "text": "이것은 고정된 예제 자막입니다."},
            {"start": 2.8, "end": 5.001, "text": "음성 인식이나 API 호출 없이 SRT를 확인합니다."},
        ],
        str(output),
    )
    print(output.resolve())
