"""
Config Loader Module
설정 파일 로드 및 환경 변수 관리
"""
import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

# .env 파일 로드 (python-dotenv 없이 직접 구현)
def _load_env_file(env_path: Path = None):
    """
    .env 파일을 읽어 환경변수에 설정
    python-dotenv 없이도 동작하도록 직접 구현
    """
    if env_path is None:
        env_path = Path.cwd() / ".env"
    
    if not env_path.exists():
        return
    
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 빈 줄이나 주석 스킵
            if not line or line.startswith("#"):
                continue
            # KEY=VALUE 형태 파싱
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # 따옴표 제거
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                # 환경변수에 설정 (이미 있으면 덮어쓰지 않음)
                if key and key not in os.environ:
                    os.environ[key] = value

# 모듈 로드 시 .env 파일 자동 로드
_load_env_file()


@dataclass
class BrandConfig:
    name: str
    main_color: str
    sub_color: str
    style_keywords: List[str]


@dataclass
class OutputConfig:
    format: str
    width: int
    height: int
    transparent_background: bool
    upscale: bool


@dataclass
class PathsConfig:
    character_dir: Path
    output_dir: Path


@dataclass
class ApiConfig:
    provider: str
    model: str
    max_reference_images: int
    text_model: str = "gemini-2.0-flash"  # 프롬프트 향상용 모델


@dataclass
class PromptsConfig:
    fixed_prefix: str
    fixed_suffix: str
    negative: str


@dataclass
class Config:
    brand: BrandConfig
    output: OutputConfig
    paths: PathsConfig
    api: ApiConfig
    prompts: PromptsConfig
    
    @classmethod
    def load(cls, config_path: str = "config.json") -> "Config":
        """설정 파일 로드"""
        # config.json 위치 기준으로 .env 다시 로드 시도
        config_dir = Path(config_path).parent
        env_path = config_dir / ".env" if config_dir != Path(".") else Path(".env")
        _load_env_file(env_path)
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls(
            brand=BrandConfig(**data["brand"]),
            output=OutputConfig(**data["output"]),
            paths=PathsConfig(
                character_dir=Path(data["paths"]["character_dir"]),
                output_dir=Path(data["paths"]["output_dir"])
            ),
            api=ApiConfig(**data["api"]),
            prompts=PromptsConfig(**data["prompts"])
        )
    
    def get_api_key(self) -> Optional[str]:
        """API 키 반환"""
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def load_config(config_path: str = "config.json") -> Config:
    """설정 로드 헬퍼 함수"""
    return Config.load(config_path)
