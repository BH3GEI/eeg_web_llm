from typing import Callable, Dict, Any, Optional, Union, List

class DifyDecoder:
    @staticmethod
    def stream_get_answer(frame: Dict[str, Any]):
        event = frame.get("event", "")
        
        if event == "message":
            answer = frame.get("answer") or frame.get("data", {}).get("answer")
            if answer:
                return answer
            else:
                return None
        else:
            return None