# 赛博爹妈 CyberParents

AI驱动的智能任务管理和专注力提升工具，集成多模态交互与情感分析。

## ✨ 核心功能

### 🎯 任务管理
- **AI任务分解**：输入大目标，AI自动分解为可执行小任务
- **智能分组**：任务自动归类和优先级管理
- **进度追踪**：实时任务完成状态可视化

### 💬 智能对话
- **AI聊天助手**：支持任务规划和学习指导
- **语音交互**：语音输入/输出，解放双手
- **父母角色切换**：不同AI人格提供差异化建议

### 🧘 专注模式
- **沉浸式专注**：弹幕提醒和专注氛围营造
- **干扰阻断**：专注时段智能提醒管理
- **专注统计**：专注时长和效率分析

### 📊 数据集成
- **脑电数据**：集成EEG设备监测专注状态
- **情感分析**：EmotionCV实时情绪识别
- **多源数据融合**：综合生理和行为数据

## 🚀 快速启动

### 1. 启动后端服务
```bash
./start_backend.sh
```
后端将运行在：http://localhost:8000

### 2. 启动前端服务
```bash
./start_frontend.sh  
```
前端将运行在：http://localhost:3000

## 📁 项目结构

```
CyberParents/
├── backend/                 # Python FastAPI后端
│   ├── main.py             # 主要API路由
│   ├── real_data_reader.py # EEG数据读取
│   └── requirements.txt
├── frontend/               # Vue3前端应用
│   ├── src/
│   │   ├── App.vue        # 主应用组件
│   │   ├── components/    # 功能组件
│   │   │   ├── chat/      # 聊天相关组件
│   │   │   ├── common/    # 通用组件
│   │   │   ├── focus/     # 专注模式组件
│   │   │   └── tasks/     # 任务管理组件
│   │   ├── composables/   # Vue组合式函数
│   │   │   ├── useChat.js    # 聊天逻辑
│   │   │   ├── useTasks.js   # 任务管理
│   │   │   └── useVoiceChat.js # 语音功能
│   │   ├── styles/        # 样式文件
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
└── logo.jpg               # 项目Logo
```

## 🔧 技术栈

### 前端
- **Vue3** + **Vite** - 现代前端框架
- **SCSS** - CSS预处理器
- **Axios** - HTTP客户端
- **Web Audio API** - 语音功能

### 后端
- **Python** + **FastAPI** - 异步Web框架
- **SQLite** - 轻量级数据库
- **WebSocket** - 实时通信

### AI & 数据
- **Kimi K2** - AI对话和任务分解
- **EEG设备集成** - 脑电数据采集
- **EmotionCV** - 计算机视觉情感识别

## 📋 主要API

### 任务管理
- `POST /breakdown` - AI任务分解
- `GET /todos` - 获取任务列表
- `PUT /todos/{id}` - 更新任务状态
- `DELETE /todos/{id}` - 删除任务

### 实时数据
- `WebSocket /ws` - 实时数据推送
- `GET /eeg-data` - 获取脑电数据
- `GET /emotion-data` - 获取情绪数据





## 🧠 核心价值

赛博爹妈不只是任务管理工具，而是通过AI和生理数据融合，为用户提供**智能化的生活和学习助手**，帮助建立更好的专注习惯和执行力。

---

