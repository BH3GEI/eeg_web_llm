import { ref, computed } from 'vue'
import axios from 'axios'

export function useTasks() {
  const goals = ref([])
  const loading = ref(false)

  // 计算所有任务
  const allTasks = computed(() => {
    return goals.value.flatMap(goal => goal.tasks || [])
  })

  // 计算完成的任务数量
  const completedCount = computed(() => {
    return allTasks.value.filter(task => task.completed).length
  })

  // 计算总任务数量
  const totalTaskCount = computed(() => {
    return allTasks.value.length
  })

  // 计算完成率
  const completionRate = computed(() => {
    return totalTaskCount.value === 0 ? 0 : Math.round((completedCount.value / totalTaskCount.value) * 100)
  })

  // 加载目标列表
  const loadGoals = async () => {
    try {
      const response = await axios.get('/api/goals')
      goals.value = response.data
    } catch (error) {
      console.error('加载目标失败:', error)
    }
  }

  // 分解目标
  const breakdownGoal = async (goalText) => {
    if (!goalText.trim()) return

    loading.value = true
    try {
      const response = await axios.post('/api/breakdown', {
        goal: goalText.trim()
      })
      
      // 添加新目标到列表顶部
      goals.value.unshift(response.data.goal)
      return response.data.goal
    } catch (error) {
      console.error('分解任务失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 更新任务状态
  const updateTask = async (task) => {
    try {
      await axios.put(`/api/tasks/${task.id}`, task)
      if (task.completed) {
        // 重新加载数据以更新目标完成状态
        await loadGoals()
      }
    } catch (error) {
      console.error('更新任务失败:', error)
      // 回滚状态
      task.completed = !task.completed
      throw error
    }
  }

  // 删除任务
  const deleteTask = async (goalId, taskId) => {
    try {
      await axios.delete(`/api/tasks/${taskId}`)
      // 从前端数据中移除任务
      const goal = goals.value.find(g => g.id === goalId)
      if (goal) {
        goal.tasks = goal.tasks.filter(task => task.id !== taskId)
      }
    } catch (error) {
      console.error('删除任务失败:', error)
      throw error
    }
  }

  // 删除目标
  const deleteGoal = async (goalId) => {
    try {
      await axios.delete(`/api/goals/${goalId}`)
      goals.value = goals.value.filter(goal => goal.id !== goalId)
    } catch (error) {
      console.error('删除目标失败:', error)
      throw error
    }
  }

  // 添加从聊天生成的目标
  const addGoalFromChat = (goal) => {
    goals.value.unshift(goal)
  }

  return {
    // 状态
    goals,
    loading,
    
    // 计算属性
    allTasks,
    completedCount,
    totalTaskCount,
    completionRate,
    
    // 方法
    loadGoals,
    breakdownGoal,
    updateTask,
    deleteTask,
    deleteGoal,
    addGoalFromChat
  }
}