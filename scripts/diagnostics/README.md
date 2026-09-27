# 개발 진단 도구

저장소 루트에서 모듈로 실행합니다. 일반 실행이나 테스트에는 필요하지 않습니다.

- `python -m scripts.diagnostics.debug_gpu_paths`: GPU 라이브러리 경로 조사
- `python -m scripts.diagnostics.debug_gpu_paths_v2`: 추가 GPU 경로 조사
- `python -m scripts.diagnostics.debug_gemini_models`: 저장된 키 또는 환경변수로 Gemini 모델 목록 조회. 실제 네트워크 요청을 수행합니다.

출력 로그는 커밋하지 않습니다. 과거 수동 테스트는 `tests/`의 pytest 테스트로 대체했습니다.
