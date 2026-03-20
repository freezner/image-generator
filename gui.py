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
APP_VERSION = "1.0.0"
CONFIG_FILE = "config.json"
ENV_FILE = ".env"


class ImageGeneratorApp:
    """메인 애플리케이션"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = APP_NAME
        self.page.window.width = 900
        self.page.window.height = 700
        self.page.window.min_width = 700
        self.page.window.min_height = 500
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.page.padding = 20
        
        # 상태 변수
        self.is_generating = False
        self.generator = None
        self.enhancer = None
        self.builder = None
        self.config = None
        
        # UI 컴포넌트
        self._create_ui()
        
        # 컴포넌트 초기화
        self._initialize_components()
    
    def _create_ui(self):
        """UI 생성"""
        # 헤더
        header = ft.Row(
            controls=[
                ft.Text(
                    "🎨 JB Bank AI Image Generator",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS,
                    tooltip="설정",
                    on_click=self._open_settings,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        # 캐릭터 정보
        self.character_text = ft.Text(
            "🎭 등록된 캐릭터: 로딩 중...",
            size=14,
        )
        
        self.open_assets_btn = ft.TextButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN, size=16),
                    ft.Text("캐릭터 폴더 열기", size=12),
                ],
                tight=True,
                spacing=4,
            ),
            on_click=self._open_assets_folder,
            visible=False,  # 캐릭터 없을 때만 표시
        )
        
        self.refresh_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            icon_size=18,
            tooltip="캐릭터 목록 새로고침",
            on_click=self._refresh_characters,
        )
        
        self.character_row = ft.Row(
            controls=[
                self.character_text,
                self.open_assets_btn,
                self.refresh_btn,
            ],
            spacing=10,
        )
        
        # 프롬프트 입력
        self.prompt_field = ft.TextField(
            label="📝 이미지 설명 입력",
            hint_text="예: JB가 선물 상자를 들고 있는 모습",
            multiline=True,
            min_lines=3,
            max_lines=5,
            expand=True,
        )
        
        # 옵션
        self.enhance_checkbox = ft.Checkbox(
            label="프롬프트 자동 최적화",
            value=True,
        )
        
        # 버튼
        self.generate_btn = ft.Button(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.AUTO_AWESOME),
                    ft.Text("이미지 생성"),
                ],
                tight=True,
                spacing=8,
            ),
            on_click=self._start_generation,
            style=ft.ButtonStyle(
                padding=ft.Padding(left=30, top=15, right=30, bottom=15),
                bgcolor=ft.Colors.BLUE,
                color=ft.Colors.WHITE,
            ),
        )
        
        self.open_folder_btn = ft.OutlinedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN),
                    ft.Text("결과 폴더 열기"),
                ],
                tight=True,
                spacing=8,
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
            size=12,
            color=ft.Colors.GREY_700,
        )
        
        # 로그 출력
        self.log_output = ft.TextField(
            label="📋 로그",
            multiline=True,
            read_only=True,
            min_lines=8,
            max_lines=12,
            expand=True,
            text_size=12,
        )
        
        # 레이아웃 구성
        self.page.add(
            header,
            ft.Divider(),
            self.character_row,
            ft.Container(height=10),
            self.prompt_field,
            ft.Container(height=10),
            self.enhance_checkbox,
            ft.Container(height=10),
            ft.Row(
                controls=[
                    self.generate_btn,
                    self.open_folder_btn,
                ],
                spacing=10,
            ),
            ft.Container(height=10),
            self.progress_bar,
            self.status_text,
            ft.Container(height=10),
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
                
                # 작업 디렉토리 설정
                if getattr(sys, 'frozen', False):
                    app_dir = Path(sys.executable).parent
                    os.chdir(app_dir)
                
                # src 모듈 임포트
                from src import load_config, create_enhancer, create_builder, create_generator
                
                # 설정 로드
                self.config = load_config(CONFIG_FILE)
                self._log(f"   브랜드: {self.config.brand.name}")
                
                # API 키 확인
                api_key = self.config.get_api_key()
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
                available_chars = self.generator.get_available_characters()
                if available_chars:
                    self.character_text.value = f"🎭 등록된 캐릭터: {', '.join(available_chars)}"
                    self.open_assets_btn.visible = False
                else:
                    self.character_text.value = "🎭 등록된 캐릭터: 없음"
                    self.open_assets_btn.visible = True
                
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
                main_color = brand.get("main_color", "")
                sub_color = brand.get("sub_color", "")
        
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
        
        main_color_field = ft.TextField(
            label="메인 컬러 (예: #FF6B35)",
            value=main_color,
            width=200,
        )
        
        sub_color_field = ft.TextField(
            label="서브 컬러 (예: #004E89)",
            value=sub_color,
            width=200,
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
            new_main = main_color_field.value.strip()
            new_sub = sub_color_field.value.strip()
            
            if new_brand:
                config["brand"]["name"] = new_brand
            if new_main:
                config["brand"]["main_color"] = new_main
            if new_sub:
                config["brand"]["sub_color"] = new_sub
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
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
                        ft.Container(height=20),
                        ft.Text("🎨 브랜드 설정", weight=ft.FontWeight.BOLD),
                        brand_name_field,
                        ft.Row(
                            controls=[main_color_field, sub_color_field],
                            spacing=10,
                        ),
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
        available_chars = self.generator.get_available_characters()
        if available_chars:
            self.character_text.value = f"🎭 등록된 캐릭터: {', '.join(available_chars)}"
            self.open_assets_btn.visible = False
            self._log(f"✅ {len(available_chars)}개 캐릭터 발견: {', '.join(available_chars)}")
        else:
            self.character_text.value = "🎭 등록된 캐릭터: 없음"
            self.open_assets_btn.visible = True
            self._log("⚠️ 캐릭터를 찾을 수 없습니다.")
        
        self.page.update()
    
    def _open_folder(self, folder_path: Path):
        """폴더 열기 (OS별)"""
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
        
        prompt = self.prompt_field.value.strip() if self.prompt_field.value else ""
        if not prompt:
            self._show_error("이미지 설명을 입력하세요.")
            return
        
        self.is_generating = True
        self.generate_btn.disabled = True
        self.generate_btn.content.controls[1].value = "생성 중..."
        self.page.update()
        
        def generate_thread():
            try:
                self._update_status("캐릭터 감지 중...", 0.1)
                self._log(f"\n📝 입력: {prompt}")
                
                # 캐릭터 감지
                detected_char = self.generator.detect_character_from_prompt(prompt)
                reference_images = self.generator.load_reference_images(detected_char)
                
                # 프롬프트 정제
                clean_prompt = prompt
                if detected_char:
                    clean_prompt = self.generator.remove_character_name_from_prompt(prompt, detected_char)
                    self._log(f"🎭 캐릭터 감지: {detected_char}")
                    self._log(f"   참조 이미지: {len(reference_images)}개")
                
                self._update_status("프롬프트 최적화 중...", 0.3)
                
                # 프롬프트 향상
                if self.enhance_checkbox.value:
                    self._log("🔄 프롬프트 최적화 중...")
                    enhanced = self.enhancer.enhance(clean_prompt)
                    self._log(f"   → {enhanced[:50]}...")
                else:
                    enhanced = clean_prompt
                
                self._update_status("이미지 생성 중...", 0.5)
                
                # 최종 프롬프트 생성 (캐릭터 참조 시 색상 보존)
                has_char_ref = bool(reference_images)
                final_prompt = self.builder.build_simple(enhanced, has_character_reference=has_char_ref)
                negative = self.builder.get_negative_prompt()
                
                self._log("🎨 이미지 생성 중...")
                
                # 이미지 생성
                image, filepath = self.generator.generate_and_save(
                    prompt=final_prompt,
                    reference_images=reference_images,
                    negative_prompt=negative,
                    name_hint=prompt[:30]
                )
                
                self._update_status("완료!", 1.0)
                
                if image:
                    self._log(f"✅ 이미지 생성 완료: {filepath}")
                    self.page.run_thread(
                        lambda: self._show_success(f"이미지가 생성되었습니다!\n\n저장 위치: {filepath}")
                    )
                else:
                    self._log("❌ 이미지 생성 실패")
                    self.page.run_thread(
                        lambda: self._show_error("이미지 생성에 실패했습니다.\n로그를 확인하세요.")
                    )
                    
            except Exception as ex:
                self._log(f"❌ 오류: {ex}")
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
    
    def _show_success(self, message: str):
        """성공 다이얼로그"""
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


def main(page: ft.Page):
    """Flet 앱 진입점"""
    ImageGeneratorApp(page)


if __name__ == "__main__":
    ft.app(main)
