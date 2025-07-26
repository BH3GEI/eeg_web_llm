#!/usr/bin/env python3
import sounddevice as sd
import sherpa_onnx
import json
import asyncio
import numpy as np

class MicrophoneDevice:
    def __init__(self, device: int = None, sample_rate: int = 16000):
        self.device = device
        self.sample_rate = sample_rate
        self.recorder = sd.InputStream(
            device=self.device,
            channels=1,
            dtype="float32",
            samplerate=self.sample_rate,
        )

    def start(self):
        self.recorder.start()
        print("Recording started.")

    def stop(self):
        self.recorder.stop()
        self.recorder.close()
        print("Recording stopped.")

class VadModule:
    def __init__(self):
        self.sample_rate = 16000
        self.frame_size = 100  # 0.1 second = 100 ms
        config = sherpa_onnx.VadModelConfig()
        config.silero_vad.model = "./models/silero_vad.onnx"
        config.sample_rate = self.sample_rate
        self.vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)
        
    async def vad_handler(self,vad_callback,recorder : sd.InputStream):
        
        try:
            with recorder:
                while True:
                    samples, _ = recorder.read(self.frame_size) 
                    self.vad.accept_waveform(samples)
                    while not self.vad.empty():
                        samples = self.vad.front.samples
                        vad_callback(samples)
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
    
# class WhisperModule:
#     def __init__(self):
#         self.sample_rate = 16000
#         self.frame_size = 1600  # 对应 0.1 秒采样
#         self.tokens = "./models/large-v3-tokens.txt"
#         self.encoder = "./models/large-v3-encoder.int8.onnx"
#         self.decoder = "./models/large-v3-decoder.int8.onnx"

#         self.asr = sherpa_onnx.OfflineRecognizer.from_whisper(
#             encoder=self.encoder,
#             decoder=self.decoder,
#             tokens=self.tokens,
#             num_threads=8,
#             decoding_method="greedy_search",
#             debug=True,
#             language="zh",
#             task="transcribe",
#             tail_paddings=-1,
#             provider="cuda"
#         )

#     def asr_forward(self, samples: np.ndarray) -> str:
#         stream = self.asr.create_stream()
#         stream.accept_waveform(self.sample_rate, samples)
#         self.asr.decode_stream(stream)
#         result = stream.result.text.strip()

#         print(f"[ASR Result] {result}")
#         return result
    
async def main():
    microphone = MicrophoneDevice()
    vad_module = VadModule()
    asr_module = AsrModule()
    # asr_whisper = WhisperModule()
    

    def vad_callback(samples):
        asr_module.asr_forward(samples)
        print("callback")
        # asr_whisper.asr_forward(samples)
        
    await vad_module.vad_handler(vad_callback,recorder=microphone.recorder)
        
    

if __name__ == "__main__":
    asyncio.run(main())
