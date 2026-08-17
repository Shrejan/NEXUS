import time
import numpy as np
import pyaudio
import openwakeword
from openwakeword.model import Model


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

SAMPLE_RATE = 16000

# 1280 samples = 80 ms at 16 kHz
CHUNK = 1280

THRESHOLD = 0.5


# --------------------------------------------------
# DOWNLOAD PRETRAINED MODELS
# --------------------------------------------------

print("Loading openWakeWord models...")

openwakeword.utils.download_models()


# --------------------------------------------------
# LOAD "HEY JARVIS" MODEL
# --------------------------------------------------

model = Model(
    wakeword_models=["hey_mycroft"],
    inference_framework="onnx"
)

print("Model loaded.")


# --------------------------------------------------
# MICROPHONE
# --------------------------------------------------

audio = pyaudio.PyAudio()

stream = audio.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=SAMPLE_RATE,
    input=True,
    frames_per_buffer=CHUNK
)


# --------------------------------------------------
# LISTEN
# --------------------------------------------------

print()
print("=" * 50)
print("NEXUS WAKE WORD DETECTOR")
print("=" * 50)
print("Say:  Hey Jarvis")
print("Press Ctrl+C to stop")
print("=" * 50)
print()


try:

    while True:

        # Read microphone audio
        audio_data = stream.read(
            CHUNK,
            exception_on_overflow=False
        )

        # Convert bytes → int16 numpy array
        audio_frame = np.frombuffer(
            audio_data,
            dtype=np.int16
        )

        # Run wake-word detection
        prediction = model.predict(audio_frame)

        # Get scores
        for wake_word, score in prediction.items():

            print(
                f"\r{wake_word}: {score:.3f}",
                end=""
            )

            # Wake word detected
            if score >= THRESHOLD:

                print()
                print()
                print("================================")
                print("🔥 WAKE WORD DETECTED!")
                print("================================")
                print()

                # Prevent immediate repeated detections
                time.sleep(1)


except KeyboardInterrupt:

    print("\nStopping...")


finally:

    stream.stop_stream()
    stream.close()
    audio.terminate()