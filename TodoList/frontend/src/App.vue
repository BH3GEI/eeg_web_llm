<template>
  <div class="app">
    <header class="header">
      <h1>智能待办清单</h1>
      <p>AI驱动的任务分解与管理</p>
    </header>

    <main class="main">
      <!-- 对话模式切换 -->
      <div class="mode-switch">
        <button 
          @click="currentMode = 'chat'" 
          :class="{ active: currentMode === 'chat' }"
          class="mode-btn"
        >
          AI引导对话
        </button>
        <button 
          @click="currentMode = 'direct'" 
          :class="{ active: currentMode === 'direct' }"
          class="mode-btn"
        >
          直接分解
        </button>
      </div>

      <!-- 对话模式界面 -->
      <div v-if="currentMode === 'chat'" class="chat-container">
        <div class="chat-messages" ref="chatMessages">
          <div v-if="chatMessages.length === 0" class="welcome-message">
            <div class="ai-avatar"><i class="fas fa-robot"></i></div>
            <div class="message-content">
              <p>你好！我是你的AI助手</p>
              <p>我可以帮你把模糊的想法变成清晰的行动计划。你最近有什么想做的事情吗？哪怕只是一个大概的想法都可以。</p>
            </div>
          </div>
          
          <div 
            v-for="(message, index) in chatMessages" 
            :key="index"
            :class="['message', message.role]"
          >
            <div v-if="message.role === 'assistant'" class="ai-avatar"><i class="fas fa-robot"></i></div>
            <div class="message-content">
              <p>{{ message.content }}</p>
            </div>
            <div v-if="message.role === 'user'" class="user-avatar"><i class="fas fa-user"></i></div>
          </div>
          
          <div v-if="chatLoading" class="message assistant">
            <div class="ai-avatar"><i class="fas fa-robot"></i></div>
            <div class="message-content typing">
              <p>AI思考中...</p>
            </div>
          </div>
        </div>
        
        <div class="chat-input-area">
          <div class="chat-input-container">
            <textarea
              v-model="chatInput"
              placeholder="告诉我你的想法..."
              :disabled="chatLoading"
              @keydown="handleChatKeydown"
              class="chat-input"
              rows="2"
            ></textarea>
            <button 
              @click="sendChatMessage" 
              :disabled="!chatInput.trim() || chatLoading"
              class="send-btn"
            >
              <span v-if="chatLoading"><i class="fas fa-circle-notch fa-spin"></i></span>
              <span v-else><i class="fas fa-paper-plane"></i></span>
            </button>
          </div>
          
          <div v-if="canGenerateTasks" class="generate-tasks-hint">
            <p>目标已经明确！</p>
            <button @click="generateTasksFromChat" class="generate-tasks-btn">
              生成任务计划
            </button>
          </div>
          
          <!-- 手动生成按钮（当有对话历史时显示） -->
          <div v-else-if="chatMessages.length >= 4 && conversationId" class="manual-generate-hint">
            <p>觉得聊得差不多了？</p>
            <button @click="generateTasksFromChat" class="manual-generate-btn">
              直接生成任务计划
            </button>
          </div>
          
          <!-- 新建对话按钮 -->
          <div v-if="chatMessages.length > 0" class="new-chat-hint">
            <button @click="startNewConversation" class="new-chat-btn">
              开始新对话
            </button>
          </div>
        </div>
      </div>

      <!-- 直接输入模式界面 -->
      <div v-else class="goal-input">
        <div class="input-container">
          <textarea
            v-model="goalInput"
            placeholder="输入你的目标，AI会帮你分解成可执行的小任务..."
            :disabled="loading"
            @keydown="handleKeydown"
            rows="3"
          ></textarea>
          <button @click="breakdownGoal" :disabled="!goalInput.trim() || loading">
            <span v-if="loading"><i class="fas fa-circle-notch fa-spin"></i> AI思考中...</span>
            <span v-else><i class="fas fa-magic"></i> 智能分解</span>
          </button>
        </div>
      </div>

      <!-- 目标和任务列表 -->
      <div class="goals-container" v-if="goals.length > 0">
        <h2>我的目标</h2>
        
        <!-- 遍历每个大目标 -->
        <div v-for="goal in goals" :key="goal.id" class="goal-group">
          <!-- 大目标标题 -->
          <div class="goal-header" :class="{ completed: goal.completed }">
            <div class="goal-info">
              <h3>{{ goal.title }}</h3>
              <p v-if="goal.description">{{ goal.description }}</p>
              <div class="goal-progress">
                <span class="progress-text">
                  进度: {{ goal.tasks.filter(t => t.completed).length }}/{{ goal.tasks.length }}
                </span>
                <div class="mini-progress-bar">
                  <div 
                    class="mini-progress-fill" 
                    :style="{ width: `${goal.tasks.length > 0 ? (goal.tasks.filter(t => t.completed).length / goal.tasks.length * 100) : 0}%` }"
                  ></div>
                </div>
              </div>
            </div>
            <div class="goal-actions">
              <button class="focus-goal-btn" @click="startGoalFocusMode(goal)" title="进入专注模式">
                专注
              </button>
              <button class="delete-goal-btn" @click="deleteGoal(goal.id)"></button>
            </div>
          </div>
          
          <!-- 该目标下的小任务 -->
          <div class="tasks-list" v-if="goal.tasks && goal.tasks.length > 0">
            <div
              v-for="task in goal.tasks"
              :key="task.id"
              class="task-item"
              :class="{ completed: task.completed }"
            >
              <div class="task-checkbox">
                <input
                  type="checkbox"
                  :id="`task-${task.id}`"
                  v-model="task.completed"
                  @change="updateTask(task)"
                />
                <label :for="`task-${task.id}`"></label>
              </div>
              <div class="task-content">
                <h4>{{ task.title }}</h4>
                <p v-if="task.description">{{ task.description }}</p>
              </div>
              <div class="task-actions">
                <button class="delete-task-btn" @click="deleteTask(goal.id, task.id)"></button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 总体进度统计 -->
        <div class="progress-stats">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${completionRate}%` }"></div>
          </div>
          <p>总进度: {{ completedCount }}/{{ totalTaskCount }} ({{ completionRate }}%)</p>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <div class="empty-icon"></div>
        <h3>开始你的智能任务管理之旅</h3>
        <p>输入一个目标，让AI帮你制定详细的执行计划</p>
      </div>
    </main>

    <!-- 专注模式全屏界面 -->
    <div v-if="focusMode.active" class="focus-overlay">
      <div class="focus-container">
        <!-- 头部信息 -->
        <div class="focus-header">
          <button class="exit-focus-btn" @click="exitFocusMode">×</button>
          <h2>{{ focusMode.goal.title }}</h2>
          <div class="focus-timer">{{ formatTime(focusMode.elapsedTime) }}</div>
        </div>

        <!-- 控制按钮 -->
        <div class="focus-controls focus-controls-top">
          <button class="control-btn pause-btn" @click="pauseFocus">
            {{ focusMode.paused ? '继续' : '暂停' }}
          </button>
          <button class="control-btn complete-btn" @click="completeCurrentTask">
            完成当前任务
          </button>
          <button class="control-btn next-btn" @click="nextTask">
            下一个任务
          </button>
        </div>

        <!-- 实时生理监控 -->
        <div class="monitoring-section">
          <h3>实时生理监控</h3>
          <div class="data-quality-indicator">
            <span :class="['quality-dot', focusMode.dataQuality]"></span>
            <span class="quality-text">
              {{ focusMode.dataQuality === 'good' ? '真实EEG数据' : 
                 focusMode.dataQuality === 'simulated' ? '模拟数据' : '回退数据' }}
            </span>
          </div>
          
          <!-- EEG脑电波数据区 -->
          <div class="eeg-section">
            <h4 class="section-title">脑电波指标</h4>
            <div class="eeg-grid">
              <!-- 专注度 - 主要指标 -->
              <div class="trend-chart primary">
                <div class="chart-header">
                  <h4>专注度</h4>
                  <span class="current-value">{{ Math.round((focusMode.metrics.focus_level || 0) * 100) }}%</span>
                </div>
                <div class="mini-chart">
                  <div 
                    v-for="(value, index) in focusMode.trends.focus" 
                    :key="index"
                    class="chart-bar focus"
                    :style="{ height: `${Math.max(5, value * 100)}%` }"
                  ></div>
                </div>
              </div>

              <!-- 注意力 -->
              <div class="trend-chart">
                <div class="chart-header">
                  <h4>注意力</h4>
                  <span class="current-value">{{ Math.round((focusMode.metrics.attention || 0) * 100) }}%</span>
                </div>
                <div class="mini-chart">
                  <div 
                    v-for="(value, index) in focusMode.trends.attention" 
                    :key="index"
                    class="chart-bar attention"
                    :style="{ height: `${Math.max(5, value * 100)}%` }"
                  ></div>
                </div>
              </div>

              <!-- 参与度 -->
              <div class="trend-chart">
                <div class="chart-header">
                  <h4>参与度</h4>
                  <span class="current-value">{{ Math.round((focusMode.metrics.engagement || 0) * 100) }}%</span>
                </div>
                <div class="mini-chart">
                  <div 
                    v-for="(value, index) in focusMode.trends.engagement" 
                    :key="index"
                    class="chart-bar engagement"
                    :style="{ height: `${Math.max(5, value * 100)}%` }"
                  ></div>
                </div>
              </div>

              <!-- 兴奋度 -->
              <div class="trend-chart">
                <div class="chart-header">
                  <h4>兴奋度</h4>
                  <span class="current-value">{{ Math.round((focusMode.metrics.excitement || 0) * 100) }}%</span>
                </div>
                <div class="mini-chart">
                  <div 
                    v-for="(value, index) in focusMode.trends.excitement" 
                    :key="index"
                    class="chart-bar excitement"
                    :style="{ height: `${Math.max(5, value * 100)}%` }"
                  ></div>
                </div>
              </div>

              <!-- 兴趣度 -->
              <div class="trend-chart">
                <div class="chart-header">
                  <h4>兴趣度</h4>
                  <span class="current-value">{{ Math.round((focusMode.metrics.interest || 0) * 100) }}%</span>
                </div>
                <div class="mini-chart">
                  <div 
                    v-for="(value, index) in focusMode.trends.interest" 
                    :key="index"
                    class="chart-bar interest"
                    :style="{ height: `${Math.max(5, value * 100)}%` }"
                  ></div>
                </div>
              </div>

              <!-- 压力水平 -->
              <div class="trend-chart">
                <div class="chart-header">
                  <h4>压力水平</h4>
                  <span class="current-value">{{ Math.round((focusMode.metrics.stress_level || 0) * 100) }}%</span>
                </div>
                <div class="mini-chart">
                  <div 
                    v-for="(value, index) in focusMode.trends.stress" 
                    :key="index"
                    class="chart-bar stress"
                    :style="{ height: `${Math.max(5, value * 100)}%` }"
                  ></div>
                </div>
              </div>

              <!-- 放松度 -->
              <div class="trend-chart">
                <div class="chart-header">
                  <h4>放松度</h4>
                  <span class="current-value">{{ Math.round((focusMode.metrics.relaxation || 0) * 100) }}%</span>
                </div>
                <div class="mini-chart">
                  <div 
                    v-for="(value, index) in focusMode.trends.relaxation" 
                    :key="index"
                    class="chart-bar relaxation"
                    :style="{ height: `${Math.max(5, value * 100)}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 情绪识别数据区 -->
          <div class="emotion-section">
            <h4 class="section-title">情绪识别</h4>
            <div class="emotion-display">
              <div class="current-emotion">
                <span class="emotion-label">当前情绪</span>
                <span class="emotion-indicator" :class="focusMode.metrics.current_emotion">
                  {{ getEmotionText(focusMode.metrics.current_emotion) }}
                </span>
              </div>
              <div class="emotion-confidence">
                <span class="confidence-label">置信度</span>
                <div class="confidence-bar">
                  <div 
                    class="confidence-fill" 
                    :style="{ width: `${(focusMode.metrics.emotion_confidence || 0) * 100}%` }"
                  ></div>
                </div>
                <span class="confidence-text">
                  {{ Math.round((focusMode.metrics.emotion_confidence || 0) * 100) }}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 任务列表区域 -->
        <div class="focus-tasks-section">
          <div class="tasks-header">
            <h3>任务清单</h3>
            <!-- 环形进度图 -->
            <div class="task-ring-container">
              <svg class="task-ring" :style="{ transform: `rotate(${ringRotation}deg)` }">
                <g class="ring-segments">
                  <path
                    v-for="(task, index) in focusMode.goal.tasks"
                    :key="task.id"
                    :d="getSegmentPath(index, focusMode.goal.tasks.length)"
                    :class="[
                      'ring-segment',
                      { 
                        'completed': task.completed,
                        'current': focusMode.currentTask && focusMode.currentTask.id === task.id
                      }
                    ]"
                    :stroke-width="12"
                    fill="none"
                  />
                </g>
              </svg>
              <div class="ring-info">
                <span class="completed-count">{{ focusMode.goal.tasks.filter(t => t.completed).length }}</span>
                <span class="total-count">{{ focusMode.goal.tasks.length }}</span>
              </div>
            </div>
          </div>
          <div class="focus-tasks-list">
            <div 
              v-for="task in focusMode.goal.tasks" 
              :key="task.id"
              class="focus-task-item"
              :class="{ 
                completed: task.completed,
                current: focusMode.currentTask && focusMode.currentTask.id === task.id
              }"
              @click="setCurrentTask(task)"
            >
              <div class="focus-task-checkbox">
                <input
                  type="checkbox"
                  :id="`focus-task-${task.id}`"
                  v-model="task.completed"
                  @change="updateTaskInFocus(task)"
                />
                <label :for="`focus-task-${task.id}`"></label>
              </div>
              <div class="focus-task-content">
                <h4>{{ task.title }}</h4>
                <p v-if="task.description">{{ task.description }}</p>
              </div>
              <div class="focus-task-status">
                <span v-if="focusMode.currentTask && focusMode.currentTask.id === task.id" class="current-indicator">
                  正在进行
                </span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      currentMode: 'chat', // 'chat' 或 'direct'
      goalInput: '',
      goals: [], // 改为goals数组，包含层级结构
      loading: false,
      
      // 对话相关数据
      chatInput: '',
      chatMessages: [],
      chatLoading: false,
      sessionId: null,
      conversationId: null,
      canGenerateTasks: false,
      
      // 专注模式数据
      focusMode: {
        active: false,
        goal: null,
        currentTask: null,
        sessionId: null,
        startTime: null,
        elapsedTime: 0,
        paused: false,
        timer: null,
        dataUpdateTimer: null,
        metrics: {
          focus_level: 0,
          attention: 0,
          engagement: 0,
          excitement: 0,
          interest: 0,
          stress_level: 0,
          relaxation: 0,
          current_emotion: 'neutral',
          emotion_confidence: 0
        },
        trends: {
          focus: Array(10).fill(0.8),
          attention: Array(10).fill(0.75),
          engagement: Array(10).fill(0.7),
          excitement: Array(10).fill(0.6),
          interest: Array(10).fill(0.65),
          stress: Array(10).fill(0.3),
          relaxation: Array(10).fill(0.6)
        },
        dataQuality: 'simulated'
      }
    }
  },
  computed: {
    // 计算所有任务的完成情况
    allTasks() {
      return this.goals.flatMap(goal => goal.tasks || [])
    },
    completedCount() {
      return this.allTasks.filter(task => task.completed).length
    },
    totalTaskCount() {
      return this.allTasks.length
    },
    completionRate() {
      return this.totalTaskCount === 0 ? 0 : Math.round((this.completedCount / this.totalTaskCount) * 100)
    },
    // 环形图旋转角度
    ringRotation() {
      if (!this.focusMode.currentTask || !this.focusMode.goal.tasks.length) {
        return 0
      }
      const currentIndex = this.focusMode.goal.tasks.findIndex(
        task => task.id === this.focusMode.currentTask.id
      )
      // 计算旋转角度，让当前任务在顶部
      const segmentAngle = 360 / this.focusMode.goal.tasks.length
      return -90 - (currentIndex * segmentAngle)
    }
  },
  async mounted() {
    // 持久化会话ID - 不再每次刷新都丢失！
    this.sessionId = localStorage.getItem('smart_todo_session_id') || 
                     'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    localStorage.setItem('smart_todo_session_id', this.sessionId)
    
    await this.loadGoals()
    
    // 如果是对话模式，加载对话历史
    if (this.currentMode === 'chat') {
      await this.loadChatHistory()
    }
  },
  methods: {
    handleKeydown(event) {
      // Ctrl/Cmd + Enter 快速提交
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault()
        this.breakdownGoal()
      }
    },
    
    handleChatKeydown(event) {
      // Ctrl/Cmd + Enter 发送消息
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault()
        this.sendChatMessage()
      }
    },
    
    async loadChatHistory() {
      try {
        const response = await axios.get(`/api/conversations/${this.sessionId}`)
        const data = response.data
        
        if (data.messages && data.messages.length > 0) {
          // 过滤掉欢迎消息，只显示实际对话
          this.chatMessages = data.messages.filter(msg => 
            !(msg.role === 'assistant' && msg.content.includes('你好！我是你的AI助手'))
          )
          this.conversationId = data.conversation_id
          this.canGenerateTasks = data.can_generate_tasks
        }
      } catch (error) {
        console.error('加载对话历史失败:', error)
      }
    },
    
    async sendChatMessage() {
      if (!this.chatInput.trim()) return
      
      const userMessage = this.chatInput.trim()
      this.chatInput = ''
      this.chatLoading = true
      
      // 添加用户消息到界面
      this.chatMessages.push({
        role: 'user',
        content: userMessage
      })
      
      // 滚动到底部
      this.$nextTick(() => {
        this.scrollToBottom()
      })
      
      try {
        const response = await axios.post('/api/chat', {
          session_id: this.sessionId,
          message: userMessage
        })
        
        // 添加AI回复到界面
        this.chatMessages.push({
          role: 'assistant',
          content: response.data.message
        })
        
        this.conversationId = response.data.conversation_id
        this.canGenerateTasks = response.data.can_generate_tasks
        
        // 调试信息
        console.log('对话状态:', response.data.status, '可生成任务:', response.data.can_generate_tasks)
        
        // 滚动到底部
        this.$nextTick(() => {
          this.scrollToBottom()
        })
        
      } catch (error) {
        console.error('发送消息失败:', error)
        this.showNotification('发送失败，请重试', 'error')
      } finally {
        this.chatLoading = false
      }
    },
    
    async generateTasksFromChat() {
      if (!this.conversationId) return
      
      this.chatLoading = true
      try {
        const response = await axios.post(`/api/generate-tasks/${this.conversationId}`)
        
        // 添加新目标到列表
        this.goals.unshift(response.data.goal)
        
        // 显示成功提示并切换到任务视图
        this.showNotification('任务计划已生成！')
        this.canGenerateTasks = false
        
        // 可以选择切换到任务视图
        // this.currentMode = 'direct'
        
      } catch (error) {
        console.error('生成任务失败:', error)
        this.showNotification('生成失败，请重试', 'error')
      } finally {
        this.chatLoading = false
      }
    },
    
    scrollToBottom() {
      const chatMessages = this.$refs.chatMessages
      if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight
      }
    },
    
    startNewConversation() {
      // 清空当前对话
      this.chatMessages = []
      this.conversationId = null
      this.canGenerateTasks = false
      this.chatInput = ''
      
      // 生成新的会话ID（保持同一个session但开始新对话）
      const timestamp = Date.now()
      
      // 显示确认消息
      this.showNotification('已开始新对话，之前的记忆仍会保留')
      
      // 可选：调用后端创建新对话
      this.createNewConversation()
    },
    
    async createNewConversation() {
      try {
        // 可以调用后端API来标记新对话的开始
        await axios.post('/api/new-conversation', {
          session_id: this.sessionId
        })
      } catch (error) {
        console.error('创建新对话失败:', error)
      }
    },
    
    // 专注模式相关方法
    async startGoalFocusMode(goal) {
      try {
        // 找到第一个未完成的任务作为当前任务
        const firstIncompleteTask = goal.tasks.find(task => !task.completed)
        
        this.focusMode = {
          active: true,
          goal: goal,
          currentTask: firstIncompleteTask || goal.tasks[0],
          sessionId: null,
          startTime: Date.now(),
          elapsedTime: 0,
          paused: false,
          timer: null,
          dataUpdateTimer: null,
          metrics: {
            focus_level: 0,
            attention: 0,
            engagement: 0,
            stress_level: 0,
            relaxation: 0,
            current_emotion: 'neutral',
            emotion_confidence: 0
          },
          trends: {
            focus: Array(10).fill(0.8),
            attention: Array(10).fill(0.75),
            engagement: Array(10).fill(0.7),
            stress: Array(10).fill(0.3),
            relaxation: Array(10).fill(0.6)
          },
          dataQuality: 'simulated'
        }
        
        // 阻止背景滚动
        document.body.style.overflow = 'hidden'
        
        // 启动计时器
        this.startFocusTimers()
        
        // 开始获取模拟数据
        this.startDataUpdates()
        
        this.showNotification('专注模式已启动！')
        
        // 滚动到当前任务
        this.$nextTick(() => {
          setTimeout(() => {
            this.scrollToCurrentTask()
          }, 500) // 等待动画完成
        })
        
      } catch (error) {
        console.error('启动专注模式失败:', error)
        this.showNotification('启动失败，请重试', 'error')
      }
    },
    
    startFocusTimers() {
      // 计时器
      this.focusMode.timer = setInterval(() => {
        if (!this.focusMode.paused) {
          this.focusMode.elapsedTime = Math.floor((Date.now() - this.focusMode.startTime) / 1000)
        }
      }, 1000)
    },
    
    async startDataUpdates() {
      // 每2秒更新一次数据（更实时）
      this.focusMode.dataUpdateTimer = setInterval(async () => {
        if (!this.focusMode.paused) {
          await this.updateFocusData()
        }
      }, 2000)  // 从5000改为2000毫秒
      
      // 立即获取一次数据
      await this.updateFocusData()
    },
    
    async updateFocusData() {
      try {
        // 如果有当前任务，获取该任务的数据，否则使用目标ID
        const taskId = this.focusMode.currentTask ? this.focusMode.currentTask.id : this.focusMode.goal.id
        const response = await axios.get(`/api/focus/current/${taskId}`)
        const data = response.data.current_data
        const trends = response.data.trends
        
        // 更新当前指标
        this.focusMode.metrics = {
          focus_level: data.focus_level,
          attention: data.attention,
          engagement: data.engagement,
          excitement: data.excitement,
          interest: data.interest,
          stress_level: data.stress_level,
          relaxation: data.relaxation,
          current_emotion: data.current_emotion,
          emotion_confidence: data.emotion_confidence
        }
        
        // 更新数据质量标识
        this.focusMode.dataQuality = data.data_quality === 'good' ? 'good' : 
                                     data.data_quality === 'simulated' ? 'simulated' : 'fallback'
        
        // 更新趋势数据
        if (trends.focus) {
          this.focusMode.trends.focus = trends.focus.slice(-10)
        }
        if (trends.attention) {
          this.focusMode.trends.attention = trends.attention.slice(-10)
        }
        if (trends.engagement) {
          this.focusMode.trends.engagement = trends.engagement.slice(-10)
        }
        if (trends.excitement) {
          this.focusMode.trends.excitement = trends.excitement.slice(-10)
        }
        if (trends.interest) {
          this.focusMode.trends.interest = trends.interest.slice(-10)
        }
        if (trends.stress) {
          this.focusMode.trends.stress = trends.stress.slice(-10)
        }
        if (trends.relaxation) {
          this.focusMode.trends.relaxation = trends.relaxation.slice(-10)
        }
        
        console.log('Focus data updated:', {
          metrics: this.focusMode.metrics,
          dataQuality: this.focusMode.dataQuality,
          metadata: response.data.metadata
        })
        
      } catch (error) {
        console.error('更新专注数据失败:', error)
        // 如果获取失败，设置为回退状态
        this.focusMode.dataQuality = 'fallback'
      }
    },
    
    pauseFocus() {
      this.focusMode.paused = !this.focusMode.paused
      if (this.focusMode.paused) {
        this.showNotification('专注已暂停')
      } else {
        this.focusMode.startTime = Date.now() - (this.focusMode.elapsedTime * 1000)
        this.showNotification('继续专注')
      }
    },
    
    async completeCurrentTask() {
      if (!this.focusMode.currentTask) return
      
      try {
        // 标记当前任务为完成
        this.focusMode.currentTask.completed = true
        await this.updateTask(this.focusMode.currentTask)
        
        this.showNotification('任务完成！')
        
        // 自动切换到下一个未完成任务
        this.nextTask()
        
      } catch (error) {
        console.error('完成任务失败:', error)
        this.showNotification('操作失败，请重试', 'error')
      }
    },
    
    setCurrentTask(task) {
      if (!task.completed) {
        this.focusMode.currentTask = task
        this.showNotification(`切换到: ${task.title}`)
        // 滚动到当前任务
        this.$nextTick(() => {
          this.scrollToCurrentTask()
        })
      }
    },
    
    scrollToCurrentTask() {
      if (!this.focusMode.currentTask) return
      
      const currentTaskElement = document.querySelector(`.focus-task-item.current`)
      if (currentTaskElement) {
        currentTaskElement.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        })
      }
    },
    
    // 生成环形图片段路径
    getSegmentPath(index, total) {
      if (total === 0) return ''
      
      const centerX = 50
      const centerY = 50
      const radius = 35
      const segmentAngle = 360 / total
      const startAngle = index * segmentAngle
      const endAngle = (index + 1) * segmentAngle
      
      // 在段之间留一些间隙
      const gap = total > 1 ? 2 : 0
      const adjustedStartAngle = startAngle + gap / 2
      const adjustedEndAngle = endAngle - gap / 2
      
      // 转换为弧度
      const startRad = (adjustedStartAngle * Math.PI) / 180
      const endRad = (adjustedEndAngle * Math.PI) / 180
      
      // 计算起点和终点
      const x1 = centerX + radius * Math.cos(startRad)
      const y1 = centerY + radius * Math.sin(startRad)
      const x2 = centerX + radius * Math.cos(endRad)
      const y2 = centerY + radius * Math.sin(endRad)
      
      // 判断是否为大弧
      const largeArc = adjustedEndAngle - adjustedStartAngle > 180 ? 1 : 0
      
      return `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`
    },
    
    nextTask() {
      const tasks = this.focusMode.goal.tasks
      const currentIndex = tasks.findIndex(t => t.id === this.focusMode.currentTask?.id)
      
      // 找到下一个未完成的任务
      for (let i = currentIndex + 1; i < tasks.length; i++) {
        if (!tasks[i].completed) {
          this.focusMode.currentTask = tasks[i]
          this.showNotification(`切换到: ${tasks[i].title}`)
          this.$nextTick(() => {
            this.scrollToCurrentTask()
          })
          return
        }
      }
      
      // 如果没有找到，从头开始找
      for (let i = 0; i < currentIndex; i++) {
        if (!tasks[i].completed) {
          this.focusMode.currentTask = tasks[i]
          this.showNotification(`切换到: ${tasks[i].title}`)
          this.$nextTick(() => {
            this.scrollToCurrentTask()
          })
          return
        }
      }
      
      // 所有任务都完成了
      this.showNotification('所有任务都已完成！')
      this.focusMode.currentTask = null
    },
    
    async updateTaskInFocus(task) {
      try {
        await this.updateTask(task)
        if (task.completed) {
          this.showNotification('任务完成！')
          // 如果完成的是当前任务，自动切换到下一个
          if (this.focusMode.currentTask && this.focusMode.currentTask.id === task.id) {
            this.nextTask()
          } else {
            // 如果不是当前任务被完成，也滚动到当前任务保持焦点
            this.$nextTick(() => {
              this.scrollToCurrentTask()
            })
          }
        }
      } catch (error) {
        console.error('更新任务失败:', error)
        // 回滚状态
        task.completed = !task.completed
      }
    },
    
    exitFocusMode() {
      // 清理计时器
      if (this.focusMode.timer) {
        clearInterval(this.focusMode.timer)
      }
      if (this.focusMode.dataUpdateTimer) {
        clearInterval(this.focusMode.dataUpdateTimer)
      }
      
      // 恢复body滚动
      document.body.style.overflow = 'auto'
      
      // 重置专注模式
      this.focusMode = {
        active: false,
        goal: null,
        currentTask: null,
        sessionId: null,
        startTime: null,
        elapsedTime: 0,
        paused: false,
        timer: null,
        dataUpdateTimer: null,
        metrics: {
          focus_level: 0,
          attention: 0,
          engagement: 0,
          excitement: 0,
          interest: 0,
          stress_level: 0,
          relaxation: 0,
          current_emotion: 'neutral',
          emotion_confidence: 0
        },
        trends: {
          focus: Array(10).fill(0.8),
          attention: Array(10).fill(0.75),
          engagement: Array(10).fill(0.7),
          excitement: Array(10).fill(0.6),
          interest: Array(10).fill(0.65),
          stress: Array(10).fill(0.3),
          relaxation: Array(10).fill(0.6)
        },
        dataQuality: 'simulated'
      }
    },
    
    formatTime(seconds) {
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = seconds % 60
      return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
    },
    
    async breakdownGoal() {
      if (!this.goalInput.trim()) return
      
      this.loading = true
      try {
        const response = await axios.post('/api/breakdown', {
          goal: this.goalInput.trim()
        })
        
        // 添加新的目标到列表顶部
        this.goals.unshift(response.data.goal)
        this.goalInput = ''
        
        // 显示成功提示
        this.showNotification('任务分解完成！')
      } catch (error) {
        console.error('分解任务失败:', error)
        this.showNotification('分解失败，请重试', 'error')
      } finally {
        this.loading = false
      }
    },
    
    async loadGoals() {
      try {
        const response = await axios.get('/api/goals')
        this.goals = response.data
      } catch (error) {
        console.error('加载目标失败:', error)
      }
    },
    
    async updateTask(task) {
      try {
        await axios.put(`/api/tasks/${task.id}`, task)
        if (task.completed) {
          this.showNotification('任务完成！')
          // 重新加载数据以更新目标完成状态
          await this.loadGoals()
        }
      } catch (error) {
        console.error('更新任务失败:', error)
        // 回滚状态
        task.completed = !task.completed
      }
    },
    
    async deleteTask(goalId, taskId) {
      if (!confirm('确定要删除这个任务吗？')) return
      
      try {
        await axios.delete(`/api/tasks/${taskId}`)
        // 从前端数据中移除任务
        const goal = this.goals.find(g => g.id === goalId)
        if (goal) {
          goal.tasks = goal.tasks.filter(task => task.id !== taskId)
        }
        this.showNotification('任务已删除')
      } catch (error) {
        console.error('删除任务失败:', error)
        this.showNotification('删除失败，请重试', 'error')
      }
    },
    
    async deleteGoal(goalId) {
      if (!confirm('确定要删除这个目标及其所有任务吗？')) return
      
      try {
        await axios.delete(`/api/goals/${goalId}`)
        this.goals = this.goals.filter(goal => goal.id !== goalId)
        this.showNotification('目标已删除')
      } catch (error) {
        console.error('删除目标失败:', error)
        this.showNotification('删除失败，请重试', 'error')
      }
    },
    
    getEmotionText(emotion) {
      const emotionMap = {
        'happy': '愉悦',
        'sad': '悲伤',
        'angry': '愤怒',
        'fear': '恐惧',
        'surprise': '惊讶',
        'disgust': '厌恶',
        'neutral': '中性',
        'focused': '专注',
        'calm': '平静',
        'thinking': '思考',
        'relaxed': '放松',
        'excited': '兴奋'
      }
      return emotionMap[emotion] || emotion
    },

    showNotification(message, type = 'success') {
      // 移动端友好的通知实现
      const notification = document.createElement('div')
      notification.textContent = message
      notification.className = 'notification'
      
      const isMobile = window.innerWidth <= 768
      
      notification.style.cssText = `
        position: fixed;
        ${isMobile ? 'bottom: 20px; right: 15px; left: 15px;' : 'bottom: 30px; left: 50%; transform: translateX(-50%);'}
        padding: ${isMobile ? '14px 16px' : '12px 20px'};
        background: ${type === 'error' ? '#c2998a' : '#b5a496'};
        color: white;
        border-radius: ${isMobile ? '12px' : '10px'};
        z-index: 1000;
        font-size: ${isMobile ? '14px' : '16px'};
        font-weight: 500;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        animation: slideInFromBottom 0.3s ease-out;
        text-align: center;
        max-width: ${isMobile ? 'auto' : '400px'};
      `
      
      document.body.appendChild(notification)
      
      // 移动端更短的显示时间
      const duration = isMobile ? 2500 : 3000
      setTimeout(() => {
        notification.style.animation = 'slideOutToBottom 0.3s ease-out'
        setTimeout(() => {
          if (notification.parentNode) {
            notification.remove()
          }
        }, 300)
      }, duration)
    }
  }
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  padding: 30px 20px 40px;
}

