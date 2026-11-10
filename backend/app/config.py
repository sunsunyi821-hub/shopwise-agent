import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
                                                  

class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env."""
                                              
                                         
    app_name: str = "ShopWise API"
    app_version: str = "0.1.0"
    debug: bool = False

    llm_provider: Literal["mock", "anthropic", "openai"] = "mock"
                        
    llm_model: str = "claude-opus-5-5"

    anthropic_api_key: str | None = None
    anthropic_base_url: str | None = None

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.deepseek.com/v1"
    openai_model: str = "deepseek-chat"
                                                                                        
    llm_extra_body_json: str | None = None

                                     
                                                                      
                                                    
                                                 
    embedding_provider: Literal["disabled", "openai", "mock"] = "disabled"                               
    embedding_api_key: str | None = None
    embedding_base_url: str = "https://maas.qianwenaiapi.com/compatible-mode/v1"
    embedding_model: str = "qwen3.7-text-embedding"
    embedding_batch_size: int = 20

    database_url: str = "sqlite:///./data/shopwise.db"
                                  
                                      
                           
               
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",                            
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
              
            
                         
                
                                 
          
               
                       
                               
            
    @property
    def resolved_database_url(self) -> str:
        """Turn relative SQLite paths into absolute paths under backend/."""
        prefix = "sqlite:///./"
        if self.database_url.startswith(prefix):                
            relative = self.database_url[len(prefix) :]                   
            return f"sqlite:///{(BACKEND_DIR / relative).as_posix()}"                               
        return self.database_url

    @property
    def resolved_openai_api_key(self) -> str | None:
        return self.openai_api_key or os.getenv("DEEPSEEK_API_KEY")
                                                       
    @property
    def resolved_openai_base_url(self) -> str:
        return (
            self.openai_base_url
            or os.getenv("DEEPSEEK_BASE_URL")
            or "https://api.deepseek.com/v1"
        )

    @property
    def resolved_embedding_api_key(self) -> str | None:
        return self.embedding_api_key or os.getenv("DASHSCOPE_API_KEY")

    @property
    def llm_extra_body(self) -> dict[str, Any] | None:               
        if not self.llm_extra_body_json:                            
            return None
        try:
            value = json.loads(self.llm_extra_body_json)                         
            return value if isinstance(value, dict) else None                    
        except json.JSONDecodeError:
            return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
                                                                       