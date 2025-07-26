<template>
  <div class="app">
    <!-- 使用组件化的头部 -->
    <Header />

    <main class="main">
      <!-- 使用组件化的模式切换 -->
      <ModeSwitch 
        :currentMode="currentMode" 
        @update:mode="currentMode = $event"
      />

      <!-- 使用组件化的聊天界面 -->
      <ChatContainer
        v-if="currentMode === 'chat'"
        :selectedParent="chat.selectedParent.value"
        :messages="chat.chatMessages.value"
        :loading="chat.chatLoading.value"
        :canGenerateTasks="chat.canGenerateTasks.value"
        :conversationId="chat.conversationId.value"
        @update:selectedParent="chat.selectedParent.value = $event"
        @send-message="handleSendMessage"
        @generate-tasks="handleGenerateTasks"
        @new-conversation="chat.startNewConversation"
      />

      <!-- 使用组件化的直接输入模式 -->
      <DirectInput
        v-else
        :loading="tasks.loading.value"
        @breakdown-goal="handleBreakdownGoal"
      />

      <!-- 使用组件化的目标和任务列表 -->
      <div class="goals-container" v-if="tasks.goals.value.length > 0">
        <h2>我的目标</h2>
        
        <GoalGroup
          v-for="goal in tasks.goals.value"
          :key="goal.id"
          :goal="goal"
          @update-task="handleUpdateTask"
          @delete-task="handleDeleteTask"
          @delete-goal="handleDeleteGoal"
          @start-focus="handleStartFocus"
        />
        
        <!-- 总体进度统计 -->
        <div class="progress-stats">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${tasks.completionRate.value}%` }"></div>
          </div>
          <p>总进度: {{ tasks.completedCount.value }}/{{ tasks.totalTaskCount.value }} ({{ tasks.completionRate.value }}%)</p>
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
    <FocusMode
      v-if="focusMode.active"
      :goal="focusMode.goal"
      @exit-focus="exitFocusMode"
      @update-task="handleUpdateTask"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Header from './components/common/Header.vue'
import ModeSwitch from './components/common/ModeSwitch.vue'
import DirectInput from './components/common/DirectInput.vue'
import ChatContainer from './components/chat/ChatContainer.vue'
import GoalGroup from './components/tasks/GoalGroup.vue'
import FocusMode from './components/focus/FocusMode.vue'

// 使用 composables
import { useChat } from './composables/useChat.js'
import { useTasks } from './composables/useTasks.js'
import { useNotification } from './composables/useNotification.js'

// 初始化数据和方法
const chat = useChat()
const tasks = useTasks()
const { showNotification } = useNotification()

// 应用状态
const currentMode = ref('chat')
const focusMode = ref({
  active: false,
  goal: null
})

// 聊天相关方法
const handleSendMessage = async (message) => {
  try {
    await chat.sendMessage(message)
    // 自动滚动在ChatContainer内部处理
  } catch (error) {
    showNotification('发送失败，请重试', 'error')
  }
}

const handleGenerateTasks = async () => {
  try {
    const goal = await chat.generateTasks()
    if (goal) {
      tasks.addGoalFromChat(goal)
      showNotification('任务计划已生成！')
    }
  } catch (error) {
    showNotification('生成失败，请重试', 'error')
  }
}

// 任务相关方法
const handleBreakdownGoal = async (goalText) => {
  try {
    await tasks.breakdownGoal(goalText)
    showNotification('任务分解完成！')
  } catch (error) {
    showNotification('分解失败，请重试', 'error')
  }
}

const handleUpdateTask = async (task) => {
  try {
    await tasks.updateTask(task)
  } catch (error) {
    showNotification('更新失败，请重试', 'error')
  }
}

const handleDeleteTask = async (goalId, taskId) => {
  if (!confirm('确定要删除这个任务吗？')) return
  
  try {
    await tasks.deleteTask(goalId, taskId)
    showNotification('任务已删除')
  } catch (error) {
    showNotification('删除失败，请重试', 'error')
  }
}

const handleDeleteGoal = async (goalId) => {
  if (!confirm('确定要删除这个目标及其所有任务吗？')) return
  
  try {
    await tasks.deleteGoal(goalId)
    showNotification('目标已删除')
  } catch (error) {
    showNotification('删除失败，请重试', 'error')
  }
}

// 专注模式相关方法
const handleStartFocus = (goal) => {
  focusMode.value = {
    active: true,
    goal: goal
  }
  showNotification('专注模式已启动！')
}

const exitFocusMode = () => {
  focusMode.value = {
    active: false,
    goal: null
  }
  showNotification('专注模式已退出')
}

// 初始化
onMounted(async () => {
  // 初始化会话
  chat.initSession()
  
  // 加载数据
  await tasks.loadGoals()
  
  // 如果是聊天模式，加载对话历史
  if (currentMode.value === 'chat') {
    await chat.loadChatHistory()
  }
})
</script>

<style>
/* 导入全局CSS变量和基础样式 */
@import './styles/variables.scss';

/* 应用基础样式 */
.app {
  min-height: 100vh;
  padding: 30px 20px 40px;
  background: var(--cyber-bg-primary);
  color: var(--cyber-text-primary);
  position: relative;
  overflow-x: hidden;
}

/* 动态背景网格效果 */
.app::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(var(--cyber-neon-cyan) 1px, transparent 1px),
    linear-gradient(90deg, var(--cyber-neon-cyan) 1px, transparent 1px);
  background-size: 60px 60px;
  opacity: 0.1;
  pointer-events: none;
  z-index: -1;
  animation: grid-flow 4s ease-in-out infinite;
}

/* 额外的粒子效果 */
.app::after {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 20% 80%, var(--cyber-neon-purple) 0%, transparent 50%),
              radial-gradient(circle at 80% 20%, var(--cyber-neon-cyan) 0%, transparent 50%);
  opacity: 0.05;
  pointer-events: none;
  z-index: -1;
}

.main {
  max-width: 900px;
  margin: 0 auto;
}

/* 目标容器 */
.goals-container {
  background: var(--cyber-glass);
  border-radius: 25px;
  padding: 40px;
  box-shadow: var(--cyber-shadow-neon);
  backdrop-filter: blur(25px);
  border: 1px solid var(--cyber-glass-border);
  position: relative;
}

.goals-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(0, 212, 255, 0.03) 0%, 
    rgba(176, 38, 255, 0.03) 100%);
  border-radius: 25px;
  pointer-events: none;
}

.goals-container h2 {
  margin-bottom: 35px;
  color: var(--cyber-text-primary);
  font-size: 1.8rem;
  font-weight: 700;
  position: relative;
  z-index: 1;
  text-shadow: 0 0 15px var(--cyber-neon-blue);
}

/* 进度统计 */
.progress-stats {
  margin-top: 40px;
  text-align: center;
  position: relative;
  z-index: 1;
}

.progress-bar {
  width: 100%;
  height: 10px;
  background: rgba(0, 212, 255, 0.2);
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 15px;
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.2);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--cyber-neon-blue), var(--cyber-neon-purple), var(--cyber-neon-green));
  transition: width 0.6s ease;
  border-radius: 5px;
  box-shadow: 0 0 15px var(--cyber-neon-blue);
}

.progress-stats p {
  color: var(--cyber-text-primary);
  font-weight: 600;
  font-size: 1.1rem;
  text-shadow: 0 0 10px var(--cyber-neon-blue);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 30px;
  color: var(--cyber-text-secondary);
  position: relative;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 30px;
  opacity: 0.7;
  animation: cyber-pulse 2s ease-in-out infinite;
}

.empty-state h3 {
  font-size: 1.8rem;
  margin-bottom: 15px;
  color: var(--cyber-text-primary);
  font-weight: 700;
  text-shadow: 0 0 15px var(--cyber-neon-blue);
}

.empty-state p {
  font-size: 1.2rem;
  color: var(--cyber-text-secondary);
  line-height: 1.5;
  max-width: 500px;
  margin: 0 auto;
}

/* 动画 */
@keyframes grid-flow {
  0% { opacity: 0.1; }
  50% { opacity: 0.3; }
  100% { opacity: 0.1; }
}

@keyframes cyber-pulse {
  0%, 100% { 
    transform: scale(1);
    opacity: 0.7;
  }
  50% { 
    transform: scale(1.05);
    opacity: 1;
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .app {
    padding: 10px;
    padding-bottom: 20px;
  }
  
  .main {
    max-width: 100%;
  }
  
  .goals-container {
    padding: 20px;
    border-radius: 16px;
  }
  
  .goals-container h2 {
    font-size: 1.3rem;
    margin-bottom: 20px;
  }
  
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
}
</style>