.header {
  text-align: center;
  color: #6b5d4f;
  margin-bottom: 50px;
}

.header h1 {
  font-size: 2.5rem;
  margin-bottom: 15px;
  font-weight: 600;
  color: #6b5d4f;
}

.header p {
  font-size: 1.1rem;
  color: #7a6b5c;
  font-weight: 400;
}

.main {
  max-width: 800px;
  margin: 0 auto;
}

/* 模式切换按钮 */
.mode-switch {
  display: flex;
  gap: 10px;
  margin-bottom: 25px;
  justify-content: center;
}

.mode-btn {
  padding: 12px 20px;
  border: 2px solid #d4c4b0;
  border-radius: 12px;
  background: rgba(255, 253, 250, 0.8);
  color: #5a4a3a;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.mode-btn:hover {
  border-color: #a69080;
  background: rgba(255, 253, 250, 0.95);
}

.mode-btn.active {
  border-color: #a69080;
  background: linear-gradient(135deg, #b5a496, #a69080);
  color: #5a4a3a;
}

/* 对话容器 */
.chat-container {
  background: rgba(255, 253, 250, 0.9);
  border-radius: 20px;
  box-shadow: 0 8px 25px rgba(0,0,0,0.06);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 253, 250, 0.2);
  overflow: hidden;
  margin-bottom: 35px;
}

