#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path
import sounddevice as sd
import soundfile as sf 
import numpy as np
import sherpa_onnx
import json
from typing import List

def init_microphone(sample_rate: int = 16000):
    devices = sd.query_devices()
    if len(devices) == 0:
        print("No microphone devices found")
        sys.exit(0)

    print(devices)

    if "SHERPA_ONNX_MIC_DEVICE" in os.environ:
        input_device_idx = int(os.environ.get("SHERPA_ONNX_MIC_DEVICE"))
        sd.default.device[0] = input_device_idx
        print(f'Use selected device: {devices[input_device_idx]["name"]}')
    else:
        input_device_idx = sd.default.device[0]
        print(f'Use default device: {devices[input_device_idx]["name"]}')
        
    stream = sd.InputStream(
        channels=1,
        dtype="float32",
        samplerate=sample_rate,
        device=input_device_idx
    )

    return stream

class VadModule:
    def __init__(self):
        self.sample_rate = 16000
        self.frame_size = 100  # 0.1 second = 100 ms
        config = sherpa_onnx.VadModelConfig()
        config.silero_vad.model = "./models/silero_vad.onnx"
        config.sample_rate = self.sample_rate
        self.vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)
        self.input_device =  init_microphone(self.sample_rate)
        
    async def vad_handler(self,vad_callback):
        try:
            with self.input_device:
                while True:
                    samples, _ = self.input_device.read(self.frame_size) 

                    self.vad.accept_waveform(samples)

                    # if self.vad.is_speech_detected() and not printed:
                    #     print("Detected speech")
                    #     printed = True

                    # if not self.vad.is_speech_detected():
                    #     printed = False

                    while not self.vad.empty():
                        samples = self.vad.front.samples
                        # duration = len(samples) / self.sample_rate
                        # sherpa_onnx.write_wave(filename, samples, self.sample_rate)
                        await vad_callback(samples)
                        self.vad.pop()
        except KeyboardInterrupt:
            print("Recording stopped.")

class AsrModule:
    def __init__(self):
        self.sample_rate = 16000
        self.frame_size = 100  # 0.1 second = 100 ms
        self.model = "./models/sherpa-onnx-dolphin-small-ctc-multi-lang-int8-2025-04-02/model.int8.onnx"
        self.tokens = "./models/sherpa-onnx-dolphin-small-ctc-multi-lang-int8-2025-04-02/tokens.txt"
        self.asr = sherpa_onnx.OfflineRecognizer.from_dolphin_ctc(
            model=self.model,
            tokens=self.tokens,
            debug=False,
        )
    def asr_forward(self,samples):
        stream = self.asr.create_stream()
        stream.accept_waveform(self.sample_rate, samples)
        self.asr.decode_stream(stream)
        result = json.loads(str(stream.result))
        print(result["text"])
        return result["text"]
        
class DiariModule:
    def __init__(self):
        self.sample_rate = 16000
        self.saved_wav_path = "./diari_saved_wav"
        self.config = sherpa_onnx.SpeakerEmbeddingExtractorConfig(
            model="./models/3dspeaker_speech_eres2netv2_sv_zh-cn_16k-common.onnx",
            num_threads=2,
            debug=False,
            provider="cpu"
        )
        self.manager = sherpa_onnx.SpeakerEmbeddingManager(5)
        self.extractor = sherpa_onnx.SpeakerEmbeddingExtractor(self.config)
        self.speakers = []
        self.labels = []

    def _compute_embedding_for_speaker(self, file_list: List[str]) -> np.ndarray:
        assert file_list, "No wav files provided for speaker"

        ans = None
        for filename in file_list:
            print(f"Processing {filename}")
            samples, sr = sf.read(filename)
            if sr != self.sample_rate:
                raise ValueError(f"Sample rate mismatch: expected {self.sample_rate}, got {sr}")

            stream = self.extractor.create_stream()
            stream.accept_waveform(sample_rate=sr, waveform=samples)
            stream.input_finished()

            assert self.extractor.is_ready(stream)
            embedding = self.extractor.compute(stream)
            embedding = np.array(embedding)

            if ans is None:
                ans = embedding
            else:
                ans += embedding

        return ans / len(file_list)

    def _load_speakers_from_file(self):
        wav_files = list(Path(self.saved_wav_path).glob("*.wav"))
        if not wav_files:
            print(f"No wav files found in {self.saved_wav_path}")
            return

        speaker_dict = {}
        for wav_path in wav_files:
            filename = wav_path.stem
            if "_" not in filename:
                print(f"Skipping malformed filename: {filename}")
                continue
            speaker_name = filename.split("_")[0]
            speaker_dict.setdefault(speaker_name, []).append(str(wav_path))

        for speaker_name, file_list in speaker_dict.items():
            try:
                embedding = self._compute_embedding_for_speaker(file_list)
                self.manager.add(speaker_name, embedding)
                print(f"Registered speaker: {speaker_name} with {len(file_list)} files")
            except Exception as e:
                print(f"[ERROR] Failed to process speaker {speaker_name}: {e}")
    def update_speakers(self, speakers):
        self.speakers = speakers
        self.labels = [speaker.label for speaker in speakers]
        self.embed_model.update_speakers(self.speakers)
    def get_speaker_name(self, samples):
        stream = self.extractor.create_stream()
        stream.accept_waveform(self.sample_rate, samples)
        stream.input_finished()
        embedding = self.extractor.compute(stream)
        embedding = np.array(embedding)
        name = self.manager.search(embedding, threshold=0.3)
        if not name:
            name = "unknown"
        print(f"Speaker: {name}")
        return name

    
# def main():
#     diari_module = DiariModule()
#     diari_module._load_speakers_from_file()
#     vad_module = VadModule()
#     asr_module = AsrModule()
    

#     def vad_callback(samples):
#         asr_module.asr_forward(samples)
#         diari_module.get_speaker_name(samples)
        
#     vad_module.vad_handler(vad_callback)
        
    

# if __name__ == "__main__":
#     main()
