#!/bin/bash
#
# Brand-Sync Image Generator - 손상된 앱 수정 스크립트
# 이 파일을 더블클릭하면 앱의 격리 속성을 제거합니다.
#

echo "=============================================="
echo "  🔧 JB-Bank Image Generator 앱 수정"
echo "=============================================="
echo ""

# 스크립트 위치 기준으로 앱 찾기
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="JB-Bank-Image-Generator.app"
APP_PATH="$SCRIPT_DIR/$APP_NAME"

# 앱 존재 확인
if [ -d "$APP_PATH" ]; then
    echo "📍 앱 발견: $APP_PATH"
    echo ""
    echo "🔓 격리 속성 제거 중..."
    xattr -cr "$APP_PATH"
    echo ""
    echo "✅ 완료! 이제 앱을 실행할 수 있습니다."
    echo ""
    
    # 앱 실행 여부 확인
    read -p "지금 앱을 실행하시겠습니까? (y/n): " answer
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        open "$APP_PATH"
    fi
else
    echo "❌ 앱을 찾을 수 없습니다: $APP_PATH"
    echo ""
    echo "이 스크립트를 앱과 같은 폴더에 두고 실행하세요."
    echo ""
    
    # 다른 위치에서 앱 찾기 시도
    echo "🔍 다른 위치에서 앱 찾는 중..."
    
    # Applications 폴더 확인
    if [ -d "/Applications/$APP_NAME" ]; then
        echo "📍 Applications에서 발견!"
        APP_PATH="/Applications/$APP_NAME"
        echo "🔓 격리 속성 제거 중..."
        xattr -cr "$APP_PATH"
        echo "✅ 완료!"
    else
        echo "앱을 찾을 수 없습니다."
        echo ""
        echo "수동으로 실행하려면:"
        echo "  xattr -cr /앱/경로/Brand-Sync-Image-Generator.app"
    fi
fi

echo ""
echo "아무 키나 누르면 종료됩니다..."
read -n 1
