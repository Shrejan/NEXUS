import os
import sys
import time

import numpy as np
import pyaudio
import torch
import openwakeword

from openwakeword.model import Model
from faster_whisper import WhisperModel


# ============================================================
# WINDOWS CUDA DLL FIX
# ============================================================

if sys.platform == "win32":

    venv_site_packages = os.path.join(
        os.path.dirname(sys.executable),
        "..",
        "Lib",
        "site-packages"
    )

    nvidia_base = os.path.join(
        venv_site_packages,
        "nvidia"
    )

    for pkg in ("cublas", "cudnn"):

        dll_dir = os.path.join(
            nvidia_base,
            pkg,
            "bin"
        )

        if os.path.isdir(dll_dir):

            os.environ["PATH"] = (
                dll_dir
                + os.pathsep
                + os.environ["PATH"]
            )

            os.add_dll_directory(dll_dir)


# ============================================================
# CONFIGURATION
# ============================================================

SAMPLE_RATE = 16000

# Silero VAD requires 512 samples at 16 kHz
CHUNK_SIZE = 512


# ============================================================
# WAKE WORD
# ============================================================

WAKE_THRESHOLD = 0.5

# Prevent immediate re-triggering
WAKE_COOLDOWN = 1.5


# ============================================================
# SPEECH
# ============================================================

SPEECH_THRESHOLD = 0.5

# Silence required to finish command
SILENCE_DURATION = 1.0

# Maximum time to wait for command
WAITING_TIMEOUT = 8.0


# ============================================================
# IMPORTANT
#
# After wake word detection, don't immediately run VAD.
#
# The remaining part of "Hey Jarvis" is still in the
# microphone buffer and VAD will think it is a command.
#
# Wait this long before accepting speech.
# ============================================================

WAKE_TO_COMMAND_DELAY = 0.8


# ============================================================
# WHISPER
# ============================================================

WHISPER_MODEL = "base"

WHISPER_DEVICE = "cuda"

WHISPER_COMPUTE_TYPE = "float16"


# ============================================================
# STATES
# ============================================================

SLEEPING = "SLEEPING"

WAITING_FOR_SPEECH = "WAITING_FOR_SPEECH"

RECORDING = "RECORDING"


# ============================================================
# GLOBAL STATE
# ============================================================

state = SLEEPING

command_audio = []

last_speech_time = None

waiting_start_time = None

wake_cooldown_until = 0.0

wake_detected_recently = False

wake_to_command_time = 0.0


# ============================================================
# LOAD OPENWAKEWORD
# ============================================================

print()
print("========================================")
print("Loading openWakeWord...")
print("========================================")

openwakeword.utils.download_models()

