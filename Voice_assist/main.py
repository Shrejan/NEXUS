import os
import sys
import time

import numpy as np
import pyaudio
import torch
import openwakeword

# ============================================================
# WINDOWS CUDA DLL FIX (must run before importing faster_whisper)
# ============================================================
# Pip-installed nvidia-cublas-cu12 / nvidia-cudnn-cu12 packages don't
# automatically register their DLL folders on Windows. Without this,
# WhisperModel.transcribe() crashes with:
#   RuntimeError: Library cublas64_12.dll is not found or cannot be loaded
if sys.platform == "win32":
    venv_site_packages = os.path.join(
        os.path.dirname(sys.executable), "..", "Lib", "site-packages"
    )
    nvidia_base = os.path.join(venv_site_packages, "nvidia")
    for pkg in ("cublas", "cudnn"):
        dll_dir = os.path.join(nvidia_base, pkg, "bin")
        if os.path.isdir(dll_dir):
            os.add_dll_directory(dll_dir)

from openwakeword.model import Model
from faster_whisper import WhisperModel


# ============================================================
# CONFIGURATION
# ============================================================

SAMPLE_RATE = 16000

# Silero VAD (current version) requires EXACTLY 512 samples per call
# at 16kHz. openWakeWord tolerates smaller chunks fine (it buffers
# internally), so we standardize on 512 for both.
CHUNK_SIZE = 512

WAKE_THRESHOLD = 0.5
SPEECH_THRESHOLD = 0.5

# How long silence must continue before command ends
SILENCE_DURATION = 1.0

# Whisper model
WHISPER_MODEL = "base"

# NVIDIA GPU
WHISPER_DEVICE = "cuda"
WHISPER_COMPUTE_TYPE = "float16"


# ============================================================
# LOAD OPENWAKEWORD
# ============================================================

print()
print("========================================")
print("Loading openWakeWord...")
print("========================================")

openwakeword.utils.download_models()

wake_model = Model(
    wakeword_models=["hey_mycroft"],
    inference_framework="onnx"
)

print("openWakeWord loaded")


# ============================================================
# LOAD SILERO VAD
# ============================================================

print()
print("========================================")
print("Loading Silero VAD...")
print("========================================")

vad_model, vad_utils = torch.hub.load(
    repo_or_dir="snakers4/silero-vad",
    model="silero_vad",
    force_reload=False
)

print("Silero VAD loaded")


# ============================================================
# LOAD FASTER-WHISPER
# ============================================================

print()
print("========================================")
print("Loading faster-whisper...")
print("========================================")

try:
    whisper_model = WhisperModel(
        WHISPER_MODEL,
        device=WHISPER_DEVICE,
        compute_type=WHISPER_COMPUTE_TYPE
    )
except Exception as e:
    print(f"CUDA load failed ({e}), falling back to CPU...")
    whisper_model = WhisperModel(
        WHISPER_MODEL,
        device="cpu",
        compute_type="int8"
    )

print("faster-whisper loaded")


# ============================================================
# MICROPHONE
# ============================================================

audio = pyaudio.PyAudio()

stream = audio.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=SAMPLE_RATE,
    input=True,
    frames_per_buffer=CHUNK_SIZE
)


# ============================================================
# STATES
# ============================================================

IDLE = "IDLE"
WAITING_FOR_SPEECH = "WAITING_FOR_SPEECH"
RECORDING = "RECORDING"

state = IDLE

command_audio = []

last_speech_time = None

# Safety timeout: if we never hear speech after wake word, give up
WAITING_TIMEOUT = 8.0
waiting_start_time = None


# ============================================================
# WHISPER FUNCTION
# ============================================================

