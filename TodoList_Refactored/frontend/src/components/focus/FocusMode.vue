<template>
  <div class="focus-overlay">
    <div class="focus-container">
      <!-- 头部信息 -->
      <div class="focus-header">
        <button class="exit-focus-btn" @click="$emit('exit-focus')">×</button>
        <h2>{{ goal.title }}</h2>
        <div class="focus-timer">{{ formatTime(elapsedTime) }}</div>
      </div>

      <!-- 控制按钮 -->
      <div class="focus-controls focus-controls-top">
        <button class="control-btn pause-btn" @click="pauseFocus">
          {{ paused ? '继续' : '暂停' }}
        </button>
        <button class="control-btn complete-btn" @click="completeCurrentTask">
          完成当前任务
        </button>
        <button class="control-btn next-btn" @click="nextTask">
          下一个任务
        </button>
      </div>

      <!-- 专注数据显示区域 -->
      <div class="focus-data-section">
        <div class="data-cards">
          <div class="data-card">
            <h4>专注度</h4>
            <div class="data-value focus-value">{{ (focusData.current_data?.focus_level * 100 || 0).toFixed(1) }}%</div>
            <div class="data-quality">{{ getDataQualityText(focusData.current_data?.data_quality) }}</div>
          </div>
          <div class="data-card">
            <h4>注意力</h4>
            <div class="data-value attention-value">{{ (focusData.current_data?.attention * 100 || 0).toFixed(1) }}%</div>
          </div>
          <div class="data-card">
            <h4>压力水平</h4>
            <div class="data-value stress-value">{{ (focusData.current_data?.stress_level * 100 || 0).toFixed(1) }}%</div>
          </div>
          <div class="data-card">
            <h4>当前情绪</h4>
            <div class="data-value emotion-value">{{ getEmotionText(focusData.current_data?.current_emotion) }}</div>
          </div>
        </div>
        
        <!-- 图表并列显示 -->
        <div class="charts-row">
          <!-- EEG趋势折线图 -->
          <div class="chart-section chart-half">
            <h4>EEG脑电数据</h4>
            <div class="chart-container">
              <canvas ref="eegChartCanvas" id="eegChart"></canvas>
            </div>
          </div>
          
          <!-- 情绪数据折线图 -->
          <div class="chart-section chart-half">
            <h4>情绪数据</h4>
            <div class="chart-container">
              <canvas ref="emotionChartCanvas" id="emotionChart"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- 任务列表区域 -->
      <div class="focus-tasks-section">
        <div class="tasks-header">
          <h3>任务清单</h3>
          <!-- 升级版环形进度图 -->
          <div class="task-ring-container">
            <svg class="progress-ring" width="100" height="100">
              <!-- 外环 - 任务分段 -->
              <circle 
                class="ring-background" 
                cx="50" 
                cy="50" 
                :r="outerRadius"
                fill="none" 
                stroke="var(--cyber-glass-border)" 
                stroke-width="2"
              />
              <!-- 任务分段 -->
              <g v-for="(task, index) in goal.tasks" :key="task.id">
                <path
                  :d="getSegmentPath(index, goal.tasks.length)"
                  :class="{
                    'segment-completed': task.completed,
                    'segment-current': currentTask && currentTask.id === task.id,
                    'segment-pending': !task.completed && (!currentTask || currentTask.id !== task.id)
                  }"
                  @click="setCurrentTask(task)"
                />
              </g>
              <!-- 内环 - 专注度显示 -->
              <circle 
                class="focus-ring-background" 
                cx="50" 
                cy="50" 
                :r="innerRadius"
                fill="none" 
                stroke="var(--cyber-glass-border)" 
                stroke-width="3"
              />
              <circle 
                class="focus-ring-progress" 
                cx="50" 
                cy="50" 
                :r="innerRadius"
                fill="none" 
                stroke="var(--cyber-neon-cyan)" 
                stroke-width="3"
                :stroke-dasharray="focusCircumference"
                :stroke-dashoffset="focusOffset"
                transform="rotate(-90 50 50)"
              />
            </svg>
            <div class="ring-info">
              <span class="completed-count">{{ goal.tasks.filter(t => t.completed).length }}</span>
              <span class="total-count">{{ goal.tasks.length }}</span>
              <div class="focus-percentage">{{ (focusData.current_data?.focus_level * 100 || 0).toFixed(0) }}%</div>
            </div>
          </div>
        </div>
        <div class="focus-tasks-list">
          <div 
            v-for="task in goal.tasks" 
            :key="task.id"
            class="focus-task-item"
            :class="{ 
              completed: task.completed,
              current: currentTask && currentTask.id === task.id
            }"
            @click="setCurrentTask(task)"
          >
            <div class="focus-task-checkbox">
              <input
                type="checkbox"
                :id="`focus-task-${task.id}`"
                v-model="task.completed"
                @change="$emit('update-task', task)"
              />
              <label :for="`focus-task-${task.id}`"></label>
            </div>
            <div class="focus-task-content">
              <h4>{{ task.title }}</h4>
              <p v-if="task.description">{{ task.description }}</p>
            </div>
            <div class="focus-task-status">
              <span v-if="currentTask && currentTask.id === task.id" class="current-indicator">
                正在进行
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 家长监督弹窗 -->
    <ParentPopup 
      ref="parentPopupRef"
      :focus-data="focusData"
      :focus-time="elapsedTime"
      :completed-tasks="goal.tasks.filter(t => t.completed).length"
      :total-tasks="goal.tasks.length"
      :current-task="currentTask"
      :goal="goal"
      @close="onPopupClose"
      @switch-parent="onSwitchParent"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useNotification } from '../../composables/useNotification.js'
