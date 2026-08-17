import os
import sys

# On Windows, pip-installed NVIDIA CUDA DLLs (cublas, cudnn) aren't
# automatically added to the DLL search path. Register them manually
# before importing faster_whisper / ctranslate2.
if sys.platform == "win32":
    venv_site_packages = os.path.join(
        os.path.dirname(sys.executable), "..", "Lib", "site-packages"
    )
    nvidia_base = os.path.join(venv_site_packages, "nvidia")
    for pkg in ("cublas", "cudnn"):
        dll_dir = os.path.join(nvidia_base, pkg, "bin")
        if os.path.isdir(dll_dir):
            os.add_dll_directory(dll_dir)

from faster_whisper import WhisperModel


class SpeechToText:

    def __init__(
        self,
        model_size="base",
        device="cuda",
        compute_type=None,
        language=None,
    ):
        if compute_type is None:
            compute_type = "float16" if device == "cuda" else "int8"

        self.language = language

        print(f"Loading faster-whisper (model={model_size}, device={device}, compute_type={compute_type})...")

        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
            )
        except Exception as e:
            if device == "cuda":
                print(f"CUDA load failed ({e}), falling back to CPU...")
                self.model = WhisperModel(
                    model_size,
                    device="cpu",
                    compute_type="int8",
                )
            else:
                raise

        print("faster-whisper loaded.")

    def transcribe(self, audio, language=None, vad_filter=True):
        """
        audio: file path (str) OR numpy float32 mono array at 16kHz
        """
        segments, info = self.model.transcribe(
            audio,
            beam_size=5,
            vad_filter=vad_filter,
            language=language or self.language,
        )

        text = " ".join(segment.text.strip() for segment in segments)
        text = text.strip()

        return text, info