wake_model = Model(
    wakeword_models=["alexa"],
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
# LOAD FASTER WHISPER
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

    print("Whisper running on CUDA")

except Exception as e:

    print()
    print("CUDA load failed:")
    print(e)

    print()
    print("Falling back to CPU...")

    whisper_model = WhisperModel(
        WHISPER_MODEL,
        device="cpu",
        compute_type="int8"
    )

    print("Whisper running on CPU")


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
# TRANSCRIBE AUDIO
# ============================================================

def transcribe_audio(audio_data):

    print()
    print("========================================")
    print("Transcribing...")
    print("========================================")

    start_time = time.time()

    # --------------------------------------------------------
    # Convert int16 -> float32
    # --------------------------------------------------------

    audio_float = (
        audio_data.astype(np.float32)
        / 32768.0
    )

    # --------------------------------------------------------
    # Whisper
    # --------------------------------------------------------

    segments, info = whisper_model.transcribe(
        audio_float,
        beam_size=5,
        vad_filter=False
    )

    text = ""

    for segment in segments:
        text += segment.text

    text = text.strip()

    elapsed = time.time() - start_time

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

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

    print(
        f"Time: {elapsed:.2f}s"
    )

    print("========================================")

    return text


# ============================================================
# REMOVE WAKE WORD
# ============================================================

def remove_wake_word(text):

    text_lower = text.lower().strip()

    wake_words = [
        "hey jarvis",
        "jarvis",
        "hey alexa",
        "alexa"
    ]

    for wake_word in wake_words:

        if text_lower.startswith(wake_word):

            text = text[
                len(wake_word):
            ].strip()

            break

    return text


# ============================================================
# PROCESS COMMAND
# ============================================================

def process_command(command):

    print()
    print("========================================")
    print("NEXUS COMMAND")
    print("========================================")

    print(command)

    print("========================================")

    # ========================================================
    # PUT YOUR NEXUS AGENT HERE
    # ========================================================

    # Example:
    #
    # response = nexus_agent(command)
    #
    # print("NEXUS:")
    # print(response)

    print()
    print("Command processing finished.")


# ============================================================
# GO TO SLEEP
# ============================================================

def go_to_sleep():

    global state
    global command_audio
    global last_speech_time
    global waiting_start_time
    global wake_cooldown_until
    global wake_detected_recently

    # --------------------------------------------------------
    # Clear audio
    # --------------------------------------------------------

    command_audio = []

    # --------------------------------------------------------
    # Clear timers
    # --------------------------------------------------------

    last_speech_time = None

    waiting_start_time = None

    # --------------------------------------------------------
    # Sleeping state
    # --------------------------------------------------------

    state = SLEEPING

    # --------------------------------------------------------
    # Cooldown
    # --------------------------------------------------------

    wake_cooldown_until = (
        time.time()
        + WAKE_COOLDOWN
    )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # Don't allow the same wake detection to fire again.
    # The wake score must fall below threshold first.
    # --------------------------------------------------------

    wake_detected_recently = True

    print()
    print("========================================")
    print("          NEXUS SLEEPING")
    print("========================================")

    print()
    print("Listening for wake word...")


# ============================================================
# STARTUP
# ============================================================

print()
print()

print("============================================")
print("          NEXUS VOICE ASSISTANT")
print("============================================")

print()

print("Wake word : Hey Jarvis")
print("State     : SLEEPING")

print()

print("Listening for wake word...")

print("============================================")


# ============================================================
# MAIN LOOP
# ============================================================

try:

    while True:

        # ====================================================
        # READ MICROPHONE
        # ====================================================

        data = stream.read(
            CHUNK_SIZE,
            exception_on_overflow=False
        )

        audio_chunk = np.frombuffer(
            data,
            dtype=np.int16
        )


        # ====================================================
        # STATE 1
        #
        # SLEEPING
        #
        # ONLY wake-word detection.
        # ====================================================

        if state == SLEEPING:

            # ------------------------------------------------
            # Cooldown
            # ------------------------------------------------

            if time.time() < wake_cooldown_until:

                continue


            # ------------------------------------------------
            # Run wake-word model
            # ------------------------------------------------

            prediction = wake_model.predict(
                audio_chunk
            )


            # ------------------------------------------------
            # Get highest score
            # ------------------------------------------------

            max_score = max(
                prediction.values()
            )


            # ------------------------------------------------
            # Wake score must first fall below threshold.
            #
            # This prevents:
            #
            # wake
            # ↓
            # sleep
            # ↓
            # same wake detection
            # ↓
            # wake again
            # ------------------------------------------------

            if max_score < WAKE_THRESHOLD:

                wake_detected_recently = False


            # ------------------------------------------------
            # Detect NEW wake word
            # ------------------------------------------------

            if not wake_detected_recently:

                for wake_word, score in prediction.items():

                    if score >= WAKE_THRESHOLD:

                        print()
                        print("================================")
                        print("       NEXUS ACTIVATED")
                        print("================================")

                        print(
                            f"Wake word: {wake_word}"
                        )

                        print(
                            f"Confidence: {score:.2f}"
                        )

                        print()

                        print(
                            "Waiting for your command..."
                        )


                        # ------------------------------------
                        # Mark wake as detected
                        # ------------------------------------

                        wake_detected_recently = True


                        # ------------------------------------
                        # Clear previous command audio
                        # ------------------------------------

                        command_audio = []


                        # ------------------------------------
                        # Start waiting timer
                        # ------------------------------------

                        waiting_start_time = (
                            time.time()
                        )


                        # ------------------------------------
                        # IMPORTANT
                        #
                        # Don't let VAD detect the wake word
                        # as the command.
                        # ------------------------------------

                        wake_to_command_time = (
                            time.time()
                            + WAKE_TO_COMMAND_DELAY
                        )


                        # ------------------------------------
                        # Change state
                        # ------------------------------------

                        state = WAITING_FOR_SPEECH

                        break


        # ====================================================
        # STATE 2
        #
        # WAITING FOR SPEECH
        # ====================================================

        elif state == WAITING_FOR_SPEECH:

            # =================================================
            # WAIT AFTER WAKE WORD
            #
            # Ignore audio for a short period.
            #
            # This is the critical fix.
            # =================================================

            if time.time() < wake_to_command_time:

                continue


            # =================================================
            # CHECK TIMEOUT
            # =================================================

            if (
                time.time()
                - waiting_start_time
                >= WAITING_TIMEOUT
            ):

                print()
                print("================================")
                print("No command detected.")
                print("NEXUS going back to sleep.")
                print("================================")

                go_to_sleep()

                continue


            # =================================================
            # RUN SILERO VAD
            # =================================================

            audio_float = torch.from_numpy(
                audio_chunk.astype(np.float32)
            ) / 32768.0


            speech_probability = vad_model(
                audio_float,
                SAMPLE_RATE
            ).item()


            # =================================================
            # USER STARTED SPEAKING
            # =================================================

            if speech_probability >= SPEECH_THRESHOLD:

                print()
                print("Speech detected")

                print(
                    "Recording command..."
                )


                # --------------------------------------------
                # Start recording
                # --------------------------------------------

                state = RECORDING


                # --------------------------------------------
                # Save first command chunk
                # --------------------------------------------

                command_audio.append(
                    audio_chunk.copy()
                )


                # --------------------------------------------
                # Start silence timer
                # --------------------------------------------

                last_speech_time = time.time()


        # ====================================================
        # STATE 3
        #
        # RECORDING
        # ====================================================

        elif state == RECORDING:

            # ------------------------------------------------
            # Save audio
            # ------------------------------------------------

            command_audio.append(
                audio_chunk.copy()
            )


            # ------------------------------------------------
            # VAD
            # ------------------------------------------------

            audio_float = torch.from_numpy(
                audio_chunk.astype(np.float32)
            ) / 32768.0


            speech_probability = vad_model(
                audio_float,
                SAMPLE_RATE
            ).item()


            # =================================================
            # USER SPEAKING
            # =================================================

            if speech_probability >= SPEECH_THRESHOLD:

                last_speech_time = time.time()


            # =================================================
            # USER SILENT
            # =================================================

            else:

                silence_time = (
                    time.time()
                    - last_speech_time
                )


                # ------------------------------------------------
                # Enough silence
                # ------------------------------------------------

                if silence_time >= SILENCE_DURATION:

                    print()
                    print("================================")
                    print("Speech ended")
                    print("================================")


                    # =================================================
                    # COMBINE AUDIO
                    # =================================================

                    command = np.concatenate(
                        command_audio
                    )


                    # =================================================
                    # DURATION
                    # =================================================

                    duration = (
                        len(command)
                        / SAMPLE_RATE
                    )

                    print(
                        f"Recorded: {duration:.2f} seconds"
                    )


                    # =================================================
                    # TRANSCRIBE
                    # =================================================

                    text = transcribe_audio(
                        command
                    )


                    # =================================================
                    # REMOVE WAKE WORD
                    # =================================================

                    text = remove_wake_word(
                        text
                    )


                    # =================================================
                    # USER COMMAND
                    # =================================================

                    print()
                    print("========================================")
                    print("USER COMMAND")
                    print("========================================")

                    if text:

                        print(text)

                    else:

                        print(
                            "(empty command)"
                        )

                    print(
                        "========================================"
                    )


                    # =================================================
                    # EXECUTE COMMAND
                    # =================================================

                    if text:

                        process_command(
                            text
                        )

                    else:

                        print(
                            "Nothing to execute."
                        )


                    # =================================================
                    # GO BACK TO SLEEP
                    # =================================================

                    go_to_sleep()


# ============================================================
# CTRL+C
# ============================================================

except KeyboardInterrupt:

    print()
    print()
    print("Stopping NEXUS...")


# ============================================================
# CLEANUP
# ============================================================

finally:

    print()
    print("Cleaning microphone...")

    stream.stop_stream()

    stream.close()

    audio.terminate()

    print("NEXUS stopped.")