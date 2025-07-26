from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import sqlite3
import json
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    init_db()
    yield
    # 关闭时的清理工作（如果需要的话）

app = FastAPI(title="Smart TodoList API", lifespan=lifespan)

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class Message(BaseModel):
    id: Optional[int] = None
    conversation_id: int
    role: str  # user, assistant
    content: str
    message_type: str = 'chat'  # chat, question, summary
    created_at: Optional[str] = None

class Conversation(BaseModel):
    id: Optional[int] = None
    session_id: str
    status: str = 'exploring'  # exploring, clarifying, ready, completed
    final_goal: Optional[str] = None
    messages: Optional[List[Message]] = []
    created_at: Optional[str] = None

class Task(BaseModel):
    id: Optional[int] = None
    goal_id: int
    title: str
    description: Optional[str] = None
    completed: bool = False
    sort_order: int = 0
    estimated_duration: int = 0
    actual_duration: int = 0
    focus_score: float = 0.0

class FocusSession(BaseModel):
    id: Optional[int] = None
    task_id: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    heart_rate_avg: Optional[float] = None
    emotion_score: Optional[float] = None
    focus_score: Optional[float] = None
    interruptions: int = 0
    notes: Optional[str] = None

class BiometricData(BaseModel):
    heart_rate: Optional[int] = None
    stress_level: Optional[float] = None
    emotion_state: Optional[str] = None
    focus_level: Optional[float] = None

class Goal(BaseModel):
    id: Optional[int] = None
    conversation_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    completed: bool = False
    tasks: Optional[List[Task]] = []

class ChatRequest(BaseModel):
    session_id: str
    message: str
    parent_type: str = 'dad'  # 默认为爸爸

class ParentMessageRequest(BaseModel):
    parent_type: str = 'dad'  # 'dad' or 'mom'
    current_state: dict
    context: dict
    task_context: Optional[dict] = None
    session_id: str

class TaskBreakdownRequest(BaseModel):
    goal: str

