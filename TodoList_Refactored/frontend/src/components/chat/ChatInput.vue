<template>
  <div class="chat-input-container">
    <textarea
      v-model="inputValue"
      placeholder="跟爹妈唠唠..."
      :disabled="loading"
      @keydown="handleKeydown"
      class="chat-input"
      rows="2"
    ></textarea>
    <button 
      @click="handleSend" 
      :disabled="!inputValue.trim() || loading"
      class="send-btn"
    >
      <span v-if="loading"><i class="fas fa-circle-notch fa-spin"></i></span>
      <span v-else><i class="fas fa-paper-plane"></i></span>
    </button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'send'])

const inputValue = ref(props.modelValue)

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
</style>