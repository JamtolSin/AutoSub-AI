import os
import json
import logging
import time
from typing import List, Dict, Any, Optional
from src.utils.resource_resolver import get_resource_path

# Basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMEngine:
    """
    LLM Engine using Google Gemini for subtitle correction.
    """
    def __init__(self, api_key: Optional[str] = None, prompt_path: str = "src/prompts/correction.txt", glossary_path: str = "src/prompts/glossary.json"):
        """
        Initialize LLM Engine.
        
        Args:
            api_key: Gemini API Key.
            prompt_path: Path to the system prompt file.
            glossary_path: Path to the glossary JSON file.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("Gemini API Key not found. Please provide it via init or env var.")
        
        self.prompt_path = get_resource_path(prompt_path)
        self.glossary_path = get_resource_path(glossary_path)
        
        self.base_system_prompt = self._load_prompt()
        self.glossary = self._load_glossary()

    def _load_prompt(self) -> str:
        """Load system prompt from file."""
        if not self.prompt_path.exists():
            logger.warning(f"Prompt file not found: {self.prompt_path}")
            return "You are a subtitle correction expert. Correct the following subtitles."
        return self.prompt_path.read_text(encoding="utf-8")

    def _load_glossary(self) -> Dict[str, str]:
        """Load glossary from JSON file."""
        if not self.glossary_path.exists():
            logger.warning(f"Glossary file not found: {self.glossary_path}")
            return {}
        try:
            return json.loads(self.glossary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse glossary: {e}")
            return {}

    def correct_subtitles(self, segments: List[Dict[str, Any]], batch_size: int = 30, model: str = "gemini-2.5-flash", progress_callback=None) -> List[Dict[str, Any]]:
        """
        Correct subtitles using Gemini.
        
        Args:
            segments: List of subtitle segments.
            batch_size: Number of segments to process in one API call.
            model: Gemini model to use.
            progress_callback: Optional function(current_count, total_count) to update progress.
            
        Returns:
            List of corrected segments.
        """
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        if not segments:
            return []
        if not self.api_key:
            logger.error("Gemini API Key not initialized. Skipping correction.")
            return segments

        corrected_segments = []
        
        # Prepare glossary string to append to prompt
        glossary_str = json.dumps(self.glossary, ensure_ascii=False, indent=2)
        system_prompt = f"{self.base_system_prompt}\n\n## Glossary\n{glossary_str}"
        
        total_batches = (len(segments) + batch_size - 1) // batch_size
        
        # Initialize model
        # Using generation_config to ensure JSON output if possible (Gemini 1.5 supports response_mime_type="application/json")
        generation_config = {
            "temperature": 0.0,
            "response_mime_type": "application/json"
        }
        
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            gemini_model = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                system_instruction=system_prompt
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            return segments
        
        for i in range(0, len(segments), batch_size):
            batch = segments[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{total_batches} ({len(batch)} segments)...")
            
            try:
                corrected_batch = self._process_batch(batch, gemini_model)
                corrected_segments.extend(corrected_batch)
            except Exception as e:
                logger.error(f"Failed to process batch {i//batch_size + 1}: {e}")
                # Fallback: use original segments if correction fails
                corrected_segments.extend(batch)
            
            if progress_callback:
                progress_callback(min(i + batch_size, len(segments)), len(segments))
                
        return corrected_segments

    def _process_batch(self, batch: List[Dict[str, Any]], model) -> List[Dict[str, Any]]:
        """Process a single batch of segments."""
        # Prepare input JSON
        input_json = json.dumps(batch, ensure_ascii=False, indent=2)
        
        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(input_json)
                response_text = response.text
                
                # Parse response
                corrected_data = self._parse_response(response_text)
                
                # Validate count
                if len(corrected_data) != len(batch):
                    logger.warning(f"Mismatch in corrected segments count. Expected {len(batch)}, got {len(corrected_data)}.")
                    # If mismatch, revert to original for this batch to ensure timestamp integrity
                    logger.error("Segment count mismatch. Reverting to original text for this batch.")
                    return batch
                
                # Merge corrections (keep original timestamps to be safe)
                result = []
                for original, corrected in zip(batch, corrected_data):
                    new_seg = original.copy()
                    new_seg["text"] = corrected.get("text", original["text"])
                    result.append(new_seg)
                        
                return result
                
            except Exception as e:
                logger.error(f"Error calling Gemini (Attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)
        
        return batch

    def _parse_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Extract and parse JSON from response text."""
        start = response_text.find("[")
        end = response_text.rfind("]")
        payload = response_text[start:end + 1] if 0 <= start < end else response_text
        data = json.loads(payload)
        if not isinstance(data, list) or any(
            not isinstance(item, dict)
            or not isinstance(item.get("text"), str)
            or not item["text"].strip()
            for item in data
        ):
            raise ValueError("Expected an array of objects with non-empty subtitle text")
        return data
