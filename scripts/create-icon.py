#!/usr/bin/env python3
"""
앱 아이콘 생성 스크립트
Pillow로 직접 아이콘 그리기
"""
import sys
import subprocess
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("📦 Pillow 설치 중...")
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "-q"])
    from PIL import Image, ImageDraw


def create_icon(size=512):
    """귀여운 새 캐릭터 아이콘 생성"""
    # RGBA 이미지 생성
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 스케일 팩터
    s = size / 512
    
    # 색상 정의
    bg_color = (232, 244, 252)  # 연한 하늘색 배경
    body_color = (141, 212, 248)  # 하늘색 몸통
    body_dark = (107, 196, 245)  # 약간 진한 하늘색
    white = (255, 255, 255)
    pink = (255, 138, 155)  # 볏
    pink_cheek = (255, 182, 193, 180)  # 볼터치
    yellow = (255, 217, 61)  # 부리/발
    black = (51, 51, 51)  # 눈
    
    cx, cy = size // 2, size // 2  # 중심점
    
    # 1. 배경 원
    margin = int(16 * s)
    draw.ellipse([margin, margin, size - margin, size - margin], fill=bg_color)
    
    # 2. 몸통 (타원)
    body_w, body_h = int(140 * s), int(150 * s)
    body_y = int(280 * s)
    draw.ellipse([
        cx - body_w, body_y - body_h,
        cx + body_w, body_y + body_h
    ], fill=body_color)
    
    # 3. 머리 (원)
    head_r = int(120 * s)
    head_y = int(200 * s)
    draw.ellipse([
        cx - head_r, head_y - head_r,
        cx + head_r, head_y + head_r
    ], fill=body_color)
    
    # 4. 흰 배
    belly_w, belly_h = int(80 * s), int(70 * s)
    belly_y = int(340 * s)
    draw.ellipse([
        cx - belly_w, belly_y - belly_h,
        cx + belly_w, belly_y + belly_h
    ], fill=white)
    
    # 5. 분홍 볏 (3개 타원)
    crest_y = int(95 * s)
    # 중앙
    draw.ellipse([
        cx - int(25*s), crest_y - int(40*s),
        cx + int(25*s), crest_y + int(40*s)
    ], fill=pink)
    # 왼쪽
    draw.ellipse([
        cx - int(55*s), crest_y - int(15*s),
        cx - int(15*s), crest_y + int(35*s)
    ], fill=pink)
    # 오른쪽
    draw.ellipse([
        cx + int(15*s), crest_y - int(15*s),
        cx + int(55*s), crest_y + int(35*s)
    ], fill=pink)
    
    # 6. 날개
    wing_w, wing_h = int(45 * s), int(70 * s)
    wing_y = int(260 * s)
    # 왼쪽 날개
    draw.ellipse([
        int(85*s), wing_y - wing_h,
        int(85*s) + wing_w*2, wing_y + wing_h
    ], fill=body_dark)
    # 오른쪽 날개
    draw.ellipse([
        size - int(85*s) - wing_w*2, wing_y - wing_h,
        size - int(85*s), wing_y + wing_h
    ], fill=body_dark)
    
    # 7. 눈
    eye_r = int(20 * s)
    eye_y = int(190 * s)
    eye_left_x = cx - int(46 * s)
    eye_right_x = cx + int(46 * s)
    
    # 왼쪽 눈
    draw.ellipse([
        eye_left_x - eye_r, eye_y - eye_r,
        eye_left_x + eye_r, eye_y + eye_r
    ], fill=black)
    # 왼쪽 하이라이트
    hl_r = int(6 * s)
    draw.ellipse([
        eye_left_x + int(5*s) - hl_r, eye_y - int(5*s) - hl_r,
        eye_left_x + int(5*s) + hl_r, eye_y - int(5*s) + hl_r
    ], fill=white)
    
    # 오른쪽 눈
    draw.ellipse([
        eye_right_x - eye_r, eye_y - eye_r,
        eye_right_x + eye_r, eye_y + eye_r
    ], fill=black)
    # 오른쪽 하이라이트
    draw.ellipse([
        eye_right_x + int(5*s) - hl_r, eye_y - int(5*s) - hl_r,
        eye_right_x + int(5*s) + hl_r, eye_y - int(5*s) + hl_r
    ], fill=white)
    
    # 8. 부리
    beak_w, beak_h = int(20 * s), int(15 * s)
    beak_y = int(240 * s)
    draw.ellipse([
        cx - beak_w, beak_y - beak_h,
        cx + beak_w, beak_y + beak_h
    ], fill=yellow)
    
    # 9. 볼터치
    cheek_w, cheek_h = int(25 * s), int(18 * s)
    cheek_y = int(220 * s)
    # 왼쪽 볼
    draw.ellipse([
        cx - int(86*s) - cheek_w, cheek_y - cheek_h,
        cx - int(86*s) + cheek_w, cheek_y + cheek_h
    ], fill=pink_cheek)
    # 오른쪽 볼
    draw.ellipse([
        cx + int(86*s) - cheek_w, cheek_y - cheek_h,
        cx + int(86*s) + cheek_w, cheek_y + cheek_h
    ], fill=pink_cheek)
    
    # 10. 발
    foot_w, foot_h = int(30 * s), int(15 * s)
    foot_y = int(430 * s)
    # 왼발
    draw.ellipse([
        cx - int(46*s) - foot_w, foot_y - foot_h,
        cx - int(46*s) + foot_w, foot_y + foot_h
    ], fill=yellow)
    # 오른발
    draw.ellipse([
        cx + int(46*s) - foot_w, foot_y - foot_h,
        cx + int(46*s) + foot_w, foot_y + foot_h
    ], fill=yellow)
    
    # 11. AI 반짝이 (오른쪽 상단)
    sparkle_x, sparkle_y = int(380 * s), int(100 * s)
    sparkle_size = int(20 * s)
    # 십자 모양 반짝이
    draw.polygon([
        (sparkle_x, sparkle_y - sparkle_size),
        (sparkle_x + int(5*s), sparkle_y - int(5*s)),
        (sparkle_x + sparkle_size, sparkle_y),
        (sparkle_x + int(5*s), sparkle_y + int(5*s)),
        (sparkle_x, sparkle_y + sparkle_size),
        (sparkle_x - int(5*s), sparkle_y + int(5*s)),
        (sparkle_x - sparkle_size, sparkle_y),
        (sparkle_x - int(5*s), sparkle_y - int(5*s)),
    ], fill=yellow)
    
    return img


