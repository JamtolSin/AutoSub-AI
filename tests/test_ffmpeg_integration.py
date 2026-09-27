import os
from pathlib import Path
import shutil
import subprocess

import pytest

from src.core.audio_processor import AudioProcessor


@pytest.mark.integration
def test_real_audio_extraction(tmp_path):
    executable = os.environ.get("FFMPEG_BINARY") or shutil.which("ffmpeg")
    if not executable:
        pytest.skip("FFmpeg executable is not installed")
    video = tmp_path / "sample.mp4"
    subprocess.run(
        [executable, "-hide_banner", "-loglevel", "error", "-f", "lavfi",
         "-i", "color=c=black:s=16x16:r=1", "-f", "lavfi", "-i",
         "sine=frequency=440:sample_rate=16000", "-t", "1", "-c:v", "mpeg4",
         "-c:a", "aac", str(video)], check=True,
    )
    processor = AudioProcessor(temp_dir=str(tmp_path / "audio"))
    processor.ffmpeg_path = executable
    audio = Path(processor.extract_audio(str(video)))
    assert audio.stat().st_size > 0
    subprocess.run(
        [executable, "-hide_banner", "-loglevel", "error", "-i", str(audio),
         "-f", "null", "-"], check=True,
    )
