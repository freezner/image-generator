"""
Config Loader Module
설정 파일 로드 및 환경 변수 관리
"""
import json
import os
from pathlib import Path
from dataclasses import dataclass, field
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


# 기본 설정값
DEFAULT_CONFIG = {
    "brand": {
        "name": "MyBrand",
        "main_color": "#FF6B35",
        "sub_color": "#004E89",
        "style_keywords": ["3D rendering", "cute", "soft lighting"]
    },
    "output": {
        "format": "png",
        "width": 1024,
        "height": 1024,
        "transparent_background": True,
        "upscale": False
    },
    "paths": {
        "character_dir": "./assets/character",
        "output_dir": "./output"
    },
    "api": {
        "provider": "google",
        "model": "gemini-2.5-flash-image",
        "text_model": "gemini-2.0-flash",
        "max_reference_images": 5
    },
    "prompts": {
        "fixed_prefix": "3D rendered cute character illustration, consistent character design, {MAIN_COLOR} as primary accent color, {SUB_COLOR} as secondary color,",
        "fixed_suffix": ", soft studio lighting, minimal clean background, high quality, detailed, professional product image style",
        "negative": "deformed, distorted, disfigured, poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, ugly, disgusting, blurry, out of focus"
    }
}


def _merge_config(base: dict, override: dict) -> dict:
    """기본 설정에 사용자 설정을 병합"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    return result


@dataclass
class BrandConfig:
    name: str = "MyBrand"
    main_color: str = "#FF6B35"
    sub_color: str = "#004E89"
    style_keywords: List[str] = field(default_factory=lambda: ["3D rendering", "cute", "soft lighting"])


@dataclass
class OutputConfig:
    format: str = "png"
    width: int = 1024
    height: int = 1024
    transparent_background: bool = True
    upscale: bool = False


@dataclass
class PathsConfig:
    character_dir: Path = field(default_factory=lambda: Path("./assets/character"))
    output_dir: Path = field(default_factory=lambda: Path("./output"))


@dataclass
class ApiConfig:
    provider: str = "google"
    model: str = "gemini-2.5-flash-image"
    max_reference_images: int = 5
    text_model: str = "gemini-2.0-flash"


@dataclass
class PromptsConfig:
    fixed_prefix: str = "3D rendered cute character illustration, consistent character design,"
    fixed_suffix: str = ", soft studio lighting, minimal clean background, high quality"
    negative: str = "deformed, distorted, ugly, blurry"


@dataclass
class Config:
    brand: BrandConfig
    output: OutputConfig
    paths: PathsConfig
    api: ApiConfig
    prompts: PromptsConfig
    
    @classmethod
    def load(cls, config_path: str = "config.json") -> "Config":
        """설정 파일 로드 (없는 항목은 기본값 사용)"""
        # config.json 위치 기준으로 .env 다시 로드 시도
        config_dir = Path(config_path).parent
        env_path = config_dir / ".env" if config_dir != Path(".") else Path(".env")
        _load_env_file(env_path)
        
        # 설정 파일 로드 또는 기본값 사용
        if Path(config_path).exists():
            with open(config_path, "r", encoding="utf-8") as f:
                user_data = json.load(f)
            data = _merge_config(DEFAULT_CONFIG, user_data)
        else:
            print(f"⚠️ 설정 파일 없음 ({config_path}), 기본값 사용")
            data = DEFAULT_CONFIG
        
        return cls(
            brand=BrandConfig(**data.get("brand", {})),
            output=OutputConfig(**data.get("output", {})),
            paths=PathsConfig(
                character_dir=Path(data.get("paths", {}).get("character_dir", "./assets/character")),
                output_dir=Path(data.get("paths", {}).get("output_dir", "./output"))
            ),
            api=ApiConfig(**data.get("api", {})),
            prompts=PromptsConfig(**data.get("prompts", {}))
        )
    
    @classmethod
    def create_default(cls) -> "Config":
        """기본 설정으로 Config 생성"""
        return cls(
            brand=BrandConfig(),
            output=OutputConfig(),
            paths=PathsConfig(),
            api=ApiConfig(),
            prompts=PromptsConfig()
        )
    
    def get_api_key(self) -> Optional[str]:
        """API 키 반환"""
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def load_config(config_path: str = "config.json") -> Config:
    """설정 로드 헬퍼 함수"""
    try:
        return Config.load(config_path)
    except Exception as e:
        print(f"⚠️ 설정 로드 실패 ({e}), 기본값 사용")
        return Config.create_default()
