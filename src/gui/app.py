import streamlit as st
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Add project root to sys.path to allow imports from src
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.utils.gpu_setup import add_nvidia_dll_path
from src.core.pipeline import generate_subtitles
import logging

import keyring

logger = logging.getLogger(__name__)

SERVICE_NAME = "AutoSub-AI"
USERNAME = "gemini_api_key"

def load_api_key():
    try:
        return keyring.get_password(SERVICE_NAME, USERNAME)
    except Exception as e:
        logger.error(f"Keyring error: {e}")
        return None

def save_api_key(key):
    try:
        keyring.set_password(SERVICE_NAME, USERNAME, key)
        st.toast("API Key 저장 완료", icon="🔒")
    except Exception as e:
        st.error(f"API Key 저장 실패: {e}")

def main():
    # Setup GPU paths
    add_nvidia_dll_path()

    st.set_page_config(
        page_title="AutoSub-AI",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🎬 AutoSub-AI")
    st.markdown("### 영상 파일에서 자막을 자동으로 생성하고 교정합니다.")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # API Key
        st.markdown("[🔑 Gemini API Key 발급받기](https://aistudio.google.com/app/apikey)")
        saved_key = load_api_key()
        api_key_input = st.text_input("Gemini API Key", value=saved_key if saved_key else "", type="password", help="Google Gemini API Key를 입력하세요.")
        
        if st.button("API Key 저장"):
            if api_key_input:
                save_api_key(api_key_input)
            else:
                st.warning("API Key를 입력하세요.")
        
        # Use the input value for processing
        api_key = api_key_input
        
        # Model Settings
        st.subheader("모델 설정")
        model_size = st.selectbox("Whisper 모델 크기", ["base", "small", "medium", "large-v3"], index=3)
        device = st.selectbox("디바이스", ["auto", "cuda", "cpu"], index=0)
        
        # Output Settings
        st.subheader("출력 설정")
        # Default output dir relative to project root or user home?
        # For portable app, maybe relative to exe or in Documents.
        default_output = str(project_root / "output")
        output_dir = st.text_input("출력 경로", value=default_output)
        
    # Main Content
    uploaded_file = st.file_uploader("영상 파일을 업로드하세요", type=["mp4", "mkv", "avi", "mov", "webm"])
    
    if uploaded_file:
        # Validate size (4GB limit)
        MAX_SIZE_MB = 4096
        if uploaded_file.size > MAX_SIZE_MB * 1024 * 1024:
            st.error(f"파일 크기가 너무 큽니다. (최대 {MAX_SIZE_MB}MB)")
            return

        if st.button("자막 생성 시작", type="primary"):
            st.session_state.pop("subtitle_result", None)
            if not api_key:
                st.error("API Key가 필요합니다.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()

                def report(percent, message):
                    progress_bar.progress(percent)
                    status_text.text(message)

                try:
                    # Keep uploads separate across sessions and remove them on failure too.
                    with TemporaryDirectory(prefix="autosub-upload-") as temp_dir:
                        filename = Path(uploaded_file.name.replace("\\", "/")).name
                        temp_path = Path(temp_dir) / filename
                        temp_path.write_bytes(uploaded_file.getbuffer())
                        output_path = generate_subtitles(
                            str(temp_path), output_dir,
                            api_key=api_key, model_size=model_size,
                            device=device, progress=report,
                        )
                        st.session_state["subtitle_result"] = {
                            "source": uploaded_file.file_id,
                            "path": str(output_path),
                            "content": output_path.read_text(encoding="utf-8"),
                        }
                except Exception as e:
                    st.error(f"작업 중 오류 발생: {e}")
                    logger.error("Processing error", exc_info=True)

        result = st.session_state.get("subtitle_result")
        if result and result["source"] == uploaded_file.file_id:
            st.success(f"자막 생성 완료: {result['path']}")
            st.caption("교정 요청이 실패한 구간은 원문으로 유지됩니다. 내용을 확인해주세요.")
            st.text_area("자막 내용", value=result["content"], height=300)
            st.download_button(
                "SRT 다운로드", data=result["content"].encode("utf-8"),
                file_name=Path(result["path"]).name, mime="text/plain",
            )

if __name__ == "__main__":
    main()
