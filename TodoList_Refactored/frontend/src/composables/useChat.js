import { ref, computed } from 'vue'
import axios from 'axios'

export function useChat() {
  const chatMessages = ref([])
  const chatLoading = ref(false)
  const sessionId = ref(null)
  const conversationId = ref(null)
  const canGenerateTasks = ref(false)
  const selectedParent = ref('dad')

  // 初始化会话ID
  const initSession = () => {
    sessionId.value = localStorage.getItem('smart_todo_session_id') || 
                     'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    localStorage.setItem('smart_todo_session_id', sessionId.value)
  }

  // 加载对话历史
  const loadChatHistory = async () => {
    try {
      const response = await axios.get(`/api/conversations/${sessionId.value}`)
      const data = response.data
      
      if (data.messages && data.messages.length > 0) {
        // 过滤掉欢迎消息
        chatMessages.value = data.messages.filter(msg => 
          !(msg.role === 'assistant' && msg.content.includes('你好！我是你的AI助手'))
        )
        conversationId.value = data.conversation_id
        canGenerateTasks.value = data.can_generate_tasks
      }
    } catch (error) {
      console.error('加载对话历史失败:', error)
    }
  }

  // 发送消息
  const sendMessage = async (message) => {
    if (!message.trim()) return

    chatLoading.value = true
    
    // 添加用户消息
    chatMessages.value.push({
      role: 'user',
      content: message
    })
    
    try {
      const response = await axios.post('/api/chat', {
        session_id: sessionId.value,
        message: message,
        parent_type: selectedParent.value
      })
      
      // 添加AI回复
      chatMessages.value.push({
        role: 'assistant',
        content: response.data.message
      })
      
      conversationId.value = response.data.conversation_id
      canGenerateTasks.value = response.data.can_generate_tasks
      
    } catch (error) {
      console.error('发送消息失败:', error)
      throw error
    } finally {
      chatLoading.value = false
    }
  }

  // 生成任务
  const generateTasks = async () => {
    if (!conversationId.value) return null
    
    chatLoading.value = true
    try {
      const response = await axios.post(`/api/generate-tasks/${conversationId.value}`)
      canGenerateTasks.value = false
      return response.data.goal
    } catch (error) {
      console.error('生成任务失败:', error)
      throw error
    } finally {
      chatLoading.value = false
    }
  }

  // 开始新对话
  const startNewConversation = () => {
    chatMessages.value = []
    conversationId.value = null
    canGenerateTasks.value = false
    
    // 生成新的会话ID
    sessionId.value = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    localStorage.setItem('smart_todo_session_id', sessionId.value)
  }

  return {
    // 状态
    chatMessages,
    chatLoading,
    sessionId,
    conversationId,
    canGenerateTasks,
    selectedParent,
    
    // 方法
    initSession,
    loadChatHistory,
    sendMessage,
    generateTasks,
    startNewConversation
  }
}