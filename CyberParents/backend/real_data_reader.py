import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class RealBioDataReader:
    """读取真实的生理监控数据"""
    
    def __init__(self, base_dir: str = "/Users/liyao/Code/AdventureX/SmartList/eeg_web_llm"):
        self.base_dir = base_dir
        self.eeg_file_pattern = "{base_dir}/{date}.csv"
        self.emotion_file = f"{base_dir}/EmotionCV/emotion_log.csv"
    
    def get_latest_eeg_data(self, minutes_back: int = 10) -> Dict:
        """获取最近几分钟的EEG数据"""
        today = datetime.now().strftime("%Y-%m-%d")
        eeg_file = self.eeg_file_pattern.format(base_dir=self.base_dir, date=today)
        
        if not os.path.exists(eeg_file):
            # 如果今天的文件不存在，尝试昨天的
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            eeg_file = self.eeg_file_pattern.format(base_dir=self.base_dir, date=yesterday)
        
        if not os.path.exists(eeg_file):
            return self._get_fallback_data()
        
        try:
            df = pd.read_csv(eeg_file)
            if df.empty:
                return self._get_fallback_data()
            
            # 转换时间列
            df['time'] = pd.to_datetime(df['time'])
            
            # 获取最近的数据
            recent_time = datetime.now() - timedelta(minutes=minutes_back)
            recent_data = df[df['time'] >= recent_time]
            
            if recent_data.empty:
                # 如果没有最近数据，获取最后10条
                recent_data = df.tail(10)
            
            # 获取最新的一条数据作为当前值
            latest = recent_data.iloc[-1]
            
            return {
                "current": {
                    "attention": float(latest['attention']),
                    "engagement": float(latest['engagement']),
                    "excitement": float(latest['excitement']),
                    "interest": float(latest['interest']),
                    "relaxation": float(latest['relaxation']),
                    "stress": float(latest['stress']),
                    "timestamp": latest['time'].isoformat()
                },
                "trends": {
                    "attention": recent_data['attention'].tolist()[-10:],
                    "engagement": recent_data['engagement'].tolist()[-10:],
                    "excitement": recent_data['excitement'].tolist()[-10:],
                    "interest": recent_data['interest'].tolist()[-10:],
                    "stress": recent_data['stress'].tolist()[-10:],
                    "relaxation": recent_data['relaxation'].tolist()[-10:],
                },
                "data_source": "real_eeg",
                "sample_count": len(recent_data)
            }
            
        except Exception as e:
            print(f"读取EEG数据失败: {e}")
            return self._get_fallback_data()
    
    def get_latest_emotion_data(self, minutes_back: int = 5) -> Dict:
        """获取最近的情绪识别数据"""
        if not os.path.exists(self.emotion_file):
            return self._get_fallback_emotion()
        
        try:
            df = pd.read_csv(self.emotion_file)
            if df.empty:
                return self._get_fallback_emotion()
            
            # 转换时间列
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            
            # 获取最近的数据
            recent_time = datetime.now() - timedelta(minutes=minutes_back)
            recent_data = df[df['Timestamp'] >= recent_time]
            
            if recent_data.empty:
                recent_data = df.tail(5)
            
            # 获取最新情绪
            latest = recent_data.iloc[-1]
            
            # 统计最近情绪分布
            emotion_counts = recent_data['Dominant Emotion'].value_counts()
            emotion_distribution = {
                emotion: count / len(recent_data) 
                for emotion, count in emotion_counts.items()
            }
            
            return {
                "current_emotion": latest['Dominant Emotion'],
                "emotion_scores": {
                    "angry": float(latest['Angry']),
                    "disgust": float(latest['Disgust']),
                    "fear": float(latest['Fear']),
                    "happy": float(latest['Happy']),
                    "sad": float(latest['Sad']),
                    "surprise": float(latest['Surprise']),
                    "neutral": float(latest['Neutral'])
                },
                "recent_distribution": emotion_distribution,
                "timestamp": latest['Timestamp'].isoformat(),
                "data_source": "real_emotion",
                "sample_count": len(recent_data)
            }
            
        except Exception as e:
            print(f"读取情绪数据失败: {e}")
            return self._get_fallback_emotion()
    
    def _get_fallback_data(self) -> Dict:
        """当无法读取真实数据时的回退数据"""
        import random
        return {
            "current": {
                "attention": round(random.uniform(0.6, 0.9), 3),
                "engagement": round(random.uniform(0.5, 0.8), 3),
                "excitement": round(random.uniform(0.3, 0.7), 3),
                "interest": round(random.uniform(0.5, 0.8), 3),
                "relaxation": round(random.uniform(0.3, 0.6), 3),
                "stress": round(random.uniform(0.2, 0.5), 3),
                "timestamp": datetime.now().isoformat()
            },
            "trends": {
                "attention": [round(random.uniform(0.6, 0.9), 3) for _ in range(10)],
                "engagement": [round(random.uniform(0.5, 0.8), 3) for _ in range(10)],
                "excitement": [round(random.uniform(0.3, 0.7), 3) for _ in range(10)],
                "interest": [round(random.uniform(0.5, 0.8), 3) for _ in range(10)],
                "stress": [round(random.uniform(0.2, 0.5), 3) for _ in range(10)],
                "relaxation": [round(random.uniform(0.3, 0.6), 3) for _ in range(10)],
            },
            "data_source": "fallback",
            "sample_count": 10
        }
    
    def _get_fallback_emotion(self) -> Dict:
        """情绪数据回退"""
        import random
        emotions = ["happy", "neutral", "focused", "calm", "thinking"]
        current = random.choice(emotions)
        
        return {
            "current_emotion": current,
            "emotion_scores": {
                "angry": round(random.uniform(0, 0.2), 3),
                "disgust": round(random.uniform(0, 0.1), 3),
                "fear": round(random.uniform(0, 0.2), 3),
                "happy": round(random.uniform(0.3, 0.7), 3),
                "sad": round(random.uniform(0, 0.3), 3),
                "surprise": round(random.uniform(0, 0.2), 3),
                "neutral": round(random.uniform(0.2, 0.6), 3)
            },
            "recent_distribution": {current: 1.0},
            "timestamp": datetime.now().isoformat(),
            "data_source": "fallback",
            "sample_count": 1
        }
    
    def get_comprehensive_focus_data(self, task_id: int) -> Dict:
        """获取综合的专注数据"""
        eeg_data = self.get_latest_eeg_data()
        emotion_data = self.get_latest_emotion_data()
        
        # 计算综合指标
        focus_score = eeg_data["current"]["attention"] * 0.6 + \
                     eeg_data["current"]["engagement"] * 0.4
        
        stress_level = eeg_data["current"]["stress"]
        
        # 根据情绪调整
        if emotion_data["current_emotion"] in ["happy", "neutral"]:
            focus_score *= 1.1  # 积极情绪提升专注度
        elif emotion_data["current_emotion"] in ["sad", "angry"]:
            focus_score *= 0.9  # 消极情绪降低专注度
        
        focus_score = min(1.0, focus_score)  # 确保不超过1
        
        return {
            "task_id": task_id,
            "current_data": {
                "focus_level": round(focus_score, 3),
                "attention": eeg_data["current"]["attention"],
                "engagement": eeg_data["current"]["engagement"],
                "excitement": eeg_data["current"]["excitement"],
                "interest": eeg_data["current"]["interest"],
                "stress_level": eeg_data["current"]["stress"],
                "relaxation": eeg_data["current"]["relaxation"],
                "current_emotion": emotion_data["current_emotion"],
                "emotion_confidence": max(emotion_data["emotion_scores"].values()),
                "data_quality": "good" if eeg_data["data_source"] == "real_eeg" else "simulated"
            },
            "trends": {
                "focus": [
                    att * 0.6 + eng * 0.4 
                    for att, eng in zip(
                        eeg_data["trends"]["attention"], 
                        eeg_data["trends"]["engagement"]
                    )
                ],
                "attention": eeg_data["trends"]["attention"],
                "engagement": eeg_data["trends"]["engagement"],
                "excitement": eeg_data["trends"]["excitement"],
                "interest": eeg_data["trends"]["interest"],
                "stress": eeg_data["trends"]["stress"],
                "relaxation": eeg_data["trends"]["relaxation"]
            },
            "metadata": {
                "eeg_source": eeg_data["data_source"],
                "emotion_source": emotion_data["data_source"],
                "eeg_samples": eeg_data["sample_count"],
                "emotion_samples": emotion_data["sample_count"],
                "last_updated": datetime.now().isoformat()
            }
        }