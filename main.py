#!/usr/bin/env python3
"""
Brand-Sync AI Image Generator
브랜드 일관성 유지 AI 이미지 제너레이터

사용법:
    python main.py                    # 대화형 모드
    python main.py "선물 상자를 든 모습"  # 단일 생성
    python main.py --batch prompts.txt   # 일괄 생성
"""
import argparse
import sys
from pathlib import Path

from src import (
    load_config,
    create_enhancer,
    create_builder,
    create_generator,
)


def print_banner():
    """배너 출력"""
    print("""
╔═══════════════════════════════════════════════════════╗
║   🎨 Brand-Sync AI Image Generator                    ║
║   브랜드 일관성 유지 AI 이미지 제너레이터              ║
╚═══════════════════════════════════════════════════════╝
""")


def interactive_mode(config, enhancer, builder, generator):
    """대화형 모드"""
    # 사용 가능한 캐릭터 표시
    available_chars = generator.get_available_characters()
    if available_chars:
        print(f"🎭 사용 가능한 캐릭터: {', '.join(available_chars)}")
        print("   💡 프롬프트에 캐릭터 이름을 넣으면 해당 캐릭터 이미지를 참조합니다")
    
    print("\n📝 생성할 이미지를 설명해주세요 (종료: q 또는 quit)")
    print("   예시: 'JB가 선물 상자를 든 모습', 'JB가 점프하는 포즈'")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\n🖼️  프롬프트 입력: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ('q', 'quit', 'exit', '종료'):
                print("👋 종료합니다!")
                break
            
            # 캐릭터 감지 및 참조 이미지 로드
            detected_char = generator.detect_character_from_prompt(user_input)
            reference_images = generator.load_reference_images(detected_char)
            
            # 프롬프트에서 캐릭터명 제거 (이미지에 텍스트로 나오는 것 방지)
            clean_prompt = user_input
            if detected_char:
                clean_prompt = generator.remove_character_name_from_prompt(user_input, detected_char)
                print(f"   📝 정제된 프롬프트: {clean_prompt}")
            
            if not reference_images:
                print("   ⚠️ 참조 이미지 없음 - 텍스트만으로 생성")
            
            # 프롬프트 향상
            print("🔄 프롬프트 최적화 중...")
            enhanced = enhancer.enhance(clean_prompt)
            print(f"   → {enhanced}")
            
            # 최종 프롬프트 생성
            final_prompt = builder.build_simple(enhanced)
            negative = builder.get_negative_prompt()
            
            # 프롬프트 미리보기
            print("\n📋 최종 프롬프트:")
            print(f"   {final_prompt[:100]}...")
            
            # 이미지 생성
            image, filepath = generator.generate_and_save(
                prompt=final_prompt,
                reference_images=reference_images,
                negative_prompt=negative,
                name_hint=user_input
            )
            
            if image:
                print(f"✅ 이미지 생성 완료!")
            else:
                print("❌ 이미지 생성에 실패했습니다.")
                
        except KeyboardInterrupt:
            print("\n\n👋 종료합니다!")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")


def single_generate(config, enhancer, builder, generator, prompt: str):
    """단일 이미지 생성"""
    print(f"📝 입력: {prompt}")
    
    # 캐릭터 감지 및 참조 이미지 로드
    detected_char = generator.detect_character_from_prompt(prompt)
    reference_images = generator.load_reference_images(detected_char)
    
    # 프롬프트에서 캐릭터명 제거
    clean_prompt = prompt
    if detected_char:
        clean_prompt = generator.remove_character_name_from_prompt(prompt, detected_char)
        print(f"   📝 정제된 프롬프트: {clean_prompt}")
    
    if not reference_images:
        print("   ⚠️ 참조 이미지 없음")
    
    # 프롬프트 향상
    print("🔄 프롬프트 최적화 중...")
    enhanced = enhancer.enhance(clean_prompt)
    print(f"   → {enhanced}")
    
    # 최종 프롬프트 생성
    final_prompt = builder.build_simple(enhanced)
    negative = builder.get_negative_prompt()
    
    # 이미지 생성
    image, filepath = generator.generate_and_save(
        prompt=final_prompt,
        reference_images=reference_images,
        negative_prompt=negative,
        name_hint=prompt
    )
    
    if image:
        print(f"✅ 이미지 생성 완료: {filepath}")
        return True
    else:
        print("❌ 이미지 생성에 실패했습니다.")
        return False


