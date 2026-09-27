# 기여 가이드

Python 3.10 이상에서 저장소 루트 기준으로 실행합니다.

```bash
python -m venv .venv
# 가상환경 활성화 후
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m examples.demo
```

테스트는 API 키나 모델 다운로드 없이 실행됩니다. FFmpeg가 없으면 실제 추출 통합 테스트만 건너뜁니다. CI에서는 FFmpeg를 설치해 전체 테스트를 실행합니다. 실제 화면·모델 실행에는 `requirements.txt`가 별도로 필요합니다.

변경은 별도 브랜치에서 진행하고 PR에 해결한 문제, 동작 변화, 검증 결과와 미검증 범위를 적어주세요. API 호출·GPU 검증은 오프라인 테스트 결과와 구분해주세요. 오류 제보 시 키나 영상·자막의 개인 정보는 제거해주세요.
