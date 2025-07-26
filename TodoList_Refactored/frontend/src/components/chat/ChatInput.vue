<template>
  <div class="chat-input-container">
    <textarea
      v-model="inputValue"
      placeholder="跟爹妈唠唠..."
      :disabled="loading || isInCall"
      @keydown="handleKeydown"
      class="chat-input"
      rows="2"
    ></textarea>
    
    <!-- 通话按钮 -->
    <button 
      v-if="isSupported"
      @click="toggleVoiceCall" 
      :disabled="loading"
      class="voice-btn"
      :class="{ 
        'recording': callStatus === 'user_speaking', 
        'speaking': callStatus === 'ai_speaking',
        'in-call': isInCall,
        'listening': callStatus === 'listening'
      }"
    >
      <span v-if="callStatus === 'user_speaking'"><i class="fas fa-microphone-alt"></i></span>
      <span v-else-if="callStatus === 'ai_speaking'"><i class="fas fa-volume-up"></i></span>
      <span v-else-if="callStatus === 'listening'"><i class="fas fa-ear-listen"></i></span>
      <span v-else-if="isInCall"><i class="fas fa-phone-slash"></i></span>
      <span v-else><i class="fas fa-phone"></i></span>
    </button>
    
    <button 
      @click="handleSend" 
      :disabled="!inputValue.trim() || loading || isInCall"
      class="send-btn"
    >
      <span v-if="loading"><i class="fas fa-circle-notch fa-spin"></i></span>
      <span v-else><i class="fas fa-paper-plane"></i></span>
    </button>
  </div>
  
  <!-- 语音状态提示 -->
  <div v-if="isInCall" class="voice-status">
    <div v-if="callStatus === 'user_speaking'" class="status-recording">
      <i class="fas fa-microphone-alt pulse"></i>
      <span>正在听你说话...</span>
      <div class="transcript" v-if="currentTranscript">{{ currentTranscript }}</div>
    </div>
    <div v-else-if="callStatus === 'ai_speaking'" class="status-speaking">
      <i class="fas fa-volume-up pulse"></i>
      <span>{{ selectedParent === 'dad' ? '老爸' : '老妈' }}正在说话...</span>
    </div>
    <div v-else-if="callStatus === 'listening'" class="status-listening">
      <i class="fas fa-ear-listen pulse"></i>
      <span>正在等待你说话... (1.2秒静音后AI会回应)</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useVoiceChat } from '../../composables/useVoiceChat.js'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  },
  selectedParent: {
    type: String,
    default: 'dad'
  }
})

const emit = defineEmits(['update:modelValue', 'send', 'voice-message'])

const inputValue = ref(props.modelValue)

// 语音功能
const {
  isRecording,
  isSpeaking,
  isSupported,
  currentTranscript,
  isInCall,
  callStatus,
  startCall,
  stopCall
} = useVoiceChat()

watch(() => props.modelValue, (newVal) => {
  inputValue.value = newVal
})

watch(inputValue, (newVal) => {
  emit('update:modelValue', newVal)
})

const handleKeydown = (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault()
    handleSend()
  }
}

const handleSend = () => {
  if (inputValue.value.trim() && !props.loading) {
    emit('send', inputValue.value.trim())
    inputValue.value = ''
  }
}

// 语音通话处理
const toggleVoiceCall = async () => {
  try {
    if (isInCall.value) {
      // 结束通话
      stopCall()
    } else {
      // 开始通话
      startCall((transcript) => {
        // 静音超时后，自动发送识别的内容
        emit('voice-message', transcript)
      })
    }
  } catch (error) {
    console.error('语音通话错误:', error)
    alert('语音功能暂时不可用：' + error.message)
  }
}
</script>

<style scoped>
.chat-input-container {
  display: flex;
  gap: 15px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  border: 2px solid var(--cyber-glass-border);
  border-radius: 15px;
  padding: 15px 18px;
  font-size: 15px;
  resize: none;
  font-family: inherit;
  background: var(--cyber-glass);
  color: var(--cyber-text-primary);
  transition: all 0.3s ease;
  backdrop-filter: blur(15px);
}

.chat-input::placeholder {
  color: var(--cyber-text-muted);
}

.chat-input:focus {
  outline: none;
  border-color: var(--cyber-neon-blue);
  background: rgba(0, 212, 255, 0.1);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

.voice-btn {
  width: 50px;
  height: 50px;
  border: none;
  border-radius: 15px;
  background: linear-gradient(135deg, var(--cyber-neon-green), var(--cyber-neon-cyan));
  color: var(--cyber-text-dark);
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  flex-shrink: 0;
  box-shadow: 0 0 20px rgba(57, 255, 20, 0.4);
}

.voice-btn.recording {
  background: linear-gradient(135deg, #ff4757, #ff6b81);
  animation: pulse-red 1.5s infinite;
  box-shadow: 0 0 30px rgba(255, 71, 87, 0.6);
}

.voice-btn.speaking {
  background: linear-gradient(135deg, var(--cyber-neon-purple), var(--cyber-neon-pink));
  animation: pulse-purple 1.5s infinite;
  box-shadow: 0 0 30px rgba(176, 38, 255, 0.6);
}

.voice-btn:hover:not(:disabled):not(.in-call) {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 0 30px var(--cyber-neon-green), 0 0 50px var(--cyber-neon-cyan);
}

.voice-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn {
  width: 50px;
  height: 50px;
  border: none;
  border-radius: 15px;
  background: linear-gradient(135deg, var(--cyber-neon-blue), var(--cyber-neon-purple));
  color: var(--cyber-text-dark);
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  flex-shrink: 0;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.4);
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 0 30px var(--cyber-neon-blue), 0 0 50px var(--cyber-neon-purple);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 语音状态提示 */
.voice-status {
  margin-top: 15px;
  padding: 15px;
  background: var(--cyber-glass);
  border: 1px solid var(--cyber-glass-border);
  border-radius: 12px;
  backdrop-filter: blur(15px);
  text-align: center;
}

.status-recording {
  color: #ff4757;
}

.status-speaking {
  color: var(--cyber-neon-purple);
}

.voice-status span {
  font-size: 14px;
  font-weight: 600;
  margin-left: 8px;
}

.transcript {
  margin-top: 10px;
  padding: 8px 12px;
  background: rgba(0, 255, 255, 0.1);
  border-radius: 8px;
  color: var(--cyber-text-primary);
  font-size: 13px;
  border-left: 3px solid var(--cyber-neon-cyan);
}

.pulse {
  animation: pulse-scale 1.5s infinite;
}

@keyframes pulse-red {
  0%, 100% { box-shadow: 0 0 20px rgba(255, 71, 87, 0.4); }
  50% { box-shadow: 0 0 40px rgba(255, 71, 87, 0.8); }
}

@keyframes pulse-purple {
  0%, 100% { box-shadow: 0 0 20px rgba(176, 38, 255, 0.4); }
  50% { box-shadow: 0 0 40px rgba(176, 38, 255, 0.8); }
}

.voice-btn.listening {
  background: linear-gradient(135deg, var(--cyber-neon-cyan), var(--cyber-neon-blue));
  animation: pulse-cyan 2s infinite;
  box-shadow: 0 0 30px rgba(0, 255, 255, 0.6);
}

.status-listening {
  color: var(--cyber-neon-cyan);
}

@keyframes pulse-cyan {
  0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 255, 0.4); }
  50% { box-shadow: 0 0 40px rgba(0, 255, 255, 0.8); }
}

@keyframes pulse-scale {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
</style>