def batch_generate(config, enhancer, builder, generator, batch_file: str):
    """일괄 이미지 생성"""
    batch_path = Path(batch_file)
    if not batch_path.exists():
        print(f"❌ 배치 파일을 찾을 수 없습니다: {batch_file}")
        return
    
    with open(batch_path, 'r', encoding='utf-8') as f:
        prompts = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"📋 {len(prompts)}개의 이미지를 생성합니다...")
    print("-" * 50)
    
    success_count = 0
    for i, prompt in enumerate(prompts, 1):
        print(f"\n[{i}/{len(prompts)}] {prompt}")
        
        # 캐릭터 감지 및 참조 이미지 로드
        detected_char = generator.detect_character_from_prompt(prompt)
        reference_images = generator.load_reference_images(detected_char)
        
        # 프롬프트에서 캐릭터명 제거
        clean_prompt = prompt
        if detected_char:
            clean_prompt = generator.remove_character_name_from_prompt(prompt, detected_char)
        
        # 프롬프트 향상
        enhanced = enhancer.enhance(clean_prompt)
        
        # 최종 프롬프트 생성
        final_prompt = builder.build_simple(enhanced)
        negative = builder.get_negative_prompt()
        
        # 이미지 생성
        image, filepath = generator.generate_and_save(
            prompt=final_prompt,
            reference_images=reference_images,
            negative_prompt=negative,
            name_hint=prompt
        )
        
        if image:
            success_count += 1
    
    print(f"\n✅ 완료: {success_count}/{len(prompts)} 이미지 생성됨")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='Brand-Sync AI Image Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    python main.py                         # 대화형 모드
    python main.py "선물 상자를 든 모습"     # 단일 생성
    python main.py --batch prompts.txt      # 일괄 생성
    python main.py --preview "테스트"       # 프롬프트 미리보기만
        """
    )
    parser.add_argument('prompt', nargs='?', help='생성할 이미지 설명')
    parser.add_argument('--batch', '-b', help='배치 프롬프트 파일 경로')
    parser.add_argument('--config', '-c', default='config.json', help='설정 파일 경로')
    parser.add_argument('--preview', '-p', action='store_true', help='프롬프트 미리보기만 (생성 안함)')
    parser.add_argument('--no-enhance', action='store_true', help='프롬프트 향상 건너뛰기')
    
    args = parser.parse_args()
    
    print_banner()
    
    # 설정 로드
    print("⚙️ 설정 로드 중...")
    try:
        config = load_config(args.config)
        print(f"   브랜드: {config.brand.name}")
        print(f"   메인 컬러: {config.brand.main_color}")
        print(f"   서브 컬러: {config.brand.sub_color}")
    except FileNotFoundError:
        print(f"❌ 설정 파일을 찾을 수 없습니다: {args.config}")
        print("   config.json 파일을 생성해주세요.")
        sys.exit(1)
    
    # API 키 확인
    api_key = config.get_api_key()
    if not api_key:
        print("❌ API 키가 설정되지 않았습니다.")
        print("   .env 파일에 GEMINI_API_KEY를 설정하거나")
        print("   환경변수로 GEMINI_API_KEY를 설정해주세요.")
        sys.exit(1)
    
    # 컴포넌트 초기화
    print("\n🔧 컴포넌트 초기화...")
    enhancer = create_enhancer(api_key)
    builder = create_builder(config)
    generator = create_generator(config, api_key)
    
    # 사용 가능한 캐릭터 확인
    available_chars = generator.get_available_characters()
    if available_chars:
        print(f"\n🎭 등록된 캐릭터: {', '.join(available_chars)}")
    else:
        print("\n⚠️ 등록된 캐릭터 없음 - assets/character/ 폴더에 이미지를 추가하세요")
    
    print("-" * 50)
    
    # 미리보기 모드
    if args.preview and args.prompt:
        enhanced = args.prompt if args.no_enhance else enhancer.enhance(args.prompt)
        preview = builder.preview(enhanced)
        print("\n📋 프롬프트 미리보기:")
        print(f"   [PREFIX] {preview['prefix']}")
        print(f"   [VARIABLE] {preview['variable']}")
        print(f"   [SUFFIX] {preview['suffix']}")
        print(f"\n   [FINAL] {preview['final']}")
        print(f"\n   [NEGATIVE] {preview['negative']}")
        return
    
    # 실행 모드 선택
    if args.batch:
        batch_generate(config, enhancer, builder, generator, args.batch)
    elif args.prompt:
        single_generate(config, enhancer, builder, generator, args.prompt)
    else:
        interactive_mode(config, enhancer, builder, generator)


if __name__ == '__main__':
    main()
