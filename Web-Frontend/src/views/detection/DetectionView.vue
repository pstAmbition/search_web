<template>
  <div class="page-container">
    <h1 class="page-title">虚假信息检测</h1>
    
    <!-- 检测类型选择 -->
    <div class="detection-types">
      <div class="type-card" 
           :class="{ 'active': selectedType === 'text' }"
           @click="selectType('text')">
        <i class="fas fa-search-plus"></i>
        <h3>文本谣言检测</h3>
        <p>检测文本内容的真实性</p>
      </div>
      
      <div class="type-card" 
           :class="{ 'active': selectedType === 'image' }"
           @click="selectType('image')">
        <i class="fas fa-image"></i>
        <h3>图像伪造检测</h3>
        <p>检测图像是否被篡改</p>
      </div>
      
      <div class="type-card" 
           :class="{ 'active': selectedType === 'audiovideo' }"
           @click="selectType('audiovideo')">
        <i class="fas fa-play-circle"></i>
        <h3>音视频伪造检测</h3>
        <p>检测音频和视频是否被伪造</p>
      </div>
      
      <div class="type-card" 
           :class="{ 'active': selectedType === 'multimodal' }"
           @click="selectType('multimodal')">
        <i class="fas fa-layer-group"></i>
        <h3>多模态假新闻检测</h3>
        <p>综合检测多模态内容</p>
      </div>
      
      <div class="type-card" 
           :class="{ 'active': selectedType === 'entity' }"
           @click="selectType('entity')">
        <i class="fas fa-tags"></i>
        <h3>实体识别</h3>
        <p>识别文本中的实体信息</p>
      </div>
    </div>

    <!-- 检测区域 -->
    <div class="detection-area" v-if="selectedType">
      <div class="detection-header">
        <h2>{{ getTypeTitle() }}</h2>
        <div class="detection-status" :class="detectionStatus">
          {{ getStatusText() }}
        </div>
      </div>

      <!-- 多模态检测特殊布局 -->
      <div v-if="selectedType === 'multimodal'" class="multimodal-layout">
        <!-- 第一行：左侧上传图片，右侧输入文字 -->
        <div class="multimodal-row">
          <div class="multimodal-upload">
            <div class="upload-box" 
                 @click="triggerFileUpload"
                 @dragover.prevent
                 @drop.prevent="handleFileDrop">
              <i class="fas fa-cloud-upload-alt"></i>
              <p>点击上传图片</p>
              <p class="file-types">支持 PNG, JPG, GIF 格式</p>
            </div>
            <input type="file" 
                   ref="fileInput" 
                   accept=".png,.jpg,.gif"
                   @change="handleFileSelect" 
                   style="display: none;">
          </div>
          
          <div class="multimodal-text">
            <textarea v-model="textContent" 
                      placeholder="请输入要检测的文本内容..."
                      rows="6"></textarea>
          </div>
        </div>
        
        <!-- 第二行：图片展示 -->
        <div class="multimodal-preview" v-if="imagePreviewUrl">
          <div class="image-preview">
            <img :src="imagePreviewUrl" alt="预览图片" />
            <p>{{ uploadedFile?.name }}</p>
          </div>
        </div>
      </div>

      <!-- 其他检测类型的布局 -->
      <div v-else>
        <!-- 文件上传区域 -->
        <div class="upload-area" v-if="selectedType !== 'text' && selectedType !== 'entity'">
          <div class="upload-box" 
               @click="triggerFileUpload"
               @dragover.prevent
               @drop.prevent="handleFileDrop">
            <i class="fas fa-cloud-upload-alt"></i>
            <p>点击上传文件或拖拽文件到此处</p>
            <p class="file-types">{{ getSupportedFormats() }}</p>
          </div>
          <input type="file" 
                 ref="fileInput" 
                 :accept="getFileAccept()"
                 @change="handleFileSelect" 
                 style="display: none;">
          
          <!-- 图片预览 -->
          <div class="image-preview" v-if="imagePreviewUrl && selectedType === 'image'">
            <img :src="imagePreviewUrl" alt="预览图片" />
            <p>{{ uploadedFile?.name }}</p>
          </div>
          
          <!-- 音视频文件信息 -->
          <div class="file-info" v-if="uploadedFile && selectedType === 'audiovideo'">
            <div class="file-details">
              <i class="fas fa-file-audio" v-if="uploadedFile.name.match(/\.(wav|mp3)$/i)"></i>
              <i class="fas fa-file-video" v-if="uploadedFile.name.match(/\.(avi|mp4)$/i)"></i>
              <span class="file-name">{{ uploadedFile.name }}</span>
              <span class="file-size">({{ formatFileSize(uploadedFile.size) }})</span>
            </div>
          </div>
        </div>

        <!-- 文本输入区域 -->
        <div class="text-input-area" v-if="selectedType === 'text' || selectedType === 'entity'">
          <textarea v-model="textContent" 
                    :placeholder="getTextPlaceholder()"
                    rows="6"></textarea>
          <div class="text-counter" v-if="selectedType === 'entity'">
            <span :class="getTextCounterClass()">{{ textContent.length }}/{{ typeConfig.entity.maxLength }}</span>
          </div>
        </div>
      </div>

      <!-- 检测按钮 -->
      <div class="detection-actions">
        <button class="detect-btn" 
                @click="startDetection"
                :disabled="!canDetect() || detectionStatus === 'detecting'">
          <i class="fas fa-search"></i>
          {{ detectionStatus === 'detecting' ? '检测中...' : '开始检测' }}
        </button>
        <button class="clear-btn" @click="clearAll">
          <i class="fas fa-trash"></i>
          清空
        </button>
      </div>

      <!-- 检测结果 -->
      <div class="detection-results" v-if="detectionResult">
        <h3>检测结果</h3>
        <div class="result-card">
          <div class="result-item">
            <label>检测类型:</label>
            <span>{{ detectionResult.type }}</span>
          </div>
          
          <!-- 文本/图像/音视频/多模态检测结果 - 使用状态环显示 -->
          <div v-if="selectedType !== 'entity'" class="result-display">
            <div class="status-ring-container">
              <div class="status-ring" :class="getStatusRingClass()" :style="{ '--progress-angle': progressAngle + 'deg' }">
                <div class="status-ring-inner">
                  <div class="status-text" :class="getStatusTextClass()">
                    {{ getResultDisplayText() }}
                  </div>
                  <div class="confidence-text">
                    {{ Math.min(100, Math.max(0, (detectionResult.confidence * 100))).toFixed(2) }}%
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 实体识别结果 -->
          <div v-if="selectedType === 'entity'">
            <div class="result-item">
              <label>识别到实体:</label>
              <span>{{ detectionResult.total_count }} 个</span>
            </div>
            <div class="result-item">
              <label>文本长度:</label>
              <span>{{ detectionResult.text_length }} 字符</span>
            </div>
            <div class="entities-list" v-if="detectionResult.entities && detectionResult.entities.length > 0">
              <h4>实体详情:</h4>
              <div class="entity-item" v-for="(entity, index) in detectionResult.entities" :key="index">
                <span class="entity-text">{{ entity.text }}</span>
                <span class="entity-type" :class="getEntityTypeClass(entity.type)">{{ entity.type_name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

// 响应式数据
const selectedType = ref('')
const textContent = ref('')
const uploadedFile = ref(null)
const imagePreviewUrl = ref('')
const detectionResult = ref(null)
const detectionStatus = ref('idle') // idle, detecting, success, error

// 计算属性
const progressAngle = computed(() => {
  if (!detectionResult.value || !detectionResult.value.confidence) return 0
  return detectionResult.value.confidence * 360
})
const fileInput = ref(null)

// 检测类型配置
const typeConfig = {
  text: {
    title: '文本谣言检测',
    apiEndpoint: '/api/text/detect',
    supportedFormats: '支持中文文本',
    port: 5011
  },
  image: {
    title: '图像伪造检测',
    apiEndpoint: '/api/image/detect',
    supportedFormats: '支持 PNG, JPG, GIF 格式',
    port: 5013
  },
  audiovideo: {
    title: '音视频伪造检测',
    apiEndpoint: '/api/audiovideo/detect',
    supportedFormats: '支持 WAV, MP3, AVI, MP4 格式（最大100MB）',
    port: 5014
  },
  multimodal: {
    title: '多模态假新闻检测',
    apiEndpoint: '/api/multimodal/detect',
    supportedFormats: '支持 PNG, JPG, GIF 格式',
    port: 5017
  },
  entity: {
    title: '实体识别',
    apiEndpoint: '/api/entity/detect',
    supportedFormats: '支持中文文本（最多2000字符）',
    maxLength: 2000,
    port: 5016
  }
}

// 方法
const selectType = (type) => {
  selectedType.value = type
  clearAll()
}

const getTypeTitle = () => {
  return typeConfig[selectedType.value]?.title || ''
}

const getSupportedFormats = () => {
  return typeConfig[selectedType.value]?.supportedFormats || ''
}

const getFileAccept = () => {
  if (selectedType.value === 'image' || selectedType.value === 'multimodal') {
    return '.png,.jpg,.gif'
  } else if (selectedType.value === 'audiovideo') {
    return '.wav,.mp3,.avi,.mp4'
  }
  return '*'
}

const triggerFileUpload = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    // 检查文件大小（限制为100MB）
    const maxSize = 100 * 1024 * 1024 // 100MB
    if (file.size > maxSize) {
      alert('文件大小不能超过100MB')
      return
    }
    
    // 根据检测类型检查文件类型
    const fileExt = file.name.split('.').pop().toLowerCase()
    let allowedExts = []
    let errorMessage = ''
    
    if (selectedType.value === 'image' || selectedType.value === 'multimodal') {
      allowedExts = ['png', 'jpg', 'gif']
      errorMessage = '只支持 PNG, JPG, GIF 格式'
    } else if (selectedType.value === 'audiovideo') {
      allowedExts = ['wav', 'mp3', 'avi', 'mp4']
      errorMessage = '只支持 WAV, MP3, AVI, MP4 格式'
    }
    
    if (allowedExts.length > 0 && !allowedExts.includes(fileExt)) {
      alert(errorMessage)
      return
    }
    
    uploadedFile.value = file
    
    // 创建图片预览
    if ((selectedType.value === 'image' || selectedType.value === 'multimodal') && file.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        imagePreviewUrl.value = e.target.result
      }
      reader.readAsDataURL(file)
    }
  }
}

