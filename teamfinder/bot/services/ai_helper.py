import logging
from typing import Dict, Any, Optional
from config.settings import settings

logger = logging.getLogger(__name__)


class AIHelper:
    """
    Gemini AI integration service for assistive candidate profiling.
    Strict rule: AI NEVER makes accept/reject decisions; it only assists humans with structuring text.
    """

    def __init__(self) -> None:
        self.api_key = settings.GEMINI_API_KEY

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    async def analyze_skills_and_summary(self, role: str, raw_skills: str, about: str) -> Optional[Dict[str, Any]]:
        """
        Extract primary skill tags and clean summary using Gemini if configured.
        Falls back smoothly if API key is not configured.
        """
        if not self.is_available:
            return None

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            prompt = (
                f"You are a technical recruiter assistant. Given the candidate role: {role}, "
                f"raw skills: {raw_skills}, and bio: {about}.\n"
                f"Return a concise 2-sentence summary and 3-5 normalized technology tags. Keep Russian language."
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                ),
            )
            return {"summary": response.text.strip()}
        except Exception as e:
            logger.warning(f"AIHelper generation skipped or failed gracefully: {e}")
            return None


ai_helper = AIHelper()
