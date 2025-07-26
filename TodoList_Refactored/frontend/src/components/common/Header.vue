<template>
  <header class="app-header">
    <h1> CYBERPARENTS</h1>
    <p>您最好的赛博爹妈</p>
  </header>
</template>

<script setup>
// 头部组件，纯展示性
</script>

<style scoped>
.app-header {
  text-align: center;
  color: var(--cyber-text-primary);
  margin-bottom: 50px;
  text-shadow: var(--cyber-shadow-neon);
}

.app-header h1 {
  font-size: 3.2rem;
  margin-bottom: 15px;
  font-weight: 900;
  color: var(--cyber-neon-cyan);
  text-shadow: 0 0 20px var(--cyber-neon-cyan), 0 0 40px var(--cyber-neon-cyan);
  letter-spacing: 4px;
  font-family: 'Orbitron', 'Monaco', 'Courier New', monospace;
  animation: neon-text-glow 3s ease-in-out infinite;
  position: relative;
}

.app-header h1::before {
  content: ' CYBERPARENTS ';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  color: var(--cyber-neon-purple);
  text-shadow: 0 0 20px var(--cyber-neon-purple);
  opacity: 0.3;
  animation: neon-text-glow 3s ease-in-out infinite reverse;
}

.app-header p {
  font-size: 1.2rem;
  color: var(--cyber-text-secondary);
  font-weight: 500;
  opacity: 0.9;
  text-shadow: 0 0 10px var(--cyber-neon-cyan);
}

@media (max-width: 768px) {
  .app-header {
    margin-bottom: 25px;
  }
  
  .app-header h1 {
    font-size: 1.8rem;
    margin-bottom: 5px;
  }
  
  .app-header p {
    font-size: 0.9rem;
  }
}
</style>