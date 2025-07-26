<template>
  <div class="mode-switch">
    <button 
      @click="$emit('update:mode', 'chat')" 
      :class="{ active: currentMode === 'chat' }"
      class="mode-btn"
    >
       跟爹妈聊
    </button>
    <button 
      @click="$emit('update:mode', 'direct')" 
      :class="{ active: currentMode === 'direct' }"
      class="mode-btn"
    >
       直接梳理
    </button>
  </div>
</template>

<script setup>
defineProps({
  currentMode: {
    type: String,
    required: true
  }
})

defineEmits(['update:mode'])
</script>

<style scoped>
.mode-switch {
  display: flex;
  gap: 15px;
  margin-bottom: 30px;
  justify-content: center;
}

.mode-btn {
  padding: 15px 25px;
  border: 2px solid var(--cyber-glass-border);
  border-radius: 30px;
  background: var(--cyber-glass);
  color: var(--cyber-text-primary);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(20px);
  box-shadow: var(--cyber-shadow-neon);
  position: relative;
  overflow: hidden;
}

.mode-btn::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, var(--cyber-neon-blue), var(--cyber-neon-purple));
  border-radius: 30px;
  z-index: -1;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.mode-btn:hover {
  border-color: var(--cyber-neon-blue);
  background: rgba(0, 212, 255, 0.2);
  box-shadow: var(--cyber-shadow-glow);
  transform: translateY(-3px);
}

.mode-btn:hover::before {
  opacity: 0.3;
}

.mode-btn.active {
  border-color: var(--cyber-neon-blue);
  background: linear-gradient(135deg, var(--cyber-neon-blue), var(--cyber-neon-purple));
  color: var(--cyber-text-dark);
  box-shadow: 0 0 30px var(--cyber-neon-blue), 0 0 60px var(--cyber-neon-purple);
  animation: cyber-pulse 2s ease-in-out infinite;
}
</style>