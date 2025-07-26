<template>
  <div class="barrage-container">
    <!-- 弹幕消息 -->
    <transition-group name="barrage" tag="div" class="barrage-list">
      <div
        v-for="barrage in barrages"
        :key="barrage.id"
        class="barrage-item"
        :style="{
          top: barrage.top + 'px',
          animationDuration: barrage.duration + 's'
        }"
      >
        <div class="barrage-content">
          <span class="parent-avatar">{{ barrage.parentType === 'dad' ? '👨' : '👩' }}</span>
          <span class="parent-name">{{ barrage.parentType === 'dad' ? '老爸' : '老妈' }}</span>
          <span class="barrage-text">{{ barrage.message }}</span>
        </div>
      </div>
    </transition-group>

    <!-- 控制面板（小而精简） -->
    <div class="barrage-controls">
      <button 
        class="control-btn switch-parent" 
        @click="switchParent"
        :title="`切换到${parentType === 'dad' ? '老妈' : '老爸'}`"
      >
        {{ parentType === 'dad' ? '👩' : '👨' }}
      </button>
      <button 
        class="control-btn toggle-barrage" 
        @click="toggleBarrage"
        :title="barrageEnabled ? '关闭吐槽' : '开启吐槽'"
      >
        {{ barrageEnabled ? '🔇' : '🔊' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
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

const emit = defineEmits(['switch-parent'])

// 弹幕状态
const barrages = ref([])
const parentType = ref('dad')
const barrageEnabled = ref(true)
const barrageId = ref(0)
const messageHistory = ref([])

// 确保弹幕在组件挂载时被启用

onMounted(() => {
  console.log('🎬 弹幕组件已挂载，启用状态:', barrageEnabled.value)
  // 强制启用弹幕
  barrageEnabled.value = true
  
  // 3秒后创建一个测试弹幕
  setTimeout(() => {
    console.log('🧪 创建测试弹幕...')
    createBarrage('测试弹幕：你好世界！')
  }, 3000)
})

// 弹幕轨道管理（避免重叠）
const tracks = ref([false, false, false, false, false]) // 5条轨道
const trackHeight = 60 // 每条轨道高度

// 生成弹幕消息
const generateBarrage = async () => {
  console.log('🎯 准备生成弹幕...', { barrageEnabled: barrageEnabled.value })
  if (!barrageEnabled.value) {
    console.warn('⚠️ 弹幕被禁用，强制启用中...')
    barrageEnabled.value = true
  }

  try {
    // 构建状态和任务信息
    const currentState = {
      focusLevel: props.focusData.current_data?.focus_level || 0,
      stressLevel: props.focusData.current_data?.stress_level || 0,
      emotion: props.focusData.current_data?.current_emotion || 'neutral',
      completionRate: props.completedTasks / props.totalTasks,
      focusTime: props.focusTime
    }

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

    const context = buildLLMContext(currentState, messageHistory.value, taskContext)

    // 调用LLM API
    const response = await axios.post('http://localhost:8000/generate-parent-message', {
      parent_type: parentType.value,
      current_state: currentState,
      context: context,
      task_context: taskContext,
      session_id: `focus_${Date.now()}`
    })

    const message = response.data.message || "孩子，继续加油！"
    
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

    // 创建弹幕
    console.log('✅ LLM生成消息成功:', message)
    createBarrage(message)

  } catch (error) {
    console.error('❌ 生成弹幕失败:', error)
    // 降级消息
    const taskName = props.currentTask?.title || "学习"
    const fallbackMessages = {
      'dad': [`${taskName}要认真点！`, `专注度还可以，继续！`, `别走神，听爸爸的！`],
      'mom': [`${taskName}要加油哦！`, `妈妈相信你可以的！`, `专注一点，孩子！`]
    }
    const message = fallbackMessages[parentType.value][Math.floor(Math.random() * 3)]
    createBarrage(message)
  }
}

// 创建弹幕
const createBarrage = (message) => {
  console.log('🚀 创建弹幕:', message)
  // 找到空闲轨道
  let trackIndex = tracks.value.findIndex(track => !track)
  if (trackIndex === -1) {
    trackIndex = Math.floor(Math.random() * tracks.value.length)
  }
  console.log('📍 使用轨道:', trackIndex)
  
  // 占用轨道
  tracks.value[trackIndex] = true
  
  const newBarrage = {
    id: barrageId.value++,
    message: message,
    parentType: parentType.value,
    top: 100 + trackIndex * trackHeight, // 从100px开始，避免遮挡头部
    duration: 8 + Math.random() * 4, // 8-12秒的动画时间
    trackIndex: trackIndex
  }
  
  barrages.value.push(newBarrage)
  
  // 动画结束后清理弹幕和轨道
  setTimeout(() => {
    const index = barrages.value.findIndex(b => b.id === newBarrage.id)
    if (index !== -1) {
      barrages.value.splice(index, 1)
      tracks.value[trackIndex] = false
    }
  }, newBarrage.duration * 1000)
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
  
  if (taskContext) {
    context.task_info = taskContext
  }
  
  return context
}

// 切换父母
const switchParent = () => {
  parentType.value = parentType.value === 'dad' ? 'mom' : 'dad'
  messageHistory.value = [] // 清空历史，重新开始
  emit('switch-parent', parentType.value)
}

// 开关弹幕
const toggleBarrage = () => {
  barrageEnabled.value = !barrageEnabled.value
  if (!barrageEnabled.value) {
    // 清空现有弹幕
    barrages.value = []
    tracks.value.fill(false)
  }
}

// 暴露方法给父组件
defineExpose({
  generateBarrage,
  toggleBarrage,
  switchParent
})
</script>

<style scoped>
.barrage-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 9999;
  overflow: hidden;
}

.barrage-list {
  position: relative;
  width: 100%;
  height: 100%;
}

.barrage-item {
  position: absolute;
  right: -100%;
  white-space: nowrap;
  animation: slideLeft linear;
  pointer-events: none;
}

@keyframes slideLeft {
  0% {
    transform: translateX(100vw);
    opacity: 1;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateX(-100%);
    opacity: 0;
  }
}

.barrage-content {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.7);
  border: 1px solid var(--cyber-neon-cyan);
  border-radius: 20px;
  padding: 8px 16px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 15px rgba(0, 255, 255, 0.2);
}

