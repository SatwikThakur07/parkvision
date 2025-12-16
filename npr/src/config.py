"""Configuration management module"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    # App config
    app_name: str = "License Plate Detection Service"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Model config
    yolo_model_path: str = "license_plate_best.pt"
    confidence_threshold: float = 0.5
    gpu_enabled: bool = True
    
    # OCR config
    ocr_languages: str = "en"
    ocr_gpu_enabled: bool = True
    
    # API config
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    max_upload_size_mb: int = 500
    
    # Paths
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    log_dir: str = "logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        for dir_path in [self.upload_dir, self.output_dir, self.log_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    @property
    def ocr_languages_list(self) -> List[str]:
        """Convert OCR languages string to list"""
        return [lang.strip() for lang in self.ocr_languages.split(",")]


# Global settings instance
settings = Settings()