import axios from 'axios'
import ParentPopup from './ParentPopup.vue'
import { 
  Chart, 
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  LineController,
  Title, 
  Tooltip, 
  Legend 
} from 'chart.js'

Chart.register(
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  LineController,
  Title, 
  Tooltip, 
  Legend
)

const props = defineProps({
  goal: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['exit-focus', 'update-task'])

const { showNotification } = useNotification()

// 专注模式状态
const currentTask = ref(null)
const startTime = ref(Date.now())
const elapsedTime = ref(0)
const paused = ref(false)
const timer = ref(null)

// 家长弹窗相关
const parentPopupRef = ref(null)
const parentPopupTimer = ref(null)
const parentPopupInitTimer = ref(null)
const currentParentType = ref('dad')

// 专注数据状态
const focusData = ref({
  current_data: {
    focus_level: 0,
    attention: 0,
    stress_level: 0,
    current_emotion: 'neutral'
  },
  trends: {
    attention: [],
    engagement: [],
    excitement: [],
    interest: [],
    stress: [],
    relaxation: []
  }
})
const dataUpdateTimer = ref(null)

// Chart.js相关
const eegChartCanvas = ref(null)
const emotionChartCanvas = ref(null)
let eegChart = null
let emotionChart = null

// SVG环形图参数
const outerRadius = 40
const innerRadius = 25
const focusCircumference = computed(() => 2 * Math.PI * innerRadius)
const focusOffset = computed(() => {
  const progress = focusData.value.current_data?.focus_level || 0
  return focusCircumference.value * (1 - progress)
})

// 计时器相关
const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}

const startTimer = () => {
  timer.value = setInterval(() => {
    if (!paused.value) {
      elapsedTime.value = Math.floor((Date.now() - startTime.value) / 1000)
    }
  }, 1000)
}

const pauseFocus = () => {
  paused.value = !paused.value
  if (paused.value) {
    showNotification('专注已暂停')
    // 暂停时停止家长弹窗
    stopParentPopupTimer()
  } else {
    startTime.value = Date.now() - (elapsedTime.value * 1000)
    showNotification('继续专注')
    // 继续时重启家长弹窗
    startParentPopupTimer()
  }
}

// 任务操作
const setCurrentTask = (task) => {
  if (!task.completed) {
    currentTask.value = task
    showNotification(`切换到: ${task.title}`)
  }
}

const completeCurrentTask = async () => {
  if (!currentTask.value) return
  
  try {
    currentTask.value.completed = true
    emit('update-task', currentTask.value)
    showNotification('任务完成！')
    nextTask()
  } catch (error) {
    showNotification('操作失败，请重试', 'error')
  }
}

const nextTask = () => {
  const tasks = props.goal.tasks
  const currentIndex = tasks.findIndex(t => t.id === currentTask.value?.id)
  
  // 找到下一个未完成的任务
  for (let i = currentIndex + 1; i < tasks.length; i++) {
    if (!tasks[i].completed) {
      currentTask.value = tasks[i]
      showNotification(`切换到: ${tasks[i].title}`)
      return
    }
  }
  
  // 如果没有找到，从头开始找
  for (let i = 0; i < currentIndex; i++) {
    if (!tasks[i].completed) {
      currentTask.value = tasks[i]
      showNotification(`切换到: ${tasks[i].title}`)
      return
    }
  }
  
  // 所有任务都完成了
  showNotification('所有任务都已完成！')
  currentTask.value = null
}

