import time

import sounddevice as sd
import soundfile as sf

from STT import SpeechToText


SAMPLE_RATE = 16000
RECORD_SECONDS = 5
OUTPUT_FILE = "test.wav"


def record_audio(duration, sample_rate):
    print(f"Recording for {duration}s...")
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    return audio


def main():
    print("Loading STT...")
    stt = SpeechToText(
        model_size="base",
        device="cuda",
        compute_type="float16",
    )

    audio = record_audio(RECORD_SECONDS, SAMPLE_RATE)

    sf.write(OUTPUT_FILE, audio, SAMPLE_RATE)
    print(f"Saved recording to {OUTPUT_FILE}")

    print("Transcribing...")
    start = time.time()
    text, info = stt.transcribe(audio.flatten())
    elapsed = time.time() - start

    print()
    print("================================")
    print("TRANSCRIPTION:")
    print(text if text else "(no speech detected)")
    print("--------------------------------")
    print(f"Detected language: {info.language} (p={info.language_probability:.2f})")
    print(f"Time taken: {elapsed:.2f}s")
    print("================================")


if __name__ == "__main__":
    main()