def transcribe_audio(audio_data):

    print()
    print("Transcribing...")

    start_time = time.time()

    # Convert int16 -> float32
    audio_float = (
        audio_data.astype(np.float32) / 32768.0
    )

    segments, info = whisper_model.transcribe(
        audio_float,
        beam_size=5,
        vad_filter=False
    )

    text = ""

    for segment in segments:
        text += segment.text

    elapsed = time.time() - start_time

    text = text.strip()

    print()
    print("========================================")
    print("TRANSCRIPTION")
    print("========================================")

    if text:
        print(text)
    else:
        print("(no speech detected)")

    print("----------------------------------------")
    print(
        f"Language: {info.language} "
        f"(p={info.language_probability:.2f})"
    )
    print(f"Time: {elapsed:.2f}s")
    print("========================================")

    return text


# ============================================================
# REMOVE WAKE WORD
# ============================================================

def remove_wake_word(text):

    text_lower = text.lower().strip()

    wake_words = [
        "hey jarvis",
        "jarvis"
    ]

    for wake_word in wake_words:

        if text_lower.startswith(wake_word):

            text = text[len(wake_word):].strip()

            break

    return text


# ============================================================
# MAIN LOOP
# ============================================================

print()
print()
print("============================================")
print("          NEXUS VOICE ASSISTANT")
print("============================================")
print()
print("Wake word : Hey Jarvis")
print("State     : IDLE")
print()
print("Waiting for wake word...")
print("============================================")


try:

    while True:

        # ----------------------------------------------------
        # READ MICROPHONE
        # ----------------------------------------------------

        data = stream.read(
            CHUNK_SIZE,
            exception_on_overflow=False
        )

        audio_chunk = np.frombuffer(
            data,
            dtype=np.int16
        )


        # ====================================================
        # STATE 1 - IDLE
        # ====================================================

        if state == IDLE:

            prediction = wake_model.predict(
                audio_chunk
            )

            for wake_word, score in prediction.items():

                if score >= WAKE_THRESHOLD:

                    print()
                    print("================================")
                    print("NEXUS ACTIVATED")
                    print("================================")

                    state = WAITING_FOR_SPEECH

                    command_audio = []

                    waiting_start_time = time.time()

                    break


        # ====================================================
        # STATE 2 - WAITING FOR SPEECH
        # ====================================================

        elif state == WAITING_FOR_SPEECH:

            audio_float = torch.from_numpy(
                audio_chunk.astype(np.float32)
            ) / 32768.0

            speech_probability = vad_model(
                audio_float,
                SAMPLE_RATE
            ).item()

            if speech_probability >= SPEECH_THRESHOLD:

                print("Speech detected")

                state = RECORDING

                command_audio.append(
                    audio_chunk.copy()
                )

                last_speech_time = time.time()

            elif time.time() - waiting_start_time >= WAITING_TIMEOUT:

                print()
                print("No speech detected, going back to sleep.")
                print("Listening for wake word...")

                state = IDLE


        # ====================================================
        # STATE 3 - RECORDING
        # ====================================================

        elif state == RECORDING:

            command_audio.append(
                audio_chunk.copy()
            )

            audio_float = torch.from_numpy(
                audio_chunk.astype(np.float32)
            ) / 32768.0

            speech_probability = vad_model(
                audio_float,
                SAMPLE_RATE
            ).item()

            # -----------------------------------------------
            # USER IS SPEAKING
            # -----------------------------------------------

            if speech_probability >= SPEECH_THRESHOLD:

                last_speech_time = time.time()

            # -----------------------------------------------
            # USER IS SILENT
            # -----------------------------------------------

            else:

                silence_time = (
                    time.time() - last_speech_time
                )

                if silence_time >= SILENCE_DURATION:

                    print()
                    print("Speech ended")

                    command = np.concatenate(
                        command_audio
                    )

                    duration = (
                        len(command) / SAMPLE_RATE
                    )

                    print(f"Recorded: {duration:.2f} seconds")

                    text = transcribe_audio(command)

                    text = remove_wake_word(text)

                    print()
                    print("USER COMMAND:")
                    print(text)

                    command_audio = []

                    state = IDLE

                    print()
                    print("----------------------------------------")
                    print("Listening for wake word...")
                    print("----------------------------------------")


except KeyboardInterrupt:

    print()
    print("Stopping NEXUS...")


finally:

    stream.stop_stream()
    stream.close()

    audio.terminate()

    print("NEXUS stopped.")