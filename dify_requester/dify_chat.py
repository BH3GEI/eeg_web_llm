from dify_user.config import DifyUserConfig
from typing import Callable, Dict, Any, Optional, Union, List
import json
import uuid
import httpx
import time

class DifyChat:
    def __init__(self, 
                user_config: DifyUserConfig,
                conversation_id: Optional[str] = None):
        self.user_config = user_config
        self.conversation_id = conversation_id
        self.task_id = None
        self.last_request_time = 0.0
    
    def new_conversation(self):
        """
        Initialize a new conversation.

        This method generates a new unique conversation ID by using a UUID (Universally Unique Identifier)
        and converts it to a string format. This ensures that each conversation has a unique identifier,
        which is useful for tracking and management purposes.
        """
        old_id = self.conversation_id
        while True:
            new_id = str(uuid.uuid4())
            if new_id != old_id:
                break
        self.conversation_id = new_id
    def request(
        self,
        query: str = "",
        inputs: Union[str, Dict] = None,
        files: Optional[List[Dict]] = None
    ):
        """
        Sends a request to the chat service to process a query.
    
        Parameters:
        - query (str): The query string for the chat.
        - inputs (Union[str, Dict]): Additional input data for the chat, can be a string or dictionary.
        - files (Optional[List[Dict]]): List of file dictionaries to upload, if any.
    
        Returns:
        - dict: The JSON response from the chat service.
        """
    
        headers = {
            "Authorization": f"Bearer {self.user_config.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "blocking",
            "conversation_id": self.conversation_id or "",
            "user": self.user_config.user,
            "files": files or [],
        }
        
        chat_url = f"{self.user_config.base_url}/chat-messages"
        time_start = time.time()

        with httpx.Client(timeout=30.0) as client:
            response = client.post(chat_url, json=payload, headers=headers)

        time_end = time.time()
        self.last_request_time = time_end - time_start

        if response.status_code != 200:
            raise RuntimeError(f"[{response.status_code}] {response.text}")

        if self.conversation_id is None:
            self.conversation_id = response.json()["conversation_id"]

        return response.json()
    async def request_async(
        self,
        query: str = "",
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        finish_callback: Optional[Callable[[], None]] = None,
        inputs: Union[str, Dict] = None,
        files: Optional[List[Dict]] = None
    ):
        if callback is None:
            raise ValueError("Callback function must be provided")

        headers = {
            "Authorization": f"Bearer {self.user_config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "streaming",
            "conversation_id": self.conversation_id or "",
            "user": self.user_config.user,
        }

        chat_url = f"{self.user_config.base_url}/chat-messages"

        time_start = time.time()
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=60.0)) as client:
            async with client.stream("POST", chat_url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise RuntimeError(
                        f"HTTP request error:\n"
                        f"URL: {chat_url}\n"
                        f"Status Code: {response.status_code}\n"
                        f"Reason: {response.reason_phrase}\n"
                        f"Response Body: {error_text.decode(errors='ignore')}"
                    )
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[len("data: "):].strip()
                        if data == "[DONE]":
                            break
                        try:
                            frame = json.loads(data)
                            #Update task id
                            if self.task_id is None and frame.get("task_id"):
                                self.task_id = frame.get("task_id")
                            #Update the conversation_id if not provided in initialization
                            if self.conversation_id is None and frame.get('conversation_id'):
                                self.conversation_id = frame.get('conversation_id')
                            callback(frame)
                        except json.JSONDecodeError:
                            continue
        #clear task_id after done
        self.task_id = None
        if finish_callback is not None:
            finish_callback()
        time_end = time.time()
        self.last_request_time = time_end - time_start
    async def request_async_stop(self):
        if self.task_id is None:
            return

        url = f"{self.user_config.base_url}/chat-messages/{self.task_id}/stop"
        headers = {
            "Authorization": f"Bearer {self.user_config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "user": self.user_config.user
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                raise RuntimeError(f"Failed to stop streaming: [{response.status_code}] {response.text}")
            else:
                print("Streaming stopped")
    

    def print_config(self):
        print(self.user_config.api_key)
        print(self.user_config.base_url)
        print(self.conversation_id)
        print(self.user_config.user)