.chat-messages {
  max-height: 400px;
  overflow-y: auto;
  padding: 25px;
  padding-bottom: 15px;
}

/* 欢迎消息样式 */
.welcome-message {
  display: flex;
  gap: 15px;
  align-items: flex-start;
  margin-bottom: 20px;
}

.welcome-message .message-content {
  background: rgba(129, 199, 132, 0.1);
  border: 1px solid rgba(129, 199, 132, 0.2);
  border-radius: 15px;
  padding: 15px 18px;
}

/* 消息样式 */
.message {
  display: flex;
  gap: 12px;
  margin-bottom: 18px;
  align-items: flex-start;
}

.message.user {
  flex-direction: row-reverse;
}

.ai-avatar, .user-avatar {
  width: 35px;
  height: 35px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 2px;
}

.ai-avatar {
  background: linear-gradient(135deg, #b5a496, #a69080);
  color: #5a4a3a;
}

.user-avatar {
  background: linear-gradient(135deg, #968d7a, #8a8067);
  color: #5a4a3a;
}

.message-content {
  max-width: 70%;
  background: #f8fafb;
  border: 1px solid #e2e8f0;
  border-radius: 15px;
  padding: 12px 16px;
  word-wrap: break-word;
}

.message.user .message-content {
  background: linear-gradient(135deg, #968d7a, #8a8067);
  color: white;
  border-color: #968d7a;
}

.message.assistant .message-content {
  background: rgba(212, 184, 150, 0.08);
  border-color: rgba(212, 184, 150, 0.2);
}

.message-content p {
  margin: 0;
  line-height: 1.5;
  font-size: 14px;
}

.message-content p + p {
  margin-top: 8px;
}

/* 打字动画 */
.typing {
  opacity: 0.7;
}

/* 聊天输入区域 */
.chat-input-area {
  border-top: 1px solid #e2e8f0;
  padding: 20px 25px;
  background: rgba(248, 250, 252, 0.6);
}

.chat-input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 15px;
  font-size: 14px;
  resize: none;
  font-family: inherit;
  background: rgba(255, 253, 250, 0.8);
  transition: all 0.3s ease;
}

.chat-input:focus {
  outline: none;
  border-color: #a69080;
  background: rgba(255, 253, 250, 0.95);
  box-shadow: 0 0 0 3px rgba(196, 164, 132, 0.1);
}

.send-btn {
  width: 45px;
  height: 45px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #b5a496, #a69080);
  color: #5a4a3a;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(196, 164, 132, 0.3);
}

.send-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 生成任务提示 */
.generate-tasks-hint {
  margin-top: 15px;
  padding: 15px;
  background: rgba(212, 184, 150, 0.1);
  border: 1px solid rgba(212, 184, 150, 0.2);
  border-radius: 12px;
  text-align: center;
}

.generate-tasks-hint p {
  margin: 0 0 10px 0;
  color: #5a4a3a;
  font-weight: 500;
}

.generate-tasks-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #b5a496, #a69080);
  color: #5a4a3a;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.generate-tasks-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(196, 164, 132, 0.3);
}

/* 手动生成任务提示 */
.manual-generate-hint {
  margin-top: 15px;
  padding: 12px;
  background: rgba(100, 181, 246, 0.1);
  border: 1px solid rgba(100, 181, 246, 0.2);
  border-radius: 12px;
  text-align: center;
}

.manual-generate-hint p {
  margin: 0 0 8px 0;
  color: #4a5568;
  font-size: 13px;
}

.manual-generate-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #a4a086, #908972);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.manual-generate-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(100, 181, 246, 0.3);
}