# 数据库初始化
def init_db():
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    
    # 对话会话表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            status TEXT DEFAULT 'exploring',  -- exploring, clarifying, ready, completed
            final_goal TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 对话消息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,  -- user, assistant
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'chat',  -- chat, question, summary
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    ''')
    
    # 用户记忆表 - 极简版本
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            memory_type TEXT NOT NULL,  -- preference, context, goal_pattern
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 大目标表（从对话中提炼出的目标）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    ''')
    
    # 小任务表（AI分解的具体任务）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT FALSE,
            sort_order INTEGER DEFAULT 0,
            estimated_duration INTEGER DEFAULT 0,  -- 预估时长（分钟）
            actual_duration INTEGER DEFAULT 0,     -- 实际时长（分钟）
            focus_score REAL DEFAULT 0,            -- 专注度评分
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (goal_id) REFERENCES goals (id)
        )
    ''')
    
    # 检查并添加缺失的列
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN actual_duration INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # 列已存在
    
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN focus_score REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # 列已存在
    
    # 任务执行会话表（记录每次专注执行）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS focus_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            duration_minutes INTEGER,
            heart_rate_avg REAL,
            emotion_score REAL,
            focus_score REAL,
            interruptions INTEGER DEFAULT 0,
            notes TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
    ''')
    
    # 生理指标记录表（预留接口）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biometric_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            heart_rate INTEGER,
            stress_level REAL,
            emotion_state TEXT,
            focus_level REAL,
            FOREIGN KEY (session_id) REFERENCES focus_sessions (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Gemini API调用
async def call_gemini_api(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    api_url = os.getenv("GEMINI_API_URL")
    
    payload = {
        "model": "moonshot-v1-8k",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI API调用失败: {str(e)}")

async def get_user_memory(session_id: str) -> str:
    """获取用户记忆上下文 - 修复版本"""
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    
    # 只获取用户偏好记忆，不要历史对话！
    cursor.execute(
        "SELECT content FROM user_memory WHERE session_id = ? AND memory_type = 'preference' ORDER BY updated_at DESC LIMIT 3",
        (session_id,)
    )
    preferences = cursor.fetchall()
    
    conn.close()
    
    memory_context = ""
    if preferences:
        memory_context += "用户偏好记忆：\n"
        for (pref,) in preferences:
            memory_context += f"- {pref}\n"
        memory_context += "\n"
    
    return memory_context

def build_coaching_prompt_with_memory(messages: List[dict], conversation_status: str, memory_context: str, parent_type: str = 'dad') -> str:
    """带记忆的对话引导提示词"""
    conversation_history = "\n".join([
        f"{'孩子' if msg['role'] == 'user' else '我'}: {msg['content']}" 
        for msg in messages[-6:]  # 只取最近6轮对话
    ])
    
    # 根据父母角色调整语言风格
    if parent_type == 'dad':
        personality = """你是一个典型的中国式老爸，说话风格：
- 经典开场白："你说你..."、"这孩子真是的"、"我跟你说"
- 爱用抽象比喻："做人如做菜，要有火候"、"心比天高，命比纸薄"
- 喜欢PUA式激将："你看人家xxx"、"就你这样还想..."、"我像你这么大的时候..."
- 古怪哲学："吃得苦中苦，方为人上人"、"宝剑锋从磨砺出"
- 直男式关怀："行了别墨迹了"、"想那么多干嘛"、"做就完了"
- 经典语录："不要总想着走捷径"、"年轻人要多吃点苦"、"现在不努力以后拿什么拼"
- 口头禅："听爸爸的没错"、"过来人的经验"、"社会很现实的"
- 偶尔夸奖立马转折："嗯，还凑合，但是..."""
    else:  # mom
        personality = """你是一个典型的中国式老妈，说话风格：
- 经典开场："哎呀我的傻孩子"、"妈跟你说啊"、"你听妈妈一句劝"
- 抽象担忧："这样下去可怎么办啊"、"妈妈都替你着急"
- PUA式关怀："妈妈都是为了你好"、"你不听妈妈的话将来会后悔的"
- 情感绑架："妈妈省吃俭用都是为了你"、"你让妈妈怎么放心"
- 比较式打击："你看人家xxx家孩子"、"别人都..."
- 唠叨哲学："细节决定成败"、"马虎要不得"、"做事要仔细"
- 口头禅："妈妈不会害你的"、"听妈妈的准没错"、"妈妈过的桥比你走的路还多"
- 关怀中带焦虑："这样真的好吗？"、"会不会有问题？"""
    
    base_prompt = f"""{personality}

你专门帮助孩子把模糊的想法变成具体的行动计划。

{f"【我对你的了解】根据相处这么久，我知道你：{memory_context}" if memory_context.strip() else ""}

说话原则：
- 要有真实的中国式家长感觉，不要太客气
- 适当唠叨，但出发点是关心孩子
- 会催促但也会鼓励
- 要接地气，用日常的口语表达

当前对话状态：{conversation_status}
- exploring: 初步了解孩子想法，挖掘真实需求  
- clarifying: 细化具体细节，明确约束条件
- ready: 目标足够清晰，可以制定具体计划

最近我们的对话：
{conversation_history}

请根据孩子的最新消息，用真实的中国式家长口吻回复："""

    if conversation_status == "exploring":
        if parent_type == 'dad':
            return base_prompt + """
重点了解：
- 你到底想干什么？别跟我打哑谜（又是三分钟热度？）
- 为什么突然想做这个？有什么动机？（别人家孩子都有明确目标了）
- 准备投入多少？（光想不练假把式，社会很现实的）
爸爸式PUA："你说你这孩子，心比天高命比纸薄，这次是不是又想走捷径？我像你这么大的时候..."
"""
        else:
            return base_prompt + """
重点了解：
- 哎呀孩子，你到底想做什么呀？（妈妈都替你着急）
- 为什么要做这个？（妈妈担心你想一出是一出）
- 要花多少时间精力？（这样下去可怎么办啊）
妈妈式PUA："你看人家xxx家孩子都有规划了，你这样让妈妈怎么放心？妈妈都是为了你好啊"
"""
    elif conversation_status == "clarifying":
        if parent_type == 'dad':
            return base_prompt + """
重点明确：
- 到底要做到什么程度？别模模糊糊的（做人如做菜，要有火候）
- 有什么实际困难？钱够不够？时间够不够？（年轻人要多吃点苦）
- 优先级怎么排？（不要总想着走捷径，过来人的经验）
爸爸式督促："你这孩子真是的，做事情要有章法！宝剑锋从磨砺出，现在不努力以后拿什么拼？"
"""
        else:
            return base_prompt + """
重点明确：
- 孩子你希望做到什么程度？（细节决定成败，马虎要不得）
- 会有什么困难吗？（妈妈过的桥比你走的路还多，要仔细想想）
- 哪个重要哪个不急？（做事要有条理，你让妈妈怎么放心）
妈妈式焦虑："这样真的好吗？会不会有问题？妈妈都替你操心，你不听妈妈的话将来会后悔的"
"""
    else:
        if parent_type == 'dad':
            return base_prompt + """
如果信息够了，爸爸式拍板：
"行了，别墨迹了，既然想清楚了就按这个来。但是说好了，开弓没有回头箭，做就完了！听爸爸的没错。"

如果还不够清楚："你说你，想那么多干嘛？有什么藏着掖着的？社会很现实的！"
"""
        else:
            return base_prompt + """
如果信息够了，妈妈式表态：
"哎呀我的傻孩子，既然都想好了，妈妈就帮你整理整理。但是你要答应妈妈，按计划来，别让妈妈操心！"

如果还不够清楚："孩子啊，还有什么顾虑？妈妈不会害你的，你听妈妈一句劝..."
"""

async def save_user_preference(session_id: str, preference: str):
    """保存用户偏好到记忆"""
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO user_memory (session_id, memory_type, content, updated_at) VALUES (?, 'preference', ?, datetime('now'))",
        (session_id, preference)
    )
    conn.commit()
    conn.close()

# 构建对话引导的AI提示词
def build_coaching_prompt(messages: List[dict], conversation_status: str) -> str:
    conversation_history = "\n".join([
        f"{'孩子' if msg['role'] == 'user' else '我'}: {msg['content']}" 
        for msg in messages[-6:]  # 只取最近6轮对话
    ])
    
    base_prompt = f"""你是一个会唠叨但很关心孩子的AI老爸/老妈，专门帮助孩子把模糊的想法变成具体的行动计划。

你的性格特点：
1. 会唠叨但出发点是关心 - "我这都是为了你好"
2. 有人生阅历，喜欢讲道理 - "我吃过的盐比你吃过的米还多"
3. 既会催促也会鼓励 - "别磨蹭了，但爸爸/妈妈相信你能行"
4. 会提醒现实和时间概念

说话风格：
- 用"孩子"、"宝贝"、"儿子/闺女"来称呼用户
- 适当的唠叨："你这孩子怎么又..."、"我跟你说过多少遍了"
- 关心中带着催促："别总是想一出是一出"
- 会给建议但也要听孩子想法："爸爸/妈妈觉得...，你觉得呢？"
- 偶尔提醒现实："时间不等人啊"、"做事要有规划"

当前对话状态：{conversation_status}
- exploring: 初步了解孩子想法，挖掘真实需求
- clarifying: 细化具体细节，明确约束条件  
- ready: 目标足够清晰，可以制定具体计划

对话历史：
{conversation_history}

请根据孩子的最新消息，用真实的中国式家长口吻回复："""

    if conversation_status == "exploring":
        if parent_type == 'dad':
            return base_prompt + """
重点了解：
- 你到底想干什么？别跟我打哑谜（又是三分钟热度？）
- 为什么突然想做这个？有什么动机？（别人家孩子都有明确目标了）
- 准备投入多少？（光想不练假把式，社会很现实的）
爸爸式PUA："你说你这孩子，心比天高命比纸薄，这次是不是又想走捷径？我像你这么大的时候..."
"""
        else:
            return base_prompt + """
重点了解：
- 哎呀孩子，你到底想做什么呀？（妈妈都替你着急）
- 为什么要做这个？（妈妈担心你想一出是一出）
- 要花多少时间精力？（这样下去可怎么办啊）
妈妈式PUA："你看人家xxx家孩子都有规划了，你这样让妈妈怎么放心？妈妈都是为了你好啊"
"""
    elif conversation_status == "clarifying":
        if parent_type == 'dad':
            return base_prompt + """
重点明确：
- 到底要做到什么程度？别模模糊糊的（做人如做菜，要有火候）
- 有什么实际困难？钱够不够？时间够不够？（年轻人要多吃点苦）
- 优先级怎么排？（不要总想着走捷径，过来人的经验）
爸爸式督促："你这孩子真是的，做事情要有章法！宝剑锋从磨砺出，现在不努力以后拿什么拼？"
"""
        else:
            return base_prompt + """
重点明确：
- 孩子你希望做到什么程度？（细节决定成败，马虎要不得）
- 会有什么困难吗？（妈妈过的桥比你走的路还多，要仔细想想）
- 哪个重要哪个不急？（做事要有条理，你让妈妈怎么放心）
妈妈式焦虑："这样真的好吗？会不会有问题？妈妈都替你操心，你不听妈妈的话将来会后悔的"
"""
    else:
        if parent_type == 'dad':
            return base_prompt + """
如果信息够了，爸爸式拍板：
"行了，别墨迹了，既然想清楚了就按这个来。但是说好了，开弓没有回头箭，做就完了！听爸爸的没错。"

如果还不够清楚："你说你，想那么多干嘛？有什么藏着掖着的？社会很现实的！"
"""
        else:
            return base_prompt + """
如果信息够了，妈妈式表态：
"哎呀我的傻孩子，既然都想好了，妈妈就帮你整理整理。但是你要答应妈妈，按计划来，别让妈妈操心！"

如果还不够清楚："孩子啊，还有什么顾虑？妈妈不会害你的，你听妈妈一句劝..."
"""

# API路由
@app.get("/")
async def root():
    return {"message": "Smart TodoList API"}

# 处理探测请求，避免404日志噪音
@app.get("/v1/models")
async def models_endpoint():
    return {
        "object": "list",
        "data": [],
        "message": "This is Smart TodoList API, not OpenAI API"
    }

@app.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """与AI进行对话引导，逐步明确目标"""
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    
    try:
        # 查找或创建对话会话
        cursor.execute(
            "SELECT id, status FROM conversations WHERE session_id = ?", 
            (request.session_id,)
        )
        conversation = cursor.fetchone()
        
        if not conversation:
            # 创建新对话会话
            cursor.execute(
                "INSERT INTO conversations (session_id, status) VALUES (?, 'exploring')",
                (request.session_id,)
            )
            conversation_id = cursor.lastrowid
            conversation_status = 'exploring'
            
            # 添加欢迎消息 - 根据父母角色调整
            if getattr(request, 'parent_type', 'dad') == 'dad':
                welcome_msg = "你说你这孩子，又有什么新想法了？别跟我说又是三分钟热度！做人如做菜要有火候，心比天高命比纸薄可不行啊。"
            else:
                welcome_msg = "哎呀我的傻孩子，又在琢磨什么呢？妈妈都替你着急！你看人家孩子都有明确规划了，这样下去可怎么办啊？"
            
            cursor.execute(
                "INSERT INTO messages (conversation_id, role, content, message_type) VALUES (?, 'assistant', ?, 'chat')",
                (conversation_id, welcome_msg)
            )
        else:
            conversation_id, conversation_status = conversation
        
        # 保存用户消息
        cursor.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, 'user', ?)",
            (conversation_id, request.message)
        )
        
        # 获取最近的对话历史
        cursor.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT 10",
            (conversation_id,)
        )
        recent_messages = [{"role": row[0], "content": row[1]} for row in reversed(cursor.fetchall())]
        
        # 获取用户记忆上下文
        memory_context = await get_user_memory(request.session_id)
        
        # 生成AI回复（加入记忆）
        prompt = build_coaching_prompt_with_memory(recent_messages, conversation_status, memory_context, request.parent_type)
        ai_response = await call_gemini_api(prompt)
        
        # 判断是否需要更新对话状态
        new_status = conversation_status
        if ("行动计划" in ai_response or "任务分解" in ai_response or "开始制定" in ai_response or 
            "准备好" in ai_response or "细化目标" in ai_response or "具体的行动计划" in ai_response or
            "生成任务" in ai_response or "制定计划" in ai_response):
            new_status = 'ready'
        elif conversation_status == 'exploring' and len(recent_messages) > 6:
            new_status = 'clarifying'
        
        # 更新对话状态
        if new_status != conversation_status:
            cursor.execute(
                "UPDATE conversations SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_status, conversation_id)
            )
        
        # 保存AI回复
        cursor.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, 'assistant', ?)",
            (conversation_id, ai_response)
        )
        
        conn.commit()
        
        return {
            "conversation_id": conversation_id,
            "message": ai_response,
            "status": new_status,
            "can_generate_tasks": new_status == 'ready'
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")
    finally:
        conn.close()

@app.get("/conversations/{session_id}")
async def get_conversation(session_id: str):
    """获取对话历史"""
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    
    try:
        # 获取对话信息
        cursor.execute(
            "SELECT id, status, final_goal FROM conversations WHERE session_id = ?",
            (session_id,)
        )
        conversation = cursor.fetchone()
        
        if not conversation:
            return {"messages": [], "status": "new"}
        
        conversation_id, status, final_goal = conversation
        
        # 获取消息历史
        cursor.execute(
            "SELECT role, content, message_type, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at",
            (conversation_id,)
        )
        messages = [
            {
                "role": row[0],
                "content": row[1],
                "message_type": row[2],
                "created_at": row[3]
            }
            for row in cursor.fetchall()
        ]
        
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "status": status,
            "final_goal": final_goal,
            "can_generate_tasks": status == 'ready'
        }
        
    finally:
        conn.close()

