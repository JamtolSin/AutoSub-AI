# AutoSub-AI

영상에서 한국어 음성을 인식하고 Gemini로 문장을 교정해 SRT 자막을 만드는 개인 프로젝트입니다. Streamlit 화면과 자막 처리 로직을 분리해 각 단계를 독립적으로 검토할 수 있습니다.

## 처리 흐름

`영상 → FFmpeg 오디오 추출 → faster-whisper 음성 인식 → Gemini 텍스트 교정 → SRT`

- 교정 결과에는 원래 인식된 시간 정보를 유지합니다.
- 교정 실패 또는 구간 수 불일치 시 해당 구간의 원문을 유지합니다. 결과를 직접 확인해야 합니다.
- 업로드 파일과 추출된 오디오는 작업별 임시 폴더를 사용하고 완료·실패 시 정리합니다.
- 결과 SRT는 지정한 출력 폴더에 남습니다.

## 코드부터 확인하기

1. [처리 흐름](src/core/pipeline.py): 화면과 분리된 실행 순서, 임시 파일 수명, 진행률
2. [LLM 교정](src/core/llm_engine.py): 배치 처리, 재시도, 응답 검증, 원본 시간 보존
3. [SRT 출력](src/core/srt_generator.py): 밀리초 반올림과 입력 검증
4. [테스트](tests): 실패 경로, 파일 정리, 잘못된 교정 응답, 실제 FFmpeg 추출

## API 없이 확인하기

Python 3.10 이상이 필요합니다. 테스트는 Python 3.11 기준입니다. 아래 명령은 저장소 루트에서 실행합니다.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q -m "not integration"
python -m examples.demo
```

예제는 고정된 두 문장으로 `output/demo.srt`를 만듭니다. 음성 인식·AI 교정 성능을 보여주는 예제는 아닙니다. 모델 다운로드, GPU, API 키가 필요하지 않습니다.

## 실제 영상 처리

FFmpeg 실행 파일을 PATH에 등록하고 다음을 실행합니다. Windows에서는 `tools/ffmpeg.exe`도 지원합니다.

```bash
python -m pip install -r requirements.txt
python -m streamlit run src/gui/app.py
```

화면에서 Gemini API 키, Whisper 모델, 처리 장치, 출력 폴더를 선택한 뒤 영상을 업로드합니다. 키 저장은 선택 사항이며 운영체제의 keyring을 사용합니다. 첫 인식 시 Whisper 모델이 다운로드됩니다. 인식된 자막 텍스트는 교정을 위해 Gemini API로 전송되며 API 이용 비용이 발생할 수 있습니다.

CPU는 `cpu`를 선택합니다. CUDA 사용 시 호환되는 NVIDIA 드라이버와 CUDA 라이브러리가 별도로 필요합니다. 선택 의존성은 `requirements-gpu.txt`에 있습니다. 모델 크기와 장치에 따른 속도·정확도는 이 저장소에서 정량 검증하지 않았습니다.

## 검증 범위와 한계

```bash
# FFmpeg가 설치되어 있으면 실제 추출 테스트까지 실행
python -m pytest -q
```

- CI는 모델/API 없이 핵심 로직과 실제 FFmpeg 추출을 검사합니다. FFmpeg가 없는 로컬 환경에서는 추출 통합 테스트 하나가 건너뛰어집니다. `FFMPEG_BINARY`로 테스트용 실행 파일 경로를 지정할 수 있습니다.
- 실제 Whisper 추론, Gemini 서비스 응답, CUDA 실행, Windows 실행 파일 패키징은 자동 테스트 범위에 포함하지 않습니다.
- Gemini 연동은 기존 `google-generativeai` SDK를 유지합니다. 서비스·모델 지원 변경에 따라 별도 점검이 필요합니다.
- 청크 병렬 처리 옵션은 구현되지 않아 화면에서 제거했습니다.

## 기타 파일

- `src/gui_launcher.py`, `autosub.spec`: 기존 Windows 트레이 실행 및 패키징 코드. 패키징 의존성은 `requirements-build.txt`에 있으며 이번 정리에서 EXE를 재빌드하지 않았습니다.
- [진단 스크립트](scripts/diagnostics/README.md): 개발용 도구
- [초기 설계 기록](docs/history/README.md): 현재 동작과 다른 과거 계획·설정

기여 방법은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요. 현재 별도 LICENSE 파일은 포함되어 있지 않습니다.