const handleFileDrop = (event) => {
  const file = event.dataTransfer.files[0]
  if (file) {
    // 检查文件大小（限制为100MB）
    const maxSize = 100 * 1024 * 1024 // 100MB
    if (file.size > maxSize) {
      alert('文件大小不能超过100MB')
      return
    }
    
    // 根据检测类型检查文件类型
    const fileExt = file.name.split('.').pop().toLowerCase()
    let allowedExts = []
    let errorMessage = ''
    
    if (selectedType.value === 'image' || selectedType.value === 'multimodal') {
      allowedExts = ['png', 'jpg', 'gif']
      errorMessage = '只支持 PNG, JPG, GIF 格式'
    } else if (selectedType.value === 'audiovideo') {
      allowedExts = ['wav', 'mp3', 'avi', 'mp4']
      errorMessage = '只支持 WAV, MP3, AVI, MP4 格式'
    }
    
    if (allowedExts.length > 0 && !allowedExts.includes(fileExt)) {
      alert(errorMessage)
      return
    }
    
    uploadedFile.value = file
    
    // 创建图片预览
    if ((selectedType.value === 'image' || selectedType.value === 'multimodal') && file.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        imagePreviewUrl.value = e.target.result
      }
      reader.readAsDataURL(file)
    }
  }
}

