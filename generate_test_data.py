#!/usr/bin/env python3
"""
测试数据生成脚本
生成模拟的EEG和情绪数据到CSV文件，用于测试前端图表功能
"""

import csv
import random
import time
from datetime import datetime, timedelta
import os
import argparse

def generate_eeg_data(duration_minutes=5, interval_seconds=1):
    """生成EEG数据"""
    data = []
    start_time = datetime.now()
    
    # 基础值，模拟真实的脑电状态
    base_attention = 0.75
    base_engagement = 0.65
    base_excitement = 0.4
    base_interest = 0.7
    base_relaxation = 0.5
    base_stress = 0.3
    
    # 生成数据点
    for i in range(duration_minutes * 60 // interval_seconds):
        timestamp = start_time + timedelta(seconds=i * interval_seconds)
        
        # 添加随机波动和趋势
        time_factor = i / (duration_minutes * 60 // interval_seconds)
        
        # 模拟专注时的状态变化：开始低，中间高，结束时疲劳下降
        attention_trend = 0.2 * (1 - abs(time_factor - 0.5) * 2)  # 中间高
        stress_trend = 0.3 * time_factor  # 随时间增加
        
        attention = max(0, min(1, base_attention + attention_trend + random.uniform(-0.1, 0.1)))
        engagement = max(0, min(1, base_engagement + attention_trend * 0.8 + random.uniform(-0.1, 0.1)))
        excitement = max(0, min(1, base_excitement + random.uniform(-0.2, 0.3)))
        interest = max(0, min(1, base_interest + random.uniform(-0.15, 0.15)))
        relaxation = max(0, min(1, base_relaxation - stress_trend + random.uniform(-0.15, 0.15)))
        stress = max(0, min(1, base_stress + stress_trend + random.uniform(-0.1, 0.1)))
        
        data.append({
            'attention': round(attention, 3),
            'engagement': round(engagement, 3),
            'excitement': round(excitement, 3),
            'interest': round(interest, 3),
            'relaxation': round(relaxation, 3),
            'stress': round(stress, 3),
            'time': timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        })
    
    return data

def generate_emotion_data(duration_minutes=5, interval_seconds=2):
    """生成情绪数据"""
    data = []
    start_time = datetime.now()
    
    # 定义情绪状态转换（简单的马尔可夫链）
    emotions = ['happy', 'neutral', 'focused', 'calm', 'thinking']
    emotion_weights = {
        'happy': {'happy': 0.7, 'neutral': 0.2, 'focused': 0.1},
        'neutral': {'happy': 0.3, 'neutral': 0.4, 'focused': 0.2, 'calm': 0.1},
        'focused': {'focused': 0.6, 'neutral': 0.2, 'thinking': 0.2},
        'calm': {'calm': 0.5, 'neutral': 0.3, 'happy': 0.2},
        'thinking': {'thinking': 0.5, 'focused': 0.3, 'neutral': 0.2}
    }
    
    current_emotion = 'neutral'
    
    for i in range(duration_minutes * 60 // interval_seconds):
        timestamp = start_time + timedelta(seconds=i * interval_seconds)
        
        # 情绪转换
        if random.random() < 0.3:  # 30%的概率转换情绪
            if current_emotion in emotion_weights:
                weights = emotion_weights[current_emotion]
                current_emotion = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
        
        # 生成具体的情绪分数
        emotion_scores = {
            'Angry': 0.0,
            'Disgust': 0.0,
            'Fear': 0.0,
            'Happy': 0.0,
            'Sad': 0.0,
            'Surprise': 0.0,
            'Neutral': 0.0
        }
        
        # 根据当前主导情绪设置分数
        if current_emotion == 'happy':
            emotion_scores['Happy'] = round(random.uniform(0.6, 0.9), 3)
            emotion_scores['Neutral'] = round(random.uniform(0.1, 0.4), 3)
        elif current_emotion == 'focused':
            emotion_scores['Neutral'] = round(random.uniform(0.7, 0.9), 3)
            emotion_scores['Happy'] = round(random.uniform(0.1, 0.3), 3)
        elif current_emotion == 'calm':
            emotion_scores['Neutral'] = round(random.uniform(0.6, 0.8), 3)
            emotion_scores['Happy'] = round(random.uniform(0.2, 0.4), 3)
        elif current_emotion == 'thinking':
            emotion_scores['Neutral'] = round(random.uniform(0.5, 0.7), 3)
            emotion_scores['Surprise'] = round(random.uniform(0.2, 0.4), 3)
        else:  # neutral
            emotion_scores['Neutral'] = round(random.uniform(0.5, 0.8), 3)
            emotion_scores['Happy'] = round(random.uniform(0.1, 0.3), 3)
        
        # 添加一些随机噪声到其他情绪
        for emotion in emotion_scores:
            if emotion_scores[emotion] == 0.0:
                emotion_scores[emotion] = round(random.uniform(0.0, 0.2), 3)
        
        data.append({
            'Timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'),
            'Dominant Emotion': current_emotion,
            **emotion_scores
        })
    
    return data

def write_eeg_csv(data, filename):
    """写入EEG数据到CSV"""
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['attention', 'engagement', 'excitement', 'interest', 'relaxation', 'stress', 'time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def write_emotion_csv(data, filename):
    """写入情绪数据到CSV"""
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Timestamp', 'Dominant Emotion', 'Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def append_eeg_data(filename, duration_seconds=30):
    """向现有EEG文件追加新数据"""
    new_data = generate_eeg_data(duration_minutes=duration_seconds/60, interval_seconds=1)
    
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['attention', 'engagement', 'excitement', 'interest', 'relaxation', 'stress', 'time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for row in new_data:
            writer.writerow(row)

def append_emotion_data(filename, duration_seconds=30):
    """向现有情绪文件追加新数据"""
    new_data = generate_emotion_data(duration_minutes=duration_seconds/60, interval_seconds=2)
    
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['Timestamp', 'Dominant Emotion', 'Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for row in new_data:
            writer.writerow(row)

def main():
    parser = argparse.ArgumentParser(description='生成测试用的EEG和情绪数据')
    parser.add_argument('--mode', choices=['init', 'stream'], default='init', help='运行模式：init(初始化) 或 stream(持续生成)')
    parser.add_argument('--duration', type=int, default=5, help='生成数据的时长（分钟），仅用于init模式')
    parser.add_argument('--interval', type=int, default=5, help='stream模式下的生成间隔（秒）')
    
    args = parser.parse_args()
    
    # 文件路径
    base_dir = "/Users/liyao/Code/AdventureX/SmartList/eeg_web_llm"
    today = datetime.now().strftime("%Y-%m-%d")
    eeg_file = f"{base_dir}/{today}.csv"
    emotion_file = f"{base_dir}/EmotionCV/emotion_log.csv"
    
    # 确保目录存在
    os.makedirs(f"{base_dir}/EmotionCV", exist_ok=True)
    
    if args.mode == 'init':
        print(f"🚀 初始化模式：生成 {args.duration} 分钟的测试数据...")
        
        # 生成初始数据
        eeg_data = generate_eeg_data(duration_minutes=args.duration)
        emotion_data = generate_emotion_data(duration_minutes=args.duration)
        
        # 写入文件
        write_eeg_csv(eeg_data, eeg_file)
        write_emotion_csv(emotion_data, emotion_file)
        
        print(f"✅ EEG数据已写入: {eeg_file} ({len(eeg_data)} 条记录)")
        print(f"✅ 情绪数据已写入: {emotion_file} ({len(emotion_data)} 条记录)")
        
    elif args.mode == 'stream':
        print(f"📡 流模式：每 {args.interval} 秒生成新数据...")
        print("按 Ctrl+C 停止")
        
        try:
            while True:
                print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - 生成新数据...")
                
                # 追加新数据
                append_eeg_data(eeg_file, duration_seconds=args.interval)
                append_emotion_data(emotion_file, duration_seconds=args.interval)
                
                print(f"✅ 数据已追加到文件")
                time.sleep(args.interval)
                
        except KeyboardInterrupt:
            print("\n🛑 已停止数据生成")

if __name__ == "__main__":
    main()