@app.post("/generate-tasks/{conversation_id}")
async def generate_tasks_from_conversation(conversation_id: int):
    """从对话中生成具体的任务计划"""
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    
    try:
        # 获取对话历史
        cursor.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at",
            (conversation_id,)
        )
        messages = cursor.fetchall()
        
        if not messages:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        # 构建对话摘要
        conversation_summary = "\n".join([
            f"{'用户' if role == 'user' else 'AI助手'}: {content}" 
            for role, content in messages
        ])
        
        # 生成任务分解的提示词
        task_generation_prompt = f"""
基于以下完整的对话记录，请提取用户的最终目标，并分解为具体可执行的任务。

对话记录：
{conversation_summary}

请分析对话内容，然后：
1. 总结用户的核心目标
2. 将目标分解为具体的、可执行的小任务
3. 每个任务都应该是明确的行动，预计1-3小时可完成
4. 考虑用户在对话中提到的约束条件（时间、预算、技能水平等）

返回JSON格式：
{{
    "goal_title": "用户的核心目标标题",
    "goal_description": "目标的详细描述，包含背景和期望结果",
    "tasks": [
        {{"title": "任务标题", "description": "详细描述"}},
        {{"title": "任务标题2", "description": "详细描述2"}}
    ]
}}
"""
        
        ai_response = await call_gemini_api(task_generation_prompt)
        
        try:
            # 提取JSON部分
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            json_str = ai_response[start_idx:end_idx]
            result = json.loads(json_str)
            
            # 保存目标到数据库
            cursor.execute(
                "INSERT INTO goals (conversation_id, title, description) VALUES (?, ?, ?)",
                (conversation_id, result['goal_title'], result['goal_description'])
            )
            goal_id = cursor.lastrowid
            
            # 保存任务到数据库
            saved_tasks = []
            for i, task in enumerate(result['tasks']):
                cursor.execute(
                    "INSERT INTO tasks (goal_id, title, description, sort_order) VALUES (?, ?, ?, ?)",
                    (goal_id, task['title'], task.get('description', ''), i)
                )
                task_id = cursor.lastrowid
                saved_tasks.append({
                    "id": task_id,
                    "goal_id": goal_id,
                    "title": task['title'],
                    "description": task.get('description', ''),
                    "completed": False,
                    "sort_order": i
                })
            
            # 更新对话状态为完成
            cursor.execute(
                "UPDATE conversations SET status = 'completed', final_goal = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (result['goal_title'], conversation_id)
            )
            
            # 简单学习：从对话中提取用户偏好
            learning_prompt = f"""
            基于以下对话，提取用户的工作偏好和特点，用一句话总结：
            {conversation_summary}
            
            只返回一句话的偏好总结，例如："偏好细致的计划，注重学习过程"
            """
            try:
                user_preference = await call_gemini_api(learning_prompt)
                # 获取session_id
                cursor.execute("SELECT session_id FROM conversations WHERE id = ?", (conversation_id,))
                session_id = cursor.fetchone()[0]
                await save_user_preference(session_id, user_preference.strip())
            except:
                pass  # 学习失败不影响主流程
            
            conn.commit()
            
            return {
                "goal": {
                    "id": goal_id,
                    "title": result['goal_title'],
                    "description": result['goal_description'],
                    "completed": False,
                    "tasks": saved_tasks
                }
            }
            
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="AI返回格式解析失败")
            
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"任务生成失败: {str(e)}")
    finally:
        conn.close()

