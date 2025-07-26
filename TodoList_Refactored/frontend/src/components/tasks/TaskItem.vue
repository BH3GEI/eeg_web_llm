<template>
  <div class="task-item" :class="{ completed: task.completed }">
    <div class="task-checkbox">
      <input
        type="checkbox"
        :id="`task-${task.id}`"
        v-model="task.completed"
        @change="$emit('update-task', task)"
      />
      <label :for="`task-${task.id}`"></label>
    </div>
    <div class="task-content">
      <h4>{{ task.title }}</h4>
      <p v-if="task.description">{{ task.description }}</p>
    </div>
    <div class="task-actions">
      <button class="delete-task-btn" @click="$emit('delete-task', task.id)"></button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  task: {
    type: Object,
    required: true
  }
})

defineEmits(['update-task', 'delete-task'])
</script>

<style scoped>
.task-item {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  padding: 20px 30px;
  border-bottom: 1px solid var(--cyber-glass-border);
  transition: all 0.3s ease;
  background: var(--cyber-glass);
  backdrop-filter: blur(15px);
  position: relative;
}

.task-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(0, 212, 255, 0.05) 0%, 
    rgba(176, 38, 255, 0.03) 100%);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.task-item:last-child {
  border-bottom: none;
}

.task-item:hover {
  background: rgba(0, 212, 255, 0.1);
  transform: translateX(8px);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
}

.task-item:hover::before {
  opacity: 1;
}

.task-item.completed {
  opacity: 0.6;
  transform: none;
}

.task-item.completed .task-content h4 {
  text-decoration: line-through;
  color: var(--cyber-text-muted);
}

.task-checkbox {
  position: relative;
  margin-top: 3px;
}

.task-checkbox input[type="checkbox"] {
  opacity: 0;
  position: absolute;
}

.task-checkbox label {
  display: block;
  width: 24px;
  height: 24px;
  border: 2px solid var(--cyber-glass-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--cyber-glass);
  backdrop-filter: blur(15px);
  position: relative;
}

.task-checkbox label::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, var(--cyber-neon-blue), var(--cyber-neon-purple));
  border-radius: 8px;
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: -1;
}

.task-checkbox input:checked + label {
  background: linear-gradient(135deg, var(--cyber-neon-blue), var(--cyber-neon-purple));
  border-color: var(--cyber-neon-blue);
  box-shadow: 0 0 15px var(--cyber-neon-blue);
}

.task-checkbox input:checked + label::before {
  opacity: 1;
}

.task-checkbox input:checked + label::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--cyber-text-dark);
  font-weight: bold;
  font-size: 14px;
}

.task-content {
  flex: 1;
  position: relative;
  z-index: 1;
}

.task-content h4 {
  font-size: 1.1rem;
  color: var(--cyber-text-primary);
  margin-bottom: 8px;
  font-weight: 500;
  line-height: 1.4;
  text-shadow: 0 0 5px rgba(0, 212, 255, 0.3);
}

.task-content p {
  color: var(--cyber-text-secondary);
  font-size: 0.9rem;
  line-height: 1.5;
}

.task-actions {
  display: flex;
  gap: 10px;
  position: relative;
  z-index: 1;
}

.delete-task-btn {
  padding: 10px;
  background: var(--cyber-glass);
  border: 1px solid rgba(255, 20, 147, 0.3);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
  color: var(--cyber-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(15px);
}

.delete-task-btn:hover {
  background: rgba(255, 20, 147, 0.2);
  border-color: var(--cyber-neon-pink);
  color: var(--cyber-neon-pink);
  box-shadow: 0 0 15px rgba(255, 20, 147, 0.3);
  transform: scale(1.1);
}

.delete-task-btn::before {
  content: '×';
  font-size: 16px;
  font-weight: bold;
}
</style>