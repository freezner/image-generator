"""
Image Generator Module
Google GenAI SDK를 사용한 이미지 생성 (Imagen 3)
"""
import os
import base64
import unicodedata
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple
from PIL import Image
import io
import traceback


def normalize_text(text: str) -> str:
    """유니코드 정규화 (NFC) - macOS 파일명 호환"""
    return unicodedata.normalize('NFC', text)

from google import genai
from google.genai import types

from .config_loader import Config


class ImageGenerationError(Exception):
    """이미지 생성 오류 (사용자 친화적 메시지 포함)"""
    
    # 알려진 오류 코드별 안내 메시지
    ERROR_MESSAGES = {
        "PERMISSION_DENIED": "🔑 API 키 권한 오류\n\n• API 키가 유효하지 않거나 만료되었습니다.\n• Google AI Studio에서 새 API 키를 발급받으세요.\n• https://aistudio.google.com/apikey",
        "RESOURCE_EXHAUSTED": "⏳ API 할당량 초과\n\n• 일일 사용량 한도에 도달했습니다.\n• 잠시 후 다시 시도하거나 내일 다시 시도하세요.",
        "INVALID_ARGUMENT": "⚠️ 잘못된 요청\n\n• 프롬프트가 너무 길거나 부적절한 내용이 포함되었을 수 있습니다.\n• 프롬프트를 수정하고 다시 시도하세요.",
        "SAFETY": "🛡️ 안전 필터 차단\n\n• 생성 요청이 안전 정책에 의해 차단되었습니다.\n• 프롬프트를 수정하고 다시 시도하세요.",
        "INTERNAL": "🔧 서버 오류\n\n• Google 서버에 일시적인 문제가 발생했습니다.\n• 잠시 후 다시 시도하세요.",
        "UNAVAILABLE": "🌐 서비스 일시 중단\n\n• 서비스가 일시적으로 사용 불가능합니다.\n• 잠시 후 다시 시도하세요.",
        "DEADLINE_EXCEEDED": "⏱️ 요청 시간 초과\n\n• 이미지 생성에 너무 오래 걸렸습니다.\n• 네트워크 상태를 확인하고 다시 시도하세요.",
    }
    
    def __init__(self, original_error: Exception, context: str = ""):
        self.original_error = original_error
        self.context = context
        self.user_message = self._parse_error(original_error)
        super().__init__(self.user_message)
    
    def _parse_error(self, error: Exception) -> str:
        """오류를 분석하여 사용자 친화적 메시지 생성"""
        error_str = str(error).upper()
        
        # 알려진 오류 코드 확인
        for code, message in self.ERROR_MESSAGES.items():
            if code in error_str:
                return message
        
        # 네트워크 오류
        if "CONNECTION" in error_str or "TIMEOUT" in error_str or "NETWORK" in error_str:
            return "🌐 네트워크 오류\n\n• 인터넷 연결을 확인하세요.\n• 방화벽이나 프록시 설정을 확인하세요."
        
        # API 키 관련
        if "API" in error_str and "KEY" in error_str:
            return "🔑 API 키 오류\n\n• API 키를 확인하세요.\n• 설정에서 올바른 API 키를 입력했는지 확인하세요."
        
        # 기본 메시지
        return f"❌ 오류 발생\n\n{self.context}\n\n상세: {str(error)[:200]}"
    
    def get_technical_details(self) -> str:
        """기술적 세부 정보 반환"""
        return f"Type: {type(self.original_error).__name__}\nMessage: {str(self.original_error)}\nTraceback: {traceback.format_exc()}"