const canDetect = () => {
  if (selectedType.value === 'text' || selectedType.value === 'entity') {
    const textLength = textContent.value.trim().length
    if (selectedType.value === 'entity') {
      return textLength > 0 && textLength <= typeConfig.entity.maxLength
    }
    return textLength > 0
  } else if (selectedType.value === 'multimodal') {
    // 多模态检测需要同时有文本和图片
    return textContent.value.trim().length > 0 && uploadedFile.value !== null
  } else {
    return uploadedFile.value !== null
  }
}

const startDetection = async () => {
  if (!canDetect() || detectionStatus.value === 'detecting') return

  detectionStatus.value = 'detecting'
  detectionResult.value = null

  try {
    const config = typeConfig[selectedType.value]
    if (!config) {
      throw new Error('不支持的检测类型')
    }

    let requestData = {}
    
    if (selectedType.value === 'text' || selectedType.value === 'entity') {
      // 文本检测
      requestData = {
        text: textContent.value.trim()
      }
    } else if (selectedType.value === 'multimodal') {
      // 多模态检测
      if (!uploadedFile.value) {
        throw new Error('请选择图片文件')
      }
      if (!textContent.value.trim()) {
        throw new Error('请输入文本内容')
      }
      
      // 发送文本和图片文件进行检测
      const formData = new FormData()
      formData.append('text', textContent.value.trim())
      formData.append('image', uploadedFile.value)
      
      // 直接调用检测接口
      const response = await axios.post(`http://localhost:${config.port}${config.apiEndpoint}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 30000
      })
      
      if (response.data.success) {
        // 处理多模态检测结果，将FAKE转换为中文
        const result = response.data.data
        if (result.result === 'FAKE') {
          result.result = '虚假'
        } else if (result.result === 'REAL') {
          result.result = '真实'
        }
        detectionResult.value = result
        detectionStatus.value = 'success'
      } else {
        throw new Error(response.data.message || '检测失败')
      }
      return
    } else if (selectedType.value === 'image') {
      // 图像检测
      if (!uploadedFile.value) {
        throw new Error('请选择图像文件')
      }
      
      // 直接发送图像文件进行检测
      const formData = new FormData()
      formData.append('image', uploadedFile.value)
      
      // 直接调用检测接口
      const response = await axios.post(`http://localhost:${config.port}${config.apiEndpoint}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 30000
      })
      
      if (response.data.success) {
        detectionResult.value = response.data.data
        detectionStatus.value = 'success'
      } else {
        throw new Error(response.data.message || '检测失败')
      }
      return
    } else if (selectedType.value === 'audiovideo') {
      // 音视频检测
      if (!uploadedFile.value) {
        throw new Error('请选择音视频文件')
      }
      
      // 直接发送音视频文件进行检测
      const formData = new FormData()
      formData.append('file', uploadedFile.value)
      
      // 直接调用检测接口
      const response = await axios.post(`http://localhost:${config.port}${config.apiEndpoint}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 60000 // 音视频检测可能需要更长时间
      })
      
      if (response.data.success) {
        detectionResult.value = response.data.data
        detectionStatus.value = 'success'
      } else {
        throw new Error(response.data.message || '检测失败')
      }
      return
    } else {
      // 其他文件检测 - 暂时返回模拟结果
      await new Promise(resolve => setTimeout(resolve, 2000))
      detectionResult.value = {
        type: getTypeTitle(),
        result: Math.random() > 0.5 ? '真实' : '虚假',
        confidence: Math.random() * 0.4 + 0.6,
        details: {
          algorithm: '模拟算法',
          timestamp: new Date().toISOString()
        }
      }
      detectionStatus.value = 'success'
      return
    }

    // 调用API
    const response = await axios.post(`http://localhost:${config.port}${config.apiEndpoint}`, requestData, {
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 30000 // 30秒超时
    })

    if (response.data.success) {
      detectionResult.value = response.data.data
      detectionStatus.value = 'success'
    } else {
      throw new Error(response.data.message || '检测失败')
    }
    
  } catch (error) {
    detectionStatus.value = 'error'
    console.error('检测失败:', error)
    
    // 显示错误信息
    detectionResult.value = {
      type: getTypeTitle(),
      result: '检测失败',
      confidence: 0,
      details: {
        error: error.message,
        timestamp: new Date().toISOString()
      }
    }
  }
}

