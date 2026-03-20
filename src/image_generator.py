"""
Image Generator Module
Google GenAI SDK를 사용한 이미지 생성 (Imagen 3)
"""
import os
import base64
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple
from PIL import Image
import io

from google import genai
from google.genai import types

from .config_loader import Config


class ImageGenerator:
    """AI 이미지 생성기 (Imagen 3)"""
    
    def __init__(self, config: Config, api_key: str):
        """
        Args:
            config: 설정 객체
            api_key: Google API 키
        """
        self.config = config
        self.client = genai.Client(api_key=api_key)
        
        # 이미지 생성 모델 설정 (config에서 가져옴)
        self.image_model = config.api.model
        
        # 출력 디렉토리 생성
        self.config.paths.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_reference_images(self) -> List[Image.Image]:
        """
        참조 캐릭터 이미지 로드
        
        Returns:
            PIL Image 객체 리스트
        """
        images = []
        char_dir = self.config.paths.character_dir
        
        if not char_dir.exists():
            print(f"⚠️ 캐릭터 디렉토리가 없습니다: {char_dir}")
            return images
        
        # 지원 포맷
        supported_formats = {'.png', '.jpg', '.jpeg', '.webp'}
        
        # 이미지 파일 로드
        image_files = sorted([
            f for f in char_dir.iterdir() 
            if f.suffix.lower() in supported_formats
        ])
        
        # 최대 개수 제한
        max_images = self.config.api.max_reference_images
        image_files = image_files[:max_images]
        
        for img_path in image_files:
            try:
                img = Image.open(img_path)
                images.append(img)
                print(f"✓ 참조 이미지 로드: {img_path.name}")
            except Exception as e:
                print(f"⚠️ 이미지 로드 실패 ({img_path.name}): {e}")
        
        return images
    
    def generate(
        self, 
        prompt: str,
        reference_images: Optional[List[Image.Image]] = None,
        negative_prompt: Optional[str] = None
    ) -> Optional[Image.Image]:
        """
        이미지 생성
        
        Args:
            prompt: 생성 프롬프트
            reference_images: 참조 이미지 리스트
            negative_prompt: 네거티브 프롬프트
            
        Returns:
            생성된 PIL Image 또는 None
        """
        try:
            # Gemini 이미지 모델인지 Imagen인지 확인
            is_gemini = "gemini" in self.image_model.lower()
            
            if is_gemini:
                return self._generate_with_gemini(prompt, reference_images)
            else:
                return self._generate_with_imagen(prompt)
                
        except Exception as e:
            print(f"❌ 이미지 생성 실패: {e}")
            return None
    
    def _generate_with_gemini(
        self, 
        prompt: str, 
        reference_images: Optional[List[Image.Image]] = None
    ) -> Optional[Image.Image]:
        """Gemini 모델로 이미지 생성"""
        print(f"🎨 이미지 생성 중 ({self.image_model})...")
        
        # 컨텐츠 구성
        contents = []
        
        # 참조 이미지 추가
        if reference_images:
            for ref_img in reference_images:
                # PIL Image를 bytes로 변환
                img_byte_arr = io.BytesIO()
                ref_img.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                
                contents.append(types.Part.from_bytes(
                    data=img_bytes,
                    mime_type="image/png"
                ))
            
            # 참조 이미지와 함께 프롬프트
            full_prompt = f"""Based on the reference character image above, generate a new image:

{prompt}

IMPORTANT: Maintain the exact same character design and style. Generate as a high-quality image."""
        else:
            full_prompt = f"Generate an image: {prompt}"
        
        contents.append(full_prompt)
        
        # 이미지 생성 요청
        response = self.client.models.generate_content(
            model=self.image_model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            )
        )
        
        # 응답에서 이미지 추출
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    image_data = part.inline_data.data
                    image = Image.open(io.BytesIO(image_data))
                    return image
        
        print("⚠️ 응답에 이미지가 없습니다")
        return None
    
    def _generate_with_imagen(self, prompt: str) -> Optional[Image.Image]:
        """Imagen 모델로 이미지 생성 (유료)"""
        print(f"🎨 이미지 생성 중 ({self.image_model})...")
        
        response = self.client.models.generate_images(
            model=self.image_model,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="BLOCK_LOW_AND_ABOVE",
                person_generation="ALLOW_ADULT",
            )
        )
        
        if response.generated_images:
            image_data = response.generated_images[0].image.image_bytes
            image = Image.open(io.BytesIO(image_data))
            return image
        
        print("⚠️ 응답에 이미지가 없습니다")
        return None
    
    def post_process(self, image: Image.Image) -> Image.Image:
        """
        이미지 후처리
        
        Args:
            image: 원본 이미지
            
        Returns:
            처리된 이미지
        """
        # 리사이즈
        target_size = (self.config.output.width, self.config.output.height)
        if image.size != target_size:
            image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # 투명 배경 처리 (PNG의 경우)
        if self.config.output.transparent_background:
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
        
        return image
    
    def save(self, image: Image.Image, name_hint: str = "") -> Path:
        """
        이미지 저장
        
        Args:
            image: 저장할 이미지
            name_hint: 파일명 힌트
            
        Returns:
            저장된 파일 경로
        """
        # 타임스탬프 기반 파일명
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 힌트에서 안전한 파일명 생성
        safe_hint = "".join(c for c in name_hint[:30] if c.isalnum() or c in "_ -").strip()
        if safe_hint:
            filename = f"{timestamp}_{safe_hint}"
        else:
            filename = timestamp
        
        # 확장자
        ext = self.config.output.format.lower()
        if ext == "jpg":
            ext = "jpeg"
        
        filepath = self.config.paths.output_dir / f"{filename}.{ext}"
        
        # 저장
        if ext == "png":
            image.save(filepath, "PNG", optimize=True)
        else:
            # JPEG는 RGB 모드 필요
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            image.save(filepath, "JPEG", quality=95)
        
        print(f"💾 저장됨: {filepath}")
        return filepath
    
    def generate_and_save(
        self, 
        prompt: str,
        reference_images: Optional[List[Image.Image]] = None,
        negative_prompt: Optional[str] = None,
        name_hint: str = ""
    ) -> Tuple[Optional[Image.Image], Optional[Path]]:
        """
        이미지 생성 + 후처리 + 저장 통합 메서드
        
        Returns:
            (이미지, 파일경로) 튜플
        """
        # 생성
        image = self.generate(prompt, reference_images, negative_prompt)
        if image is None:
            return None, None
        
        # 후처리
        image = self.post_process(image)
        
        # 저장
        filepath = self.save(image, name_hint)
        
        return image, filepath


def create_generator(config: Config, api_key: str) -> ImageGenerator:
    """이미지 생성기 생성 헬퍼"""
    return ImageGenerator(config, api_key)