// 数据获取和处理
const fetchFocusData = async () => {
  if (!currentTask.value) return
  
  try {
    const response = await axios.get(`http://localhost:8000/focus/current/${currentTask.value.id}`)
    focusData.value = response.data
    updateCharts()
  } catch (error) {
    console.error('获取专注数据失败:', error)
  }
}

// 初始化EEG图表
const initEegChart = () => {
  if (!eegChartCanvas.value) return
  
  const ctx = eegChartCanvas.value.getContext('2d')
  eegChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: Array.from({ length: 10 }, (_, i) => `${i + 1}`),
      datasets: [
        {
          label: '专注度',
          data: [],
          borderColor: '#00FFFF',
          backgroundColor: 'rgba(0, 255, 255, 0.1)',
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6
        },
        {
          label: '注意力',
          data: [],
          borderColor: '#00D4FF',
          backgroundColor: 'rgba(0, 212, 255, 0.1)',
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6
        },
        {
          label: '参与度',
          data: [],
          borderColor: '#39FF14',
          backgroundColor: 'rgba(57, 255, 20, 0.1)',
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6
        },
        {
          label: '兴奋度',
          data: [],
          borderColor: '#FF45B4',
          backgroundColor: 'rgba(255, 69, 180, 0.1)',
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6
        },
        {
          label: '压力水平',
          data: [],
          borderColor: '#FF6B6B',
          backgroundColor: 'rgba(255, 107, 107, 0.1)',
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6
        },
        {
          label: '放松度',
          data: [],
          borderColor: '#9B59B6',
          backgroundColor: 'rgba(155, 89, 182, 0.1)',
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: '#E2E8F0',
            font: {
              size: 12
            }
          }
        },
        title: {
          display: false
        }
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(226, 232, 240, 0.1)'
          },
          ticks: {
            color: '#94A3B8'
          }
        },
        y: {
          min: 0,
          max: 1,
          grid: {
            color: 'rgba(226, 232, 240, 0.1)'
          },
          ticks: {
            color: '#94A3B8',
            callback: function(value) {
              return (value * 100).toFixed(0) + '%'
            }
          }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      }
    }
  })
}

// 初始化情绪图表
const initEmotionChart = () => {
  if (!emotionChartCanvas.value) return
  
  const ctx = emotionChartCanvas.value.getContext('2d')
  emotionChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: Array.from({ length: 10 }, (_, i) => `${i + 1}`),
      datasets: [
        {
          label: '开心度',
          data: [],
          borderColor: '#FFD700',
          backgroundColor: 'rgba(255, 215, 0, 0.1)',
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6
        },
        {
          label: '平静度',
          data: [],
          borderColor: '#87CEEB',
          backgroundColor: 'rgba(135, 206, 235, 0.1)',
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6
        },
        {
          label: '愤怒度',
          data: [],
          borderColor: '#FF4444',
          backgroundColor: 'rgba(255, 68, 68, 0.1)',
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6
        },
        {
          label: '悲伤度',
          data: [],
          borderColor: '#6495ED',
          backgroundColor: 'rgba(100, 149, 237, 0.1)',
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: '#E2E8F0',
            font: {
              size: 12
            }
          }
        },
        title: {
          display: false
        }
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(226, 232, 240, 0.1)'
          },
          ticks: {
            color: '#94A3B8'
          }
        },
        y: {
          min: 0,
          max: 1,
          grid: {
            color: 'rgba(226, 232, 240, 0.1)'
          },
          ticks: {
            color: '#94A3B8',
            callback: function(value) {
              return (value * 100).toFixed(0) + '%'
            }
          }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      }
    }
  })
}

// 更新图表数据
const updateCharts = () => {
  if (!focusData.value.trends) return
  
  const trends = focusData.value.trends
  
  // 更新EEG图表
  if (eegChart) {
    eegChart.data.datasets[0].data = trends.focus || []
    eegChart.data.datasets[1].data = trends.attention || []
    eegChart.data.datasets[2].data = trends.engagement || []
    eegChart.data.datasets[3].data = trends.excitement || []
    eegChart.data.datasets[4].data = trends.stress || []
    eegChart.data.datasets[5].data = trends.relaxation || []
    eegChart.update('none')
  }
  
  // 更新情绪图表
  if (emotionChart && trends.happiness) {
    emotionChart.data.datasets[0].data = trends.happiness || []
    emotionChart.data.datasets[1].data = trends.neutral || []
    emotionChart.data.datasets[2].data = trends.anger || []
    emotionChart.data.datasets[3].data = trends.sadness || []
    emotionChart.update('none')
  }
}

