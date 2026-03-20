# 🎨 Brand-Sync AI Image Generator

브랜드 일관성을 유지하며 AI 이미지를 생성하는 도구입니다.

참조 캐릭터 이미지와 브랜드 색상을 기반으로, 간단한 키워드 입력만으로 일관된 스타일의 이미지를 자동 생성합니다.

## ✨ 주요 기능

- 🖼️ **참조 이미지 기반 생성**: 캐릭터 원본 이미지를 참조하여 형태/비율 유지
- 🎨 **브랜드 색상 자동 적용**: 설정된 메인/서브 컬러가 자동으로 프롬프트에 반영
- 🤖 **LLM 프롬프트 향상**: 간단한 한국어 키워드를 정교한 영어 프롬프트로 자동 변환
- ⚡ **고정 + 변동 프롬프트 자동 결합**: 브랜드 톤앤매너 강제
- 📦 **일괄 생성 지원**: 여러 이미지를 한 번에 생성

## 📁 프로젝트 구조

```
image-generator/
├── main.py                 # 메인 CLI 진입점
├── config.json             # 설정 파일
├── requirements.txt        # 의존성
├── .env                    # API 키 (생성 필요)
├── src/
│   ├── __init__.py
│   ├── config_loader.py    # 설정 로더
│   ├── prompt_enhancer.py  # 프롬프트 향상기 (LLM)
│   ├── prompt_builder.py   # 프롬프트 빌더
│   └── image_generator.py  # 이미지 생성기
├── assets/
│   └── character/          # 참조 캐릭터 이미지
└── output/                 # 생성된 이미지 저장
```

## 🚀 시작하기

### 1. 설치

```bash
# 의존성 설치
pip install -r requirements.txt
```

### 2. API 키 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 API 키 입력
GEMINI_API_KEY=your_api_key_here
```

API 키는 [Google AI Studio](https://aistudio.google.com/app/apikey)에서 발급받으세요.

### 3. 참조 이미지 준비

`assets/character/` 폴더에 참조할 캐릭터 이미지를 넣어주세요.

- 지원 포맷: PNG, JPG, JPEG, WebP
- 권장: 정면, 측면 등 다양한 각도의 이미지 2-5장
- 최대 5장까지 동시 참조 가능

### 4. 설정 커스터마이징

`config.json` 파일을 편집하여 브랜드 설정을 변경하세요:

```json
{
  "brand": {
    "name": "MyBrand",
    "main_color": "#FF6B35",    // 메인 컬러 (Hex)
    "sub_color": "#004E89",      // 서브 컬러 (Hex)
    "style_keywords": ["3D rendering", "cute", "soft lighting"]
  },
  "output": {
    "format": "png",             // png 또는 jpg
    "width": 1024,
    "height": 1024,
    "transparent_background": true
  }
}
```

## 💻 사용법

### 대화형 모드

```bash
python main.py
```

프롬프트를 입력하면 이미지가 생성됩니다:

```
🖼️  프롬프트 입력: 선물 상자를 든 모습
🔄 프롬프트 최적화 중...
   → holding a gift box with both hands, cheerful expression
🎨 이미지 생성 중...
✅ 이미지 생성 완료!
💾 저장됨: output/20260319_182345_선물 상자를 든 모습.png
```

### 단일 생성

```bash
python main.py "계산기를 들고 설명하는 포즈"
```

### 일괄 생성

프롬프트 파일을 준비하고:

```text
# prompts.txt
선물 상자를 든 모습
점프하는 포즈
손을 흔드는 인사
```

일괄 실행:

```bash
python main.py --batch prompts.txt
```

### 프롬프트 미리보기

실제 생성 없이 프롬프트만 확인:

```bash
python main.py --preview "선물 상자"
```

## 🔧 프롬프트 구조

최종 프롬프트는 다음 구조로 자동 생성됩니다:

```
{고정 PREFIX} + {변동 프롬프트} + {고정 SUFFIX}
```

### 예시

**입력:** `선물 상자를 든 모습`

**LLM 향상:** `holding a gift box with both hands, cheerful expression, looking at the viewer`

**최종 프롬프트:**
```
3D rendered cute character illustration, consistent character design, 
#FF6B35 as primary accent color, #004E89 as secondary color, 
holding a gift box with both hands, cheerful expression, looking at the viewer, 
soft studio lighting, minimal clean background, high quality, detailed, 
professional product image style
```

## ⚙️ 고급 설정

### 고정 프롬프트 수정

`config.json`의 `prompts` 섹션을 수정:

```json
{
  "prompts": {
    "fixed_prefix": "3D rendered cute character illustration, ...",
    "fixed_suffix": ", soft studio lighting, ...",
    "negative": "deformed, distorted, ..."
  }
}
```

### 네거티브 프롬프트

품질 저하 요소를 제외하는 네거티브 프롬프트가 자동 적용됩니다.

## 📝 API 참고

### Gemini API

- 모델: `gemini-2.0-flash-exp-image-generation`
- [API 문서](https://ai.google.dev/docs)

### 지원 예정

- OpenAI DALL-E 3
- Stability AI
- Midjourney (via API)

## 🤝 기여

이슈나 PR은 언제나 환영합니다!

## 📄 라이선스

MIT License
