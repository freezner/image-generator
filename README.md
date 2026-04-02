# 🎨 JB-Bank AI Image Generator

브랜드 일관성을 유지하며 AI 이미지를 생성하는 도구입니다.

참조 캐릭터 이미지와 브랜드 색상을 기반으로, 간단한 키워드 입력만으로 일관된 스타일의 이미지를 자동 생성합니다.

---

## ✨ 주요 기능

- 🖼️ **참조 이미지 기반 생성**: 캐릭터 원본 이미지를 참조하여 형태/비율 유지
- 🎭 **캐릭터 자동 감지**: 프롬프트에서 캐릭터 이름 감지 후 자동 참조
- 🎨 **브랜드 색상 자동 적용**: 설정된 메인/서브 컬러가 프롬프트에 자동 반영
- 🤖 **LLM 프롬프트 향상**: 간단한 한국어 키워드를 정교한 영어 프롬프트로 자동 변환
- ⚡ **고정 + 변동 프롬프트 자동 결합**: 브랜드 톤앤매너 일관성 유지
- 📦 **일괄 생성 지원**: 여러 이미지를 한 번에 생성
- 🖥️ **GUI 앱 지원**: Mac/Windows에서 실행 가능한 데스크톱 앱 (Flet 기반)
- ⚙️ **캐릭터별 크기 가중치**: GUI에서 캐릭터별 출력 비율 조정 가능
- 🔔 **사용자 친화적 오류 안내**: API 오류 코드별 한국어 해결 방법 안내

---

## 📁 프로젝트 구조

```
image-generator/
├── main.py                 # CLI 진입점
├── gui.py                  # GUI 애플리케이션 (Flet, v0.0.3)
├── build.py                # PyInstaller 패키징 스크립트
├── build_flet.py           # Flet 전용 빌드 스크립트
├── build_native.sh         # 네이티브 빌드 셸 스크립트
├── config.json             # 브랜드 설정 파일
├── requirements.txt        # 의존성
├── requirements-dev.txt    # 개발 의존성
├── .env.example            # API 키 예시
├── assets/
│   ├── logo.png            # 앱 로고 이미지
│   ├── icon.svg            # 앱 아이콘
│   └── character/          # 참조 캐릭터 이미지 폴더
├── scripts/
│   ├── Fix-Damaged-App.command  # macOS 손상된 앱 복구 스크립트
│   ├── create-dmg.sh            # DMG 패키지 생성 스크립트
│   ├── create-icon.py           # 아이콘 생성 스크립트
│   └── convert-icon.py          # 아이콘 변환 스크립트
├── src/
│   ├── __init__.py
│   ├── config_loader.py    # 설정 로더
│   ├── prompt_enhancer.py  # 프롬프트 향상기 (LLM)
│   ├── prompt_builder.py   # 프롬프트 빌더
│   └── image_generator.py  # 이미지 생성기 (Google GenAI SDK)
└── output/                 # 생성된 이미지 저장 위치
```

---

## 🚀 시작하기

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. API 키 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 API 키를 입력합니다:

```
GEMINI_API_KEY=your_api_key_here
```

