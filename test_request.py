import asyncio
from typing import Callable, Dict, Any, Optional, Union, List
from dify_requester import DifyRequester,DifyDecoder
from segmentation import JsonDecoder
import os
import json
DIFY_API_KEY_APP_1 = os.environ.get("DIFY_API_KEY_APP_1")
DIFY_API_KEY_APP_2 = os.environ.get("DIFY_API_KEY_APP_2")
DIFY_BASE_URL = os.environ.get("DIFY_BASE_URL")
print(DIFY_API_KEY_APP_1)
print(DIFY_API_KEY_APP_2)
print(DIFY_BASE_URL)
json_buffer = ""
response = None

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
jd = JsonDecoder()
def cleanup():
    seg.clear_buffer()
    response = jd.json_decode()
    jd.clear_buffer()
    print(response["function"])
    
def meg_callback(msg: str):
    print(f"callback {msg}")
def chat_callback(frame: Dict[str, Any]):
    buffer = DifyDecoder.stream_get_answer(frame)
    if buffer is None: 
        return
    else:
        seg.append_new_message(buffer,message_callback=meg_callback)
        jd.append_buffer(buffer)
        # print(f"Buffer: {buffer}")
async def main():
    requester = DifyRequester(DIFY_API_KEY_APP_2, base_url=DIFY_BASE_URL, user="user")
    requester2 = DifyRequester(DIFY_API_KEY_APP_2, base_url=DIFY_BASE_URL, user="user")
    

    # task = asyncio.create_task(
    #     requester.chat.request_async("给我讲个故事，并告诉我今天的天气", callback=chat_callback)
    # )
    
    inputs = {"speaker":"master"}
    task2 = asyncio.create_task(
        requester2.chat.request_async("讲个黑色幽默", callback=chat_callback,inputs=inputs,finish_callback=cleanup)
    )
    
    # await task
    await task2
    task2 = asyncio.create_task(
        requester2.chat.request_async("讲个黑色幽默", callback=chat_callback,inputs=inputs,finish_callback=cleanup)
    )
    await task2
    print(f"time async:{requester2.chat.last_request_time}")
    # response = requester2.chat.request("我是谁",inputs=inputs)
    # print(response["answer"])
    # print(f"time sync:{requester2.chat.last_request_time}")

asyncio.run(main())
