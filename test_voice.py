#!/usr/bin/env python3
import time
import sys

print("app-6q3N1F4cxq895oHk8w11self")
print("http://111.229.56.5:8086/v1")
print("声音测试")

# 模拟语音脚本的输出
for i in range(5):
    print(f"ASR: 测试语音识别 {i+1}")
    time.sleep(2)
    print(f"AI回复: {{'text': '这是测试回复 {i+1}', 'function': 'none'}}")
    time.sleep(1)
    print(f"[MatchaTTS] Text: 这是测试回复 {i+1}")
    time.sleep(1)
    
print("测试完成")