/* 新建对话提示 */
.new-chat-hint {
  margin-top: 15px;
  padding: 12px;
  background: rgba(164, 160, 134, 0.08);
  border: 1px solid rgba(164, 160, 134, 0.2);
  border-radius: 12px;
  text-align: center;
}

.new-chat-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #a4a086, #908972);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.new-chat-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(164, 160, 134, 0.3);
}

.goal-input {
  background: rgba(255, 253, 250, 0.9);
  border-radius: 20px;
  padding: 35px;
  margin-bottom: 35px;
  box-shadow: 0 8px 25px rgba(0,0,0,0.06);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 253, 250, 0.2);
}

.input-container {
  display: flex;
  gap: 20px;
  align-items: flex-end;
}

.input-container textarea {
  flex: 1;
  min-height: 80px;
  padding: 18px;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  font-size: 16px;
  resize: vertical;
  font-family: inherit;
  transition: all 0.3s ease;
  background: rgba(255, 253, 250, 0.8);
  color: #4a5568;
}

.input-container textarea:focus {
  outline: none;
  border-color: #a4a086;
  background: rgba(255, 253, 250, 0.95);
  box-shadow: 0 0 0 3px rgba(129, 199, 132, 0.1);
}

.input-container button {
  padding: 18px 28px;
  background: linear-gradient(135deg, #a4a086, #908972);
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  box-shadow: 0 4px 15px rgba(129, 199, 132, 0.2);
}

.input-container button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(129, 199, 132, 0.25);
  background: linear-gradient(135deg, #b5ab92, #a4a086);
}

.input-container button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 3px 10px rgba(129, 199, 132, 0.2);
}

