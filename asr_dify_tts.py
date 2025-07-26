from audio_input import *
from audio_output import *
import asyncio
from typing import Callable, Dict, Any, Optional, Union, List
from segmentation import JsonDecoder,RealTimeResponseSegmentation
import json

DIFY_API_KEY_APP_2 = "app-6q3N1F4cxq895oHk8w11self"
DIFY_API_KEY_DATASET = "dataset-767RnqkWPQe1JSZ3xCiYpM7v"
DIFT_DATASET_ID = "9c7a9c6d-5647-4060-b99f-f1d936ed4784"
DIFY_BASE_URL = "http://111.229.56.5:8086/v1"
print(DIFY_API_KEY_APP_2)
print(DIFY_BASE_URL)
json_buffer = ""
response = None
        
seg = RealTimeResponseSegmentation()
jd = JsonDecoder()
def cleanup():
    seg.clear_buffer()
    response = jd.json_decode()
    jd.clear_buffer()
    print(response["function"])
    
def meg_callback(msg: str):
    print(f"callback {msg}")
        
def dify_knowledge_find_file_id(database:DifyKnowledge ,filename: str):
    file_array = database.get_file_list()
    for file in file_array:
        if file["name"] == "2025-7-23.txt":
            file_id = file["id"]
            
    chunk = ["sb1",'sb2']
    database.add_chunks_to_document(document_id=file_id,content=chunk)
    print(file_array)

async def main():
    
    # dify_database = DifyKnowledge(api_key=DIFY_API_KEY_DATASET,base_url=DIFY_BASE_URL,dataset_id=DIFT_DATASET_ID)
    # dify_knowledge_find_file_id(dify_database, "test.txt")
    vad = VadModule()
    asr = AsrModule()
    tts = MatchaTTS()
    microphone = MicrophoneDevice()
    speaker_device = SpeakerDevice()
    def chat_callback(frame: Dict[str, Any]):
        buffer = DifyDecoder.stream_get_answer(frame)
        if buffer is None: 
            return
        else:
            seg.append_new_message(buffer,message_callback=meg_callback)
            jd.append_buffer(buffer)
            print(f"Buffer: {buffer}")
            tts.text_to_speech(buffer)
           
    
    def fucking_callback(samples):
        text = asr.asr_forward(samples)

        
        requester = DifyRequester(DIFY_API_KEY_APP_2, base_url=DIFY_BASE_URL, user='123')
        inputs = {"speaker":'123',"emotion":"happy"}
        # inputs = {}
        # task2 = asyncio.create_task(
        #     requester.chat.request_async(query=text, callback=chat_callback,inputs=inputs,finish_callback=cleanup)
        # )
        # await task2
        
        response = requester.chat.request(query=text, inputs=inputs)
        print(response["answer"])
        samples,sample_rate = tts.synthesize(json.loads(response["answer"])["text"])
        speaker_device.play(samples,sample_rate)
    
    await vad.vad_handler(fucking_callback,microphone.recorder)


asyncio.run(main())