.parent-avatar {
  font-size: 1.2rem;
  background: var(--cyber-glass);
  border: 1px solid var(--cyber-neon-cyan);
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 8px rgba(0, 255, 255, 0.3);
}

.parent-name {
  color: var(--cyber-neon-cyan);
  font-size: 0.85rem;
  font-weight: 600;
  min-width: 32px;
}

.barrage-text {
  color: var(--cyber-text-primary);
  font-size: 0.9rem;
  text-shadow: 0 0 4px rgba(0, 255, 255, 0.3);
}

.barrage-controls {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  gap: 8px;
  pointer-events: auto;
  z-index: 10000;
}

.control-btn {
  background: var(--cyber-glass);
  border: 1px solid var(--cyber-glass-border);
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 255, 255, 0.1);
}

.control-btn:hover {
  background: rgba(0, 255, 255, 0.1);
  border-color: var(--cyber-neon-cyan);
  box-shadow: 0 0 12px rgba(0, 255, 255, 0.3);
  transform: scale(1.05);
}

.control-btn:active {
  transform: scale(0.95);
}

/* 弹幕进入/离开动画 */
.barrage-enter-active {
  transition: all 0.3s ease;
}

.barrage-leave-active {
  transition: all 0.3s ease;
}

.barrage-enter-from {
  opacity: 0;
  transform: translateX(100px);
}

.barrage-leave-to {
  opacity: 0;
  transform: translateX(-100px);
}

/* 响应式适配 */
@media (max-width: 768px) {
  .barrage-content {
    padding: 6px 12px;
    gap: 6px;
  }
  
  .parent-avatar {
    width: 24px;
    height: 24px;
    font-size: 1rem;
  }
  
  .parent-name {
    font-size: 0.8rem;
  }
  
  .barrage-text {
    font-size: 0.85rem;
  }
  
  .barrage-controls {
    top: 10px;
    right: 10px;
  }
  
  .control-btn {
    width: 36px;
    height: 36px;
    font-size: 1rem;
  }
}
</style>