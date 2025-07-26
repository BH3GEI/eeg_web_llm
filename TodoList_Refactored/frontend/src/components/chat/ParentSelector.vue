<template>
  <div class="parent-selection">
    <label>选择你的赛博家长：</label>
    <div class="parent-buttons">
      <button 
        @click="$emit('update:selectedParent', 'dad')" 
        :class="{ active: selectedParent === 'dad' }" 
        class="parent-btn"
      >
         唠叨老爸
      </button>
      <button 
        @click="$emit('update:selectedParent', 'mom')" 
        :class="{ active: selectedParent === 'mom' }" 
        class="parent-btn"
      >
         关怀老妈
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  selectedParent: {
    type: String,
    required: true
  }
})

defineEmits(['update:selectedParent'])
</script>

<style scoped>
.parent-selection {
  padding: 25px 30px;
  border-bottom: 1px solid var(--cyber-glass-border);
  background: var(--cyber-bg-secondary);
  position: relative;
  z-index: 1;
}

.parent-selection label {
  display: block;
  color: var(--cyber-text-primary);
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 15px;
  text-shadow: 0 0 10px var(--cyber-neon-blue);
}

.parent-buttons {
  display: flex;
  gap: 15px;
}

.parent-btn {
  padding: 12px 20px;
  border: 2px solid var(--cyber-glass-border);
  border-radius: 25px;
  background: var(--cyber-glass);
  color: var(--cyber-text-primary);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  backdrop-filter: blur(15px);
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.3);
  position: relative;
  overflow: hidden;
}

.parent-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.3), transparent);
  transition: left 0.5s ease;
}

.parent-btn:hover {
  border-color: var(--cyber-neon-blue);
  background: rgba(0, 212, 255, 0.2);
  box-shadow: 0 0 25px var(--cyber-neon-blue);
  transform: translateY(-2px);
}

.parent-btn:hover::before {
  left: 100%;
}

.parent-btn.active {
  border-color: var(--cyber-neon-blue);
  background: linear-gradient(135deg, var(--cyber-neon-blue), var(--cyber-neon-purple));
  color: var(--cyber-text-dark);
  box-shadow: 0 0 30px var(--cyber-neon-blue);
}
</style>