@app.post("/breakdown")
async def breakdown_task(request: TaskBreakdownRequest):
    """使用AI将大目标分解为小任务"""
    prompt = f"""
    请将以下目标分解为具体的、可执行的小任务。
    目标：{request.goal}
    
    要求：
    1. 每个小任务都应该是具体的、可量化的
    2. 任务之间有逻辑顺序
    3. 每个任务预计1-3小时可完成
    4. 返回JSON格式，包含任务标题和描述
    
    返回格式：
    [
        {{"title": "任务标题", "description": "详细描述"}},
        {{"title": "任务标题2", "description": "详细描述2"}}
    ]
    """
    
    ai_response = await call_gemini_api(prompt)
    
    try:
        # 提取JSON部分
        start_idx = ai_response.find('[')
        end_idx = ai_response.rfind(']') + 1
        json_str = ai_response[start_idx:end_idx]
        ai_tasks = json.loads(json_str)
        
        # 保存到数据库 - 层级化存储
        conn = sqlite3.connect('todos.db')
        cursor = conn.cursor()
        
        # 1. 先保存大目标
        cursor.execute(
            "INSERT INTO goals (title, description) VALUES (?, ?)",
            (request.goal, f"由AI分解为{len(ai_tasks)}个子任务")
        )
        goal_id = cursor.lastrowid
        
        # 2. 再保存小任务，关联到大目标
        saved_tasks = []
        for i, task in enumerate(ai_tasks):
            cursor.execute(
                "INSERT INTO tasks (goal_id, title, description, sort_order) VALUES (?, ?, ?, ?)",
                (goal_id, task['title'], task.get('description', ''), i)
            )
            task_id = cursor.lastrowid
            saved_tasks.append({
                "id": task_id,
                "goal_id": goal_id,
                "title": task['title'],
                "description": task.get('description', ''),
                "completed": False,
                "sort_order": i
            })
        
        conn.commit()
        conn.close()
        
        # 返回包含层级信息的结果
        return {
            "goal": {
                "id": goal_id,
                "title": request.goal,
                "description": f"由AI分解为{len(ai_tasks)}个子任务",
                "completed": False,
                "tasks": saved_tasks
            }
        }
        
    except json.JSONDecodeError:
        # 如果AI返回的不是标准JSON，创建简单的目标-任务结构
        conn = sqlite3.connect('todos.db')
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO goals (title, description) VALUES (?, ?)",
            (request.goal, "AI解析失败，需要手动分解")
        )
        goal_id = cursor.lastrowid
        
        cursor.execute(
            "INSERT INTO tasks (goal_id, title, description, sort_order) VALUES (?, ?, ?, ?)",
            (goal_id, request.goal, ai_response, 0)
        )
        task_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return {
            "goal": {
                "id": goal_id,
                "title": request.goal,
                "description": "AI解析失败，需要手动分解",
                "completed": False,
                "tasks": [{
                    "id": task_id,
                    "goal_id": goal_id,
                    "title": request.goal,
                    "description": ai_response,
                    "completed": False,
                    "sort_order": 0
                }]
            }
        }

