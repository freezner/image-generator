#!/usr/bin/env python3
"""
JB Bank Image Generator - Flet 네이티브 빌드 스크립트
flet build 명령어를 사용하여 단일 앱으로 패키징
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

APP_NAME = "JB-Bank-Image-Generator"
BUNDLE_ID = "com.jbbank.imagegenerator"

def check_flet_cli():
    """Flet CLI 확인"""
    result = subprocess.run(
        [sys.executable, "-m", "flet", "--version"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"✓ Flet {result.stdout.strip()}")
        return True
    return False

def prepare_assets():
    """assets 준비"""
    assets_dir = Path("assets")
    
    # 아이콘 확인
    icon_png = assets_dir / "icon.png"
    if not icon_png.exists():
        print("⚠️ assets/icon.png가 없습니다.")
        print("   scripts/create-icon.py를 먼저 실행하세요.")
        return False
    
    return True

def build_macos():
    """macOS 앱 빌드"""
    print("\n🍎 macOS 앱 빌드 중...")
    
    cmd = [
        sys.executable, "-m", "flet", "build", "macos",
        "--project", APP_NAME,
        "--org", "com.jbbank",
        "--product", APP_NAME,
        "--build-version", "1.0.0",
        "--template", "gh:nickmyv/nickmyv",  # 기본 템플릿
    ]
    
    # 아이콘이 있으면 추가
    if Path("assets/icon.png").exists():
        cmd.extend(["--icon", "assets/icon.png"])
    
    print(f"실행: {' '.join(cmd[:8])}...")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ 빌드 완료!")
        print(f"📦 결과물: build/macos/{APP_NAME}.app")
        return True
    else:
        print("\n❌ 빌드 실패")
        return False

def build_with_pyinstaller_single():
    """PyInstaller로 단일 프로세스 빌드 (대안)"""
    print("\n🔧 PyInstaller 단일 프로세스 빌드...")
    
    # flet 뷰 모드를 FLET_APP_HIDDEN으로 설정하는 래퍼 생성
    wrapper_code = '''
import os
import sys

# Flet 프로세스 숨기기
os.environ["FLET_VIEW_MACOS"] = "FLET_APP_HIDDEN"
os.environ["FLET_WEB_RENDERER"] = "html"

# 메인 앱 실행
from gui import main
import flet as ft

if __name__ == "__main__":
    ft.app(main)
'''
    
    with open("launcher.py", "w") as f:
        f.write(wrapper_code)
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onefile",  # 단일 파일
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data", f"config.json{os.pathsep}.",
        "--add-data", f"src{os.pathsep}src",
        "--add-data", f"assets{os.pathsep}assets",
        "--hidden-import", "flet",
        "--collect-all", "flet",
        "--collect-all", "flet_core", 
        "--collect-all", "flet_runtime",
    ]
    
    # 아이콘
    if Path("assets/icon.icns").exists():
        cmd.extend(["--icon", "assets/icon.icns"])
    
    cmd.append("launcher.py")
    
    result = subprocess.run(cmd)
    
    # launcher.py 정리
    Path("launcher.py").unlink(missing_ok=True)
    
    return result.returncode == 0

def main():
    print("=" * 50)
    print(f"  {APP_NAME} 빌드")
    print("=" * 50)
    
    if not check_flet_cli():
        print("❌ Flet이 설치되지 않았습니다.")
        sys.exit(1)
    
    if not prepare_assets():
        sys.exit(1)
    
    print("\n빌드 방식 선택:")
    print("  1. flet build (권장 - 깔끔한 단일 앱)")
    print("  2. PyInstaller (대안)")
    
    choice = input("\n선택 (1/2): ").strip()
    
    if choice == "1":
        build_macos()
    elif choice == "2":
        build_with_pyinstaller_single()
    else:
        print("기본값: flet build")
        build_macos()

if __name__ == "__main__":
    main()
