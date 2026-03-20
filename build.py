#!/usr/bin/env python3
"""
Build script for JB-Bank AI Image Generator
Flet 앱 패키징 스크립트
"""
import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path


APP_NAME = "JB-Bank-Image-Generator"
MAIN_SCRIPT = "gui.py"


def check_flet():
    """Flet 설치 확인"""
    try:
        import flet
        version = getattr(flet, '__version__', None) or getattr(getattr(flet, 'version', None), '__version__', 'unknown')
        print(f"✓ Flet {version} 설치됨")
        return True
    except ImportError:
        print("❌ Flet이 설치되지 않았습니다.")
        print("   설치: pip install flet")
        return False


def check_pyinstaller():
    """PyInstaller 설치 확인"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} 설치됨")
        return True
    except ImportError:
        print("❌ PyInstaller가 설치되지 않았습니다.")
        return False


def build_app():
    """앱 빌드 (PyInstaller 사용)"""
    system = platform.system()
    print(f"\n🔧 빌드 시작 ({system})...")
    
    # flet 패키지 위치 찾기
    import flet
    flet_path = Path(flet.__file__).parent
    
    # PyInstaller 명령어 구성
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onedir",
        "--windowed",  # GUI 앱 (콘솔 창 숨김)
        "--noconfirm",
        "--clean",
        # 데이터 파일 추가
        "--add-data", f"config.json{os.pathsep}.",
        "--add-data", f"src{os.pathsep}src",
        "--add-data", f"assets{os.pathsep}assets",
        # Flet 관련 임포트
        "--hidden-import", "flet",
        "--hidden-import", "flet_core",
        "--hidden-import", "flet_runtime",
        "--collect-all", "flet",
        "--collect-all", "flet_core",
        "--collect-all", "flet_runtime",
        # 기타 의존성
        "--hidden-import", "google.genai",
        "--hidden-import", "PIL",
        "--hidden-import", "httpx",
        "--hidden-import", "websockets",
    ]
    
    # OS별 아이콘 설정
    if system == "Darwin":
        icon_path = Path("assets/icon.icns")
        if icon_path.exists():
            cmd.extend(["--icon", str(icon_path)])
        cmd.extend([
            "--osx-bundle-identifier", "com.jbbank.imagegenerator",
        ])
    elif system == "Windows":
        icon_path = Path("assets/icon.ico")
        if icon_path.exists():
            cmd.extend(["--icon", str(icon_path)])
    
    # 메인 스크립트 추가
    cmd.append(MAIN_SCRIPT)
    
    print(f"실행 명령:\n{' '.join(cmd[:10])}...\n")
    
    # 빌드 실행
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ 빌드 완료!")
        
        # 결과물 위치 안내
        if system == "Darwin":
            app_path = f"dist/{APP_NAME}.app"
            if Path(app_path).exists():
                print(f"\n📦 앱 위치: {app_path}")
                print(f"\n실행 방법:")
                print(f"  open 'dist/{APP_NAME}.app'")
            else:
                print(f"\n📦 결과물 위치: dist/{APP_NAME}/")
        elif system == "Windows":
            exe_path = f"dist/{APP_NAME}/{APP_NAME}.exe"
            print(f"\n📦 실행파일 위치: {exe_path}")
        else:
            print(f"\n📦 결과물 위치: dist/{APP_NAME}/")
        
        return True
    else:
        print("\n❌ 빌드 실패!")
        return False


def main():
    """메인 함수"""
    print("=" * 50)
    print(f"  {APP_NAME} Build Script")
    print("=" * 50)
    
    # 작업 디렉토리 확인
    if not Path(MAIN_SCRIPT).exists():
        print(f"❌ {MAIN_SCRIPT}를 찾을 수 없습니다.")
        print("   프로젝트 루트 디렉토리에서 실행하세요.")
        sys.exit(1)
    
    # Flet 확인
    if not check_flet():
        install = input("\nFlet을 설치하시겠습니까? (y/n): ")
        if install.lower() == 'y':
            subprocess.run([sys.executable, "-m", "pip", "install", "flet"])
        else:
            sys.exit(1)
    
    # PyInstaller 확인
    if not check_pyinstaller():
        install = input("\nPyInstaller를 설치하시겠습니까? (y/n): ")
        if install.lower() == 'y':
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        else:
            sys.exit(1)
    
    # 빌드
    build_app()
    
    print("\n완료!")


if __name__ == "__main__":
    main()
