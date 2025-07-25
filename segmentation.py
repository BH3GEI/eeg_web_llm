from typing import Callable, Dict, Any, Optional, Union, List
import json

class RealTimeResponseSegmentation():
    def __init__(self):
        self.buffer = ""
        self.last_callback_index = 0
        self.answer_start = None
        self.answer_end = None
        self.punctuation_list = [
            ".", "!", "?", ",", ";", ":",
            "。", "！", "？", "，", "；", "：",
            "\n", "\r",
        ]
        
    def append_new_message(self, new_text, message_callback):
        self.buffer += new_text
        
        if self.answer_start is None:
            start_idx = self.buffer.find('"answer": "')
            if start_idx != -1:
                self.answer_start = start_idx + len('"answer": "')
                self.last_callback_index = self.answer_start

        if self.answer_start is not None and self.answer_end is None:
            end_idx = self.buffer.find('", "', self.answer_start)
            if end_idx != -1:
                self.answer_end = end_idx

        if self.answer_start is not None:
            effective_end = self.answer_end if self.answer_end is not None else len(self.buffer)

            answer_str = self.buffer[self.last_callback_index:effective_end]

            for i, ch in enumerate(answer_str):
                if ch in self.punctuation_list:
                    segment = self.buffer[self.last_callback_index:self.last_callback_index + i + 1].strip()
                    if segment:
                        message_callback(segment)
                        self.last_callback_index += i + 1
                    break
    def clear_buffer(self):
        self.buffer = ""
        self.last_callback_index = 0
        self.answer_start = None
        self.answer_end = None
        
seg = RealTimeResponseSegmentation()

def cleanup():
    seg.clear_buffer()
def meg_callback(msg: str):
    print(f"callback {msg}")

class JsonDecoder():
    def __init__(self):
        self.buffer = ""
    
    def append_buffer(self, data: str):
        self.buffer += data
    def json_decode(self) -> Dict[str, Any]:
        try:
            result = json.loads(self.buffer)
            return result
        except json.JSONDecodeError:
            return None
    def clear_buffer(self):
        self.buffer = ""