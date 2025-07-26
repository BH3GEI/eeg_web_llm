#!/usr/bin/env python3
"""
生成模拟情绪数据的测试脚本
模拟脑机接口采集到的情绪识别数据
"""

import csv
import time
import random
from datetime import datetime
import os

# CSV文件路径
csv_file = "/Users/liyao/Code/AdventureX/SmartList/eeg_web_llm/EmotionCV/emotion_log.csv"

# 情绪类型和权重（模拟真实情况下不同情绪出现的概率）
emotions = ['happy', 'sad', 'angry', 'fear', 'surprise', 'disgust', 'neutral']
emotion_weights = [0.3, 0.15, 0.1, 0.05, 0.1, 0.05, 0.25]  # neutral和happy更常见

def generate_emotion_scores(dominant_emotion):
    """生成情绪分数，让主导情绪分数更高，其他情绪有一些随机噪声"""
    scores = {}
    
    for emotion in emotions:
        if emotion == dominant_emotion:
            # 主导情绪分数在0.6-0.9之间
            scores[emotion] = round(random.uniform(0.6, 0.9), 3)
        else:
            # 其他情绪分数在0.0-0.4之间，大部分接近0
            if random.random() < 0.3:  # 30%概率有一些分数
                scores[emotion] = round(random.uniform(0.05, 0.4), 3)
            else:
                scores[emotion] = 0.0
    
    return scores

def simulate_emotion_transition():
    """模拟情绪变化模式 - 情绪通常有一定的持续性"""
    current_emotion = random.choices(emotions, weights=emotion_weights)[0]
    duration = random.randint(3, 15)  # 每种情绪持续3-15次采样
    
    return current_emotion, duration

def write_emotion_data():
    """写入情绪数据到CSV文件"""
    
    # 确保目录存在
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    
    # 检查文件是否存在，如果不存在则写入表头
    file_exists = os.path.exists(csv_file)
    
    print(f"🧠 开始生成模拟脑机情绪数据...")
    print(f"📁 数据文件: {csv_file}")
    print(f"⏱️  采样间隔: 0.5秒")
    print(f"🎭 支持情绪: {', '.join(emotions)}")
    print("-" * 50)
    
    current_emotion = 'neutral'
    emotion_duration = 0
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # 如果是新文件，写入表头
        if not file_exists:
            header = ['Timestamp', 'Dominant Emotion', 'Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
            writer.writerow(header)
            print("📝 已创建CSV文件并写入表头")
        
        try:
            sample_count = 0
            while True:
                # 检查是否需要切换情绪
                if emotion_duration <= 0:
                    current_emotion, emotion_duration = simulate_emotion_transition()
                    print(f"🎭 情绪切换到: {current_emotion} (持续{emotion_duration}次采样)")
                
                # 生成当前时间戳
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                
                # 生成情绪分数
                scores = generate_emotion_scores(current_emotion)
                
                # 写入数据行
                row = [
                    timestamp,
                    current_emotion,
                    scores['angry'],
                    scores['disgust'], 
                    scores['fear'],
                    scores['happy'],
                    scores['sad'],
                    scores['surprise'],
                    scores['neutral']
                ]
                
                writer.writerow(row)
                f.flush()  # 立即写入文件
                
                sample_count += 1
                emotion_duration -= 1
                
                # 每10次采样显示一次状态
                if sample_count % 10 == 0:
                    confidence = max(scores.values()) * 100
                    print(f"📊 样本#{sample_count:4d} | 情绪: {current_emotion:8s} | 置信度: {confidence:5.1f}% | 时间: {timestamp}")
                
                # 模拟实时采样间隔
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 用户中断，已生成 {sample_count} 个样本")
            print(f"📁 数据已保存到: {csv_file}")

def generate_batch_data(num_samples=100):
    """生成一批测试数据（不实时）"""
    
    # 确保目录存在
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    
    print(f"🧠 生成 {num_samples} 个模拟情绪数据样本...")
    
    current_emotion = 'neutral'
    emotion_duration = 0
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # 写入表头
        header = ['Timestamp', 'Dominant Emotion', 'Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        writer.writerow(header)
        
        for i in range(num_samples):
            # 检查是否需要切换情绪
            if emotion_duration <= 0:
                current_emotion, emotion_duration = simulate_emotion_transition()
            
            # 生成时间戳（模拟过去几分钟的数据）
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            
            # 生成情绪分数
            scores = generate_emotion_scores(current_emotion)
            
            # 写入数据行
            row = [
                timestamp,
                current_emotion,
                scores['angry'],
                scores['disgust'], 
                scores['fear'],
                scores['happy'],
                scores['sad'],
                scores['surprise'],
                scores['neutral']
            ]
            
            writer.writerow(row)
            emotion_duration -= 1
            
            # 小间隔模拟采样时间
            time.sleep(0.01)
    
    print(f"✅ 已生成 {num_samples} 个样本")
    print(f"📁 数据保存到: {csv_file}")

if __name__ == "__main__":
    import sys
    
    print("🧠 模拟脑机情绪数据生成器")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        # 批量模式：快速生成测试数据
        num_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        generate_batch_data(num_samples)
    else:
        # 实时模式：模拟真实的脑机数据流
        print("💡 提示：")
        print("   - 实时模式：python generate_fake_emotion_data.py")
        print("   - 批量模式：python generate_fake_emotion_data.py batch [数量]")
        print("   - 按Ctrl+C停止")
        print()
        
        write_emotion_data()