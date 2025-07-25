from dify_user.config import DifyUserConfig
import mimetypes
import httpx
from pathlib import Path

class DifyFile:
    def __init__(self, user_config: DifyUserConfig):
        self.user_config = user_config

    def upload_file(self, file_path: str) -> dict:
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        url = f"{self.user_config.base_url}/files/upload"
        headers = {
            "Authorization": f"Bearer {self.user_config.api_key}"
        }

        with open(file_path, "rb") as f:
            files = {
                "file": (path.name, f, mime_type)
            }
            data = {
                "user": self.user_config.user
            }

            response = httpx.post(url, headers=headers, files=files, data=data)

        if response.status_code != 201:
            raise RuntimeError(f"Upload failed: [{response.status_code}] {response.text}")

        return {
            "type": "image",
            "transfer_method": "file_id",
            "id": response.json().get("id")
        }