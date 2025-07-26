<template>
  <div 
    :class="['message', message.role]"
  >
    <div v-if="message.role === 'assistant'" class="ai-avatar">
      <i class="fas fa-robot"></i>
    </div>
    <div class="message-content">
      <p>{{ message.content }}</p>
    </div>
    <div v-if="message.role === 'user'" class="user-avatar">
      <i class="fas fa-user"></i>
    </div>
  </div>
</template>

<script setup>
defineProps({
  message: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.message {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  align-items: flex-start;
  position: relative;
  z-index: 1;
}

.message.user {
  flex-direction: row-reverse;
}

.ai-avatar, .user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 3px;
  border: 2px solid var(--cyber-neon-blue);
  box-shadow: 0 0 20px var(--cyber-neon-blue);
  position: relative;
  overflow: hidden;
}

.ai-avatar::before,
.user-avatar::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: conic-gradient(from 0deg, var(--cyber-neon-blue), var(--cyber-neon-purple), var(--cyber-neon-green), var(--cyber-neon-blue));
  border-radius: 50%;
  z-index: -1;
  animation: spin 3s linear infinite;
}

.ai-avatar {
  background: linear-gradient(135deg, var(--cyber-neon-blue), var(--cyber-neon-purple));
  color: var(--cyber-text-dark);
  border: 2px solid var(--cyber-neon-blue);
  box-shadow: 0 0 25px var(--cyber-neon-blue);
}

.user-avatar {
  background: linear-gradient(135deg, var(--cyber-neon-purple), var(--cyber-neon-pink));
  color: var(--cyber-text-primary);
  border: 2px solid var(--cyber-neon-purple);
  box-shadow: 0 0 25px var(--cyber-neon-purple);
}

.message-content {
  max-width: 75%;
  background: var(--cyber-glass);
  border: 1px solid var(--cyber-glass-border);
  border-radius: 20px;
  padding: 15px 20px;
  word-wrap: break-word;
  color: var(--cyber-text-primary);
  backdrop-filter: blur(15px);
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
  position: relative;
}

.message-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(0, 212, 255, 0.1) 0%, 
    rgba(176, 38, 255, 0.05) 100%);
  border-radius: 20px;
  pointer-events: none;
}

.message.user .message-content {
  background: linear-gradient(135deg, var(--cyber-neon-purple), var(--cyber-neon-pink));
  color: var(--cyber-text-dark);
  border-color: var(--cyber-neon-purple);
  box-shadow: 0 0 20px rgba(176, 38, 255, 0.4);
}

.message.assistant .message-content {
  background: var(--cyber-glass);
  border-color: var(--cyber-glass-border);
}

.message-content p {
  margin: 0;
  line-height: 1.6;
  font-size: 15px;
  position: relative;
  z-index: 1;
}
</style>