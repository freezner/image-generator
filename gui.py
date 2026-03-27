#!/usr/bin/env python3
"""
JB Bank AI Image Generator - GUI Application
Flet 기반 크로스 플랫폼 GUI (Mac/Windows/Linux)
"""
import os
import sys
import json
import threading
import subprocess
import platform
from pathlib import Path
from typing import Optional

import flet as ft

# 앱 기본 설정
APP_NAME = "JB Bank AI Image Generator"
APP_VERSION = "0.0.2"
CONFIG_FILE = "config.json"
ENV_FILE = ".env"


class ImageGeneratorApp:
    """메인 애플리케이션"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = f"{APP_NAME} v{APP_VERSION}"
        self.page.window.width = 700
        self.page.window.height = 600
        self.page.window.min_width = 600
        self.page.window.min_height = 500
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.page.padding = 16
        
        # 상태 변수
        self.is_generating = False
        self.generator = None
        self.enhancer = None
        self.builder = None
        self.config = None
        self.character_scales = {}  # 캐릭터별 크기 가중치 저장
        
        # UI 컴포넌트
        self._create_ui()
        
        # 컴포넌트 초기화
        self._initialize_components()
        
        # 3초 후에도 로딩 중이면 자동 갱신
        def auto_refresh():
            import time
            time.sleep(3)
            if "로딩 중" in self.character_text.value:
                self._refresh_characters(None)
        
        threading.Thread(target=auto_refresh, daemon=True).start()
    
    def _create_ui(self):
        """UI 생성"""
        # 헤더
        logo_path = Path("resources/logo.png")
        logo_src = str(logo_path) if logo_path.exists() else None
        
        header = ft.Row(
            controls=[
                ft.Row([
                    ft.Image(
                        src=logo_src if logo_src else None,
                        width=40,
                        height=40,
                        fit="contain",
                    ) if logo_src else ft.Container(),
                    ft.Container(width=12) if logo_src else ft.Container(),
                    ft.Column([
                        ft.Text(
                            "JB Bank AI Image Generator",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            f"v{APP_VERSION}",
                            size=11,
                            color=ft.Colors.GREY_500,
                        ),
                    ], spacing=0, alignment=ft.CrossAxisAlignment.START),
                ], spacing=0),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS,
                    tooltip="설정",
                    icon_size=20,
                    on_click=self._open_settings,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        # 캐릭터 정보
        self.character_text = ft.Text(
            "🎭 등록된 캐릭터: 로딩 중...",
            size=13,
        )
        
        self.character_chips = ft.Row(
            controls=[],
            spacing=4,
            wrap=True,
        )
        
        self.open_assets_btn = ft.TextButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ADD_PHOTO_ALTERNATE, size=14),
                    ft.Text("캐릭터 추가", size=11),
                ],
                tight=True,
                spacing=2,
            ),
            on_click=self._open_assets_folder,
            tooltip="캐릭터 폴더 열기 (이미지 추가)",
        )
        
        self.refresh_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            icon_size=16,
            tooltip="캐릭터 목록 새로고침",
            on_click=self._refresh_characters,
        )
        
        self.character_row = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.character_text,
                        ft.Container(expand=True),
                        self.open_assets_btn,
                        self.refresh_btn,
                    ],
                    spacing=4,
                ),
                self.character_chips,
            ],
            spacing=4,
        )
        
        # 프롬프트 입력 - 캐릭터 설명
        self.character_prompt = ft.TextField(
            label="🎭 캐릭터 동작/표정",
            hint_text="예: JB가 선물 상자를 들고 웃고 있는 모습",
            multiline=True,
            min_lines=2,
            max_lines=3,
            expand=True,
            text_size=13,
        )
        
        # 프롬프트 입력 - 배경
        self.background_prompt = ft.TextField(
            label="🖼️ 배경 설정",
            hint_text="예: 투명 배경 / 파란 하늘과 구름 / 사무실 내부 / 단색 흰 배경",
            multiline=True,
            min_lines=2,
            max_lines=3,
            expand=True,
            text_size=13,
        )
        
        # 설정값 (설정 화면에서 변경)
        self.enhance_enabled = True
        self.image_count_value = "1"
        
        # 버튼
        self.generate_btn = ft.Button(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.AUTO_AWESOME, size=18),
                    ft.Text("이미지 생성", size=14, weight=ft.FontWeight.W_500),
                ],
                tight=True,
                spacing=6,
            ),
            on_click=self._start_generation,
            style=ft.ButtonStyle(
                padding=ft.Padding(left=24, top=12, right=24, bottom=12),
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
            ),
        )
        
        self.open_folder_btn = ft.OutlinedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN, size=16),
                    ft.Text("결과 폴더", size=13),
                ],
                tight=True,
                spacing=4,
            ),
            on_click=self._open_output_folder,
        )
        
        # 프로그레스
        self.progress_bar = ft.ProgressBar(
            value=0,
            visible=False,
        )
        
        self.status_text = ft.Text(
            "준비됨",
            size=11,
            color=ft.Colors.GREY_600,
        )
        
        # 로그 출력
        self.log_output = ft.TextField(
            label="📋 로그",
            multiline=True,
            read_only=True,
            min_lines=6,
            max_lines=8,
            expand=True,
            text_size=11,
        )
        
        # 레이아웃 구성 - 밀도 높게
        self.page.add(
            header,
            ft.Divider(height=1),
            self.character_row,
            ft.Container(height=6),
            self.character_prompt,
            ft.Container(height=4),
            self.background_prompt,
            ft.Container(height=6),
            ft.Row(
                controls=[
                    self.generate_btn,
                    self.open_folder_btn,
                    ft.Container(expand=True),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Container(height=4),
            self.progress_bar,
            self.status_text,
            ft.Container(height=4),
            self.log_output,
        )
    
    def _log(self, message: str):
        """로그 메시지 추가"""
        current = self.log_output.value or ""
        self.log_output.value = current + message + "\n"
        self.page.update()
    
    def _update_status(self, message: str, progress: float = None):
        """상태 업데이트"""
        self.status_text.value = message
        if progress is not None:
            self.progress_bar.value = progress
            self.progress_bar.visible = progress > 0
        self.page.update()
    
    def _initialize_components(self):
        """컴포넌트 초기화"""
        def init_thread():
            try:
                self._update_status("컴포넌트 초기화 중...", 0.1)
                self._log("⚙️ 컴포넌트 초기화 중...")
                
                # 작업 디렉토리 설정 및 로깅
                import os
                cwd = os.getcwd()
                self._log(f"   작업 디렉토리: {cwd}")
                
                if getattr(sys, 'frozen', False):
                    app_dir = Path(sys.executable).parent
                    os.chdir(app_dir)
                    self._log(f"   앱 디렉토리: {app_dir}")
                
                # src 모듈 임포트
                from src import load_config, create_enhancer, create_builder, create_generator
                
                # 설정 로드
                self.config = load_config(CONFIG_FILE)
                self._log(f"   브랜드: {self.config.brand.name}")
                
                # API 키 확인
                api_key = self.config.get_api_key()
                self._log(f"   API 키: {'설정됨 (' + api_key[:8] + '...)' if api_key else '없음'}")
                if not api_key:
                    self._log("⚠️ API 키가 설정되지 않았습니다.")
                    self._log("   설정 창을 열어 API 키를 입력하세요.")
                    self._update_status("API 키 필요", 0)
                    # 설정 창 자동 열기
                    self.page.run_thread(lambda: self._open_settings(None))
                    return
                
                self._update_status("컴포넌트 초기화 중...", 0.3)
                
                # 컴포넌트 생성
                self.enhancer = create_enhancer(api_key)
                self.builder = create_builder(self.config)
                self.generator = create_generator(self.config, api_key)
                
                self._update_status("컴포넌트 초기화 중...", 0.7)
                
                # 캐릭터 목록 표시
                self._update_character_display()
                
                self._log("✅ 초기화 완료!")
                self._update_status("준비됨", 0)
                
            except FileNotFoundError as e:
                self._log(f"❌ 설정 파일 없음: {e}")
                self._update_status("설정 파일 필요", 0)
            except Exception as e:
                self._log(f"❌ 초기화 오류: {e}")
                self._update_status("오류 발생", 0)
        
        threading.Thread(target=init_thread, daemon=True).start()
    
    def _open_settings(self, e):
        """설정 다이얼로그 열기"""
        # 현재 설정 로드
        api_key = ""
        brand_name = ""
        main_color = ""
        sub_color = ""
        
        env_path = Path(ENV_FILE)
        if env_path.exists():
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break
        
        config_path = Path(CONFIG_FILE)
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
                brand = config.get("brand", {})
                brand_name = brand.get("name", "")
        
        # 입력 필드
        api_key_field = ft.TextField(
            label="Gemini API Key",
            value=api_key,
            password=True,
            can_reveal_password=True,
            expand=True,
        )
        
        brand_name_field = ft.TextField(
            label="브랜드 이름",
            value=brand_name,
            expand=True,
        )
        
        # 생성 옵션
        enhance_checkbox = ft.Checkbox(
            label="프롬프트 자동 최적화",
            value=self.enhance_enabled,
        )
        
        image_count_dropdown = ft.Dropdown(
            label="생성 개수",
            value=self.image_count_value,
            options=[
                ft.dropdown.Option("1", "1장"),
                ft.dropdown.Option("2", "2장"),
                ft.dropdown.Option("3", "3장"),
            ],
            width=120,
        )
        
        def save_settings(e):
            # API 키 저장
            new_api_key = api_key_field.value.strip()
            if new_api_key:
                with open(ENV_FILE, "w", encoding="utf-8") as f:
                    f.write(f"GEMINI_API_KEY={new_api_key}\n")
            
            # config.json 업데이트
            config_path = Path(CONFIG_FILE)
            if config_path.exists():
                with open(config_path, encoding="utf-8") as f:
                    config = json.load(f)
            else:
                config = {}
            
            if "brand" not in config:
                config["brand"] = {}
            
            new_brand = brand_name_field.value.strip()
            
            if new_brand:
                config["brand"]["name"] = new_brand
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # 생성 옵션 저장 (인스턴스 변수)
            self.enhance_enabled = enhance_checkbox.value
            self.image_count_value = image_count_dropdown.value
            
            dialog.open = False
            self.page.update()
            
            # 컴포넌트 재초기화
            self._log("\n🔄 설정 저장됨. 재초기화 중...")
            self._initialize_components()
        
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚙️ 설정"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("🔑 API 설정", weight=ft.FontWeight.BOLD),
                        api_key_field,
                        ft.Container(height=15),
                        ft.Text("🎨 브랜드 설정", weight=ft.FontWeight.BOLD),
                        brand_name_field,
                        ft.Container(height=15),
                        ft.Text("🖼️ 생성 옵션", weight=ft.FontWeight.BOLD),
                        image_count_dropdown,
                        enhance_checkbox,
                    ],
                    tight=True,
                    spacing=10,
                ),
                width=450,
                padding=10,
            ),
            actions=[
                ft.TextButton("취소", on_click=close_dialog),
                ft.FilledButton("저장", on_click=save_settings),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _open_output_folder(self, e):
        """결과 폴더 열기"""
        output_dir = Path("output")
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
        
        self._open_folder(output_dir)
    
    def _open_assets_folder(self, e):
        """캐릭터 폴더 열기"""
        assets_dir = Path("assets/character")
        if not assets_dir.exists():
            assets_dir.mkdir(parents=True)
        
        self._open_folder(assets_dir)
        self._log("📂 캐릭터 폴더를 열었습니다.")
        self._log("   이미지 추가 후 🔄 버튼을 눌러 새로고침하세요.")
    
    def _refresh_characters(self, e):
        """캐릭터 목록 새로고침"""
        if not self.generator:
            self._log("⚠️ 먼저 API 키를 설정하세요.")
            return
        
        self._log("🔄 캐릭터 목록 새로고침 중...")
        
        # 캐릭터 캐시 초기화
        self.generator._character_names = None
        
        # 캐릭터 목록 다시 로드
        self._update_character_display()
        
        self.page.update()
    
    def _update_character_display(self):
        """캐릭터 표시 업데이트"""
        if not self.generator:
            return
        
        available_chars = self.generator.get_available_characters()
        
        if available_chars:
            self.character_text.value = f"🎭 등록된 캐릭터 ({len(available_chars)}개):"
            
            # 캐릭터 칩 생성
            chips = []
            for char_name in available_chars:
                img_count = self.generator.get_character_image_count(char_name)
                scale = self.character_scales.get(char_name, 1.0)
                chip = ft.Chip(
                    label=ft.Text(f"{char_name} ({img_count}) ×{scale:.1f}", size=11),
                    bgcolor=ft.Colors.BLUE_50,
                    padding=ft.Padding(left=8, top=2, right=8, bottom=2),
                    on_click=lambda e, name=char_name: self._open_character_scale_dialog(name),
                )
                chips.append(chip)
            
            self.character_chips.controls = chips
            self.character_chips.visible = True
            self._log(f"✅ {len(available_chars)}개 캐릭터: {', '.join(available_chars)}")
        else:
            self.character_text.value = "🎭 등록된 캐릭터: 없음 (캐릭터 추가 버튼 클릭)"
            self.character_chips.controls = []
            self.character_chips.visible = False
            self._log("⚠️ 캐릭터를 찾을 수 없습니다. 캐릭터 폴더에 이미지를 추가하세요.")
        
        self.page.update()
    
    def _open_folder(self, folder_path: Path):
        """폴더 열기 (OS별)"""

    def _open_character_scale_dialog(self, char_name: str):
        """캐릭터 크기 설정 다이얼로그"""
        current_scale = self.character_scales.get(char_name, 1.0)

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        def save_scale(e):
            self.character_scales[char_name] = scale_slider.value
            dialog.open = False
            self.page.update()
            self._update_character_display()
            self._log(f"🎭 '{char_name}' 크기 설정: ×{scale_slider.value:.1f}")

        # 값 표시용 텍스트 (슬라이더 위에 표시)
        value_display = ft.Text(f"×{current_scale:.1f}", size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)

        def on_slider_change(e):
            # 슬라이더 값 변경 시 값 표시 업데이트
            value_display.value = f"×{scale_slider.value:.1f}"
            self.page.update()

        scale_slider = ft.Slider(
            min=0.5,
            max=2.0,
            value=current_scale,
            divisions=15,
            on_change=on_slider_change,
            width=300,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"🎭 {char_name} 크기 설정"),
            content=ft.Column([
                ft.Text("캐릭터 크기 가중치를 설정하세요.", size=12),
                ft.Text("1.0 = 기본 크기, 0.5 = 절반, 2.0 = 2배", size=11, color=ft.Colors.GREY_600),
                ft.Container(height=15),
                value_display,
                ft.Container(height=5),
                scale_slider,
            ], tight=True, spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton("취소", on_click=close_dialog),
                ft.FilledButton("저장", on_click=save_scale),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _open_folder(self, folder_path: Path):
        """폴다 열기 (OS별)"""
        system = platform.system()
        if system == "Darwin":
            subprocess.run(["open", str(folder_path)])
        elif system == "Windows":
            subprocess.run(["explorer", str(folder_path)])
        else:
            subprocess.run(["xdg-open", str(folder_path)])

    def _start_generation(self, e):
        """이미지 생성 시작"""
        if self.is_generating:
            return
        
        if not self.generator:
            self._show_error("컴포넌트가 초기화되지 않았습니다.\n설정에서 API 키를 확인하세요.")
            return
        
        # 프롬프트 가져오기
        char_prompt = self.character_prompt.value.strip() if self.character_prompt.value else ""
        bg_prompt = self.background_prompt.value.strip() if self.background_prompt.value else ""
        
        if not char_prompt:
            self._show_error("캐릭터 동작/표정을 입력하세요.")
            return
        
        # 프롬프트 합치기
        if bg_prompt:
            prompt = f"{char_prompt}. 배경: {bg_prompt}"
        else:
            prompt = char_prompt
        
        self.is_generating = True
        self.generate_btn.disabled = True
        self.generate_btn.content.controls[1].value = "생성 중..."
        self.page.update()
        
        def generate_thread():
            try:
                # 생성 개수
                num_images = int(self.image_count_value)
                
                self._update_status("캐릭터 감지 중...", 0.1)
                self._log(f"\n📝 캐릭터: {char_prompt}")
                if bg_prompt:
                    self._log(f"🖼️ 배경: {bg_prompt}")
                self._log(f"🔢 생성 개수: {num_images}장")
                
                # 여러 캐릭터 감지
                detected_chars = self.generator.detect_characters_from_prompt(prompt)
                
                # 캐릭터별 이미지 그룹화
                character_images = {}
                if detected_chars:
                    character_images = self.generator.load_reference_images_grouped(detected_chars)
                
                # 총 참조 이미지 수 계산
                total_ref_images = sum(len(imgs) for imgs in character_images.values())
                
                # 프롬프트 정제
                clean_prompt = prompt
                if detected_chars:
                    clean_prompt = self.generator.remove_character_names_from_prompt(prompt, detected_chars)
                    self._log(f"🎭 캐릭터 감지: {', '.join(detected_chars)}")
                    for char_name, imgs in character_images.items():
                        self._log(f"   • {char_name}: {len(imgs)}개 참조 이미지")
                    self._log(f"   총 참조 이미지: {total_ref_images}개")
                
                self._update_status("프롬프트 최적화 중...", 0.2)
                
                # 프롬프트 향상
                if self.enhance_enabled:
                    self._log("🔄 프롬프트 최적화 중...")
                    enhanced = self.enhancer.enhance(clean_prompt)
                    self._log(f"   → {enhanced[:50]}...")
                else:
                    enhanced = clean_prompt
                
                # === 프롬프트 강화 ===
                
                # 1. 캐릭터별 속성 추출 (프롬프트에서 각 캐릭터의 특징 파싱)
                char_attributes = {}
                for char_name in detected_chars:
                    # 캐릭터 이름 앞뒤의 단어들을 속성으로 추정
                    import re
                    pattern = rf"(\w+)\s*{re.escape(char_name)}|\s*{re.escape(char_name)}\s*(\w+)"
                    matches = re.findall(pattern, clean_prompt, re.IGNORECASE)
                    attrs = []
                    for m in matches:
                        for word in m:
                            if word and len(word) > 1:
                                attrs.append(word)
                    if attrs:
                        char_attributes[char_name] = attrs
                
                # 2. 각 캐릭터별 고유 속성 프롬프트 생성
                char_specific_prompts = []
                size_constraints = []  # 크기 강제 규칙 별도 수집
                
                for char_name in detected_chars:
                    attrs = char_attributes.get(char_name, [])
                    attr_text = ", ".join(attrs) if attrs else "default appearance"
                    
                    # 크기 가중치 적용 - 더 강제적인 표현
                    scale = self.character_scales.get(char_name, 1.0)
                    scale_text = ""
                    if scale != 1.0:
                        if scale < 1.0:
                            scale_text = f" (small {scale:.1f}x)"
                            size_constraints.append(f"{char_name} height must be exactly {int(scale*100)}% of normal")
                        else:
                            scale_text = f" (large {scale:.1f}x)"
                            size_constraints.append(f"{char_name} height must be exactly {int(scale*100)}% of normal")
                    
                    char_specific_prompts.append(f"{char_name}: {attr_text}{scale_text}")
                
                # 2.5 크기 강제 규칙을 별도로 추가
                size_rule = ""
                if size_constraints:
                    size_rule = "STRICT SIZE RULE: " + "; ".join(size_constraints) + ". "
                    self._log(f"📏 강제 크기: {'; '.join(size_constraints)}")
                
                # 3. 최종 프롬프트 조립
                has_char_ref = bool(character_images)
                base_prompt = self.builder.build_simple(enhanced, has_character_reference=has_char_ref)
                
                # 캐릭터별 속성을 명확히 분리 + 크기 강제 규칙 추가
                char_rules = " | ".join(char_specific_prompts)
                final_prompt = f"{size_rule}CHARACTER RULES: {char_rules}. {base_prompt}"
                
                negative = self.builder.get_negative_prompt()

                # 4. 배경 설정 처리
                if bg_prompt:
                    # 배경 설정이 있는 경우 - 명시적으로 배경 지시
                    final_prompt = f"{final_prompt} BACKGROUND: {bg_prompt}."
                    self._log(f"🖼️ 배경: {bg_prompt}")
                else:
                    # 배경 설정이 없는 경우 투명 배경 강제 (Gemini 특화)
                    final_prompt = f"{final_prompt} ISOLATED SUBJECT. White background, no shadows, no ground, no environment."
                    negative = f"{negative}, colored background, gradient background, complex background, environment, scenery, ground, floor, shadows, lighting effects"
                    self._log("🫥 배경: 흰색/단순 (후처리 투명)")
                
                # 5. 크기 가중치가 없는 캐릭터도 명시적으로 1.0x 표시
                for char_name in detected_chars:
                    if char_name not in self.character_scales:
                        self._log(f"   • {char_name}: 기본 크기 (1.0x)")
                
                # 최종 프롬프트 로그 출력
                self._log(f"\n📝 최종 프롬프트:\n{final_prompt[:200]}...")
                self._log(f"🚫 네거티브 프롬프트:\n{negative[:150]}...")

                # 여러 이미지 생성
                generated_images = []  # (image, filepath) 리스트

                for i in range(num_images):
                    progress = 0.3 + (0.6 * i / num_images)
                    self._update_status(f"이미지 생성 중... ({i+1}/{num_images})", progress)
                    self._log(f"\n🎨 이미지 생성 중... ({i+1}/{num_images})")

                    try:
                        image, filepath = self.generator.generate_and_save(
                            prompt=final_prompt,
                            negative_prompt=negative,
                            name_hint=f"{prompt[:25]}_{i+1}",
                            character_images=character_images if character_images else None
                        )
                        if image and filepath:
                            generated_images.append((image, filepath))
                            self._log(f"   ✅ 저장: {filepath.name}")
                    except Exception as gen_err:
                        from src.image_generator import ImageGenerationError
                        
                        if isinstance(gen_err, ImageGenerationError):
                            self._log(f"❌ 생성 오류 ({i+1}/{num_images}):\n{gen_err.user_message}")
                            if i == 0:  # 첫 번째 이미지 실패 시 중단
                                self.page.run_thread(
                                    lambda: self._show_detailed_error(gen_err.user_message, gen_err.get_technical_details())
                                )
                                return
                        else:
                            self._log(f"❌ 생성 오류 ({i+1}/{num_images}): {gen_err}")
                            if i == 0:
                                raise gen_err
                
                self._update_status("완료!", 1.0)
                
                if generated_images:
                    self._log(f"✅ 총 {len(generated_images)}장 생성 완료!")
                    # 이미지 경로 리스트 전달
                    filepaths = [fp for _, fp in generated_images]
                    self.page.run_thread(
                        lambda: self._show_success_with_preview(filepaths)
                    )
                else:
                    self._log("❌ 이미지 생성 실패 (결과 없음)")
                    self.page.run_thread(
                        lambda: self._show_error("이미지 생성에 실패했습니다.\n로그를 확인하세요.")
                    )
                    
            except Exception as ex:
                import traceback
                self._log(f"❌ 오류: {type(ex).__name__}: {ex}")
                self._log(f"   상세: {traceback.format_exc()[:300]}")
                self.page.run_thread(lambda: self._show_error(str(ex)))
            finally:
                self.is_generating = False
                self.generate_btn.disabled = False
                self.generate_btn.content.controls[1].value = "이미지 생성"
                self.page.update()
                
                # 2초 후 상태 초기화
                import time
                time.sleep(2)
                self._update_status("준비됨", 0)
        
        threading.Thread(target=generate_thread, daemon=True).start()
    
    def _show_error(self, message: str):
        """에러 다이얼로그"""
        def close(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("❌ 오류"),
            content=ft.Text(message),
            actions=[ft.TextButton("확인", on_click=close)],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _show_detailed_error(self, user_message: str, technical_details: str = ""):
        """상세 에러 다이얼로그 (사용자 친화적 + 기술 정보)"""
        show_details = {"value": False}
        
        def close(e):
            dialog.open = False
            self.page.update()
        
        def toggle_details(e):
            show_details["value"] = not show_details["value"]
            details_container.visible = show_details["value"]
            toggle_btn.text = "기술 정보 숨기기" if show_details["value"] else "기술 정보 보기"
            self.page.update()
        
        def copy_details(e):
            self.page.set_clipboard(technical_details)
            self._log("📋 기술 정보가 클립보드에 복사되었습니다.")
        
        # 기술 정보 컨테이너
        details_container = ft.Container(
            content=ft.Column([
                ft.Divider(),
                ft.Text("🔧 기술 정보 (지원 요청 시 사용)", size=12, weight=ft.FontWeight.BOLD),
                ft.TextField(
                    value=technical_details,
                    multiline=True,
                    read_only=True,
                    min_lines=3,
                    max_lines=6,
                    text_size=10,
                ),
                ft.TextButton("복사", icon=ft.Icons.COPY, on_click=copy_details),
            ], tight=True, spacing=5),
            visible=False,
        )
        
        toggle_btn = ft.TextButton("기술 정보 보기", on_click=toggle_details)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠️ 이미지 생성 실패"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(user_message, selectable=True),
                    ft.Container(height=10),
                    toggle_btn,
                    details_container,
                ], tight=True, spacing=5),
                width=400,
                padding=10,
            ),
            actions=[ft.FilledButton("확인", on_click=close)],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _show_success(self, message: str):
        """성공 다이얼로그 (기본)"""
        def close(e):
            dialog.open = False
            self.page.update()
        
        def open_folder(e):
            dialog.open = False
            self._open_output_folder(None)
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("✅ 생성 완료"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("확인", on_click=close),
                ft.FilledButton("폴더 열기", on_click=open_folder),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _show_success_with_preview(self, filepaths: list):
        """성공 다이얼로그 + 이미지 미리보기 + 페이징"""
        import base64
        
        if not filepaths:
            self._show_success("이미지가 생성되었습니다.")
            return
        
        current_index = [0]
        
        def close(e):
            dialog.open = False
            self.page.update()
        
        def open_folder(e):
            dialog.open = False
            self._open_output_folder(None)
            self.page.update()
        
        def load_image(index: int):
            fp = filepaths[index]
            try:
                with open(fp, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode()
                return img_data, fp.name
            except Exception:
                return None, fp.name
        
        def update_preview():
            idx = current_index[0]
            img_data, filename = load_image(idx)
            if img_data:
                preview_image.src = f"data:image/png;base64,{img_data}"
                preview_image.visible = True
            else:
                preview_image.visible = False
            filename_text.value = filename
            page_indicator.value = f"{idx + 1} / {len(filepaths)}"
            prev_btn.disabled = (idx == 0)
            next_btn.disabled = (idx == len(filepaths) - 1)
            self.page.update()
        
        def go_prev(e):
            if current_index[0] > 0:
                current_index[0] -= 1
                update_preview()
        
        def go_next(e):
            if current_index[0] < len(filepaths) - 1:
                current_index[0] += 1
                update_preview()
        
        preview_image = ft.Image(src="", width=300, height=300, fit="contain", border_radius=0)
        filename_text = ft.Text(size=12, color=ft.Colors.GREY_700, text_align=ft.TextAlign.CENTER)
        page_indicator = ft.Text(size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY)
        
        prev_btn = ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="이전 이미지", on_click=go_prev)
        next_btn = ft.IconButton(icon=ft.Icons.ARROW_FORWARD, tooltip="다음 이미지", on_click=go_next)
        
        preview_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    prev_btn,
                    ft.Container(content=preview_image, alignment=ft.Alignment(0, 0), width=320, height=320),
                    next_btn,
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=8),
                filename_text,
                ft.Container(height=4),
                page_indicator,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10,
        )
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"{len(filepaths)}장 생성 완료"),
            content=ft.Container(content=preview_container, width=420),
            actions=[
                ft.TextButton("확인", on_click=close),
                ft.FilledButton("폴더 열기", on_click=open_folder),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        update_preview()
        self.page.update()


def main(page: ft.Page):
    """Flet 앱 진입점"""
    ImageGeneratorApp(page)


if __name__ == "__main__":
    ft.run(main)
