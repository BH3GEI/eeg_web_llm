import { ref, computed } from 'vue'

export function useVoiceChat() {
  const isRecording = ref(false)
  const isSpeaking = ref(false)
  const isInCall = ref(false)  // 通话状态
  const recognition = ref(null)
  const synthesis = ref(null)
  const isSupported = ref(false)
  const currentTranscript = ref('')
  const finalTranscript = ref('')
  
  // 通话相关状态
  const silenceTimer = ref(null)
  const callCallback = ref(null)
  const SILENCE_TIMEOUT = 1200 // 1.2秒静音后触发
  const lastSpeechTime = ref(0) // 最后说话时间
  const MIN_SPEECH_LENGTH = 300 // 最少说话300ms才触发
  
  // 检查浏览器支持
  const checkSupport = () => {
    const speechSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window
    const synthesisSupported = 'speechSynthesis' in window
    isSupported.value = speechSupported && synthesisSupported
    return isSupported.value
  }

  // 重置静音计时器
  const resetSilenceTimer = () => {
    if (silenceTimer.value) {
      clearTimeout(silenceTimer.value)
      silenceTimer.value = null
    }
  }

  // 启动静音计时器
  const startSilenceTimer = () => {
    resetSilenceTimer()
    
    // 只有说话时间足够长才启动计时器
    const speechDuration = Date.now() - lastSpeechTime.value
    if (speechDuration < MIN_SPEECH_LENGTH) {
      return
    }
    
    silenceTimer.value = setTimeout(() => {
      if (finalTranscript.value.trim() && callCallback.value) {
        // 有内容且静音超时，发送给LLM
        console.log('静音超时，发送:', finalTranscript.value.trim())
        callCallback.value(finalTranscript.value.trim())
        finalTranscript.value = ''
        currentTranscript.value = ''
      }
    }, SILENCE_TIMEOUT)
  }

  // 初始化连续语音识别
  const initContinuousRecognition = () => {
    if (!checkSupport()) return false

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    recognition.value = new SpeechRecognition()
    
    // 配置连续识别
    recognition.value.lang = 'zh-CN'
    recognition.value.continuous = true  // 连续识别
    recognition.value.interimResults = true  // 实时结果
    recognition.value.maxAlternatives = 1

    // 识别事件监听
    recognition.value.onstart = () => {
      isRecording.value = true
      console.log('开始连续语音识别')
    }

    recognition.value.onresult = (event) => {
      let interimTranscript = ''
      let finalText = ''
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalText += transcript
        } else {
          interimTranscript += transcript
        }
      }
      
      // 记录说话时间
      if (interimTranscript.trim() || finalText.trim()) {
        lastSpeechTime.value = Date.now()
      }
      
      // 更新显示
      if (finalText) {
        finalTranscript.value += finalText
        currentTranscript.value = finalTranscript.value + interimTranscript
        
        // 有最终结果，重新启动静音计时器
        startSilenceTimer()
      } else {
        // 只有临时结果
        currentTranscript.value = finalTranscript.value + interimTranscript
        
        // 如果有内容在说话，暂停静音计时器，但记录说话时间
        if (interimTranscript.trim()) {
          resetSilenceTimer()
        }
      }
    }

    recognition.value.onend = () => {
      if (isInCall.value) {
        // 通话中自动重启识别
        setTimeout(() => {
          if (isInCall.value && recognition.value) {
            try {
              recognition.value.start()
            } catch (e) {
              console.log('重启识别失败，可能正在运行')
            }
          }
        }, 100)
      } else {
        isRecording.value = false
      }
    }

    recognition.value.onerror = (event) => {
      console.error('语音识别错误:', event.error)
      if (event.error === 'not-allowed') {
        alert('请允许麦克风权限')
        stopCall()
      }
    }

    return true
  }

  // 初始化语音合成
  const initSynthesis = () => {
    if (!checkSupport()) return false
    synthesis.value = window.speechSynthesis
    return true
  }

  // 开始语音通话
  const startCall = (messageCallback) => {
    if (!initContinuousRecognition()) {
      throw new Error('浏览器不支持语音识别')
    }
    
    callCallback.value = messageCallback
    isInCall.value = true
    currentTranscript.value = ''
    finalTranscript.value = ''
    
    // 停止当前播放
    if (synthesis.value) {
      synthesis.value.cancel()
      isSpeaking.value = false
    }
    
    try {
      recognition.value.start()
    } catch (e) {
      console.log('识别可能已在运行')
    }
  }

  // 停止语音通话
  const stopCall = () => {
    isInCall.value = false
    isRecording.value = false
    resetSilenceTimer()
    
    if (recognition.value) {
      recognition.value.stop()
    }
    
    if (synthesis.value) {
      synthesis.value.cancel()
      isSpeaking.value = false
    }
    
    callCallback.value = null
    currentTranscript.value = ''
    finalTranscript.value = ''
  }

  // 语音合成（通话中自动管理状态）
  const speak = (text, voiceType = 'mom') => {
    return new Promise((resolve, reject) => {
      if (!synthesis.value && !initSynthesis()) {
        reject(new Error('浏览器不支持语音合成'))
        return
      }

      // 停止当前播放
      synthesis.value.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      
      // 根据父母角色配置声音
      const voices = synthesis.value.getVoices()
      const chineseVoices = voices.filter(voice => 
        voice.lang.startsWith('zh') || voice.lang.startsWith('cmn')
      )
      
      if (chineseVoices.length > 0) {
        const femaleVoice = chineseVoices.find(voice => 
          voice.name.includes('Female') || voice.name.includes('女')
        )
        const maleVoice = chineseVoices.find(voice => 
          voice.name.includes('Male') || voice.name.includes('男')
        )
        
        if (voiceType === 'mom' && femaleVoice) {
          utterance.voice = femaleVoice
        } else if (voiceType === 'dad' && maleVoice) {
          utterance.voice = maleVoice
        } else {
          utterance.voice = chineseVoices[0]
        }
      }

      // 配置语音参数
      utterance.rate = 0.9
      utterance.pitch = voiceType === 'mom' ? 1.1 : 0.9
      utterance.volume = 0.8

      utterance.onstart = () => {
        isSpeaking.value = true
        // 说话时暂停语音识别（避免识别到自己的声音）
        if (isInCall.value && recognition.value) {
          recognition.value.stop()
        }
      }

      utterance.onend = () => {
        isSpeaking.value = false
        resolve()
        
        // 播放完成后恢复语音识别
        if (isInCall.value) {
          setTimeout(() => {
            if (isInCall.value && recognition.value) {
              try {
                recognition.value.start()
              } catch (e) {
                console.log('恢复识别失败')
              }
            }
          }, 500) // 延迟500ms避免识别到尾音
        }
      }

      utterance.onerror = (event) => {
        isSpeaking.value = false
        reject(new Error(`语音合成错误: ${event.error}`))
      }

      synthesis.value.speak(utterance)
    })
  }

  // 停止语音播放
  const stopSpeaking = () => {
    if (synthesis.value) {
      synthesis.value.cancel()
      isSpeaking.value = false
    }
  }

  // 通话状态
  const callStatus = computed(() => {
    if (!isInCall.value) return 'idle'
    if (isSpeaking.value) return 'ai_speaking'
    if (currentTranscript.value.trim()) return 'user_speaking'
    return 'listening'
  })

  // 初始化
  checkSupport()

  return {
    // 状态
    isRecording,
    isSpeaking,
    isSupported,
    currentTranscript,
    isInCall,
    callStatus,
    
    // 通话方法
    startCall,
    stopCall,
    speak,
    stopSpeaking,
    
    // 工具方法
    checkSupport
  }
}