"""Subtitle workflow, independent of the Streamlit interface."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

from src.core.srt_generator import SRTGenerator


def generate_subtitles(
    video_path: str,
    output_dir: str,
    *,
    api_key: str,
    model_size: str = "large-v3",
    device: str = "auto",
    progress: Callable[[int, str], None] | None = None,
    audio_factory=None,
    stt_factory=None,
    llm_factory=None,
) -> Path:
    """Run extraction → transcription → correction → SRT.

    Factories allow offline tests without model downloads or API calls.
    Only this job's extracted audio is removed; the source video is retained.
    """
    if audio_factory is None:
        from src.core.audio_processor import AudioProcessor
        audio_factory = AudioProcessor
    if stt_factory is None:
        from src.core.stt_engine import STTEngine
        stt_factory = STTEngine
    if llm_factory is None:
        from src.core.llm_engine import LLMEngine
        llm_factory = LLMEngine

    def report(percent: int, message: str):
        if progress:
            progress(percent, message)

    def stage_progress(start: int, end: int, message: str):
        def update(current, total):
            if total > 0:
                fraction = max(0, min(current / total, 1))
                report(start + int(fraction * (end - start)), message)
        return update

    with TemporaryDirectory(prefix="autosub-audio-") as temp_dir:
        report(0, "오디오 추출 중...")
        audio_path = audio_factory(temp_dir=temp_dir).extract_audio(video_path)
        report(10, "음성 인식 중...")
        segments = stt_factory(model_size=model_size, device=device).transcribe(
            audio_path, progress_callback=stage_progress(10, 50, "음성 인식 중...")
        )
        if not segments:
            raise ValueError("인식된 음성이 없습니다. 다른 영상을 확인해주세요.")
        report(50, "자막 교정 중...")
        corrected = llm_factory(api_key=api_key).correct_subtitles(
            segments, progress_callback=stage_progress(50, 90, "자막 교정 중...")
        )
        report(90, "SRT 파일 생성 중...")
        output = Path(SRTGenerator.generate_output_filename(video_path, output_dir))
        SRTGenerator.generate_srt(corrected, str(output))
    report(100, "완료!")
    return output