const getDataQualityText = (quality) => {
  const qualityMap = {
    'good': '真实数据',
    'real_eeg': '真实数据', 
    'fallback': '',
    'simulated': ''
  }
  return qualityMap[quality] || ''
}

const getEmotionText = (emotion) => {
  const emotionMap = {
    'focused': '专注',
    'calm': '平静',
    'neutral': '中性',
    'thinking': '思考中',
    'happy': '开心',
    'sad': '伤心',
    'angry': '愤怒',
    'fear': '恐惧',
    'surprise': '惊讶',
    'disgust': '厌恶'
  }
  return emotionMap[emotion] || emotion || ''
}

// SVG路径生成
const getSegmentPath = (index, totalTasks) => {
  const startAngle = (index * 360 / totalTasks) * Math.PI / 180
  const endAngle = ((index + 1) * 360 / totalTasks) * Math.PI / 180
  const gap = 0.05 // 分段间隙
  
  const x1 = 50 + (outerRadius - 8) * Math.cos(startAngle + gap)
  const y1 = 50 + (outerRadius - 8) * Math.sin(startAngle + gap)
  const x2 = 50 + (outerRadius - 8) * Math.cos(endAngle - gap)
  const y2 = 50 + (outerRadius - 8) * Math.sin(endAngle - gap)
  const x3 = 50 + outerRadius * Math.cos(endAngle - gap)
  const y3 = 50 + outerRadius * Math.sin(endAngle - gap)
  const x4 = 50 + outerRadius * Math.cos(startAngle + gap)
  const y4 = 50 + outerRadius * Math.sin(startAngle + gap)
  
  const largeArcFlag = (endAngle - startAngle) > Math.PI ? 1 : 0
  
  return `M ${x1} ${y1} A ${outerRadius - 8} ${outerRadius - 8} 0 ${largeArcFlag} 1 ${x2} ${y2} L ${x3} ${y3} A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 0 ${x4} ${y4} Z`
}

// 家长弹窗控制
const startParentPopupTimer = () => {
  // 清理之前的定时器
  if (parentPopupTimer.value) {
    clearInterval(parentPopupTimer.value)
  }
  if (parentPopupInitTimer.value) {
    clearTimeout(parentPopupInitTimer.value)
  }
  
  // 60秒后显示第一次弹窗，之后每2分钟显示一次
  parentPopupInitTimer.value = setTimeout(() => {
    if (!paused.value && parentPopupRef.value) {
      parentPopupRef.value.showPopup()
    }
    
    // 之后每2分钟弹一次
    parentPopupTimer.value = setInterval(() => {
      if (!paused.value && parentPopupRef.value) {
        parentPopupRef.value.showPopup()
      }
    }, 120000) // 2分钟间隔
  }, 60000) // 1分钟后第一次弹窗
}

const stopParentPopupTimer = () => {
  if (parentPopupTimer.value) {
    clearInterval(parentPopupTimer.value)
    parentPopupTimer.value = null
  }
  if (parentPopupInitTimer.value) {
    clearTimeout(parentPopupInitTimer.value)
    parentPopupInitTimer.value = null
  }
}

const onPopupClose = () => {
  // 弹窗关闭后的处理
  console.log('家长弹窗已关闭')
}

const onSwitchParent = (parentType) => {
  currentParentType.value = parentType
  showNotification(`切换到${parentType === 'dad' ? '爸爸' : '妈妈'}模式`)
}

// 生命周期
onMounted(async () => {
  // 找到第一个未完成的任务作为当前任务
  const firstIncompleteTask = props.goal.tasks.find(task => !task.completed)
  currentTask.value = firstIncompleteTask || props.goal.tasks[0]
  
  // 阻止背景滚动
  document.body.style.overflow = 'hidden'
  
  // 启动计时器
  startTimer()
  
  // 等待DOM更新后初始化图表
  await nextTick()
  initEegChart()
  initEmotionChart()
  
  // 启动数据更新定时器
  fetchFocusData() // 立即获取一次
  dataUpdateTimer.value = setInterval(fetchFocusData, 2000) // 每2秒更新
  
  // 启动家长弹窗定时器
  startParentPopupTimer()
})