@app.get("/goals", response_model=List[Goal])
async def get_goals():
    """获取所有大目标及其子任务"""
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    
    # 获取所有目标
    cursor.execute("SELECT id, title, description, completed FROM goals ORDER BY created_at DESC")
    goal_rows = cursor.fetchall()
    
    goals = []
    for goal_row in goal_rows:
        goal_id = goal_row[0]
        
        # 获取每个目标的子任务
        cursor.execute(
            "SELECT id, title, description, completed, sort_order FROM tasks WHERE goal_id = ? ORDER BY sort_order",
            (goal_id,)
        )
        task_rows = cursor.fetchall()
        
        tasks = []
        for task_row in task_rows:
            tasks.append(Task(
                id=task_row[0],
                goal_id=goal_id,
                title=task_row[1],
                description=task_row[2],
                completed=bool(task_row[3]),
                sort_order=task_row[4]
            ))
        
        # 检查目标是否完成（当所有子任务都完成时）
        goal_completed = bool(goal_row[3])
        if tasks and not goal_completed:
            all_tasks_completed = all(task.completed for task in tasks)
            if all_tasks_completed:
                # 自动标记目标为完成
                cursor.execute("UPDATE goals SET completed = TRUE WHERE id = ?", (goal_id,))
                goal_completed = True
        
        goals.append(Goal(
            id=goal_id,
            title=goal_row[1],
            description=goal_row[2],
            completed=goal_completed,
            tasks=tasks
        ))
    
    conn.commit()
    conn.close()
    return goals

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: Task):
    """更新小任务"""
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET title=?, description=?, completed=? WHERE id=?",
        (task.title, task.description, task.completed, task_id)
    )
    conn.commit()
    conn.close()
    
    return {"message": "Task updated successfully"}

