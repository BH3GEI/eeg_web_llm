#!/usr/bin/env python3
"""
生成模拟EEG脑电数据的测试脚本
模拟脑机接口采集到的6个生理指标
"""

import csv
import time
import random
import math
from datetime import datetime
import os

# CSV文件路径（基于时间戳命名）
base_dir = "/Users/liyao/Code/AdventureX/SmartList/eeg_web_llm"
csv_file = os.path.join(base_dir, f"{datetime.now().strftime('%Y-%m-%d')}.csv")

# EEG指标定义
eeg_metrics = ['attention', 'engagement', 'excitement', 'interest', 'relaxation', 'stress']

def generate_realistic_eeg_pattern():
    """生成符合真实EEG特征的数据模式"""
    
    # 模拟不同的生理状态
    states = {
        'focused': {  # 专注状态
            'attention': (0.7, 0.9),
            'engagement': (0.6, 0.8),
            'excitement': (0.3, 0.5),
            'interest': (0.6, 0.8),
            'relaxation': (0.3, 0.5),
            'stress': (0.2, 0.4)
        },
        'relaxed': {  # 放松状态
            'attention': (0.3, 0.5),
            'engagement': (0.2, 0.4),
            'excitement': (0.1, 0.3),
            'interest': (0.2, 0.4),
            'relaxation': (0.7, 0.9),
            'stress': (0.1, 0.3)
        },
        'excited': {  # 兴奋状态
            'attention': (0.4, 0.6),
            'engagement': (0.7, 0.9),
            'excitement': (0.8, 0.95),
            'interest': (0.7, 0.9),
            'relaxation': (0.1, 0.3),
            'stress': (0.3, 0.6)
        },
        'stressed': {  # 压力状态
            'attention': (0.2, 0.4),
            'engagement': (0.3, 0.5),
            'excitement': (0.4, 0.7),
            'interest': (0.2, 0.4),
            'relaxation': (0.1, 0.3),
            'stress': (0.7, 0.9)
        },
        'tired': {  # 疲劳状态
            'attention': (0.1, 0.3),
            'engagement': (0.1, 0.3),
            'excitement': (0.0, 0.2),
            'interest': (0.1, 0.3),
            'relaxation': (0.4, 0.6),
            'stress': (0.3, 0.5)
        }
    }
    
    # 随机选择一个状态
    state_name = random.choice(list(states.keys()))
    state_ranges = states[state_name]
    
    # 生成状态持续时间
    duration = random.randint(10, 30)  # 10-30秒
    
    return state_name, state_ranges, duration

def add_noise_and_variation(base_value, noise_level=0.1):
    """添加噪声和自然波动"""
    noise = random.uniform(-noise_level, noise_level)
    # 使用正弦波模拟自然的生理节律
    rhythm = math.sin(time.time() * 0.1) * 0.05
    
    result = base_value + noise + rhythm
    return max(0.0, min(1.0, result))  # 限制在0-1范围内

def generate_eeg_sample(state_ranges):
    """生成一个EEG数据样本"""
    sample = {}
    
    for metric in eeg_metrics:
        min_val, max_val = state_ranges[metric]
        base_value = random.uniform(min_val, max_val)
        sample[metric] = round(add_noise_and_variation(base_value), 3)
    
    return sample

def write_eeg_data():
    """写入EEG数据到CSV文件"""
    
    # 确保目录存在
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    
    # 检查文件是否存在，如果不存在则写入表头
    file_exists = os.path.exists(csv_file)
    
    print(f"🧠 开始生成模拟EEG脑电数据...")
    print(f"📁 数据文件: {csv_file}")
    print(f"⏱️  采样间隔: 1秒")
    print(f"📊 监测指标: {', '.join(eeg_metrics)}")
    print("-" * 60)
    
    current_state = None
    state_duration = 0
    state_ranges = None
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # 如果是新文件，写入表头
        if not file_exists:
            header = eeg_metrics + ['time']
            writer.writerow(header)
            print("📝 已创建CSV文件并写入表头")
        
        try:
            sample_count = 0
            while True:
                # 检查是否需要切换状态
                if state_duration <= 0:
                    current_state, state_ranges, state_duration = generate_realistic_eeg_pattern()
                    print(f"🧠 生理状态切换到: {current_state} (持续{state_duration}秒)")
                
                # 生成当前时间戳
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # 精确到毫秒
                
                # 生成EEG数据样本
                eeg_sample = generate_eeg_sample(state_ranges)
                
                # 写入数据行
                row = [eeg_sample[metric] for metric in eeg_metrics] + [timestamp]
                writer.writerow(row)
                f.flush()  # 立即写入文件
                
                sample_count += 1
                state_duration -= 1
                
                # 每10次采样显示一次状态
                if sample_count % 10 == 0:
                    avg_attention = eeg_sample['attention'] * 100
                    avg_stress = eeg_sample['stress'] * 100
                    print(f"📊 样本#{sample_count:4d} | 状态: {current_state:8s} | 注意力: {avg_attention:5.1f}% | 压力: {avg_stress:5.1f}% | 时间: {timestamp}")
                
                # 模拟1Hz采样频率
                time.sleep(1.0)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 用户中断，已生成 {sample_count} 个样本")
            print(f"📁 数据已保存到: {csv_file}")

def generate_batch_data(num_samples=120):
    """生成一批测试数据（不实时，快速生成2分钟的数据）"""
    
    # 确保目录存在
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    
    print(f"🧠 生成 {num_samples} 个模拟EEG数据样本...")
    
    current_state = None
    state_duration = 0
    state_ranges = None
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # 写入表头
        header = eeg_metrics + ['time']
        writer.writerow(header)
        
        for i in range(num_samples):
            # 检查是否需要切换状态
            if state_duration <= 0:
                current_state, state_ranges, state_duration = generate_realistic_eeg_pattern()
                print(f"🧠 状态: {current_state} (持续{state_duration}秒)")
            
            # 生成时间戳（向前推移1秒）
            import datetime as dt
            timestamp = (dt.datetime.now() - dt.timedelta(seconds=num_samples-i)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # 生成EEG数据样本
            eeg_sample = generate_eeg_sample(state_ranges)
            
            # 写入数据行
            row = [eeg_sample[metric] for metric in eeg_metrics] + [timestamp]
            writer.writerow(row)
            
            state_duration -= 1
            
            # 小间隔
            time.sleep(0.01)
    
    print(f"✅ 已生成 {num_samples} 个样本 (2分钟数据)")
    print(f"📁 数据保存到: {csv_file}")
    
    # 显示最后几行数据预览
    print("\n📋 数据预览（最后5行）:")
    print("-" * 80)
    with open(csv_file, 'r') as f:
        lines = f.readlines()
        for line in lines[-6:]:  # 包含表头
            print(line.strip())

if __name__ == "__main__":
    import sys
    
    print("🧠 模拟EEG脑电数据生成器")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        # 批量模式：快速生成测试数据
        num_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 120
        generate_batch_data(num_samples)
    else:
        # 实时模式：模拟真实的EEG数据流
        print("💡 提示：")
        print("   - 实时模式：python generate_fake_eeg_data.py")
        print("   - 批量模式：python generate_fake_eeg_data.py batch [数量]")
        print("   - 按Ctrl+C停止")
        print()
        
        write_eeg_data()