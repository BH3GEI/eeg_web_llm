from datetime import datetime

class Conversation:
    def __init__(self):
        self.message_list = []
        
    def get_string(self):
        message = "Begin\n"
        for i in range(len(self.message_list)):
            message += f"{self.message_list[i]}"
        message += "End\n\n"
        
        return message
    def clear(self):
        self.message_list.clear()
    def new_message(self,spearker: str, message: str,master_motion: str):
        time = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        emotion = f"[master_emotion:{master_motion}]"
        message = f"{time} {emotion} {spearker}: {message}\n"
        self.message_list.append(message)
        