def main():
    print("=" * 50)
    print("  🎨 JB Bank 앱 아이콘 생성")
    print("=" * 50)
    print()
    
    assets_dir = Path(__file__).parent.parent / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    # 다양한 크기로 생성
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    
    print("🎨 아이콘 생성 중...")
    for size in sizes:
        img = create_icon(size)
        path = assets_dir / f"icon_{size}.png"
        img.save(path, "PNG")
        print(f"   ✓ {size}x{size}")
    
    # 기본 icon.png
    img = create_icon(512)
    img.save(assets_dir / "icon.png", "PNG")
    print("   ✓ icon.png (512x512)")
    
    # macOS ICNS 생성
    if sys.platform == "darwin":
        print()
        print("🍎 ICNS 생성 중...")
        create_icns(assets_dir)
    
    # Windows ICO 생성
    print()
    print("🪟 ICO 생성 중...")
    create_ico(assets_dir)
    
    print()
    print("✅ 완료!")
    print()
    print("생성된 파일:")
    for f in sorted(assets_dir.glob("icon*")):
        if f.is_file():
            print(f"   {f.name}")


def create_icns(assets_dir):
    """macOS ICNS 생성"""
    import shutil
    
    iconset_dir = assets_dir / "icon.iconset"
    iconset_dir.mkdir(exist_ok=True)
    
    mappings = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]
    
    for size, name in mappings:
        src = assets_dir / f"icon_{size}.png"
        if src.exists():
            shutil.copy(src, iconset_dir / name)
    
    icns_path = assets_dir / "icon.icns"
    result = subprocess.run(
        ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
        capture_output=True
    )
    
    shutil.rmtree(iconset_dir)
    
    if result.returncode == 0:
        print(f"   ✓ icon.icns")
    else:
        print(f"   ❌ ICNS 생성 실패")


def create_ico(assets_dir):
    """Windows ICO 생성"""
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        path = assets_dir / f"icon_{size}.png"
        if path.exists():
            images.append(Image.open(path))
    
    if images:
        ico_path = assets_dir / "icon.ico"
        images[0].save(
            str(ico_path),
            format='ICO',
            sizes=[(img.width, img.height) for img in images]
        )
        print(f"   ✓ icon.ico")


if __name__ == "__main__":
    main()
