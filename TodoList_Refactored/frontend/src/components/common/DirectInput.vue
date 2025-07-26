<template>
  <div class="goal-input">
    <div class="input-container">
      <textarea
        v-model="goalInput"
        placeholder="唠唠，我会帮你分解成可执行的小任务..."
        :disabled="loading"
        @keydown="handleKeydown"
        rows="3"
      ></textarea>
      <button @click="handleBreakdown" :disabled="!goalInput.trim() || loading">
        <span v-if="loading"><i class="fas fa-circle-notch fa-spin"></i> AI思考中...</span>
        <span v-else><i class="fas fa-magic"></i> 智能分解</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['breakdown-goal'])

const goalInput = ref('')

const handleKeydown = (event) => {
  // Ctrl/Cmd + Enter 快速提交
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault()
    handleBreakdown()
  }
}

const handleBreakdown = () => {
  if (!goalInput.value.trim()) return
  emit('breakdown-goal', goalInput.value.trim())
  goalInput.value = ''
}
</script>

<style scoped>
.goal-input {
  background: var(--cyber-glass);
  border-radius: 25px;
  padding: 40px;
  margin-bottom: 40px;
  box-shadow: var(--cyber-shadow-neon);
  backdrop-filter: blur(25px);
  border: 1px solid var(--cyber-glass-border);
  position: relative;
}

.goal-input::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(0, 212, 255, 0.05) 0%, 
    rgba(176, 38, 255, 0.05) 100%);
  border-radius: 25px;
  pointer-events: none;
}

.input-container {
  display: flex;
  gap: 25px;
  align-items: flex-end;
  position: relative;
  z-index: 1;
}

.input-container textarea {
  flex: 1;
  min-height: 100px;
  padding: 20px;
  border: 2px solid var(--cyber-glass-border);
  border-radius: 20px;
  font-size: 16px;
  resize: vertical;
  font-family: inherit;
  transition: all 0.3s ease;
  background: var(--cyber-glass);
  color: var(--cyber-text-primary);
  backdrop-filter: blur(15px);
}

.input-container textarea::placeholder {
  color: var(--cyber-text-muted);
}

.input-container textarea:focus {
  outline: none;
  border-color: var(--cyber-neon-blue);
  background: rgba(0, 212, 255, 0.1);
  box-shadow: 0 0 25px rgba(0, 212, 255, 0.3);
}

.input-container button {
  padding: 20px 32px;
  background: linear-gradient(135deg, var(--cyber-neon-blue), var(--cyber-neon-purple));
  color: var(--cyber-text-dark);
  border: none;
  border-radius: 20px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  box-shadow: 0 0 25px rgba(0, 212, 255, 0.4);
}

.input-container button:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 0 35px var(--cyber-neon-blue), 0 0 55px var(--cyber-neon-purple);
  background: linear-gradient(135deg, var(--cyber-neon-purple), var(--cyber-neon-blue));
}

.input-container button:active:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 0 20px var(--cyber-neon-blue);
}

.input-container button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 移动端适配 */
@media (max-width: 768px) {
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
    font-size: 16px;
    border-radius: 8px;
  }
  
  .input-container button {
    align-self: stretch;
    padding: 16px 20px;
    font-size: 16px;
    border-radius: 8px;
    min-height: 50px;
  }
}
</style>