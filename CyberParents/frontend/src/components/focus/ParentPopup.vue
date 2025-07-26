<template>
  <div v-if="isVisible" class="parent-notification" :class="{ 'fade-out': isFadingOut }">
    <div class="notification-content">
      <div class="parent-info">
        <div class="avatar-icon">{{ parentType === 'dad' ? '👨' : '👩' }}</div>
        <div class="parent-label">{{ parentType === 'dad' ? '老爸' : '老妈' }}</div>
        <div class="switch-btn" @click="switchParent" title="切换家长">🔄</div>
      </div>
      
      <div class="message-text">
        {{ currentMessage }}
      </div>
      
      <div class="action-buttons">
        <button class="know-btn" @click="hidePopup">我知道了</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

const props = defineProps({
  focusData: {
    type: Object,
    default: () => ({
      current_data: {
        focus_level: 0,
        stress_level: 0,
        current_emotion: 'neutral'
      }
    })
  },
  focusTime: {
    type: Number,
    default: 0
  },
  completedTasks: {
    type: Number,
    default: 0
  },
  totalTasks: {
    type: Number,
    default: 1
  },
  currentTask: {
    type: Object,
    default: null
  },
  goal: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'switch-parent'])

const isVisible = ref(false)
const isFadingOut = ref(false)
const currentMessage = ref('')
const parentType = ref('dad') // 'dad' or 'mom'
const messageHistory = ref([]) // 存储消息历史用于上下文
const isGenerating = ref(false)
let hideTimer = null

// 计算属性
const focusLevel = computed(() => props.focusData.current_data?.focus_level || 0)
const stressLevel = computed(() => props.focusData.current_data?.stress_level || 0)
const emotion = computed(() => props.focusData.current_data?.current_emotion || 'neutral')
const completionRate = computed(() => props.completedTasks / props.totalTasks)

// 显示通知
const showPopup = async () => {
  // 清除之前的定时器
  if (hideTimer) {
    clearTimeout(hideTimer)
  }
  
  isFadingOut.value = false
  isVisible.value = true
  isGenerating.value = true
  currentMessage.value = "正在思考中..."
  
  try {
    await generateMessage()
  } catch (error) {
    currentMessage.value = "哎呀，网络有点问题，但爸爸/妈妈还是关心你的！"
  } finally {
    isGenerating.value = false
  }
  
  // 8秒后自动隐藏（LLM生成的内容可能更长）
  hideTimer = setTimeout(() => {
    hidePopup()
  }, 8000)
}

// 隐藏通知
const hidePopup = () => {
  isFadingOut.value = true
  
  // 等待动画完成后隐藏
  setTimeout(() => {
    isVisible.value = false
    isFadingOut.value = false
    emit('close')
  }, 300)
}

// 切换家长
const switchParent = () => {
  parentType.value = parentType.value === 'dad' ? 'mom' : 'dad'
  messageHistory.value = [] // 清空历史，重新开始
  generateMessage()
  emit('switch-parent', parentType.value)
}

// 时间格式化
const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  return `${minutes}分${seconds % 60}秒`
}

// 移除了样式类函数，不再需要

// 通过LLM生成家长式吐槽消息
const generateMessage = async () => {
  const currentState = {
    focusLevel: focusLevel.value,
    stressLevel: stressLevel.value,
    emotion: emotion.value,
    completionRate: completionRate.value,
    focusTime: props.focusTime
  }
  
  // 构建任务上下文信息
  const taskContext = {
    currentTask: props.currentTask ? {
      title: props.currentTask.title,
      description: props.currentTask.description
    } : null,
    goal: props.goal ? {
      title: props.goal.title,
      description: props.goal.description
    } : null,
    totalTasks: props.totalTasks,
    completedTasks: props.completedTasks
  }
  
  // 构建给LLM的上下文
  const context = buildLLMContext(currentState, messageHistory.value, taskContext)
  
  try {
    // 调用后端LLM API
    const response = await axios.post('http://localhost:8000/generate-parent-message', {
      parent_type: parentType.value,
      current_state: currentState,
      context: context,
      task_context: taskContext,
      session_id: `focus_${Date.now()}`
    })
    
    const message = response.data.message || "孩子，继续加油！"
    currentMessage.value = message
    
    // 记录消息历史
    messageHistory.value.push({
      timestamp: Date.now(),
      state: currentState,
      message: message
    })
    
    // 只保留最近3条记录
    if (messageHistory.value.length > 3) {
      messageHistory.value = messageHistory.value.slice(-3)
    }
    
  } catch (error) {
    console.error('LLM生成消息失败:', error)
    // 降级到简单消息
    const fallbackMessages = parentType.value === 'dad' 
      ? [`专注度${Math.round(focusLevel.value * 100)}%，还行！继续努力，听爸爸的没错。`]
      : [`孩子，专注度${Math.round(focusLevel.value * 100)}%还可以，妈妈相信你能做得更好！`]
    currentMessage.value = fallbackMessages[0]
  }
}

