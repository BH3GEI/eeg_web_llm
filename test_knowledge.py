from dify_knowledge import DifyKnowledge
import os
import json
from datetime import datetime
from conversation import Conversation

def print_json(data):
    print(json.dumps(data, indent=4))

DIFY_BASE_URL = os.environ.get("DIFY_BASE_URL")
DIFY_KNOWLEDGE_API_KEY = "dataset-767RnqkWPQe1JSZ3xCiYpM7v"
DIFY_KNOWLEDGE_ID = "9c7a9c6d-5647-4060-b99f-f1d936ed4784"

knowledge = DifyKnowledge(api_key=DIFY_KNOWLEDGE_API_KEY, base_url=DIFY_BASE_URL,dataset_id=DIFY_KNOWLEDGE_ID,user="test")

# file_name = datetime.now().strftime("%Y-%m-%d") + ".txt"
# print(file_name)

con = Conversation()

con.new_message("user","hello","sad")
con.new_message("assistant","hello","sad")
con.new_message("user","how are you?","sad")
con.new_message("assistant","I'm fine, thanks!","sad")

print(con.get_string())


# response = knowledge.create_doc_from_text(name="2025-7-23.txt", text=con.get_string(),separator="\n\n",chunk_overlap="50",max_tokens="1024")
# print(response["document"]["id"])


detail = knowledge.get_file_list()
print_json(detail)

id = "2c3476e5-8c70-40d3-821a-e3754532d176"
response = knowledge.add_chunks_to_document(id, [con.get_string()])