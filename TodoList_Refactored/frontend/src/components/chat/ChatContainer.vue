<template>
  <div class="chat-container">
    <ParentSelector 
      :selectedParent="selectedParent"
      @update:selectedParent="$emit('update:selectedParent', $event)"
    />
    
    <div class="chat-messages" ref="chatMessages">
      <div v-if="messages.length === 0" class="welcome-message">
        <div class="ai-avatar"><i class="fas fa-robot"></i></div>
        <div class="message-content">
          <p v-if="selectedParent === 'dad'">
            你说你这孩子，又有什么新想法了？别跟我说又是三分钟热度！做人如做菜要有火候，心比天高命比纸薄可不行啊。
          </p>
          <p v-else>
            哎呀我的傻孩子，又在琢磨什么呢？妈妈都替你着急！你看人家孩子都有明确规划了，这样下去可怎么办啊？
          </p>
        </div>
      </div>
      
      <ChatMessage 
        v-for="(message, index) in messages" 
        :key="index"
        :message="message"
      />
      
      <div v-if="loading" class="message assistant">
        <div class="ai-avatar"><i class="fas fa-robot"></i></div>
        <div class="message-content typing">
          <p>AI思考中...</p>
        </div>
      </div>
    </div>
    
    <div class="chat-input-area">
      <ChatInput 
        v-model="inputValue"
        :loading="loading"
        @send="handleSend"
      />
      
      <div v-if="canGenerateTasks" class="generate-tasks-hint">
        <p>目标已经明确？</p>
        <button @click="$emit('generate-tasks')" class="generate-tasks-btn">
          生成任务计划
        </button>
      </div>
      
      <div v-else-if="messages.length >= 4 && conversationId" class="manual-generate-hint">
        <p>觉得聊得差不多了？</p>
        <button @click="$emit('generate-tasks')" class="manual-generate-btn">
          直接生成任务计划
        </button>
      </div>
      
      <div v-if="messages.length > 0" class="new-chat-hint">
        <button @click="$emit('new-conversation')" class="new-chat-btn">
          开始新对话
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import ParentSelector from './ParentSelector.vue'
import ChatMessage from './ChatMessage.vue'
import ChatInput from './ChatInput.vue'

const props = defineProps({
  selectedParent: {
    type: String,
    required: true
  },
  messages: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  canGenerateTasks: {
    type: Boolean,
    default: false
  },
  conversationId: {
    type: String,
    default: null
  }
})

const emit = defineEmits([
  'update:selectedParent', 
  'send-message', 
  'generate-tasks', 
  'new-conversation'
])

const inputValue = ref('')
const chatMessages = ref(null)

const handleSend = (message) => {
  emit('send-message', message)
}

const scrollToBottom = () => {
  if (chatMessages.value) {
    chatMessages.value.scrollTop = chatMessages.value.scrollHeight
  }
}

// 监听消息变化，自动滚动到底部
watch(() => props.messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
}, { deep: true })
</script>

<style scoped>
.chat-container {
  background: var(--cyber-glass);
  border-radius: 25px;
  box-shadow: var(--cyber-shadow-neon);
  backdrop-filter: blur(25px);
  border: 1px solid var(--cyber-glass-border);
  overflow: hidden;
  margin-bottom: 35px;
  position: relative;
}

.chat-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(0, 212, 255, 0.05) 0%, 
    rgba(176, 38, 255, 0.05) 100%);
  pointer-events: none;
  z-index: 0;
}

.chat-messages {
  max-height: 400px;
  overflow-y: auto;
  padding: 30px;
  padding-bottom: 20px;
  background: rgba(11, 13, 23, 0.3);
  position: relative;
  z-index: 1;
}

.welcome-message {
  display: flex;
  gap: 15px;
  align-items: flex-start;
  margin-bottom: 25px;
  position: relative;
  z-index: 1;
}

.welcome-message .message-content {
  background: var(--cyber-glass);
  border: 1px solid var(--cyber-neon-blue);
  border-radius: 20px;
  padding: 18px 22px;
  color: var(--cyber-text-primary);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
  backdrop-filter: blur(15px);
}

.chat-input-area {
  border-top: 1px solid var(--cyber-glass-border);
  padding: 25px 30px;
  background: var(--cyber-bg-secondary);
  position: relative;
  z-index: 1;
}

.typing {
  opacity: 0.8;
  animation: cyber-pulse 1.5s ease-in-out infinite;
}

.generate-tasks-hint {
  margin-top: 18px;
  padding: 18px;
  background: var(--cyber-glass);
  border: 1px solid var(--cyber-neon-green);
  border-radius: 15px;
  text-align: center;
  backdrop-filter: blur(15px);
  box-shadow: 0 0 20px rgba(57, 255, 20, 0.2);
}

.generate-tasks-hint p {
  margin: 0 0 12px 0;
  color: var(--cyber-text-primary);
  font-weight: 600;
}

.generate-tasks-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, var(--cyber-neon-green), var(--cyber-neon-blue));
  color: var(--cyber-text-dark);
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0 20px rgba(57, 255, 20, 0.4);
}

.generate-tasks-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 30px var(--cyber-neon-green);
}

.manual-generate-hint,
.new-chat-hint {
  margin-top: 15px;
  padding: 15px;
  background: var(--cyber-glass);
  border: 1px solid var(--cyber-glass-border);
  border-radius: 12px;
  text-align: center;
  backdrop-filter: blur(15px);
}

.manual-generate-hint p,
.new-chat-hint p {
  margin: 0 0 10px 0;
  color: var(--cyber-text-secondary);
  font-size: 14px;
}

.manual-generate-btn,
.new-chat-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, var(--cyber-neon-purple), var(--cyber-neon-pink));
  color: var(--cyber-text-dark);
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0 15px rgba(176, 38, 255, 0.3);
}

.manual-generate-btn:hover,
.new-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 25px var(--cyber-neon-purple);
}
</style>