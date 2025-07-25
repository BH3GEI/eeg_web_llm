from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import sqlite3
import json
import requests
import os
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
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI API调用失败: {str(e)}")

# 构建对话引导的AI提示词
def build_coaching_prompt(messages: List[dict], conversation_status: str) -> str:
    conversation_history = "\n".join([
        f"{'用户' if msg['role'] == 'user' else 'AI助手'}: {msg['content']}" 
        for msg in messages[-6:]  # 只取最近6轮对话
    ])
    
    base_prompt = f"""你是一个温和、耐心的AI任务规划助手，专门帮助用户明确和细化他们的目标。

你的核心职责：
1. 通过提问引导用户深入思考
2. 帮助用户明确模糊的想法
3. 让用户意识到重要的细节
4. 营造轻松、无压力的对话氛围

对话原则：
- 一次只问1-2个问题，不要让用户感到压力
- 用温和、好奇的语气，像朋友聊天一样
- 关注用户的真实动机和约束条件
- 如果用户说不知道，给出几个选项让他们选择
- 适当使用emoji让对话更轻松

当前对话状态：{conversation_status}
- exploring: 初步了解用户想法，挖掘真实需求
- clarifying: 细化具体细节，明确约束条件  
- ready: 目标足够清晰，可以生成任务计划

对话历史：
{conversation_history}

请根据用户的最新消息，以温和引导的方式回复："""

    if conversation_status == "exploring":
        return base_prompt + """
重点挖掘：
- 用户的真实动机（为什么想做这件事？）
- 大致的时间范围和投入程度
- 是否有相关经验或基础
"""
    elif conversation_status == "clarifying":
        return base_prompt + """
重点明确：
- 具体的成功标准是什么？
- 有哪些现实约束（时间、预算、技能）？
- 优先级如何排序？
"""
    else:
        return base_prompt + """
如果信息足够清晰，请明确表示准备好生成任务计划，例如：
"太好了！我们已经把目标理清楚了，现在我准备好为你制定一个具体的行动计划。"
或者："信息很完整了！我现在可以生成任务计划了"

如果还需要澄清关键信息，继续温和地提问。
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
            
            # 添加欢迎消息
            cursor.execute(
                "INSERT INTO messages (conversation_id, role, content, message_type) VALUES (?, 'assistant', ?, 'chat')",
                (conversation_id, "你好！我是你的AI助手，我可以帮你把模糊的想法变成清晰的行动计划。你最近有什么想做的事情吗？哪怕只是一个大概的想法都可以~")
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
        
        # 生成AI回复
        prompt = build_coaching_prompt(recent_messages, conversation_status)
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
    """获取当前任务的专注数据（模拟数据）"""
    import random
    import time
    
    # 模拟实时数据
    current_time = int(time.time())
    
    return {
        "task_id": task_id,
        "current_data": {
            "heart_rate": random.randint(70, 90),
            "stress_level": round(random.uniform(0.2, 0.8), 2),
            "emotion_state": random.choice(["平静", "愉悦", "思考", "中性", "紧张"]),
            "focus_level": round(random.uniform(0.6, 0.95), 2),
            "session_duration": random.randint(5, 45),  # 分钟
            "interruptions": random.randint(0, 3)
        },
        "trends": {
            "heart_rate_trend": [random.randint(70, 90) for _ in range(10)],
            "focus_trend": [round(random.uniform(0.6, 0.95), 2) for _ in range(10)]
        },
        "timestamp": current_time
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)