// 构建LLM上下文
const buildLLMContext = (currentState, history, taskContext = null) => {
  const recentMessages = history.slice(-2).map(h => h.message).join(' ')
  
  const context = {
    recent_history: recentMessages,
    focus_trend: history.length >= 2 ? 
      (currentState.focusLevel > history[history.length - 1].state.focusLevel ? 'improving' : 'declining') : 'stable',
    stress_trend: history.length >= 2 ? 
      (currentState.stressLevel > history[history.length - 1].state.stressLevel ? 'increasing' : 'decreasing') : 'stable'
  }
  
  // 如果有任务上下文，添加到context中
  if (taskContext) {
    context.task_info = taskContext
  }
  
  return context
}

// 状态分析
const analyzeState = (state) => {
  const issues = []
  const positives = []
  
  // 专注度分析
  if (state.focusLevel < 0.4) {
    issues.push('focus_low')
  } else if (state.focusLevel > 0.8) {
    positives.push('focus_high')
  }
  
  // 压力分析
  if (state.stressLevel > 0.7) {
    issues.push('stress_high')
  } else if (state.stressLevel < 0.3) {
    positives.push('stress_low')
  }
  
  // 任务完成率
  if (state.completionRate < 0.2) {
    issues.push('progress_slow')
  } else if (state.completionRate > 0.8) {
    positives.push('progress_good')
  }
  
  // 专注时间
  if (state.focusTime < 300) { // 5分钟
    issues.push('time_short')
  } else if (state.focusTime > 1800) { // 30分钟
    issues.push('time_long')
  }
  
  // 情绪分析
  if (['sad', 'angry'].includes(state.emotion)) {
    issues.push('emotion_negative')
  } else if (['happy', 'focused'].includes(state.emotion)) {
    positives.push('emotion_positive')
  }
  
  return { issues, positives, overall: issues.length > positives.length ? 'concern' : 'good' }
}

// 生成上下文相关消息
const generateContextualMessage = (analysis, history) => {
  const isDad = parentType.value === 'dad'
  
  // 检查是否有重复模式
  const recentIssues = history.slice(-3).map(h => h.analysis.issues).flat()
  const hasRepeatedIssues = recentIssues.length > 0 && new Set(recentIssues).size < recentIssues.length
  
  // 爸爸的消息模板
  const dadMessages = {
    // 专注度问题
    focus_low: [
      "你说你这孩子，专注度才{focus}%？心思都跑哪去了？",
      "专注度这么低，还想着成功？我像你这么大的时候...",
      "你看看这专注度，{focus}%！别人家孩子都80%以上了！"
    ],
    focus_low_repeated: [
      "我说了多少遍了，专注度还是{focus}%！耳朵是摆设？",
      "老爸刚才不是说了吗？怎么专注度还在原地踏步？",
      "你这孩子真是的，说一遍不听，专注度还是这么低！"
    ],
    
    // 压力过高
    stress_high: [
      "压力{stress}%了，别给自己太大压力。做人如做菜，要有火候。",
      "这压力水平有点高啊，放松点，宝剑锋从磨砺出但也别把自己逼太紧。",
      "压力这么大干嘛？年轻人要多吃点苦，但也要劳逸结合。"
    ],
    
    // 进度慢
    progress_slow: [
      "任务完成{completion}%？这效率我都替你着急！",
      "进度这么慢，什么时候能完成？时间不等人啊！",
      "你这速度，别人都完成两轮了！社会很现实的！"
    ],
    
    // 时间太短
    time_short: [
      "才专注{time}？三分钟热度又犯了？",
      "这点时间怎么够？做事要有始有终！",
      "刚开始就想歇？吃得苦中苦，方为人上人！"
    ],
    
    // 正面反馈
    focus_high: [
      "嗯，专注度{focus}%，还凑合！但是别骄傲...",
      "这次专注度不错，{focus}%！继续保持，听爸爸的没错。",
      "专注度挺好的，{focus}%！看来我的教育还是有用的。"
    ],
    
    // 默认鼓励
    default: [
      "行了，别墨迹了，专注度{focus}%还行。继续努力！",
      "做就完了！专注度{focus}%，压力{stress}%，保持节奏。",
      "年轻人就要有冲劲！现在专注度{focus}%，再接再厉！"
    ]
  }
  
  // 妈妈的消息模板
  const momMessages = {
    focus_low: [
      "哎呀我的傻孩子，专注度才{focus}%？妈妈都替你着急！",
      "专注度这么低，是不是哪里不舒服？妈妈担心你...",
      "孩子啊，{focus}%的专注度可不行，你看人家xxx..."
    ],
    focus_low_repeated: [
      "妈妈刚才不是说了吗？专注度怎么还是{focus}%？",
      "你这孩子怎么不听妈妈话？专注度一直这么低！",
      "哎呀，说了你也不听，专注度还是没提升！"
    ],
    
    stress_high: [
      "压力{stress}%了，别给自己太大压力！妈妈心疼...",
      "孩子，压力这么大可怎么办啊？要不要休息一下？",
      "压力水平这么高，妈妈看着都难受！"
    ],
    
    progress_slow: [
      "任务才完成{completion}%？这样下去可怎么办啊？",
      "进度这么慢，妈妈都替你操心！是不是任务太难了？",
      "完成度这么低，妈妈担心你完不成任务..."
    ],
    
    time_short: [
      "才专注{time}？是不是坐不住？妈妈给你泡杯茶？",
      "这么快就想休息？是不是太累了？",
      "孩子，要有耐心，不能总是三分钟热度！"
    ],
    
    focus_high: [
      "哎呀不错！专注度{focus}%！妈妈就知道你可以的！",
      "专注度这么好，{focus}%！妈妈为你骄傲！",
      "看看，专注度{focus}%！妈妈没白疼你！"
    ],
    
    default: [
      "孩子，专注度{focus}%还可以，妈妈相信你能做得更好！",
      "现在专注度{focus}%，压力{stress}%，要注意身体哦！",
      "妈妈看着你这么努力，心里很欣慰。专注度{focus}%不错！"
    ]
  }
  
  const messages = isDad ? dadMessages : momMessages
  
  // 选择合适的消息类型
  let messageType = 'default'
  let messageTemplates = messages.default
  
  if (analysis.issues.length > 0) {
    const primaryIssue = analysis.issues[0]
    if (hasRepeatedIssues && messages[primaryIssue + '_repeated']) {
      messageType = primaryIssue + '_repeated'
      messageTemplates = messages[primaryIssue + '_repeated']
    } else if (messages[primaryIssue]) {
      messageType = primaryIssue
      messageTemplates = messages[primaryIssue]
    }
  } else if (analysis.positives.length > 0) {
    const primaryPositive = analysis.positives[0]
    if (messages[primaryPositive]) {
      messageType = primaryPositive
      messageTemplates = messages[primaryPositive]
    }
  }
  
  // 随机选择一个模板
  const template = messageTemplates[Math.floor(Math.random() * messageTemplates.length)]
  
  // 替换变量
  return template
    .replace('{focus}', Math.round(focusLevel.value * 100))
    .replace('{stress}', Math.round(stressLevel.value * 100))
    .replace('{completion}', Math.round(completionRate.value * 100))
    .replace('{time}', formatTime(props.focusTime))
}

