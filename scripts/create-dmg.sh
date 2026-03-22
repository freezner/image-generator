#!/bin/bash
#
# Brand-Sync Image Generator - DMG 패키지 생성 스크립트
#

set -e

APP_NAME="JB-Bank-Image-Generator"
DMG_NAME="${APP_NAME}-Installer"
VERSION="1.0.0"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_DIR/dist"
APP_PATH="$DIST_DIR/${APP_NAME}.app"
DMG_PATH="$DIST_DIR/${DMG_NAME}.dmg"
TEMP_DMG="$DIST_DIR/temp_${DMG_NAME}.dmg"
MOUNT_DIR="/Volumes/${DMG_NAME}"

echo "=============================================="
echo "  📀 DMG 패키지 생성"
echo "=============================================="
echo ""

# 앱 존재 확인
if [ ! -d "$APP_PATH" ]; then
    echo "❌ 앱을 찾을 수 없습니다: $APP_PATH"
    echo "   먼저 'python build.py'를 실행하세요."
    exit 1
fi

echo "📍 앱 경로: $APP_PATH"

# 기존 DMG 삭제
if [ -f "$DMG_PATH" ]; then
    echo "🗑️  기존 DMG 삭제 중..."
    rm -f "$DMG_PATH"
fi

if [ -f "$TEMP_DMG" ]; then
    rm -f "$TEMP_DMG"
fi

# 마운트된 볼륨이 있으면 언마운트
if [ -d "$MOUNT_DIR" ]; then
    echo "📤 기존 마운트 해제 중..."
    hdiutil detach "$MOUNT_DIR" -force 2>/dev/null || true
fi

# 임시 디렉토리 생성
STAGING_DIR=$(mktemp -d)
echo "📁 스테이징 디렉토리: $STAGING_DIR"

# 파일 복사
echo "📋 파일 복사 중..."
cp -R "$APP_PATH" "$STAGING_DIR/"

# Applications 링크 생성
ln -s /Applications "$STAGING_DIR/Applications"

# Fix 스크립트 복사
if [ -f "$SCRIPT_DIR/Fix-Damaged-App.command" ]; then
    cp "$SCRIPT_DIR/Fix-Damaged-App.command" "$STAGING_DIR/"
    chmod +x "$STAGING_DIR/Fix-Damaged-App.command"
fi

# README 생성
cat > "$STAGING_DIR/README.txt" << 'EOF'
JB Bank AI Image Generator
==========================

설치 방법:
1. JB-Bank-Image-Generator.app을 Applications 폴더로 드래그
2. 처음 실행 시 "손상됨" 오류가 나타나면:
   - Fix-Damaged-App.command를 더블클릭하여 실행
   - 또는 터미널에서: xattr -cr /Applications/JB-Bank-Image-Generator.app

사용 방법:
1. 앱 실행
2. 설정에서 Gemini API 키 입력
3. assets/character 폴더에 캐릭터 이미지 추가 (JB1.png, JB2.png 등)
4. 프롬프트 입력 후 이미지 생성!

API 키 발급:
https://aistudio.google.com/app/apikey

문의: https://github.com/jbbank-hjpark/image-generator
EOF

# DMG 크기 계산 (여유 있게)
SIZE_MB=$(du -sm "$STAGING_DIR" | cut -f1)
SIZE_MB=$((SIZE_MB + 50))  # 50MB 여유

echo "💿 DMG 생성 중... (${SIZE_MB}MB)"

# DMG 생성
hdiutil create \
    -volname "$DMG_NAME" \
    -srcfolder "$STAGING_DIR" \
    -ov \
    -format UDZO \
    -imagekey zlib-level=9 \
    "$DMG_PATH"

# 정리
echo "🧹 임시 파일 정리 중..."
rm -rf "$STAGING_DIR"

# 결과 확인
if [ -f "$DMG_PATH" ]; then
    DMG_SIZE=$(du -h "$DMG_PATH" | cut -f1)
    echo ""
    echo "=============================================="
    echo "  ✅ DMG 생성 완료!"
    echo "=============================================="
    echo ""
    echo "📀 파일: $DMG_PATH"
    echo "📊 크기: $DMG_SIZE"
    echo ""
    echo "배포 방법:"
    echo "  1. DMG 파일을 공유"
    echo "  2. 사용자가 DMG를 열고 앱을 Applications로 드래그"
    echo "  3. 필요시 Fix-Damaged-App.command 실행"
else
    echo "❌ DMG 생성 실패"
    exit 1
fi