onUnmounted(() => {
  // 恢复body滚动
  document.body.style.overflow = 'auto'
  
  // 清理计时器
  if (timer.value) {
    clearInterval(timer.value)
  }
  if (dataUpdateTimer.value) {
    clearInterval(dataUpdateTimer.value)
  }
  
  // 清理家长弹窗定时器
  stopParentPopupTimer()
  
  // 清理图表
  if (eegChart) {
    eegChart.destroy()
    eegChart = null
  }
  if (emotionChart) {
    emotionChart.destroy()
    emotionChart = null
  }
})
</script>

<style scoped>
/* 专注模式全屏界面样式 */
.focus-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--cyber-bg-primary);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.5s ease-out;
  overflow: hidden;
}

/* 专注数据显示区域 */
.focus-data-section {
  margin-bottom: 30px;
}

.data-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.data-card {
  background: var(--cyber-glass);
  border: 1px solid var(--cyber-glass-border);
  border-radius: 12px;
  padding: 15px;
  text-align: center;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.data-card:hover {
  border-color: var(--cyber-neon-cyan);
  box-shadow: 0 0 15px rgba(0, 255, 255, 0.2);
}

.data-card h4 {
  color: var(--cyber-text-secondary);
  font-size: 0.9rem;
  margin: 0 0 8px 0;
  font-weight: 500;
}

.data-value {
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 5px;
}

.focus-value {
  color: var(--cyber-neon-cyan);
  text-shadow: 0 0 10px var(--cyber-neon-cyan);
}

.attention-value {
  color: var(--cyber-neon-blue);
}

.stress-value {
  color: var(--cyber-neon-pink);
}

.emotion-value {
  color: var(--cyber-neon-green);
  font-size: 1.1rem;
}

.data-quality {
  font-size: 0.7rem;
  color: var(--cyber-text-muted);
  opacity: 0.8;
}

/* 图表区域样式 */
.charts-row {
  display: flex;
  gap: 20px;
  margin-top: 30px;
}

.chart-section {
  background: var(--cyber-glass);
  border: 1px solid var(--cyber-glass-border);
  border-radius: 15px;
  padding: 20px;
  backdrop-filter: blur(10px);
}

.chart-half {
  flex: 1;
}

.chart-section h4 {
  color: var(--cyber-text-primary);
  font-size: 1.1rem;
  margin: 0 0 15px 0;
  font-weight: 600;
  text-shadow: 0 0 10px var(--cyber-neon-cyan);
}

.chart-container {
  height: 300px;
  position: relative;
}

/* 移动端适配 - 图表堆叠 */
@media (max-width: 768px) {
  .charts-row {
    flex-direction: column;
    gap: 15px;
  }
  
  .chart-container {
    height: 250px;
  }
}

.focus-overlay::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(var(--cyber-neon-cyan) 1px, transparent 1px),
    linear-gradient(90deg, var(--cyber-neon-cyan) 1px, transparent 1px);
  background-size: 60px 60px;
  opacity: 0.05;
  pointer-events: none;
  animation: grid-flow 4s ease-in-out infinite;
}

.focus-container {
  width: 100%;
  max-width: 1200px;
  height: 100vh;
  padding: 40px;
  display: flex;
  flex-direction: column;
  color: var(--cyber-text-primary);
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
  position: relative;
  z-index: 1;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
}

/* 专注模式头部 */
.focus-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 40px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--cyber-glass-border);
}

.exit-focus-btn {
  background: var(--cyber-glass);
  color: var(--cyber-text-primary);
  border: 1px solid var(--cyber-glass-border);
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
  background: rgba(255, 69, 180, 0.2);
  border-color: var(--cyber-neon-pink);
  transform: scale(1.1);
  box-shadow: 0 4px 15px rgba(255, 69, 180, 0.3);
}

.focus-header h2 {
  flex: 1;
  text-align: center;
  font-size: 2rem;
  margin: 0;
  color: var(--cyber-text-primary);
  font-weight: 600;
  text-shadow: 0 0 10px var(--cyber-neon-cyan);
}

.focus-timer {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--cyber-neon-cyan);
  text-shadow: 0 0 20px var(--cyber-neon-cyan);
  font-family: 'Courier New', monospace;
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
  color: var(--cyber-text-primary);
  font-size: 1.3rem;
  margin: 0;
  font-weight: 600;
  text-shadow: 0 0 10px var(--cyber-neon-blue);
}

