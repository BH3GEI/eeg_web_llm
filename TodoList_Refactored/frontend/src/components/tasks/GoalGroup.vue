<template>
  <div class="goal-group">
    <div class="goal-header" :class="{ completed: goal.completed }">
      <div class="goal-info">
        <h3>{{ goal.title }}</h3>
        <p v-if="goal.description">{{ goal.description }}</p>
        <div class="goal-progress">
          <span class="progress-text">
            进度: {{ completedTasks }}/{{ totalTasks }}
          </span>
          <div class="mini-progress-bar">
            <div 
              class="mini-progress-fill" 
              :style="{ width: `${progressPercentage}%` }"
            ></div>
          </div>
        </div>
      </div>
      <div class="goal-actions">
        <button class="focus-goal-btn" @click="$emit('start-focus', goal)" title="进入专注模式">
          专注
        </button>
        <button class="delete-goal-btn" @click="$emit('delete-goal', goal.id)"></button>
      </div>
    </div>
    
    <div class="tasks-list" v-if="goal.tasks && goal.tasks.length > 0">
      <TaskItem
        v-for="task in goal.tasks"
        :key="task.id"
        :task="task"
        @update-task="$emit('update-task', $event)"
        @delete-task="$emit('delete-task', goal.id, $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import TaskItem from './TaskItem.vue'

const props = defineProps({
  goal: {
    type: Object,
    required: true
  }
})

defineEmits(['update-task', 'delete-task', 'delete-goal', 'start-focus'])

const completedTasks = computed(() => {
  return props.goal.tasks?.filter(task => task.completed).length || 0
})

const totalTasks = computed(() => {
  return props.goal.tasks?.length || 0
})

const progressPercentage = computed(() => {
  return totalTasks.value > 0 ? Math.round((completedTasks.value / totalTasks.value) * 100) : 0
})
</script>

<style scoped>
.goal-group {
  margin-bottom: 40px;
  border: 1px solid var(--cyber-glass-border);
  border-radius: 20px;
  overflow: hidden;
  background: var(--cyber-glass);
  backdrop-filter: blur(15px);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.1);
  position: relative;
  z-index: 1;
}

.goal-group:last-child {
  margin-bottom: 0;
}

.goal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 25px 30px;
  background: var(--cyber-bg-secondary);
  border-bottom: 1px solid var(--cyber-glass-border);
  transition: all 0.3s ease;
  position: relative;
}

.goal-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(0, 212, 255, 0.1) 0%, 
    rgba(176, 38, 255, 0.05) 100%);
  pointer-events: none;
}

.goal-header.completed {
  opacity: 0.7;
  background: rgba(57, 255, 20, 0.1);
}

.goal-info {
  flex: 1;
  position: relative;
  z-index: 1;
}

.goal-info h3 {
  font-size: 1.4rem;
  color: var(--cyber-text-primary);
  margin-bottom: 10px;
  font-weight: 600;
  text-shadow: 0 0 10px var(--cyber-neon-blue);
}

.goal-info p {
  color: var(--cyber-text-secondary);
  font-size: 0.95rem;
  margin-bottom: 15px;
  line-height: 1.5;
}

.goal-progress {
  display: flex;
  align-items: center;
  gap: 15px;
}

.progress-text {
  font-size: 0.9rem;
  color: var(--cyber-text-primary);
  font-weight: 600;
  white-space: nowrap;
}

.mini-progress-bar {
  flex: 1;
  height: 6px;
  background: rgba(0, 212, 255, 0.2);
  border-radius: 3px;
  overflow: hidden;
}

.mini-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--cyber-neon-blue), var(--cyber-neon-purple));
  transition: width 0.4s ease;
  box-shadow: 0 0 10px var(--cyber-neon-blue);
}

.goal-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  position: relative;
  z-index: 1;
}

.focus-goal-btn {
  padding: 12px 20px;
  background: linear-gradient(135deg, var(--cyber-neon-green), var(--cyber-neon-blue));
  color: var(--cyber-text-dark);
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  box-shadow: 0 0 15px rgba(57, 255, 20, 0.3);
}

.focus-goal-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 25px var(--cyber-neon-green);
}

.delete-goal-btn {
  padding: 12px;
  background: var(--cyber-glass);
  border: 1px solid rgba(255, 20, 147, 0.3);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 16px;
  color: var(--cyber-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
}

.delete-goal-btn:hover {
  background: rgba(255, 20, 147, 0.2);
  border-color: var(--cyber-neon-pink);
  color: var(--cyber-neon-pink);
  box-shadow: 0 0 15px rgba(255, 20, 147, 0.3);
}

.delete-goal-btn::before {
  content: '×';
  font-size: 18px;
  font-weight: bold;
}

.tasks-list {
  padding: 0;
  position: relative;
  z-index: 1;
}
</style>