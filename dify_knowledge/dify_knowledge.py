from dify_user.config import DifyUserConfig
from typing import Callable, Dict, Any, Optional, Union, List
from pathlib import Path
import json
import httpx
import time

class DifyKnowledge:
    def __init__(self, api_key: str, 
                 base_url: str = None, 
                 dataset_id:str = None,
                 user: str = None):
        self.user_config = DifyUserConfig(api_key, base_url, user)
        self.dataset_id = dataset_id

    def create_doc_from_text(self,
                            name: str = None,
                            text: str = None,
                            indexing_technique: str = "high_quality",
                            pre_processing_rules: list = None,
                            separator: str = "\n\n",
                            max_tokens: int = 1024,
                            chunk_overlap: int = 50) -> dict:
        
        if pre_processing_rules is None:
            pre_processing_rules = [
                {"id": "remove_extra_spaces", "enabled": True},
                {"id": "remove_urls_emails", "enabled": True}
            ]
            
        headers = {
            "Authorization": f"Bearer {self.user_config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "name": name,
            "text": text,
            "indexing_technique": indexing_technique,
            "process_rule": {
                "rules": {
                    "pre_processing_rules": pre_processing_rules,
                    "segmentation": {
                        "separator": separator,
                        "max_tokens": max_tokens,
                        "chunk_overlap": chunk_overlap
                    }
                },
                "mode": "custom"
            }
        }

        url = f"{self.user_config.base_url}/datasets/{self.dataset_id}/document/create-by-text"

        time_start = time.time()
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
        time_end = time.time()
        self.last_request_time = time_end - time_start

        if response.status_code != 200:
            raise RuntimeError(f"Failed to create document: [{response.status_code}] {response.text}")

        return response.json()
    
    def create_doc_from_file(self,
                            file_path: str,
                            indexing_technique: str = "high_quality",
                            pre_processing_rules: list = None,
                            separator: str = "\n\n",
                            max_tokens: int = 1024,
                            chunk_overlap: int = 50) -> dict:
        """
        上传文件并创建文档到指定 dataset。
        """
        if pre_processing_rules is None:
            pre_processing_rules = [
                {"id": "remove_extra_spaces", "enabled": True},
                {"id": "remove_urls_emails", "enabled": True}
            ]

        headers = {
            "Authorization": f"Bearer {self.user_config.api_key}",
        }

        process_rule = {
            "indexing_technique": indexing_technique,
            "process_rule": {
                "rules": {
                    "pre_processing_rules": pre_processing_rules,
                    "segmentation": {
                        "separator": separator,
                        "max_tokens": max_tokens,
                        "chunk_overlap": chunk_overlap
                    }
                },
                "mode": "custom"
            }
        }
        

        files = {
            "data": (None, json.dumps(process_rule), "text/plain"),
            "file": (Path(file_path).name, open(file_path, "rb"), "application/octet-stream")
        }

        url = f"{self.user_config.base_url}/v1/datasets/{self.dataset_id}/document/create-by-file"

        time_start = time.time()
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, files=files)
        time_end = time.time()
        self.last_request_time = time_end - time_start

        if response.status_code != 200:
            raise RuntimeError(f"Failed to create document from file: [{response.status_code}] {response.text}")

        return response.json()
    
    def add_chunks_to_document(
        self,
        document_id: str,
        content: List[str],
        answers: List[str] = None,
        keywords: List[str] = None,
    ) -> dict:
        """
        向指定文档添加chunks（segments）
        
        参数:
          document_id: 文档ID
          segments: List[Dict]，每个dict包括:
              - content (str): 必填，文本内容
              - answer (str, optional): 答案内容，Q&A模式时用
              - keywords (List[str], optional): 关键词列表
        
        返回:
          返回接口响应json
        """
        url = f"{self.user_config.base_url}/datasets/{self.dataset_id}/documents/{document_id}/segments"

        headers = {
            "Authorization": f"Bearer {self.user_config.api_key}",
            "Content-Type": "application/json",
        }
        
        segments_list = []

        for i in range(len(content)):
            temp_segment = {
                "content": content[i]
            }
            if answers:
                temp_segment["answer"] = answers[i]
            if keywords:
                temp_segment["keywords"] = keywords[i]
            segments_list.append(temp_segment)
            
        payload = {
            "segments": segments_list,
        }

        time_start = time.time()
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
        time_end = time.time()
        self.last_request_time = time_end - time_start

        if response.status_code != 200:
            raise RuntimeError(f"Failed to add chunks: [{response.status_code}] {response.text}")

        return response.json()
    
    def get_file_list(self)-> dict:

        url = f"{self.user_config.base_url}/datasets/{self.dataset_id}/documents"

        headers = {
            "Authorization": f"Bearer {self.user_config.api_key}",
        }

        time_start = time.time()
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
        time_end = time.time()
        self.last_request_time = time_end - time_start

        if response.status_code != 200:
            raise RuntimeError(f"Failed to add chunks: [{response.status_code}] {response.text}")
        
        file_array = []
        
        for item in response.json()["data"]:
            temp_dict = {"id":"","name":""}
            temp_dict["id"] = item["id"]
            temp_dict["name"] = item["data_source_detail_dict"]["upload_file"]["name"]
            file_array.append(temp_dict)

        return file_array
    