// 暴露方法给父组件
defineExpose({
  showPopup,
  hidePopup
})
</script>

<style scoped>
.parent-notification {
  position: fixed;
  bottom: 80px;
  right: 20px;
  background: var(--cyber-glass);
  border: 1px solid var(--cyber-glass-border);
  border-radius: 15px;
  padding: 15px;
  max-width: 350px;
  min-width: 280px;
  backdrop-filter: blur(15px);
  box-shadow: 0 8px 25px rgba(0, 255, 255, 0.15);
  z-index: 1500;
  animation: slideInRight 0.4s ease-out;
}

.parent-notification.fade-out {
  animation: slideOutRight 0.3s ease-in forwards;
}

.notification-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.parent-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar-icon {
  font-size: 1.8rem;
  background: var(--cyber-glass);
  border: 1px solid var(--cyber-neon-cyan);
  border-radius: 50%;
  width: 35px;
  height: 35px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.2);
}

.parent-label {
  color: var(--cyber-text-primary);
  font-size: 1rem;
  font-weight: 600;
  flex: 1;
}

.switch-btn {
  font-size: 0.9rem;
  cursor: pointer;
  opacity: 0.7;
  transition: all 0.2s ease;
  padding: 2px;
  border-radius: 4px;
}

.switch-btn:hover {
  opacity: 1;
  background: rgba(0, 255, 255, 0.1);
}

.message-text {
  color: var(--cyber-text-primary);
  font-size: 0.95rem;
  line-height: 1.4;
  background: rgba(0, 255, 255, 0.05);
  border-left: 3px solid var(--cyber-neon-cyan);
  padding: 10px 12px;
  border-radius: 8px;
  margin: 8px 0;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.know-btn {
  background: var(--cyber-glass);
  border: 1px solid var(--cyber-neon-cyan);
  border-radius: 8px;
  padding: 6px 16px;
  color: var(--cyber-neon-cyan);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
}

.know-btn:hover {
  background: rgba(0, 255, 255, 0.1);
  border-color: var(--cyber-neon-cyan);
  color: white;
  box-shadow: 0 0 8px rgba(0, 255, 255, 0.3);
}

.know-btn:active {
  transform: scale(0.98);
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideOutRight {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(100%);
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .parent-notification {
    bottom: 10px;
    right: 10px;
    left: 10px;
    max-width: none;
    min-width: auto;
  }
  
  .action-buttons {
    justify-content: center;
  }
  
  .know-btn {
    padding: 8px 20px;
    font-size: 0.9rem;
  }
}
</style>