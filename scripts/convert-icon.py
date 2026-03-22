#!/usr/bin/env python3
"""
앱 아이콘 변환 스크립트
SVG → PNG → ICNS (macOS) / ICO (Windows)
"""
import os
import sys
import subprocess
from pathlib import Path

def install_cairosvg():
    """cairosvg 설치"""
    print("📦 cairosvg 설치 중...")
    subprocess.run([sys.executable, "-m", "pip", "install", "cairosvg", "-q"])

def convert_svg_to_png():
    """SVG를 PNG로 변환"""
    try:
        import cairosvg
    except ImportError:
        install_cairosvg()
        import cairosvg
    
    assets_dir = Path(__file__).parent.parent / "assets"
    svg_path = assets_dir / "icon.svg"
    
    if not svg_path.exists():
        print(f"❌ SVG 파일을 찾을 수 없습니다: {svg_path}")
        return False
    
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    
    print("🎨 PNG 변환 중...")
    for size in sizes:
        output = assets_dir / f"icon_{size}.png"
        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(output),
            output_width=size,
            output_height=size
        )
        print(f"   ✓ {size}x{size}")
    
    # 기본 icon.png (512x512)
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(assets_dir / "icon.png"),
        output_width=512,
        output_height=512
    )
    print("   ✓ icon.png (512x512)")
    
    return True

def create_icns():
    """macOS용 ICNS 파일 생성"""
    if sys.platform != "darwin":
        print("⚠️ ICNS 생성은 macOS에서만 가능합니다.")
        return False
    
    assets_dir = Path(__file__).parent.parent / "assets"
    iconset_dir = assets_dir / "icon.iconset"
    
    # iconset 디렉토리 생성
    iconset_dir.mkdir(exist_ok=True)
    
    # 필요한 크기와 파일명
    icon_sizes = [
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
    
    print("📁 iconset 생성 중...")
    for size, filename in icon_sizes:
        src = assets_dir / f"icon_{size}.png"
        dst = iconset_dir / filename
        if src.exists():
            import shutil
            shutil.copy(src, dst)
    
    # iconutil로 ICNS 생성
    print("🍎 ICNS 생성 중...")
    icns_path = assets_dir / "icon.icns"
    result = subprocess.run(
        ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
        capture_output=True
    )
    
    if result.returncode == 0:
        print(f"   ✓ {icns_path}")
        # iconset 정리
        import shutil
        shutil.rmtree(iconset_dir)
        return True
    else:
        print(f"❌ ICNS 생성 실패: {result.stderr.decode()}")
        return False

def create_ico():
    """Windows용 ICO 파일 생성"""
    try:
        from PIL import Image
    except ImportError:
        print("📦 Pillow 설치 중...")
        subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "-q"])
        from PIL import Image
    
    assets_dir = Path(__file__).parent.parent / "assets"
    
    # 다양한 크기의 PNG를 ICO로 합치기
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    print("🪟 ICO 생성 중...")
    for size in sizes:
        png_path = assets_dir / f"icon_{size}.png"
        if png_path.exists():
            img = Image.open(png_path)
            images.append(img)
    
    if images:
        ico_path = assets_dir / "icon.ico"
        images[0].save(
            str(ico_path),
            format='ICO',
            sizes=[(img.width, img.height) for img in images]
        )
        print(f"   ✓ {ico_path}")
        return True
    else:
        print("❌ PNG 파일이 없습니다. 먼저 SVG를 PNG로 변환하세요.")
        return False

def main():
    print("=" * 50)
    print("  🎨 앱 아이콘 변환")
    print("=" * 50)
    print()
    
    # 1. SVG → PNG
    if not convert_svg_to_png():
        return
    
    print()
    
    # 2. macOS: ICNS 생성
    if sys.platform == "darwin":
        create_icns()
        print()
    
    # 3. Windows: ICO 생성
    create_ico()
    
    print()
    print("✅ 완료!")
    print()
    print("생성된 파일:")
    assets_dir = Path(__file__).parent.parent / "assets"
    for f in sorted(assets_dir.glob("icon*")):
        if f.is_file():
            size = f.stat().st_size
            print(f"   {f.name} ({size:,} bytes)")

if __name__ == "__main__":
    main()
