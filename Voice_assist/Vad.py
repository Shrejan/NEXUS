import torch
import numpy as np


class SileroVAD:

    def __init__(self):

        print("Loading Silero VAD...")

        self.model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False
        )

        (
            self.get_speech_timestamps,
            self.save_audio,
            self.read_audio,
            self.VADIterator,
            self.collect_chunks
        ) = utils

        print("Silero VAD loaded.")

    def is_speech(self, audio_chunk, sample_rate=16000):

        # Convert numpy → torch
        audio = torch.from_numpy(
            audio_chunk.astype(np.float32)
        )

        # Normalize int16 → float32
        audio = audio / 32768.0

        speech_probability = self.model(
            audio,
            sample_rate
        ).item()

        return speech_probability, speech_probability > 0.5