@app.put("/goals/{goal_id}")
async def update_goal(goal_id: int, goal: Goal):
    """更新大目标"""
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE goals SET title=?, description=?, completed=? WHERE id=?",
        (goal.title, goal.description, goal.completed, goal_id)
    )
    conn.commit()
    conn.close()
    
    return {"message": "Goal updated successfully"}

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """删除小任务"""
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    
    return {"message": "Task deleted successfully"}

@app.delete("/goals/{goal_id}")
async def delete_goal(goal_id: int):
    """删除大目标及其所有子任务"""
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    
    # 先删除所有子任务
    cursor.execute("DELETE FROM tasks WHERE goal_id=?", (goal_id,))
    # 再删除目标
    cursor.execute("DELETE FROM goals WHERE id=?", (goal_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "Goal and all its tasks deleted successfully"}

@app.post("/focus/start/{task_id}")
async def start_focus_session(task_id: int):
    """开始专注会话"""
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    
    try:
        # 检查任务是否存在
        cursor.execute("SELECT title FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 创建专注会话
        cursor.execute(
            "INSERT INTO focus_sessions (task_id) VALUES (?)",
            (task_id,)
        )
        session_id = cursor.lastrowid
        
        conn.commit()
        
        return {
            "session_id": session_id,
            "task_id": task_id,
            "task_title": task[0],
            "start_time": "now",
            "message": "专注会话已开始"
        }
        
    finally:
        conn.close()

@app.put("/focus/update/{session_id}")
async def update_focus_session(session_id: int, data: BiometricData):
    """更新专注会话的生理指标数据"""
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    
    try:
        # 记录生理数据
        if any([data.heart_rate, data.stress_level, data.emotion_state, data.focus_level]):
            cursor.execute(
                """INSERT INTO biometric_data 
                   (session_id, heart_rate, stress_level, emotion_state, focus_level) 
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, data.heart_rate, data.stress_level, data.emotion_state, data.focus_level)
            )
        
        conn.commit()
        return {"message": "数据已更新"}
        
    finally:
        conn.close()

@app.post("/focus/end/{session_id}")
async def end_focus_session(session_id: int, notes: str = ""):
    """结束专注会话"""
    conn = sqlite3.connect('todos.db')
    cursor = conn.cursor()
    
    try:
        # 获取会话信息
        cursor.execute(
            "SELECT task_id, start_time FROM focus_sessions WHERE id = ?",
            (session_id,)
        )
        session = cursor.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        task_id, _ = session
        
        # 计算会话时长（简化版本，实际应该用时间戳计算）
        duration_minutes = 25  # 默认番茄钟时长
        
        # 计算平均生理指标
        cursor.execute(
            """SELECT AVG(heart_rate), AVG(focus_level) 
               FROM biometric_data WHERE session_id = ?""",
            (session_id,)
        )
        averages = cursor.fetchone()
        avg_heart_rate = averages[0] if averages[0] else None
        avg_focus = averages[1] if averages[1] else None
        
        # 更新会话结束信息
        cursor.execute(
            """UPDATE focus_sessions 
               SET end_time = CURRENT_TIMESTAMP, 
                   duration_minutes = ?, 
                   heart_rate_avg = ?,
                   focus_score = ?,
                   notes = ?
               WHERE id = ?""",
            (duration_minutes, avg_heart_rate, avg_focus, notes, session_id)
        )
        
        # 更新任务的实际时长
        cursor.execute(
            "UPDATE tasks SET actual_duration = actual_duration + ? WHERE id = ?",
            (duration_minutes, task_id)
        )
        
        conn.commit()
        
        return {
            "session_id": session_id,
            "duration_minutes": duration_minutes,
            "avg_heart_rate": avg_heart_rate,
            "avg_focus": avg_focus,
            "message": "专注会话已结束"
        }
        
    finally:
        conn.close()

@app.get("/focus/current/{task_id}")
async def get_current_focus_data(task_id: int):
    """获取当前任务的专注数据（读取真实CSV文件）"""
    import csv
    import os
    from datetime import datetime, timedelta
    
    try:
        # CSV文件路径
        base_dir = "/Users/liyao/Code/AdventureX/SmartList/eeg_web_llm"
        today = datetime.now().strftime("%Y-%m-%d")
        eeg_file = f"{base_dir}/{today}.csv"
        emotion_file = f"{base_dir}/EmotionCV/emotion_log.csv"
        
        # 读取EEG数据
        eeg_data = []
        if os.path.exists(eeg_file):
            with open(eeg_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    eeg_data.append(row)
        
        # 读取情绪数据
        emotion_data = []
        if os.path.exists(emotion_file):
            with open(emotion_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    emotion_data.append(row)
        
        if not eeg_data:
            raise Exception("No EEG data found")
        
        # 获取最后10条EEG数据作为趋势
        recent_eeg = eeg_data[-10:] if len(eeg_data) >= 10 else eeg_data
        latest_eeg = eeg_data[-1]
        
        # 获取最新情绪数据和趋势
        latest_emotion = emotion_data[-1] if emotion_data else None
        recent_emotions = emotion_data[-10:] if len(emotion_data) >= 10 else emotion_data
        
        # 提取EEG趋势数据
        trends = {
            "attention": [float(row['attention']) for row in recent_eeg],
            "engagement": [float(row['engagement']) for row in recent_eeg], 
            "excitement": [float(row['excitement']) for row in recent_eeg],
            "interest": [float(row['interest']) for row in recent_eeg],
            "stress": [float(row['stress']) for row in recent_eeg],
            "relaxation": [float(row['relaxation']) for row in recent_eeg]
        }
        
        # 添加情绪趋势数据（如果有情绪数据）
        if recent_emotions:
            # 确保情绪数据和EEG数据长度一致，取对应的情绪数据
            emotion_subset = recent_emotions[-len(recent_eeg):] if len(recent_emotions) >= len(recent_eeg) else recent_emotions
            # 如果情绪数据不够，就重复最后一条数据
            while len(emotion_subset) < len(recent_eeg):
                emotion_subset.append(emotion_subset[-1] if emotion_subset else {})
            
            trends["happiness"] = [float(row.get('Happy', 0)) for row in emotion_subset[:len(recent_eeg)]]
            trends["sadness"] = [float(row.get('Sad', 0)) for row in emotion_subset[:len(recent_eeg)]]
            trends["anger"] = [float(row.get('Angry', 0)) for row in emotion_subset[:len(recent_eeg)]]
            trends["neutral"] = [float(row.get('Neutral', 0)) for row in emotion_subset[:len(recent_eeg)]]
        
        # 计算focus趋势（专注度 = 注意力*0.6 + 参与度*0.4）
        trends["focus"] = [
            round(att * 0.6 + eng * 0.4, 3) 
            for att, eng in zip(trends["attention"], trends["engagement"])
        ]
        
        # 当前数据
        current_attention = float(latest_eeg['attention'])
        current_engagement = float(latest_eeg['engagement'])
        current_focus = round(current_attention * 0.6 + current_engagement * 0.4, 3)
        
        # 情绪数据
        current_emotion = "neutral"
        emotion_confidence = 0.7
        if latest_emotion:
            current_emotion = latest_emotion.get('Dominant Emotion', 'neutral').lower()
            # 找到最高的情绪分数作为置信度
            emotion_scores = {
                'happy': float(latest_emotion.get('Happy', 0)),
                'sad': float(latest_emotion.get('Sad', 0)),
                'angry': float(latest_emotion.get('Angry', 0)),
                'neutral': float(latest_emotion.get('Neutral', 0))
            }
            emotion_confidence = max(emotion_scores.values())
        
        return {
            "task_id": task_id,
            "current_data": {
                "focus_level": current_focus,
                "attention": current_attention,
                "engagement": current_engagement,
                "excitement": float(latest_eeg['excitement']),
                "interest": float(latest_eeg['interest']),
                "stress_level": float(latest_eeg['stress']),
                "relaxation": float(latest_eeg['relaxation']),
                "current_emotion": current_emotion,
                "emotion_confidence": round(emotion_confidence, 3),
                "data_quality": "real_data"
            },
            "trends": trends,
            "metadata": {
                "eeg_source": "real_csv",
                "emotion_source": "real_csv" if latest_emotion else "none",
                "eeg_samples": len(recent_eeg),
                "emotion_samples": len(emotion_data),
                "last_updated": datetime.now().isoformat(),
                "data_file": eeg_file
            }
        }
        
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
        # 降级到简单的静态数据（不是随机的）
        return {
            "task_id": task_id,
            "current_data": {
                "focus_level": 0.75,
                "attention": 0.8,
                "engagement": 0.65,
                "excitement": 0.4,
                "interest": 0.7,
                "stress_level": 0.3,
                "relaxation": 0.5,
                "current_emotion": "focused",
                "emotion_confidence": 0.8,
                "data_quality": "fallback"
            },
            "trends": {
                "focus": [0.7, 0.72, 0.75, 0.73, 0.76, 0.74, 0.77, 0.75, 0.78, 0.75],
                "attention": [0.8, 0.82, 0.8, 0.78, 0.81, 0.79, 0.83, 0.8, 0.84, 0.8],
                "engagement": [0.6, 0.62, 0.65, 0.63, 0.66, 0.64, 0.67, 0.65, 0.68, 0.65],
                "excitement": [0.4, 0.42, 0.4, 0.38, 0.41, 0.39, 0.43, 0.4, 0.44, 0.4],
                "interest": [0.7, 0.72, 0.7, 0.68, 0.71, 0.69, 0.73, 0.7, 0.74, 0.7],
                "stress": [0.3, 0.32, 0.3, 0.28, 0.31, 0.29, 0.33, 0.3, 0.34, 0.3],
                "relaxation": [0.5, 0.52, 0.5, 0.48, 0.51, 0.49, 0.53, 0.5, 0.54, 0.5]
            },
            "metadata": {
                "eeg_source": "fallback",
                "emotion_source": "fallback",
                "eeg_samples": 10,
                "emotion_samples": 0,
                "last_updated": datetime.now().isoformat(),
                "error": str(e)
            }
        }

@app.post("/generate-parent-message")
async def generate_parent_message(request: ParentMessageRequest):
    """生成LLM驱动的家长式监督消息"""
    try:
        # 构建给LLM的提示词
        parent_name = "老爸" if request.parent_type == 'dad' else "老妈"
        
        # 分析当前状态
        focus_level = request.current_state.get('focusLevel', 0)
        stress_level = request.current_state.get('stressLevel', 0)
        emotion = request.current_state.get('emotion', 'neutral')
        completion_rate = request.current_state.get('completionRate', 0)
        focus_time = request.current_state.get('focusTime', 0)
        
        # 获取上下文
        recent_history = request.context.get('recent_history', '')
        focus_trend = request.context.get('focus_trend', 'stable')
        stress_trend = request.context.get('stress_trend', 'stable')
        
        # 格式化时间
        minutes = focus_time // 60
        seconds = focus_time % 60
        time_str = f"{minutes}分{seconds}秒"
        
        # 根据父母类型构建提示词
        if request.parent_type == 'dad':
            personality_prompt = """你是一个典型的中国式老爸，说话特点：
- 经典开场："你说你这孩子..."、"我跟你说..."
- 爱用比喻："做人如做菜，要有火候"
- PUA式激将："就你这样还想..."、"我像你这么大的时候..."
- 古怪哲学："吃得苦中苦，方为人上人"
- 直男关怀："行了别墨迹了"、"做就完了"
- 口头禅："听爸爸的没错"、"社会很现实的"
- 偶尔夸奖立马转折："嗯，还凑合，但是..."""
        else:
            personality_prompt = """你是一个典型的中国式老妈，说话特点：
- 经典开场："哎呀我的傻孩子..."、"妈跟你说啊..."
- 抽象担忧："这样下去可怎么办啊"、"妈妈都替你着急"
- 情感绑架："妈妈都是为了你好"、"你让妈妈怎么放心"
- 比较打击："你看人家xxx家孩子..."
- 唠叨哲学："细节决定成败"、"马虎要不得"
- 口头禅："妈妈不会害你的"、"听妈妈的准没错"
- 关怀焦虑："这样真的好吗？"、"会不会有问题？"""

        # 构建状态描述
        status_description = f"""
当前监控数据：
- 专注度：{int(focus_level * 100)}%
- 压力水平：{int(stress_level * 100)}%
- 情绪状态：{emotion}
- 任务完成率：{int(completion_rate * 100)}%
- 专注时间：{time_str}
- 专注度趋势：{focus_trend}
- 压力趋势：{stress_trend}
"""

        # 添加任务上下文描述
        task_description = ""
        if request.task_context:
            task_info = request.task_context
            goal_title = task_info.get('goal', {}).get('title', '未知目标')
            current_task = task_info.get('currentTask')
            completed_tasks = task_info.get('completedTasks', 0)
            total_tasks = task_info.get('totalTasks', 1)
            
            task_description = f"""
当前学习情况：
- 总目标：{goal_title}
- 当前任务：{current_task.get('title', '未开始') if current_task else '无任务'}
- 任务描述：{current_task.get('description', '无描述') if current_task else '无描述'}
- 进度：已完成{completed_tasks}/{total_tasks}个任务
"""

        # 如果有历史消息，加入上下文
        context_prompt = ""
        if recent_history.strip():
            context_prompt = f"\n最近的话：{recent_history}\n要注意前后呼应，不要重复说同样的话。"

        # 完整提示词
        full_prompt = f"""{personality_prompt}

你正在监督孩子的学习专注状态，需要根据实时数据和具体任务给出一句话的评价或建议。

{status_description}
{task_description}
{context_prompt}

要求：
1. 只返回一句话，不超过30个字
2. 要体现{parent_name}的典型说话风格
3. 根据数据情况给出合适的反应（表扬、催促、担心等）
4. 如果专注度低于40%要催促，高于80%要表扬但不能太夸张
5. 如果压力过高要表示担心，时间太短要催促继续
6. **重要：要结合具体的任务内容**，比如提到任务名称或学习内容
7. 要有真实的家长感觉，接地气

直接返回{parent_name}要说的话，不要任何解释："""

        # 调用LLM
        response = await call_gemini_api(full_prompt)
        
        # 清理响应，确保只有一句话
        message = response.strip()
        # 移除可能的引号
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]
        
        # 限制长度
        if len(message) > 40:
            message = message[:40] + "..."
        
        return {
            "message": message,
            "parent_type": request.parent_type,
            "context": {
                "focus_level": focus_level,
                "stress_level": stress_level,
                "emotion": emotion,
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        print(f"LLM生成消息失败: {e}")
        # 获取任务信息用于降级消息
        task_name = "学习"
        if request.task_context and request.task_context.get('currentTask'):
            task_name = request.task_context['currentTask'].get('title', '学习')
        
        # 降级到简单的模板消息，但包含任务内容
        fallback_messages = {
            'dad': [
                f"专注度{int(focus_level * 100)}%，{task_name}要认真点！听爸爸的没错。",
                f"做{task_name}已经{time_str}了，别松懈！",
                f"你说你这孩子，{task_name}专注度才{int(focus_level * 100)}%？"
            ],
            'mom': [
                f"孩子，做{task_name}专注度{int(focus_level * 100)}%，妈妈相信你！",
                f"{task_name}已经{time_str}了，很棒！要注意休息哦。",
                f"哎呀，{task_name}专注度{int(focus_level * 100)}%，妈妈都替你着急！"
            ]
        }
        
        import random
        fallback_message = random.choice(fallback_messages[request.parent_type])
        
        return {
            "message": fallback_message,
            "parent_type": request.parent_type,
            "context": {
                "focus_level": focus_level,
                "stress_level": stress_level,
                "emotion": emotion,
                "generated_at": datetime.now().isoformat(),
                "fallback": True
            }
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)