class ImageGenerator:
    """AI 이미지 생성기"""
    
    # 지원 이미지 포맷
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.webp'}
    
    # Imagen API 지원 비율
    SUPPORTED_ASPECT_RATIOS = ["1:1", "3:4", "4:3", "9:16", "16:9"]
    
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
        
        # 사용 가능한 캐릭터 목록 캐시
        self._character_names = None
    
    def get_available_characters(self) -> List[str]:
        """
        사용 가능한 캐릭터 이름(prefix) 목록 반환
        
        Returns:
            캐릭터 이름 리스트 (예: ['JB', 'TOTO', '제이비'])
        """
        if self._character_names is not None:
            return self._character_names
        
        char_dir = self.config.paths.character_dir
        if not char_dir.exists():
            self._character_names = []
            return []
        
        # 파일명에서 prefix 추출 (숫자 제거)
        prefixes = set()
        for f in char_dir.iterdir():
            if f.suffix.lower() in self.SUPPORTED_FORMATS:
                # 파일명에서 숫자 제거하여 캐릭터 이름 추출
                # NFC 정규화 적용 (macOS 파일명 호환)
                name = normalize_text(f.stem)
                prefix = ''.join(c for c in name if not c.isdigit()).strip('_- ')
                if prefix:
                    # 한글은 upper() 해도 그대로이므로 원본 유지
                    prefixes.add(prefix)
        
        self._character_names = sorted(prefixes)
        return self._character_names
    
    def detect_character_from_prompt(self, prompt: str) -> Optional[str]:
        """
        프롬프트에서 캐릭터 이름 감지 (단일 - 하위 호환용)
        
        Args:
            prompt: 사용자 입력 프롬프트
            
        Returns:
            감지된 캐릭터 이름 또는 None
        """
        characters = self.detect_characters_from_prompt(prompt)
        return characters[0] if characters else None
    
    def detect_characters_from_prompt(self, prompt: str) -> List[str]:
        """
        프롬프트에서 여러 캐릭터 이름 감지
        
        Args:
            prompt: 사용자 입력 프롬프트
            
        Returns:
            감지된 캐릭터 이름 리스트 (등장 순서대로)
        """
        available = self.get_available_characters()
        # NFC 정규화 후 비교 (대소문자 무시)
        prompt_normalized = normalize_text(prompt).upper()
        
        detected = []
        for char_name in available:
            char_upper = char_name.upper()
            if char_upper in prompt_normalized:
                # 등장 위치 기록
                pos = prompt_normalized.find(char_upper)
                detected.append((pos, char_name))
        
        # 등장 순서대로 정렬
        detected.sort(key=lambda x: x[0])
        return [name for _, name in detected]
    
    def remove_character_name_from_prompt(self, prompt: str, character_name: str) -> str:
        """
        프롬프트에서 단일 캐릭터 이름 제거 (하위 호환용)
        """
        return self.remove_character_names_from_prompt(prompt, [character_name])
    
    def remove_character_names_from_prompt(self, prompt: str, character_names: List[str]) -> str:
        """
        프롬프트에서 여러 캐릭터 이름 제거
        
        Args:
            prompt: 원본 프롬프트
            character_names: 제거할 캐릭터 이름 리스트
            
        Returns:
            캐릭터 이름이 제거된 프롬프트
        """
        import re
        
        result = prompt
        for character_name in character_names:
            # 대소문자 무시하고 캐릭터 이름 + 조사 패턴 제거
            # 예: "JB가", "JB는", "JB를", "JB의", "JB와", "JB ", "jb가" 등
            patterns = [
                rf'\b{character_name}[가는을를의이와과랑]?\s*',
                rf'\b{character_name.lower()}[가는을를의이와과랑]?\s*',
                rf'\b{character_name.upper()}[가는을를의이와과랑]?\s*',
            ]
            
            for pattern in patterns:
                result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        
        # 앞뒤 공백 정리
        result = ' '.join(result.split())
        
        return result if result else prompt
    
    def analyze_aspect_ratio(self, images: List[Image.Image]) -> Tuple[str, float]:
        """
        참조 이미지들의 비율을 분석하여 최적의 aspect_ratio 결정
        
        Args:
            images: 참조 이미지 리스트
            
        Returns:
            (aspect_ratio 문자열, 실제 비율값) 튜플
        """
        if not images:
            return "1:1", 1.0
        
        # 모든 이미지의 비율 평균 계산
        ratios = []
        for img in images:
            w, h = img.size
            ratios.append(w / h)
        
        avg_ratio = sum(ratios) / len(ratios)
        
        # 지원되는 비율 중 가장 가까운 것 선택
        ratio_map = {
            "1:1": 1.0,
            "4:3": 4/3,      # 1.333
            "3:4": 3/4,      # 0.75
            "16:9": 16/9,    # 1.778
            "9:16": 9/16,    # 0.5625
        }
        
        best_ratio = "1:1"
        min_diff = float('inf')
        
        for ratio_str, ratio_val in ratio_map.items():
            diff = abs(avg_ratio - ratio_val)
            if diff < min_diff:
                min_diff = diff
                best_ratio = ratio_str
        
        print(f"📐 참조 이미지 비율 분석:")
        print(f"   평균 비율: {avg_ratio:.3f} (가로/세로)")
        print(f"   선택된 비율: {best_ratio}")
        
        return best_ratio, avg_ratio
    
    def load_reference_images(self, character_name: Optional[str] = None) -> List[Image.Image]:
        """
        참조 캐릭터 이미지 로드 (단일 캐릭터 - 하위 호환용)
        """
        if character_name:
            return self.load_reference_images_multi([character_name])
        return self.load_reference_images_multi([])
    
    def load_reference_images_multi(self, character_names: List[str]) -> List[Image.Image]:
        """
        여러 캐릭터의 참조 이미지 로드 (단순 리스트 반환 - 하위 호환)
        """
        char_images = self.load_reference_images_grouped(character_names)
        # 모든 캐릭터 이미지를 하나의 리스트로 합침
        all_images = []
        for images in char_images.values():
            all_images.extend(images)
        return all_images
    
    def load_reference_images_grouped(self, character_names: List[str]) -> dict:
        """
        여러 캐릭터의 참조 이미지를 캐릭터별로 그룹화해서 로드
        
        Args:
            character_names: 캐릭터 이름 리스트
        
        Returns:
            {캐릭터명: [이미지 리스트]} 딕셔너리
        """
        char_images = {}
        char_dir = self.config.paths.character_dir
        
        if not char_dir.exists():
            print(f"⚠️ 캐릭터 디렉토리가 없습니다: {char_dir}")
            return char_images
        
        # 이미지 파일 필터링 (NFC 정규화된 파일명과 함께 저장)
        all_image_files = sorted([
            (f, normalize_text(f.stem).upper())
            for f in char_dir.iterdir() 
            if f.suffix.lower() in self.SUPPORTED_FORMATS
        ], key=lambda x: x[1])
        
        # 캐릭터별 이미지 로드
        max_per_char = self.config.api.max_reference_images
        
        for char_name in character_names:
            char_upper = char_name.upper()
            char_files = [
                f for f, normalized_stem in all_image_files 
                if normalized_stem.startswith(char_upper)
            ]
            
            if char_files:
                print(f"🎭 캐릭터 '{char_name}' - {len(char_files)}개 이미지")
                images = []
                for img_path in char_files[:max_per_char]:
                    try:
                        img = Image.open(img_path)
                        images.append(img)
                        print(f"   ✓ {img_path.name}")
                    except Exception as e:
                        print(f"   ⚠️ 로드 실패 ({img_path.name}): {e}")
                
                if images:
                    char_images[char_name] = images
        
        return char_images
    
    def get_character_image_count(self, character_name: str) -> int:
        """특정 캐릭터의 참조 이미지 개수 반환"""
        char_dir = self.config.paths.character_dir
        if not char_dir.exists():
            return 0
        
        char_upper = character_name.upper()
        count = sum(
            1 for f in char_dir.iterdir()
            if f.suffix.lower() in self.SUPPORTED_FORMATS
            and normalize_text(f.stem).upper().startswith(char_upper)
        )
        return count
    
    def generate(
        self, 
        prompt: str,
        reference_images: Optional[List[Image.Image]] = None,
        negative_prompt: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        character_images: Optional[dict] = None,
        text_style_image: Optional[Image.Image] = None
    ) -> Optional[Image.Image]:
        """
        이미지 생성
        
        Args:
            prompt: 생성 프롬프트
            reference_images: 참조 이미지 리스트 (단일 캐릭터용, 하위 호환)
            negative_prompt: 네거티브 프롬프트
            aspect_ratio: 가로세로 비율 (예: "1:1", "4:3")
            character_images: {캐릭터명: [이미지 리스트]} (여러 캐릭터용)
            text_style_image: 텍스트 스타일 참조 이미지
            
        Returns:
            생성된 PIL Image 또는 None
            
        Raises:
            ImageGenerationError: 이미지 생성 실패 시
        """
        try:
            # 참조 이미지가 있으면 비율 분석
            all_ref_images = reference_images or []
            if character_images:
                for imgs in character_images.values():
                    all_ref_images.extend(imgs)
            
            if all_ref_images and not aspect_ratio:
                aspect_ratio, _ = self.analyze_aspect_ratio(all_ref_images)
            
            # 기본값
            if not aspect_ratio:
                aspect_ratio = "1:1"
            
            # Gemini 이미지 모델인지 Imagen인지 확인
            is_gemini = "gemini" in self.image_model.lower()
            
            if is_gemini:
                return self._generate_with_gemini(prompt, reference_images, aspect_ratio, character_images, text_style_image)
            else:
                return self._generate_with_imagen(prompt, aspect_ratio)
                
        except ImageGenerationError:
            raise  # 이미 처리된 오류는 그대로 전달
        except Exception as e:
            print(f"❌ 이미지 생성 실패: {e}")
            print(f"   상세: {traceback.format_exc()}")
            raise ImageGenerationError(e, context="이미지 생성 중 오류가 발생했습니다.")
    
    def _generate_with_gemini(
        self, 
        prompt: str, 
        reference_images: Optional[List[Image.Image]] = None,
        aspect_ratio: str = "1:1",
        character_images: Optional[dict] = None,
        text_style_image: Optional[Image.Image] = None
    ) -> Optional[Image.Image]:
        """Gemini 모델로 이미지 생성"""
        print(f"🎨 이미지 생성 중 ({self.image_model}, 비율: {aspect_ratio})...")
        
        # 컨텐츠 구성
        contents = []
        
        # 여러 캐릭터 모드
        if character_images and len(character_images) > 0:
            char_descriptions = []
            img_index = 1
            
            for char_name, images in character_images.items():
                start_idx = img_index
                for img in images:
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    img_bytes = img_byte_arr.getvalue()
                    contents.append(types.Part.from_bytes(
                        data=img_bytes,
                        mime_type="image/png"
                    ))
                    img_index += 1
                end_idx = img_index - 1
                
                if start_idx == end_idx:
                    char_descriptions.append(f"- **{char_name}**: Image {start_idx}")
                else:
                    char_descriptions.append(f"- **{char_name}**: Images {start_idx}-{end_idx}")
            
            char_list = "\n".join(char_descriptions)
            char_names = ", ".join(character_images.keys())
            
            full_prompt = f"""The images above show reference images for multiple characters:
{char_list}

Generate a NEW image based on this request:
{prompt}

CRITICAL RULES - MUST FOLLOW STRICTLY:
1. MULTIPLE CHARACTERS: The image MUST include ALL mentioned characters ({char_names}). Each character must be clearly visible and identifiable.
2. CHARACTER IDENTITY: Each character must look EXACTLY like their reference images. Do NOT mix up characters - {char_names} are DIFFERENT characters.
3. ASPECT RATIO: Generate with {aspect_ratio} aspect ratio.
4. CHARACTER COLORS: STRICTLY preserve the EXACT original colors of EACH character. Do NOT change any colors.
5. CHARACTER PROPORTIONS: Maintain proportions for each character as shown in their references.
6. INTERACTION: Characters should interact naturally as described in the prompt.
7. TEXT: NEVER add any text unless explicitly requested.
8. QUALITY: High-quality, clean image.

IMPORTANT: ALL characters ({char_names}) must appear in the final image together!"""
        
        # 단일 캐릭터 모드 (하위 호환)
        elif reference_images:
            for ref_img in reference_images:
                img_byte_arr = io.BytesIO()
                ref_img.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                contents.append(types.Part.from_bytes(
                    data=img_bytes,
                    mime_type="image/png"
                ))
            
            full_prompt = f"""Based on the reference character images above, generate a new image:

{prompt}

CRITICAL RULES - MUST FOLLOW STRICTLY:
1. ASPECT RATIO: Generate the image with {aspect_ratio} aspect ratio.
2. CHARACTER COLORS: STRICTLY preserve the EXACT original colors of the character.
3. CHARACTER PROPORTIONS: Maintain the exact same proportions as in the reference.
4. CHARACTER DESIGN: Maintain the exact same design, facial features, and style.
5. TEXT: NEVER add any text unless explicitly requested.
6. QUALITY: High-quality, clean image.

IMPORTANT: The character's original colors and proportions are sacred."""
        else:
            full_prompt = f"""Generate an image: {prompt}

OUTPUT FORMAT:
- Aspect ratio: {aspect_ratio}

CRITICAL RULES:
- Generate as a high-quality image with {aspect_ratio} aspect ratio
- NEVER add any text, letters, numbers, words, or watermarks UNLESS explicitly requested with exact text in quotes
- Keep the image clean and text-free by default"""
        
        # 텍스트 스타일 참조 이미지 처리
        if text_style_image:
            img_byte_arr = io.BytesIO()
            text_style_image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            contents.append(types.Part.from_bytes(
                data=img_bytes,
                mime_type="image/png"
            ))
            
            # 프롬프트에 텍스트 스타일 지시 추가
            full_prompt += f"""

TEXT STYLE REFERENCE:
The image above shows the reference style for any text to be added.
If the prompt includes text to insert (in quotes), render that text using the SAME visual style, font style, and artistic treatment as shown in the text style reference image.
Match the text style exactly: color scheme, font characteristics, decorative elements, and overall aesthetic."""
            print("   📝 텍스트 스타일 참조 이미지 포함")
        
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
    
    def _generate_with_imagen(self, prompt: str, aspect_ratio: str = "1:1") -> Optional[Image.Image]:
        """Imagen 모델로 이미지 생성 (유료)"""
        print(f"🎨 이미지 생성 중 ({self.image_model}, 비율: {aspect_ratio})...")
        
        # 지원되는 비율인지 확인
        if aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
            print(f"⚠️ 비율 {aspect_ratio}은 지원되지 않음. 1:1로 대체")
            aspect_ratio = "1:1"
        
        response = self.client.models.generate_images(
            model=self.image_model,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
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
    
    def post_process(self, image: Image.Image, preserve_ratio: bool = True) -> Image.Image:
        """
        이미지 후처리 (비율 유지)
        
        Args:
            image: 원본 이미지
            preserve_ratio: 원본 비율 유지 여부 (기본: True)
            
        Returns:
            처리된 이미지
        """
        target_width = self.config.output.width
        target_height = self.config.output.height
        
        if preserve_ratio:
            # 비율 유지하면서 리사이즈 (fit within bounds)
            original_width, original_height = image.size
            original_ratio = original_width / original_height
            target_ratio = target_width / target_height
            
            if original_ratio > target_ratio:
                # 원본이 더 넓음 → 너비 기준
                new_width = target_width
                new_height = int(target_width / original_ratio)
            else:
                # 원본이 더 높음 → 높이 기준
                new_height = target_height
                new_width = int(target_height * original_ratio)
            
            if image.size != (new_width, new_height):
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"📐 비율 유지 리사이즈: {original_width}x{original_height} → {new_width}x{new_height}")
        else:
            # 강제 리사이즈 (비율 무시)
            target_size = (target_width, target_height)
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
        name_hint: str = "",
        character_images: Optional[dict] = None,
        text_style_image: Optional[Image.Image] = None
    ) -> Tuple[Optional[Image.Image], Optional[Path]]:
        """
        이미지 생성 + 후처리 + 저장 통합 메서드
        
        Args:
            prompt: 생성 프롬프트
            reference_images: 참조 이미지 리스트 (단일 캐릭터)
            negative_prompt: 네거티브 프롬프트
            name_hint: 파일명 힌트
            character_images: {캐릭터명: [이미지]} (여러 캐릭터)
            text_style_image: 텍스트 스타일 참조 이미지
        
        Returns:
            (이미지, 파일경로) 튜플
        """
        # 생성
        image = self.generate(
            prompt, 
            reference_images, 
            negative_prompt,
            character_images=character_images,
            text_style_image=text_style_image
        )
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
