import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from src.core.srt_generator import SRTGenerator
from tqdm import tqdm

# Basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class STTEngine:
    """
    Speech-to-Text Engine using Faster-Whisper.
    """
    def __init__(self, model_size: str = "large-v3", device: str = "auto", model_path: str = "models"):
        """
        Initialize STT Engine.
        
        Args:
            model_size: Whisper model size (e.g., "base", "small", "large-v3").
            device: Device to use ("cpu", "cuda", "auto").
            model_path: Directory to store/load the model.
        """
        self.model_size = model_size
        self.model_path = Path(model_path)
        self.device = device
        
        self._ensure_model_dir()
        self.model = self._load_model()

    def _ensure_model_dir(self):
        """Ensure the model directory exists."""
        if not self.model_path.exists():
            self.model_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created model directory: {self.model_path}")

    def _load_model(self):
        """
        Load the Whisper model. Downloads it if not present.
        """
        from faster_whisper import WhisperModel

        logger.info(f"Loading Whisper model: {self.model_size} on {self.device}...")
        
        try:
            # compute_type="default" allows faster-whisper to choose the best type for the device
            # (e.g. float16 for CUDA, int8 for CPU)
            model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type="default", 
                download_root=str(self.model_path),
                local_files_only=False
            )
            logger.info("Model loaded successfully.")
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def transcribe(self, audio_path: str, language: str = "ko", progress_callback=None) -> List[Dict[str, Any]]:
        """
        Transcribe audio file using the loaded model.
        
        Args:
            audio_path: Path to the audio file.
            language: Language code (default "ko").
            progress_callback: Optional function(current_time, total_duration) to update progress.
            
        Returns:
            List of segments with start, end, text, and confidence.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Starting transcription for {audio_path}...")
        
        segments, info = self.model.transcribe(
            audio_path,
            language=language,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        result = []
        total_duration = info.duration
        
        with tqdm(total=total_duration, unit="s", desc="Transcribing") as pbar:
            for segment in segments:
                segment_dict = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "confidence": segment.avg_logprob
                }
                result.append(segment_dict)
                
                current_pos = segment.end
                update_amount = current_pos - pbar.n
                if update_amount > 0:
                    pbar.update(update_amount)
                
                if progress_callback:
                    progress_callback(current_pos, total_duration)
                
        logger.info(f"Transcription complete. {len(result)} segments found.")
        return result

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """
        Convert seconds to SRT timestamp format (00:00:00,000).
        """
        return SRTGenerator.format_timestamp(seconds)
