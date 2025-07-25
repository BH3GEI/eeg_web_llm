import time
import soundfile as sf
import sherpa_onnx
import sounddevice as sd

class SpeakerDevice:
    def __init__(self):
        pass
    def play(self,samples,sample_rate):
        sd.play(samples, samplerate=sample_rate)
        sd.wait()
        

class MatchaTTS:
    def __init__(self):
        tts_config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                matcha=sherpa_onnx.OfflineTtsMatchaModelConfig(
                    acoustic_model="./models/matcha-icefall-zh-baker/model-steps-3.onnx",
                    vocoder="./models/vocos-22khz-univ.onnx",
                    lexicon="./models/matcha-icefall-zh-baker/lexicon.txt",
                    tokens="./models/matcha-icefall-zh-baker/tokens.txt",
                    data_dir="",
                    dict_dir="./models/matcha-icefall-zh-baker/dict",
                ),
                provider="cpu",
                debug=False,
                num_threads=2,
            ),
            rule_fsts="./models/matcha-icefall-zh-baker/phone.fst,models/matcha-icefall-zh-baker/date.fst,models/matcha-icefall-zh-baker/number.fst",
            max_num_sentences=100,
        )

        if not tts_config.validate():
            raise ValueError("Invalid MatchaTTS config. Please check paths and parameters.")

        self.tts = sherpa_onnx.OfflineTts(tts_config)

    def synthesize(self, text: str, output_path: str = None, sid: int = 0, speed: float = 1.0):
        """合成语音并返回音频数据，若指定路径则保存为 .wav 文件"""
        start = time.time()
        audio = self.tts.generate(text, sid=sid, speed=speed)
        end = time.time()

        if len(audio.samples) == 0:
            raise RuntimeError("TTS synthesis failed: generated empty audio.")

        elapsed_seconds = end - start
        audio_duration = len(audio.samples) / audio.sample_rate
        real_time_factor = elapsed_seconds / audio_duration

        if output_path:
            sf.write(output_path, audio.samples, samplerate=audio.sample_rate, subtype="PCM_16")
            print(f"[MatchaTTS] Saved to {output_path}")

        print(f"[MatchaTTS] Text: {text}")
        print(f"[MatchaTTS] Elapsed: {elapsed_seconds:.3f}s, Audio: {audio_duration:.3f}s, RTF: {real_time_factor:.3f}")

        return audio.samples, audio.sample_rate

def main():
    tts = MatchaTTS()
    speaker_device = SpeakerDevice()
    samples, sample_rate = tts.synthesize("合成语音并返回音频数据，若指定路径则保存为")
    speaker_device.play(samples,sample_rate)
    
    
if __name__ == "__main__":
    main()