.input-container button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.goals-container {
  background: rgba(255, 253, 250, 0.9);
  border-radius: 20px;
  padding: 35px;
  box-shadow: 0 8px 25px rgba(0,0,0,0.06);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 253, 250, 0.2);
}

.goals-container h2 {
  margin-bottom: 30px;
  color: #2d3748;
  font-size: 1.5rem;
  font-weight: 600;
}

/* 目标组样式 */
.goal-group {
  margin-bottom: 35px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  overflow: hidden;
  background: rgba(248, 250, 252, 0.6);
}

.goal-group:last-child {
  margin-bottom: 0;
}

/* 大目标头部 */
.goal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 25px;
  background: rgba(129, 199, 132, 0.08);
  border-bottom: 1px solid rgba(129, 199, 132, 0.15);
  transition: all 0.3s ease;
}

.goal-header.completed {
  opacity: 0.7;
  background: rgba(129, 199, 132, 0.15);
}

.goal-info {
  flex: 1;
}

.goal-info h3 {
  font-size: 1.25rem;
  color: #2d3748;
  margin-bottom: 8px;
  font-weight: 600;
}

.goal-info p {
  color: #718096;
  font-size: 0.9rem;
  margin-bottom: 12px;
  line-height: 1.4;
}

.goal-progress {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-text {
  font-size: 0.85rem;
  color: #4a5568;
  font-weight: 500;
  white-space: nowrap;
}

.mini-progress-bar {
  flex: 1;
  height: 4px;
  background: rgba(226, 232, 240, 0.8);
  border-radius: 2px;
  overflow: hidden;
}

.mini-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #a4a086, #908972);
  transition: width 0.4s ease;
}

