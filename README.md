# 🎨 JB-Bank AI Image Generator

브랜드 일관성을 유지하며 AI 이미지를 생성하는 도구입니다.

참조 캐릭터 이미지와 브랜드 색상을 기반으로, 간단한 키워드 입력만으로 일관된 스타일의 이미지를 자동 생성합니다.

## ✨ 주요 기능

- 🖼️ **참조 이미지 기반 생성**: 캐릭터 원본 이미지를 참조하여 형태/비율 유지
- 🎭 **캐릭터 자동 감지**: 프롬프트에서 캐릭터 이름 감지하여 자동 참조 (예: "JB가 점프")
- 🎨 **브랜드 색상 자동 적용**: 설정된 메인/서브 컬러가 자동으로 프롬프트에 반영
- 🤖 **LLM 프롬프트 향상**: 간단한 한국어 키워드를 정교한 영어 프롬프트로 자동 변환
- ⚡ **고정 + 변동 프롬프트 자동 결합**: 브랜드 톤앤매너 강제
- 📦 **일괄 생성 지원**: 여러 이미지를 한 번에 생성
- 🖥️ **GUI 앱 지원**: Mac/Windows에서 실행 가능한 데스크톱 앱

## 📁 프로젝트 구조

```
image-generator/
├── main.py                 # CLI 진입점
├── gui.py                  # GUI 애플리케이션
├── build.py                # 패키징 스크립트
├── config.json             # 설정 파일
├── requirements.txt        # 의존성
├── requirements-dev.txt    # 개발 의존성
├── .env                    # API 키 (생성 필요)
├── src/
│   ├── __init__.py
│   ├── config_loader.py    # 설정 로더
│   ├── prompt_enhancer.py  # 프롬프트 향상기 (LLM)
│   ├── prompt_builder.py   # 프롬프트 빌더
│   └── image_generator.py  # 이미지 생성기
├── assets/
│   └── character/          # 참조 캐릭터 이미지 (JB1.png, JB2.png 등)
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

`assets/character/` 폴더에 캐릭터 이미지를 넣어주세요.

**파일명 규칙:**
- `캐릭터명 + 번호.확장자` 형식 권장
- 예: `JB1.png`, `JB2.png`, `JB3.png`
- 프롬프트에 "JB"를 입력하면 JB로 시작하는 모든 이미지를 참조

**권장 사항:**
- 지원 포맷: PNG, JPG, JPEG, WebP
- 정면, 측면 등 다양한 각도의 이미지 2-5장
- 최대 5장까지 동시 참조 가능

## 💻 사용법

### 🖥️ GUI 모드 (권장)

```bash
python gui.py
```

![GUI Screenshot](docs/gui-screenshot.png)

**GUI 기능:**
- 프롬프트 입력 창
- 생성 진행 상황 표시
- 완료 알림
- 결과 폴더 바로가기
- 설정 화면 (API 키, 브랜드 설정)

### ⌨️ CLI 대화형 모드

```bash
python main.py
```

프롬프트를 입력하면 이미지가 생성됩니다:

```
🎭 등록된 캐릭터: JB
🖼️  프롬프트 입력: JB가 선물 상자를 든 모습
🎭 캐릭터 'JB' 감지됨!
   ✓ 참조 이미지: JB1.png
   ✓ 참조 이미지: JB2.png
   ✓ 참조 이미지: JB3.png
🔄 프롬프트 최적화 중...
   → holding a gift box with both hands, cheerful expression
🎨 이미지 생성 중...
✅ 이미지 생성 완료!
💾 저장됨: output/20260320_132345_선물 상자를 든 모습.png
```

### 단일 생성

```bash
python main.py "JB가 계산기를 들고 설명하는 포즈"
```

### 일괄 생성

```bash
# prompts.txt 준비
# JB가 선물 상자를 든 모습
# JB가 점프하는 포즈
# JB가 손을 흔드는 인사

python main.py --batch prompts.txt
```

## 📦 앱 패키징 (배포용)

Mac/Windows 실행 파일로 패키징:

```bash
# 개발 의존성 설치
pip install -r requirements-dev.txt

# 빌드 실행
python build.py
```

**결과물:**
- macOS: `dist/JB Bank Image Generator.app`
- Windows: `dist/JB Bank Image Generator/JB Bank Image Generator.exe`

## ⚙️ 설정

### config.json

```json
{
  "brand": {
    "name": "MyBrand",
    "main_color": "#FF6B35",
    "sub_color": "#004E89",
    "style_keywords": ["3D rendering", "cute", "soft lighting"]
  },
  "output": {
    "format": "png",
    "width": 1024,
    "height": 1024,
    "transparent_background": true
  },
  "api": {
    "provider": "google",
    "model": "gemini-2.5-flash-image",
    "text_model": "gemini-2.0-flash",
    "max_reference_images": 5
  }
}
```

### 사용 가능한 이미지 모델

| 모델 | 설명 | 비용 |
|------|------|------|
| `gemini-2.5-flash-image` | Gemini 이미지 생성 | Free tier 가능 |
| `gemini-3.1-flash-image-preview` | Gemini 3.1 프리뷰 | Free tier 가능 |
| `imagen-4.0-generate-001` | Imagen 4.0 | 유료 |
| `imagen-4.0-ultra-generate-001` | Imagen 4.0 Ultra (최고품질) | 유료 |

## 🔧 프롬프트 규칙

### 캐릭터 자동 감지
- 프롬프트에 캐릭터 이름(JB 등)이 있으면 자동 감지
- 해당 캐릭터의 참조 이미지를 자동 로드
- 프롬프트에서 캐릭터명은 자동 제거 (이미지에 텍스트로 나오는 것 방지)

### 텍스트 규칙
- 기본적으로 이미지에 텍스트 추가 안 함
- 텍스트가 필요하면 명시적으로 요청:
  - ✅ `JB가 "안녕하세요" 말풍선을 들고 있는 모습`
  - ✅ `배경에 "SALE" 텍스트 추가`

## 📝 API 참고

- [Google AI Studio - API 키 발급](https://aistudio.google.com/app/apikey)
- [Gemini API 문서](https://ai.google.dev/docs)

## 🤝 기여

이슈나 PR은 언제나 환영합니다!

## 📄 라이선스

MIT License