/* 环形进度图 */
.task-ring-container {
  position: relative;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-ring {
  position: absolute;
  top: 0;
  left: 0;
  transform: rotate(0deg);
  transition: transform 0.5s ease;
}

/* 任务分段样式 */
.segment-completed {
  fill: var(--cyber-neon-green);
  stroke: var(--cyber-neon-green);
  stroke-width: 1;
  opacity: 0.8;
  cursor: pointer;
}

.segment-current {
  fill: var(--cyber-neon-cyan);
  stroke: var(--cyber-neon-cyan);
  stroke-width: 2;
  opacity: 1;
  cursor: pointer;
  animation: pulse-glow 2s infinite;
}

.segment-pending {
  fill: var(--cyber-glass);
  stroke: var(--cyber-glass-border);
  stroke-width: 1;
  opacity: 0.6;
  cursor: pointer;
  transition: all 0.3s ease;
}

.segment-pending:hover {
  fill: rgba(0, 212, 255, 0.3);
  stroke: var(--cyber-neon-blue);
  opacity: 0.8;
}

/* 专注度内环 */
.focus-ring-background {
  opacity: 0.3;
}

.focus-ring-progress {
  stroke-linecap: round;
  transition: stroke-dashoffset 0.5s ease;
  filter: drop-shadow(0 0 5px var(--cyber-neon-cyan));
}

.ring-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: none;
  z-index: 1;
}

.completed-count {
  color: var(--cyber-text-primary);
  font-size: 1.2rem;
  font-weight: 700;
}

.total-count {
  color: var(--cyber-text-muted);
  font-size: 0.8rem;
}

.total-count::before {
  content: '/';
  margin-right: 2px;
}

.focus-percentage {
  color: var(--cyber-neon-cyan);
  font-size: 0.7rem;
  font-weight: 600;
  margin-top: 2px;
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

.focus-task-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px 20px;
  background: var(--cyber-glass);
  border-radius: 15px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.focus-task-item:hover {
  background: rgba(0, 212, 255, 0.1);
  transform: translateX(5px);
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.2);
}

.focus-task-item.current {
  border-color: var(--cyber-neon-cyan);
  background: rgba(0, 255, 255, 0.1);
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
}

.focus-task-item.completed {
  opacity: 0.6;
  background: var(--cyber-glass);
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
  border: 2px solid var(--cyber-glass-border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--cyber-glass);
}

.focus-task-checkbox input:checked + label {
  background: var(--cyber-neon-blue);
  border-color: var(--cyber-neon-blue);
  box-shadow: 0 0 10px var(--cyber-neon-blue);
}

.focus-task-checkbox input:checked + label::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--cyber-text-dark);
  font-weight: bold;
  font-size: 14px;
}

.focus-task-content {
  flex: 1;
}

.focus-task-content h4 {
  color: var(--cyber-text-primary);
  font-size: 1.1rem;
  margin-bottom: 5px;
  font-weight: 500;
}

.focus-task-content p {
  color: var(--cyber-text-secondary);
  font-size: 0.9rem;
  line-height: 1.4;
}

.focus-task-status {
  font-size: 0.8rem;
}

.current-indicator {
  background: var(--cyber-neon-cyan);
  color: var(--cyber-text-dark);
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
  border: 2px solid var(--cyber-glass-border);
  color: var(--cyber-text-primary);
  background: var(--cyber-glass);
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.pause-btn {
  background: linear-gradient(135deg, var(--cyber-neon-purple), var(--cyber-neon-pink));
  color: var(--cyber-text-dark);
  border-color: var(--cyber-neon-purple);
}

.pause-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(155, 89, 182, 0.4);
}

.complete-btn {
  background: linear-gradient(135deg, var(--cyber-neon-green), var(--cyber-neon-blue));
  color: var(--cyber-text-dark);
  border-color: var(--cyber-neon-green);
}

.complete-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(57, 255, 20, 0.4);
}

.next-btn {
  background: linear-gradient(135deg, var(--cyber-neon-blue), var(--cyber-neon-cyan));
  color: var(--cyber-text-dark);
  border-color: var(--cyber-neon-blue);
}

.next-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
}

/* 动画效果 */
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

@keyframes pulse-glow {
  0%, 100% {
    filter: drop-shadow(0 0 5px currentColor);
  }
  50% {
    filter: drop-shadow(0 0 15px currentColor);
  }
}

@keyframes grid-flow {
  0% { opacity: 0.05; }
  50% { opacity: 0.1; }
  100% { opacity: 0.05; }
}

/* 移动端适配 */
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
    width: 60px;
    height: 60px;
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