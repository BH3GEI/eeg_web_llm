from dify_user.config import DifyUserConfig
from .dify_chat import DifyChat
from .dify_file import DifyFile
from typing import List,Union, Dict, Optional

class DifyRequester:
    def __init__(
        self,
        api_key: str,
        base_url: str = None,
        user: Optional[str] = None,
        conversation_id: Optional[str] = None
    ):
        self.user_config = DifyUserConfig(api_key, base_url, user)
        self.chat = DifyChat(self.user_config,conversation_id)
        self.file = DifyFile(self.user_config)