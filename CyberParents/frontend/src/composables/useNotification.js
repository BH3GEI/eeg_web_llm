/**
 * 通知系统 Composable
 * 提供统一的通知管理功能，支持赛博朋克风格
 */

export function useNotification() {
  const showNotification = (message, type = 'success') => {
    // 移动端友好的通知实现
    const notification = document.createElement('div')
    notification.textContent = message
    notification.className = 'notification'
    
    const isMobile = window.innerWidth <= 768
    
    // 赛博朋克风格的通知样式
    const styles = {
      success: 'linear-gradient(135deg, #00FFFF, #9B59B6)',
      error: 'linear-gradient(135deg, #FF69B4, #c2998a)',
      warning: 'linear-gradient(135deg, #FFD700, #FF8C00)'
    }
    
    notification.style.cssText = `
      position: fixed;
      ${isMobile ? 'bottom: 20px; right: 15px; left: 15px;' : 'bottom: 30px; left: 50%; transform: translateX(-50%);'}
      padding: ${isMobile ? '14px 16px' : '12px 20px'};
      background: ${styles[type] || styles.success};
      color: #000000;
      border-radius: ${isMobile ? '12px' : '10px'};
      z-index: 1000;
      font-size: ${isMobile ? '14px' : '16px'};
      font-weight: 600;
      box-shadow: 0 0 20px rgba(0, 255, 255, 0.4), 0 4px 20px rgba(0,0,0,0.15);
      animation: slideInFromBottom 0.3s ease-out;
      text-align: center;
      max-width: ${isMobile ? 'auto' : '400px'};
      backdrop-filter: blur(10px);
      border: 1px solid rgba(0, 255, 255, 0.3);
      text-shadow: 0 0 5px rgba(0, 255, 255, 0.3);
    `
    
    document.body.appendChild(notification)
    
    // 移动端更短的显示时间
    const duration = isMobile ? 2500 : 3000
    setTimeout(() => {
      notification.style.animation = 'slideOutToBottom 0.3s ease-out'
      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove()
        }
      }, 300)
    }, duration)
  }

  return {
    showNotification
  }
}