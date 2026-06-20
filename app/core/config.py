import json
from typing import Dict, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    CHROMA_DB_DIR: str = "./data/chroma_db"
    STATE_DB_PATH: str = "./data/state.db"
    SCAN_INTERVAL_SECONDS: int = 3600
    
    # Pydantic parst den JSON-String aus der .env automatisch in ein Dict
    INDEX_CONFIG: Dict[str, List[str]] = Field(default_factory=dict)

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()