.delete-goal-btn {
  padding: 10px;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
  font-size: 16px;
  color: #a0aec0;
}

.delete-goal-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #e53e3e;
}

/* 任务列表容器 */
.tasks-list {
  padding: 0;
}

/* 单个任务项 */
.task-item {
  display: flex;
  align-items: flex-start;
  gap: 18px;
  padding: 18px 25px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  transition: all 0.3s ease;
  background: rgba(255, 253, 250, 0.4);
}

.task-item:last-child {
  border-bottom: none;
}

.task-item:hover {
  background: rgba(255, 253, 250, 0.7);
  transform: translateX(5px);
}

.task-item.completed {
  opacity: 0.6;
  transform: none;
}

.task-item.completed .task-content h4 {
  text-decoration: line-through;
}

.task-checkbox {
  position: relative;
  margin-top: 2px;
}

.task-checkbox input[type="checkbox"] {
  opacity: 0;
  position: absolute;
}

.task-checkbox label {
  display: block;
  width: 22px;
  height: 22px;
  border: 2px solid #cbd5e0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 253, 250, 0.9);
}

.task-checkbox input:checked + label {
  background: #a4a086;
  border-color: #a4a086;
}

.task-checkbox input:checked + label::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-weight: bold;
  font-size: 12px;
}

.task-content {
  flex: 1;
}

.task-content h4 {
  font-size: 1.05rem;
  color: #2d3748;
  margin-bottom: 6px;
  font-weight: 500;
  line-height: 1.3;
}

.task-content p {
  color: #718096;
  font-size: 0.85rem;
  line-height: 1.5;
}

.delete-task-btn {
  padding: 8px;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
  font-size: 14px;
  color: #a0aec0;
}

.delete-task-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #e53e3e;
}

/* 任务操作按钮 */
.task-actions {
  display: flex;
  gap: 8px;
}

.focus-btn {
  padding: 8px 12px;
  background: linear-gradient(135deg, #b5a496, #a69080);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.focus-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 152, 0, 0.3);
}

/* 目标操作按钮 */
.goal-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.focus-goal-btn {
  padding: 10px 16px;
  background: linear-gradient(135deg, #b5a496, #a69080);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 5px;
}

.focus-goal-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 152, 0, 0.3);
}


.progress-stats {
  margin-top: 35px;
  text-align: center;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #a4a086, #908972);
  transition: width 0.6s ease;
  border-radius: 4px;
}

.progress-stats p {
  color: #718096;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 70px 20px;
  color: #4a5568;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 25px;
  opacity: 0.7;
}

.empty-state h3 {
  font-size: 1.5rem;
  margin-bottom: 12px;
  color: #2d3748;
  font-weight: 600;
}

.empty-state p {
  font-size: 1.1rem;
  color: #718096;
  line-height: 1.4;
}

