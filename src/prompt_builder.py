"""
Prompt Builder Module
고정 프롬프트와 변동 프롬프트를 결합하여 최종 프롬프트 생성
"""
from dataclasses import dataclass
from typing import Optional
from .config_loader import Config


@dataclass
class PromptVariables:
    """변동 프롬프트 변수"""
    object: Optional[str] = None
    pose: Optional[str] = None
    background: Optional[str] = None
    custom: Optional[str] = None  # 사용자 정의 자유 텍스트


class PromptBuilder:
    """프롬프트 빌더 - 고정 + 변동 프롬프트 결합"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def _replace_color_variables(self, text: str) -> str:
        """색상 변수를 실제 값으로 치환"""
        text = text.replace("{MAIN_COLOR}", self.config.brand.main_color)
        text = text.replace("{SUB_COLOR}", self.config.brand.sub_color)
        return text
    
    def build(
        self, 
        enhanced_prompt: str,
        variables: Optional[PromptVariables] = None
    ) -> str:
        """
        최종 프롬프트 생성
        
        구조: {고정 prefix} + {변동 프롬프트} + {고정 suffix}
        
        Args:
            enhanced_prompt: LLM으로 향상된 프롬프트
            variables: 추가 변동 변수 (선택)
            
        Returns:
            완성된 프롬프트 문자열
        """
        # 고정 프롬프트에 색상 변수 적용
        prefix = self._replace_color_variables(self.config.prompts.fixed_prefix)
        suffix = self._replace_color_variables(self.config.prompts.fixed_suffix)
        
        # 변동 부분 조합
        variable_parts = [enhanced_prompt]
        
        if variables:
            if variables.object:
                variable_parts.append(f"with {variables.object}")
            if variables.pose:
                variable_parts.append(f"{variables.pose} pose")
            if variables.background:
                variable_parts.append(f"on {variables.background} background")
            if variables.custom:
                variable_parts.append(variables.custom)
        
        variable_prompt = ", ".join(variable_parts)
        
        # 최종 결합
        final_prompt = f"{prefix} {variable_prompt}{suffix}"
        
        return final_prompt
    
    def build_simple(self, user_input: str) -> str:
        """
        간단한 빌드 - 사용자 입력만으로 프롬프트 생성
        
        Args:
            user_input: 사용자가 입력한 텍스트 (향상된 상태)
            
        Returns:
            완성된 프롬프트
        """
        return self.build(user_input)
    
    def get_negative_prompt(self) -> str:
        """네거티브 프롬프트 반환"""
        return self.config.prompts.negative
    
    def preview(self, enhanced_prompt: str, variables: Optional[PromptVariables] = None) -> dict:
        """
        프롬프트 미리보기 (디버깅용)
        
        Returns:
            프롬프트 구성요소 딕셔너리
        """
        final = self.build(enhanced_prompt, variables)
        return {
            "prefix": self._replace_color_variables(self.config.prompts.fixed_prefix),
            "variable": enhanced_prompt,
            "suffix": self._replace_color_variables(self.config.prompts.fixed_suffix),
            "final": final,
            "negative": self.get_negative_prompt()
        }


def create_builder(config: Config) -> PromptBuilder:
    """프롬프트 빌더 생성 헬퍼"""
    return PromptBuilder(config)
