import math
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SRTGenerator:
    """
    Handles generation of SRT subtitle files.
    """
    
    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """
        Convert seconds to SRT timestamp format (00:00:00,000).
        
        Args:
            seconds: Time in seconds.
            
        Returns:
            Formatted timestamp string.
        """
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Timestamp must be finite and non-negative")
        total_seconds, millis = divmod(round(seconds * 1000), 1000)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def generate_srt(segments: List[Dict[str, Any]], output_path: str):
        """
        Generate SRT file from segments.
        
        Args:
            segments: List of segments with 'start', 'end', 'text'.
            output_path: Path to save the SRT file.
        """
        blocks = []
        for i, segment in enumerate(segments, start=1):
            start_time = SRTGenerator.format_timestamp(segment["start"])
            end_time = SRTGenerator.format_timestamp(segment["end"])
            if segment["end"] < segment["start"]:
                raise ValueError("Subtitle end must not precede its start")
            text = segment["text"]
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Subtitle text must be a non-empty string")
            blocks.append(f"{i}\n{start_time} --> {end_time}\n{text.strip()}\n\n")
        # Validate every segment before opening an existing output file.
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("".join(blocks), encoding="utf-8")
        logger.info("SRT file generated: %s", output_path)

    @staticmethod
    def generate_output_filename(source_path: str, output_dir: str) -> str:
        """
        Generate unique output filename.
        Pattern: {source_name}_{timestamp}.srt
        
        Args:
            source_path: Path to the source video file.
            output_dir: Directory to save the SRT file.
            
        Returns:
            Full path to the output SRT file.
        """
        source_path_obj = Path(source_path)
        stem = source_path_obj.stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{stem}_{timestamp}.srt"
        
        output_path = Path(output_dir) / filename
        
        # Ensure uniqueness (though timestamp usually suffices)
        counter = 1
        while output_path.exists():
            filename = f"{stem}_{timestamp}_{counter}.srt"
            output_path = Path(output_dir) / filename
            counter += 1
            
        return str(output_path)
