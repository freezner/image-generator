#!/bin/bash
#
# JB Bank Image Generator - 네이티브 앱 빌드 스크립트
# flet build를 사용하여 단일 앱으로 패키징
#

set -e

APP_NAME="JB Bank Image Generator"
ORG_NAME="com.jbbank"
PRODUCT_NAME="JB Bank Image Generator"

echo "=============================================="
echo "  🏗️ JB Bank Image Generator 네이티브 빌드"
echo "=============================================="
echo ""

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")"

# Python/Flet 확인
echo "🔍 환경 확인..."
if ! command -v flet &> /dev/null; then
    echo "⚠️ flet CLI를 찾을 수 없습니다."
    echo "   pip install flet 실행 후 다시 시도하세요."
    exit 1
fi

FLET_VERSION=$(flet --version 2>/dev/null || echo "unknown")
echo "   Flet: $FLET_VERSION"

# 아이콘 확인
if [ ! -f "assets/icon.png" ]; then
    echo "⚠️ assets/icon.png가 없습니다."
    echo "   아이콘 생성 중..."
    python3 scripts/create-icon.py
fi

# 빌드
echo ""
echo "🍎 macOS 앱 빌드 중..."
echo "   (처음 실행 시 Flutter SDK 다운로드로 시간이 걸릴 수 있습니다)"
echo ""

flet build macos \
    --project "$APP_NAME" \
    --product "$PRODUCT_NAME" \
    --org "$ORG_NAME" \
    --description "JB Bank AI 캐릭터 이미지 생성기" \
    --copyright "© 2026 JB Bank - Digital Asset Dept." \
    --module-name gui \
    --yes

# 결과 확인
BUILD_DIR="build/macos"
APP_PATH="$BUILD_DIR/$APP_NAME.app"

if [ -d "$APP_PATH" ]; then
    echo ""
    echo "=============================================="
    echo "  ✅ 빌드 완료!"
    echo "=============================================="
    echo ""
    echo "📦 앱 위치: $APP_PATH"
    echo ""
    echo "실행: open '$APP_PATH'"
    echo ""
    
    # dist로 복사
    mkdir -p dist
    rm -rf "dist/$APP_NAME.app"
    cp -R "$APP_PATH" "dist/"
    echo "📁 dist/ 폴더로 복사됨"
    
    # DMG 생성 여부
    read -p "DMG 패키지를 생성하시겠습니까? (y/n): " create_dmg
    if [ "$create_dmg" = "y" ] || [ "$create_dmg" = "Y" ]; then
        ./scripts/create-dmg.sh
    fi
else
    echo ""
    echo "❌ 빌드 실패"
    echo "   build/macos 디렉토리를 확인하세요."
    exit 1
fi