@keyframes slideIn {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes slideOut {
  from {
    transform: translateY(0);
    opacity: 1;
  }
  to {
    transform: translateY(-20px);
    opacity: 0;
  }
}

@keyframes slideInFromBottom {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes slideOutToBottom {
  from {
    transform: translateY(0);
    opacity: 1;
  }
  to {
    transform: translateY(20px);
    opacity: 0;
  }
}

/* 手机端专属优化 */
@media (max-width: 768px) {
  .app {
    padding: 10px;
    padding-bottom: 20px;
    -webkit-overflow-scrolling: touch; /* iOS滑动优化 */
  }
  
  /* 通用触摸优化 */
  * {
    -webkit-tap-highlight-color: transparent;
    -webkit-touch-callout: none;
    -webkit-user-select: none;
    user-select: none;
  }
  
  /* 允许文本选择 */
  .todo-content, textarea, input {
    -webkit-user-select: text;
    user-select: text;
  }
  
  .header {
    margin-bottom: 25px;
  }
  
  .header h1 {
    font-size: 1.8rem;
    margin-bottom: 5px;
  }
  
  .header p {
    font-size: 0.9rem;
  }
  
  .main {
    max-width: 100%;
  }
  
  /* 输入区域移动端优化 */
  .goal-input {
    padding: 25px;
    margin-bottom: 25px;
    border-radius: 16px;
  }
  
  .input-container {
    flex-direction: column;
    gap: 16px;
  }
  
  .input-container textarea {
    min-height: 100px;
    padding: 12px;
    font-size: 16px; /* 防止iOS缩放 */
    border-radius: 8px;
  }
  
  .input-container button {
    align-self: stretch;
    padding: 16px 20px;
    font-size: 16px;
    border-radius: 8px;
    min-height: 50px; /* 更大的触摸目标 */
    -webkit-tap-highlight-color: transparent; /* 移除默认触摸高亮 */
  }
  
  .input-container button:active:not(:disabled) {
    transform: scale(0.98);
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  }
  
  /* 目标列表移动端优化 */
  .goals-container {
    padding: 20px;
    border-radius: 16px;
  }
  
  .goals-container h2 {
    font-size: 1.3rem;
    margin-bottom: 20px;
  }
  
  .goal-group {
    margin-bottom: 25px;
    border-radius: 12px;
  }
  
  .goal-header {
    padding: 18px 20px;
  }
  
  .goal-info h3 {
    font-size: 1.1rem;
    margin-bottom: 6px;
  }
  
  .goal-info p {
    font-size: 0.85rem;
    margin-bottom: 10px;
  }
  
  .progress-text {
    font-size: 0.8rem;
  }
  
  .task-item {
    padding: 15px 20px;
    gap: 12px;
  }
  
  /* 提高触摸目标大小 */
  .task-checkbox label {
    width: 26px;
    height: 26px;
    margin-top: 1px;
  }
  
  .task-checkbox input:checked + label::after {
    font-size: 14px;
  }
  
  .task-content h4 {
    font-size: 0.95rem;
    line-height: 1.3;
    margin-bottom: 5px;
  }
  
  .task-content p {
    font-size: 0.8rem;
    line-height: 1.3;
  }
  
  .delete-task-btn,
  .delete-goal-btn {
    padding: 12px;
    font-size: 16px;
    min-width: 44px; /* 更大的触摸目标 */
    min-height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }
  
  .delete-task-btn:active,
  .delete-goal-btn:active {
    transform: scale(0.9);
    background: rgba(239, 68, 68, 0.15);
  }
  
  .task-item:active {
    transform: scale(0.99);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
  
  .goal-header:active {
    transform: scale(0.995);
  }
  
  /* 进度条移动端优化 */
  .progress-stats {
    margin-top: 20px;
  }
  
  .progress-bar {
    height: 6px;
    margin-bottom: 8px;
  }
  
  .progress-stats p {
    font-size: 0.9rem;
  }
  
  /* 空状态移动端优化 */
  .empty-state {
    padding: 40px 15px;
  }
  
  .empty-icon {
    font-size: 3rem;
    margin-bottom: 15px;
  }
  
  .empty-state h3 {
    font-size: 1.2rem;
    margin-bottom: 8px;
  }
  
  .empty-state p {
    font-size: 0.95rem;
    line-height: 1.4;
  }
  
  /* 通知移动端优化 */
  .notification {
    top: 10px !important;
    right: 10px !important;
    left: 10px !important;
    font-size: 14px !important;
  }
}

/* 小屏手机特别优化 */
@media (max-width: 480px) {
  .app {
    padding: 8px;
  }
  
  .header h1 {
    font-size: 1.6rem;
  }
  
  .goal-input {
    padding: 15px;
  }
  
  .input-container textarea {
    min-height: 90px;
    padding: 10px;
    font-size: 16px;
  }
  
  .input-container button {
    padding: 14px 16px;
    font-size: 15px;
  }
  
  .todos-container {
    padding: 12px;
  }
  
  .todo-item {
    padding: 12px;
    gap: 10px;
  }
  
  .todo-content h3 {
    font-size: 0.95rem;
  }
  
  .todo-content p {
    font-size: 0.8rem;
  }
}

/* 横屏手机优化 */
@media (max-width: 768px) and (orientation: landscape) {
  .header {
    margin-bottom: 15px;
  }
  
  .header h1 {
    font-size: 1.5rem;
  }
  
  .header p {
    font-size: 0.85rem;
  }
  
  .goal-input {
    margin-bottom: 15px;
  }
  
  .input-container textarea {
    min-height: 70px;
  }
  
  .empty-state {
    padding: 30px 15px;
  }
  
  .empty-icon {
    font-size: 2.5rem;
  }
}

/* 专注模式全屏界面样式 */
.focus-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #f7f5f3 0%, #ede8e0 50%, #e8e2da 100%);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.5s ease-out;
  overflow: hidden;
}

.focus-container {
  width: 100%;
  max-width: 1200px;
  height: 100vh;
  padding: 40px;
  display: flex;
  flex-direction: column;
  color: #6b5d4f;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
}

/* 专注模式头部 */
.focus-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 40px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(107, 93, 79, 0.1);
}

.exit-focus-btn {
  background: rgba(255, 253, 250, 0.9);
  color: #6b5d4f;
  border: 1px solid rgba(164, 160, 134, 0.3);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 24px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.exit-focus-btn:hover {
  background: rgba(164, 160, 134, 0.1);
  transform: scale(1.1);
  box-shadow: 0 4px 15px rgba(0,0,0,0.15);
}

.focus-header h2 {
  flex: 1;
  text-align: center;
  font-size: 2rem;
  margin: 0;
  color: #6b5d4f;
  font-weight: 600;
}

.focus-timer {
  font-size: 2.5rem;
  font-weight: 700;
  color: #a4a086;
  text-shadow: 0 2px 10px rgba(164, 160, 134, 0.3);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}


/* 生理监控区域 */
.monitoring-section {
  margin-bottom: 30px;
}

.monitoring-section h3 {
  color: #6b5d4f;
  font-size: 1.5rem;
  margin-bottom: 20px;
  text-align: center;
  font-weight: 600;
}

/* 数据质量指示器 */
.data-quality-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 25px;
  padding: 8px 16px;
  background: rgba(255, 253, 250, 0.9);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(164, 160, 134, 0.2);
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.quality-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.quality-dot.good {
  background: #a4a086;
  box-shadow: 0 0 8px rgba(164, 160, 134, 0.6);
}

.quality-dot.simulated {
  background: #c2b19f;
  box-shadow: 0 0 8px rgba(194, 177, 159, 0.6);
}

.quality-dot.fallback {
  background: #d4c4b0;
  box-shadow: 0 0 8px rgba(212, 196, 176, 0.6);
}

.quality-text {
  color: #6b5d4f;
  font-size: 0.9rem;
  font-weight: 500;
}

/* EEG脑电波区域 */
.eeg-section {
  margin-bottom: 25px;
}

.section-title {
  color: #6b5d4f;
  font-size: 1.1rem;
  margin-bottom: 15px;
  padding-left: 10px;
  border-left: 3px solid rgba(164, 160, 134, 0.5);
  font-weight: 500;
}

.eeg-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.trend-chart {
  background: rgba(255, 253, 250, 0.9);
  border-radius: 15px;
  padding: 15px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(164, 160, 134, 0.2);
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.trend-chart:hover {
  background: rgba(255, 253, 250, 0.95);
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

/* 主要图表强调样式 */
.trend-chart.primary {
  border: 2px solid rgba(164, 160, 134, 0.3);
  background: rgba(164, 160, 134, 0.05);
}

.trend-chart.primary:hover {
  border-color: rgba(164, 160, 134, 0.5);
  background: rgba(164, 160, 134, 0.1);
  box-shadow: 0 4px 20px rgba(164, 160, 134, 0.2);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.chart-header h4 {
  color: #6b5d4f;
  font-size: 0.9rem;
  margin: 0;
  font-weight: 500;
}

.current-value {
  color: #a4a086;
  font-size: 0.9rem;
  font-weight: 700;
}

.mini-chart {
  display: flex;
  align-items: end;
  height: 50px;
  gap: 2px;
  justify-content: space-between;
  padding: 0 2px;
}

.chart-bar {
  flex: 1;
  border-radius: 2px;
  min-height: 3px;
  transition: height 0.4s ease;
  position: relative;
}

.chart-bar.focus {
  background: linear-gradient(to top, #4ecdc4, #44a08d);
  box-shadow: 0 0 6px rgba(78, 205, 196, 0.4);
}

.chart-bar.attention {
  background: linear-gradient(to top, #667eea, #764ba2);
  box-shadow: 0 0 6px rgba(102, 126, 234, 0.4);
}

.chart-bar.engagement {
  background: linear-gradient(to top, #f093fb, #f5576c);
  box-shadow: 0 0 6px rgba(240, 147, 251, 0.4);
}

.chart-bar.excitement {
  background: linear-gradient(to top, #ff9a56, #ffd84d);
  box-shadow: 0 0 6px rgba(255, 154, 86, 0.4);
}

.chart-bar.interest {
  background: linear-gradient(to top, #a8e6cf, #88d8a3);
  box-shadow: 0 0 6px rgba(168, 230, 207, 0.4);
}

.chart-bar.stress {
  background: linear-gradient(to top, #ffa726, #ffcc02);
  box-shadow: 0 0 6px rgba(255, 167, 38, 0.4);
}

.chart-bar.relaxation {
  background: linear-gradient(to top, #a8edea, #fed6e3);
  box-shadow: 0 0 6px rgba(168, 237, 234, 0.4);
}

/* 情绪识别区域 */
.emotion-section {
  background: rgba(255, 253, 250, 0.8);
  border-radius: 15px;
  padding: 20px;
  border: 1px solid rgba(164, 160, 134, 0.2);
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.emotion-display {
  display: flex;
  align-items: center;
  gap: 25px;
  justify-content: space-between;
}

.current-emotion {
  display: flex;
  align-items: center;
  gap: 12px;
}

.emotion-label {
  color: #6b5d4f;
  font-size: 0.9rem;
  font-weight: 500;
}

.emotion-indicator {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  text-shadow: none;
  transition: all 0.3s ease;
}

.emotion-indicator.happy {
  background: linear-gradient(135deg, #d4c4b0, #c2b19f);
  color: #6b5d4f;
}

.emotion-indicator.sad {
  background: linear-gradient(135deg, #a4a086, #908972);
  color: white;
}

.emotion-indicator.angry {
  background: linear-gradient(135deg, #c2a398, #b59688);
  color: white;
}

.emotion-indicator.fear {
  background: linear-gradient(135deg, #b5a496, #a69080);
  color: white;
}

.emotion-indicator.surprise {
  background: linear-gradient(135deg, #d4c4b0, #c2b19f);
  color: #6b5d4f;
}

.emotion-indicator.disgust {
  background: linear-gradient(135deg, #a4a086, #908972);
  color: white;
}

.emotion-indicator.neutral,
.emotion-indicator.calm,
.emotion-indicator.focused,
.emotion-indicator.thinking {
  background: linear-gradient(135deg, #a4a086, #908972);
  color: white;
}

.emotion-confidence {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  max-width: 200px;
}

.confidence-label {
  color: #6b5d4f;
  font-size: 0.85rem;
  font-weight: 500;
  white-space: nowrap;
}

.confidence-bar {
  flex: 1;
  height: 8px;
  background: rgba(164, 160, 134, 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, #a4a086, #908972);
  border-radius: 4px;
  transition: width 0.4s ease;
}

.confidence-text {
  color: #6b5d4f;
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
}

/* 专注模式任务列表区域 */
.focus-tasks-section {
  margin-bottom: 30px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.tasks-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.focus-tasks-section h3 {
  color: #6b5d4f;
  font-size: 1.3rem;
  margin: 0;
  font-weight: 600;
}

/* 环形进度图 */
.task-ring-container {
  position: relative;
  width: 100px;
  height: 100px;
}

.task-ring {
  width: 100px;
  height: 100px;
  transition: transform 0.6s ease;
}

.ring-segment {
  stroke: rgba(164, 160, 134, 0.2);
  stroke-linecap: round;
  transition: all 0.3s ease;
}

.ring-segment.completed {
  stroke: #a4a086;
  filter: drop-shadow(0 0 8px rgba(164, 160, 134, 0.6));
}

.ring-segment.current {
  stroke: #6b5d4f;
  stroke-width: 16;
  filter: drop-shadow(0 0 12px rgba(107, 93, 79, 0.8));
  animation: pulse-ring 2s infinite;
}

.ring-segment.current.completed {
  stroke: #a4a086;
  filter: drop-shadow(0 0 12px rgba(164, 160, 134, 0.8));
}

.ring-info {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: none;
}

.completed-count {
  color: #6b5d4f;
  font-size: 1.2rem;
  font-weight: 700;
}

.total-count {
  color: rgba(107, 93, 79, 0.6);
  font-size: 0.8rem;
}

.total-count::before {
  content: '/';
  margin-right: 2px;
}

/* 环形图动画 */
@keyframes pulse-ring {
  0%, 100% {
    stroke-width: 16;
    opacity: 1;
  }
  50% {
    stroke-width: 18;
    opacity: 0.8;
  }
}

.focus-tasks-list {
  display: grid;
  gap: 15px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0 10px;
  min-height: 250px;
  max-height: 350px;
}

/* 滚动条样式 */
.focus-tasks-list::-webkit-scrollbar {
  width: 6px;
}

.focus-tasks-list::-webkit-scrollbar-track {
  background: rgba(164, 160, 134, 0.1);
  border-radius: 3px;
}

.focus-tasks-list::-webkit-scrollbar-thumb {
  background: rgba(164, 160, 134, 0.5);
  border-radius: 3px;
}

.focus-tasks-list::-webkit-scrollbar-thumb:hover {
  background: rgba(164, 160, 134, 0.7);
}

.focus-task-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px 20px;
  background: rgba(255, 253, 250, 0.9);
  border-radius: 15px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.focus-task-item:hover {
  background: rgba(255, 253, 250, 0.95);
  transform: translateX(5px);
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.focus-task-item.current {
  border-color: #a4a086;
  background: rgba(164, 160, 134, 0.1);
  box-shadow: 0 0 20px rgba(164, 160, 134, 0.3);
}

.focus-task-item.completed {
  opacity: 0.6;
  background: rgba(255, 253, 250, 0.7);
}

.focus-task-item.completed .focus-task-content h4 {
  text-decoration: line-through;
}

.focus-task-checkbox {
  position: relative;
}

.focus-task-checkbox input[type="checkbox"] {
  opacity: 0;
  position: absolute;
}

.focus-task-checkbox label {
  display: block;
  width: 24px;
  height: 24px;
  border: 2px solid rgba(164, 160, 134, 0.5);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 253, 250, 0.9);
}

.focus-task-checkbox input:checked + label {
  background: #a4a086;
  border-color: #a4a086;
}

.focus-task-checkbox input:checked + label::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-weight: bold;
  font-size: 14px;
}

.focus-task-content {
  flex: 1;
}

.focus-task-content h4 {
  color: #6b5d4f;
  font-size: 1.1rem;
  margin-bottom: 5px;
  font-weight: 500;
}

.focus-task-content p {
  color: rgba(107, 93, 79, 0.7);
  font-size: 0.9rem;
  line-height: 1.4;
}

.focus-task-status {
  font-size: 0.8rem;
}

.current-indicator {
  background: linear-gradient(135deg, #a4a086, #908972);
  color: white;
  padding: 4px 12px;
  border-radius: 15px;
  font-weight: 500;
  animation: pulse 2s infinite;
}

/* 控制按钮 */
.focus-controls {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.focus-controls-top {
  margin-bottom: 30px;
}

.control-btn {
  padding: 15px 35px;
  font-size: 1.1rem;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  border: 2px solid rgba(164, 160, 134, 0.2);
  color: #6b5d4f;
  background: rgba(255, 253, 250, 0.9);
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.pause-btn {
  background: linear-gradient(135deg, #d4c4b0, #c2b19f);
  color: #6b5d4f;
  border-color: rgba(212, 196, 176, 0.3);
}

.pause-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(212, 196, 176, 0.4);
}

.complete-btn {
  background: linear-gradient(135deg, #a4a086, #908972);
  color: white;
  border-color: rgba(164, 160, 134, 0.3);
}

.complete-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(164, 160, 134, 0.4);
}

.next-btn {
  background: linear-gradient(135deg, #b5a496, #a69080);
  color: white;
  border-color: rgba(181, 164, 150, 0.3);
}

.next-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(181, 164, 150, 0.4);
}

/* 专注模式动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

/* 专注模式移动端优化 */
@media (max-width: 768px) {
  .focus-container {
    padding: 20px;
  }
  
  .focus-header {
    margin-bottom: 30px;
    padding-bottom: 15px;
  }
  
  .focus-header h2 {
    font-size: 1.5rem;
  }
  
  .focus-timer {
    font-size: 2rem;
  }
  
  .trends-section h3 {
    font-size: 1.3rem;
    margin-bottom: 20px;
  }
  
  .trends-grid {
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 15px;
  }
  
  .trend-chart {
    padding: 15px;
  }
  
  .chart-header h4 {
    font-size: 0.9rem;
  }
  
  .current-value {
    font-size: 0.9rem;
  }
  
  .mini-chart {
    height: 50px;
    gap: 2px;
  }
  
  .tasks-header {
    flex-direction: column;
    gap: 15px;
    align-items: center;
  }
  
  .focus-tasks-section h3 {
    font-size: 1.1rem;
    margin: 0;
  }
  
  .task-ring-container {
    width: 80px;
    height: 80px;
  }
  
  .task-ring {
    width: 80px;
    height: 80px;
  }
  
  .completed-count {
    font-size: 1rem;
  }
  
  .total-count {
    font-size: 0.7rem;
  }
  
  .focus-tasks-list {
    min-height: 180px;
    gap: 10px;
  }
  
  .focus-task-item {
    padding: 12px 15px;
    gap: 12px;
  }
  
  .focus-task-content h4 {
    font-size: 1rem;
  }
  
  .focus-task-content p {
    font-size: 0.85rem;
  }
  
  .focus-controls {
    flex-direction: column;
    gap: 12px;
    align-items: center;
  }
  
  .focus-controls-top {
    margin-bottom: 20px;
  }
  
  .control-btn {
    padding: 12px 25px;
    font-size: 0.95rem;
    width: 100%;
    max-width: 280px;
  }
}
</style>