"""
Prompt Enhancer Module
LLM을 사용하여 간단한 키워드를 정교한 영어 프롬프트로 확장
"""
from google import genai
from google.genai import types
from typing import Optional


class PromptEnhancer:
    """LLM 기반 프롬프트 향상기"""
    
    ENHANCE_SYSTEM_PROMPT = """You are an expert AI image generation prompt engineer.
Your task is to transform simple Korean keywords or phrases into detailed, effective English prompts for image generation.

Guidelines:
1. Translate Korean to natural English
2. Add specific details about pose, expression, and composition
3. Keep the description concise but descriptive (1-2 sentences max)
4. Focus on visual elements that can be rendered
5. Do NOT include color specifications (colors will be added separately)
6. Do NOT include style keywords like "3D" or "rendering" (added separately)

Examples:
- Input: "선물 상자를 든 모습"
  Output: "holding a gift box with both hands, cheerful expression, looking at the viewer"

- Input: "계산기"
  Output: "holding a calculator, pointing at the screen, explaining pose, friendly smile"

- Input: "점프하는 포즈"
  Output: "jumping pose with arms raised, excited expression, dynamic action pose"

Respond with ONLY the enhanced English prompt, nothing else."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        """
        Args:
            api_key: Google API 키
            model: 사용할 LLM 모델
        """
        self.client = genai.Client(api_key=api_key)
        self.model = model
    
    def enhance(self, simple_prompt: str) -> str:
        """
        간단한 프롬프트를 상세한 영어 프롬프트로 변환
        
        Args:
            simple_prompt: 간단한 한국어/영어 키워드
            
        Returns:
            향상된 영어 프롬프트
        """
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"{self.ENHANCE_SYSTEM_PROMPT}\n\nInput: {simple_prompt}\nOutput:",
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=200,
                )
            )
            
            enhanced = response.text.strip()
            # 불필요한 접두사 제거
            if enhanced.lower().startswith("output:"):
                enhanced = enhanced[7:].strip()
            
            return enhanced
            
        except Exception as e:
            print(f"⚠️ 프롬프트 향상 실패, 원본 사용: {e}")
            return simple_prompt
    
    def enhance_with_context(
        self, 
        simple_prompt: str, 
        character_description: Optional[str] = None
    ) -> str:
        """
        캐릭터 컨텍스트를 포함한 프롬프트 향상
        
        Args:
            simple_prompt: 간단한 키워드
            character_description: 캐릭터 설명 (선택)
            
        Returns:
            향상된 프롬프트
        """
        context = ""
        if character_description:
            context = f"\nCharacter context: {character_description}\n"
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"{self.ENHANCE_SYSTEM_PROMPT}{context}\n\nInput: {simple_prompt}\nOutput:",
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=200,
                )
            )
            
            enhanced = response.text.strip()
            if enhanced.lower().startswith("output:"):
                enhanced = enhanced[7:].strip()
            
            return enhanced
            
        except Exception as e:
            print(f"⚠️ 프롬프트 향상 실패, 원본 사용: {e}")
            return simple_prompt


def create_enhancer(api_key: str) -> PromptEnhancer:
    """프롬프트 향상기 생성 헬퍼"""
    return PromptEnhancer(api_key)
