import os
import sys
import logging
import ffmpeg
from pathlib import Path
from typing import Optional

# Basic logging configuration (will be replaced by logger.py later)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioProcessor:
    """
    Handles audio extraction from video files using FFmpeg.
    """
    SUPPORTED_FORMATS = {'.mp4', '.mkv', '.avi', '.mov', '.webm'}

    def __init__(self, temp_dir: str = "temp"):
        """
        Initialize AudioProcessor.
        
        Args:
            temp_dir: Directory to store extracted audio files.
        """
        self.temp_dir = Path(temp_dir)
        self.ffmpeg_path = self._get_ffmpeg_path()
        self._ensure_temp_dir()

    def _get_ffmpeg_path(self) -> str:
        """
        Detect FFmpeg binary path.
        Handles PyInstaller (_MEIPASS) and local development environments.
        """
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller temp directory
            base_path = Path(sys._MEIPASS)
            ffmpeg_path = base_path / "tools" / "ffmpeg.exe"
        else:
            # Local development environment
            # Path relative to src/core/audio_processor.py -> ../../tools/ffmpeg.exe
            base_path = Path(__file__).parent.parent.parent
            ffmpeg_path = base_path / "tools" / "ffmpeg.exe"

        ffmpeg_path_str = str(ffmpeg_path.resolve())
        
        # Check if file exists and is not empty (valid binary)
        if not ffmpeg_path.exists() or ffmpeg_path.stat().st_size < 1024:
            # Fallback to system PATH if not found in tools or is invalid
            if ffmpeg_path.exists():
                logger.warning(f"FFmpeg at {ffmpeg_path_str} is too small ({ffmpeg_path.stat().st_size} bytes). Ignoring.")
            else:
                logger.warning(f"FFmpeg not found at {ffmpeg_path_str}.")
            
            logger.info("Trying system PATH 'ffmpeg'.")
            return "ffmpeg"
            
        logger.info(f"Using FFmpeg at: {ffmpeg_path_str}")
        return ffmpeg_path_str

    def _ensure_temp_dir(self):
        """Ensure the temporary directory exists."""
        if not self.temp_dir.exists():
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created temporary directory: {self.temp_dir}")

    def validate_video_file(self, video_path: str) -> bool:
        """
        Check if the file exists and has a supported extension.
        
        Args:
            video_path: Path to the video file.
            
        Returns:
            True if valid, False otherwise.
        """
        path = Path(video_path)
        if not path.is_file():
            logger.error(f"File not found: {video_path}")
            return False
        
        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            logger.error(f"Unsupported format: {path.suffix}. Supported: {self.SUPPORTED_FORMATS}")
            return False
            
        return True

    def extract_audio(self, video_path: str) -> Optional[str]:
        """
        Extract audio from video file using FFmpeg.
        
        Args:
            video_path: Path to the video file.
            
        Returns:
            Path to the extracted audio file (mp3) or None if failed.
        """
        if not self.validate_video_file(video_path):
            raise ValueError(f"Invalid video file: {video_path}")

        video_path_obj = Path(video_path)
        # Use a consistent naming convention or hash to avoid collisions? 
        # For now, simple filename based on source.
        output_filename = f"{video_path_obj.stem}_audio.mp3"
        output_path = self.temp_dir / output_filename
        output_path_str = str(output_path)

        try:
            logger.info(f"Extracting audio from {video_path} to {output_path_str}...")
            
            # ffmpeg-python stream construction
            stream = ffmpeg.input(video_path)
            # Extract audio, convert to mp3, qscale 2 (high quality variable bitrate)
            stream = ffmpeg.output(stream, output_path_str, acodec='libmp3lame', qscale=2, loglevel="error")
            
            # Run ffmpeg command
            # cmd parameter specifies the path to the ffmpeg executable
            ffmpeg.run(stream, cmd=self.ffmpeg_path, overwrite_output=True)
            
            logger.info(f"Audio extraction successful: {output_path_str}")
            return output_path_str
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode('utf8') if e.stderr else str(e)
            logger.error(f"FFmpeg error: {error_msg}")
            raise RuntimeError(f"Failed to extract audio: {error_msg}") from e
        except Exception as e:
            logger.error(f"Unexpected error during audio extraction: {e}")
            raise
