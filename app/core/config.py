import os
import random
from typing import List
from dotenv import load_dotenv
load_dotenv() 


class Settings:
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    OPENAI_API_KEYS: List[str] = os.getenv("OPENAI_API_KEYS", "").split(",")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")

    NVIDIA_API_KEYS: List[str] = os.getenv("NVIDIA_API_KEYS", "").split(",")
    NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    GOOGLE_API_KEYS: List[str] = os.getenv("GOOGLE_API_KEYS", "").split(",")

    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_BASE_URL: str = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

    @property
    def openai_api_key(self) -> str:
        return random.choice(self.OPENAI_API_KEYS) if self.OPENAI_API_KEYS else ""

    @property
    def nvidia_api_key(self) -> str:
        return random.choice(self.NVIDIA_API_KEYS) if self.NVIDIA_API_KEYS else ""

    @property
    def google_api_key(self) -> str:
        return random.choice(self.GOOGLE_API_KEYS) if self.GOOGLE_API_KEYS else ""

settings = Settings()