API 키는 [Google AI Studio](https://aistudio.google.com/app/apikey)에서 발급받으세요.

### 3. 캐릭터 이미지 준비

`assets/character/` 폴더에 캐릭터 이미지를 넣습니다.

**파일명 규칙:**
- `캐릭터명 + 번호.확장자` 형식 권장 (예: `JB1.png`, `JB2.png`)
- 프롬프트에 "JB"를 입력하면 JB로 시작하는 모든 이미지가 자동 참조됨

**권장 사항:**
- 지원 포맷: PNG, JPG, JPEG, WebP
- 정면, 측면 등 다양한 각도 이미지 2~5장
- 최대 5장까지 동시 참조 가능

---

## 💻 사용법

### 🖥️ GUI 모드 (권장)

```bash
python gui.py
```

**GUI 주요 기능:**
- 프롬프트 입력 및 이미지 생성
- 캐릭터 자동 인식 및 크기 가중치 조절
- 생성 진행 상황 실시간 표시
- 결과 폴더 바로 열기
- 설정 화면 (API 키, 브랜드 색상, 모델 선택)
- 완료 알림

### ⌨️ CLI 대화형 모드

```bash
python main.py
```

```
🎭 등록된 캐릭터: JB
🖼️  프롬프트 입력: JB가 선물 상자를 든 모습
🎭 캐릭터 'JB' 감지됨!
   ✓ 참조 이미지: JB1.png
🔄 프롬프트 최적화 중...
   → holding a gift box with both hands, cheerful expression
🎨 이미지 생성 중...
✅ 이미지 생성 완료!
💾 저장됨: output/20260402_093000_선물 상자를 든 모습.png
```

### 단일 생성

```bash
python main.py "JB가 계산기를 들고 설명하는 포즈"
```

### 일괄 생성

```bash
# prompts.txt 작성 후 실행
python main.py --batch prompts.txt
```

---

## 📦 앱 패키징 (배포용)

### Flet 빌드 (권장)

```bash
pip install -r requirements-dev.txt
python build_flet.py
```

### PyInstaller 빌드

```bash
python build.py
```

### macOS DMG 패키지 생성

```bash
bash scripts/create-dmg.sh
```

**빌드 결과물:**
- macOS: `dist/JB Bank Image Generator.app`
- macOS DMG: `dist/JBBank-Image-Generator.dmg`

> **macOS 손상된 앱 오류 시:** `scripts/Fix-Damaged-App.command` 를 더블클릭하면 자동 복구됩니다.

---

## ⚙️ 설정 (config.json)

```json
{
  "brand": {
    "name": "JBBank",
    "main_color": "#FF6B35",
    "sub_color": "#004E89",
    "style_keywords": ["3D rendering", "cute", "soft lighting", "minimal shadow"]
  },
  "output": {
    "format": "png",
    "width": 1024,
    "height": 1024,
    "transparent_background": true,
    "upscale": false
  },
  "paths": {
    "character_dir": "./assets/character",
    "output_dir": "./output"
  },
  "api": {
    "provider": "google",
    "model": "gemini-2.5-flash-image",
    "text_model": "gemini-2.0-flash",
    "max_reference_images": 5
  },
  "prompts": {
    "fixed_prefix": "3D rendered cute character illustration, ...",
    "fixed_suffix": ", soft studio lighting, minimal clean background, ...",
    "negative": "deformed, distorted, ..."
  }
}
```

---

## 🖼️ 지원 이미지 모델

| 모델 | 설명 | 비용 |
|------|------|------|
| `gemini-2.5-flash-image` | Gemini 이미지 생성 (기본값) | Free tier 가능 |
| `gemini-3.1-flash-image-preview` | Gemini 3.1 프리뷰 | Free tier 가능 |
| `imagen-4.0-generate-001` | Imagen 4.0 | 유료 |
| `imagen-4.0-ultra-generate-001` | Imagen 4.0 Ultra (최고 품질) | 유료 |

**지원 비율:** `1:1` · `3:4` · `4:3` · `9:16` · `16:9`

---

## 🔧 프롬프트 규칙

### 캐릭터 자동 감지
- 프롬프트에 캐릭터 이름 포함 시 자동 감지 및 참조 이미지 로드
- 캐릭터명은 프롬프트에서 자동 제거 (이미지 내 텍스트 출력 방지)

### 텍스트 삽입 규칙
- 기본적으로 이미지 내 텍스트 없음
- 필요 시 명시적으로 요청:
  - ✅ `JB가 "안녕하세요" 말풍선을 들고 있는 모습`
  - ✅ `배경에 "SALE" 텍스트 추가`

---

## 🛡️ 오류 안내

주요 API 오류에 대한 한국어 안내를 자동으로 제공합니다:

| 오류 코드 | 안내 |
|---|---|
| `PERMISSION_DENIED` | API 키 권한 오류 → 재발급 안내 |
| `RESOURCE_EXHAUSTED` | 일일 할당량 초과 → 재시도 안내 |
| `SAFETY` | 안전 필터 차단 → 프롬프트 수정 안내 |
| `DEADLINE_EXCEEDED` | 요청 시간 초과 → 네트워크 확인 안내 |

---

## 📝 참고 링크

- [Google AI Studio - API 키 발급](https://aistudio.google.com/app/apikey)
- [Gemini API 문서](https://ai.google.dev/docs)
- [Flet 공식 문서](https://flet.dev)

---

## 📄 라이선스

MIT License