const clearAll = () => {
  textContent.value = ''
  uploadedFile.value = null
  imagePreviewUrl.value = ''
  detectionResult.value = null
  detectionStatus.value = 'idle'
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const getStatusText = () => {
  switch (detectionStatus.value) {
    case 'detecting': return '检测中...'
    case 'success': return '检测完成'
    case 'error': return '检测失败'
    default: return '等待检测'
  }
}

// 新增：获取结果显示文本
const getResultDisplayText = () => {
  if (!detectionResult.value) return ''
  
  const result = detectionResult.value.result
  // 统一处理各种结果格式
  if (result === '非谣言' || result === '真实' || result === 'REAL' || result === '真实') {
    return '真实'
  } else if (result === '谣言' || result === '虚假' || result === 'FAKE' || result === '伪造') {
    return '虚假'
  }
  return result
}

// 新增：获取状态环的CSS类
const getStatusRingClass = () => {
  if (!detectionResult.value) return ''
  
  const result = detectionResult.value.result
  // 处理所有可能的真实结果
  if (result === '非谣言' || result === '真实' || result === 'REAL' || result === '真实') {
    return 'status-ring-real'
  } 
  // 处理所有可能的虚假结果
  else if (result === '谣言' || result === '虚假' || result === 'FAKE' || result === '伪造') {
    return 'status-ring-fake'
  }
  return 'status-ring-default'
}

// 新增：获取状态文本的CSS类
const getStatusTextClass = () => {
  if (!detectionResult.value) return ''
  
  const result = detectionResult.value.result
  // 处理所有可能的真实结果
  if (result === '非谣言' || result === '真实' || result === 'REAL' || result === '真实') {
    return 'status-text-real'
  } 
  // 处理所有可能的虚假结果
  else if (result === '谣言' || result === '虚假' || result === 'FAKE' || result === '伪造') {
    return 'status-text-fake'
  }
  return 'status-text-default'
}

const getTextPlaceholder = () => {
  if (selectedType.value === 'entity') {
    return '请输入要识别的文本内容（最多2000字符）...'
  } else if (selectedType.value === 'multimodal') {
    return '请输入要检测的文本内容...'
  }
  return '请输入要检测的文本内容...'
}

const getTextCounterClass = () => {
  const length = textContent.value.length
  const maxLength = typeConfig.entity.maxLength
  if (length > maxLength) {
    return 'text-counter-error'
  } else if (length > maxLength * 0.8) {
    return 'text-counter-warning'
  }
  return 'text-counter-normal'
}

const getEntityTypeClass = (entityType) => {
  const typeClasses = {
    // 人名相关
    'PER': 'entity-type-person',
    'PER.NAM': 'entity-type-person',
    'PER.NOM': 'entity-type-person',
    'PERSON': 'entity-type-person',
    
    // 地名相关
    'LOC': 'entity-type-location',
    'LOC.NAM': 'entity-type-location',
    'LOC.NOM': 'entity-type-location',
    'GPE': 'entity-type-location',
    'GPE.NAM': 'entity-type-location',
    'GPE.NOM': 'entity-type-location',
    'LOCATION': 'entity-type-location',
    
    // 机构相关
    'ORG': 'entity-type-organization',
    'ORG.NAM': 'entity-type-organization',
    'ORG.NOM': 'entity-type-organization',
    'ORGANIZATION': 'entity-type-organization',
    
    // 其他
    'MISC': 'entity-type-misc',
    'MISC.NAM': 'entity-type-misc',
    'MISC.NOM': 'entity-type-misc',
    'TIME': 'entity-type-time',
    'NUM': 'entity-type-number',
    'DATE': 'entity-type-time',
    'MONEY': 'entity-type-number',
    'PERCENT': 'entity-type-number'
  }
  return typeClasses[entityType] || 'entity-type-default'
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>

<style scoped>
.page-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 28px;
  color: #333;
  margin-bottom: 30px;
  text-align: center;
}

.detection-types {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.type-card {
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.type-card:hover {
  border-color: #4a90e2;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.15);
}

.type-card.active {
  border-color: #4a90e2;
  background: #f0f7ff;
}

.type-card i {
  font-size: 32px;
  color: #4a90e2;
  margin-bottom: 10px;
}

.type-card h3 {
  margin: 10px 0;
  color: #333;
  font-size: 16px;
}

.type-card p {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.detection-area {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.detection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
}

.detection-header h2 {
  margin: 0;
  color: #333;
  font-size: 24px;
}

.detection-status {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.detection-status.idle {
  background: #f5f5f5;
  color: #666;
}

.detection-status.detecting {
  background: #fff3cd;
  color: #856404;
}

.detection-status.success {
  background: #d4edda;
  color: #155724;
}

.detection-status.error {
  background: #f8d7da;
  color: #721c24;
}

/* 多模态检测特殊布局 */
.multimodal-layout {
  margin-bottom: 30px;
}

.multimodal-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.multimodal-upload {
  display: flex;
  flex-direction: column;
}

.multimodal-text {
  display: flex;
  flex-direction: column;
}

.multimodal-text textarea {
  width: 100%;
  height: 100%;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  resize: none;
}

.multimodal-preview {
  width: 100%;
}

.upload-area {
  margin-bottom: 30px;
}

.upload-box {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-box:hover {
  border-color: #4a90e2;
  background: #f9f9f9;
}

.upload-box i {
  font-size: 48px;
  color: #ccc;
  margin-bottom: 15px;
}

.upload-box p {
  margin: 5px 0;
  color: #666;
}

.file-types {
  font-size: 12px;
  color: #999;
}

.text-input-area {
  margin-bottom: 30px;
}

.text-input-area textarea {
  width: 100%;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  min-height: 120px;
}

.detection-actions {
  display: flex;
  gap: 15px;
  margin-bottom: 30px;
}

.detect-btn, .clear-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.detect-btn {
  background: #4a90e2;
  color: white;
}

.detect-btn:hover:not(:disabled) {
  background: #357abd;
}

.detect-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.clear-btn {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;
}

.clear-btn:hover {
  background: #e0e0e0;
}

.detection-results {
  margin-top: 30px;
}

.detection-results h3 {
  margin-bottom: 20px;
  color: #333;
}

.result-card {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 20px;
}

.result-item {
  display: flex;
  margin-bottom: 15px;
  align-items: flex-start;
}

.result-item label {
  font-weight: 600;
  color: #333;
  min-width: 100px;
  margin-right: 15px;
}

.result-item span {
  color: #666;
}

/* 状态环样式 */
.result-display {
  display: flex;
  justify-content: center;
  margin: 20px 0;
}

.status-ring-container {
  position: relative;
  width: 200px;
  height: 200px;
}

.status-ring {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: conic-gradient(from 0deg, transparent 0deg, transparent 360deg);
  transition: all 0.3s ease;
}

.status-ring-real {
  background: conic-gradient(from 0deg, #28a745 0deg, #28a745 var(--progress-angle, 0deg), #e9ecef var(--progress-angle, 0deg), #e9ecef 360deg);
}

.status-ring-fake {
  background: conic-gradient(from 0deg, #dc3545 0deg, #dc3545 var(--progress-angle, 0deg), #e9ecef var(--progress-angle, 0deg), #e9ecef 360deg);
}

.status-ring-default {
  background: conic-gradient(from 0deg, #6c757d 0deg, #6c757d var(--progress-angle, 0deg), #e9ecef var(--progress-angle, 0deg), #e9ecef 360deg);
}

.status-ring-inner {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

.status-text {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.status-text-real {
  color: #28a745;
}

.status-text-fake {
  color: #dc3545;
}

.status-text-default {
  color: #6c757d;
}

.confidence-text {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.result-real {
  color: #28a745; /* 绿色  真实*/
  font-weight: 600;
  font-size: 16px;
}

.result-fake {
  color: #dc3545; /* 红色  虚假*/
  font-weight: 600;
  font-size: 16px;
}

.result-item pre {
  background: white;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
  margin: 0;
}

.image-preview {
  margin-top: 20px;
  text-align: center;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #f9f9f9;
}

.image-preview img {
  max-width: 300px;
  max-height: 200px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: block;
  margin: 0 auto;
}

.image-preview p {
  margin-top: 10px;
  color: #666;
  font-size: 14px;
  text-align: center;
}

.file-info {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #f9f9f9;
}

.file-details {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-details i {
  font-size: 24px;
  color: #4a90e2;
}

.file-name {
  font-weight: 600;
  color: #333;
}

.file-size {
  color: #666;
  font-size: 14px;
}

.text-counter {
  text-align: right;
  margin-top: 5px;
  font-size: 12px;
}

.text-counter-normal {
  color: #666;
}

.text-counter-warning {
  color: #ff9800;
}

.text-counter-error {
  color: #f44336;
}

.entities-list {
  margin-top: 15px;
}

.entities-list h4 {
  margin-bottom: 10px;
  color: #333;
  font-size: 16px;
}

.entity-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 8px;
  background: #f5f5f5;
  border-radius: 6px;
  border-left: 4px solid #4a90e2;
}

.entity-text {
  font-weight: 600;
  color: #333;
}

.entity-type {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  color: white;
}

.entity-type-person {
  background: #e91e63;
}

.entity-type-location {
  background: #2196f3;
}

.entity-type-organization {
  background: #4caf50;
}

.entity-type-misc {
  background: #ff9800;
}

.entity-type-time {
  background: #9c27b0;
}

.entity-type-number {
  background: #607d8b;
}

.entity-type-default {
  background: #666;
}
</style>
