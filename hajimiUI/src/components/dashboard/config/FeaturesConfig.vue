<script setup>
import { useDashboardStore } from '../../../stores/dashboard'
import { ref, reactive, watch, onMounted } from 'vue'

const dashboardStore = useDashboardStore()

// Initialize localConfig with default structure
const localConfig = reactive({
  searchMode: false,
  searchPrompt: '',
  maxRetryNum: 0,
  fakeStreaming: false,
  fakeStreamingInterval: 0,
  randomString: false,
  randomStringLength: 0,
  concurrentRequests: 1, // Default to 1 or a sensible minimum
  increaseConcurrentOnFailure: 0,
  maxConcurrentRequests: 1, // Default to 1 or a sensible minimum
  maxEmptyResponses: 0,
  logUpstreamResponses: false // 新增日志配置
})

const populatedFromStore = ref(false);

// 日志配置状态
const loggingConfig = reactive({
  logUpstreamResponses: false,
  enableStorage: false
})

const isRefreshingLogging = ref(false)

// Watch for store changes to populate localConfig ONCE when config is loaded
watch(
  () => ({
    storeSearchMode: dashboardStore.config.searchMode,
    storeSearchPrompt: dashboardStore.config.searchPrompt,
    storeMaxRetryNum: dashboardStore.config.maxRetryNum,
    storeFakeStreaming: dashboardStore.config.fakeStreaming,
    storeFakeStreamingInterval: dashboardStore.config.fakeStreamingInterval,
    storeRandomString: dashboardStore.config.randomString,
    storeRandomStringLength: dashboardStore.config.randomStringLength,
    storeConcurrentRequests: dashboardStore.config.concurrentRequests,
    storeIncreaseConcurrentOnFailure: dashboardStore.config.increaseConcurrentOnFailure,
    storeMaxConcurrentRequests: dashboardStore.config.maxConcurrentRequests,
    storeMaxEmptyResponses: dashboardStore.config.maxEmptyResponses,
    configIsActuallyLoaded: dashboardStore.isConfigLoaded, // 观察加载状态
  }),
  (newValues) => {
    if (newValues.configIsActuallyLoaded && !populatedFromStore.value) {
      localConfig.searchMode = newValues.storeSearchMode;
      localConfig.searchPrompt = newValues.storeSearchPrompt;
      localConfig.maxRetryNum = newValues.storeMaxRetryNum;
      localConfig.fakeStreaming = newValues.storeFakeStreaming;
      localConfig.fakeStreamingInterval = newValues.storeFakeStreamingInterval;
      localConfig.randomString = newValues.storeRandomString;
      localConfig.randomStringLength = newValues.storeRandomStringLength;
      localConfig.concurrentRequests = newValues.storeConcurrentRequests;
      localConfig.increaseConcurrentOnFailure = newValues.storeIncreaseConcurrentOnFailure;
      localConfig.maxConcurrentRequests = newValues.storeMaxConcurrentRequests;
      localConfig.maxEmptyResponses = newValues.storeMaxEmptyResponses;
      populatedFromStore.value = true;
    }
  },
  { deep: true, immediate: true }
)

// 保存组件配置
async function saveComponentConfigs(passwordFromParent) {
  if (!passwordFromParent) {
    return { success: false, message: '功能配置: 密码未提供' }
  }

  let allSucceeded = true;
  let individualMessages = [];

  // 逐个保存配置项
  const configKeys = Object.keys(localConfig);
  for (const key of configKeys) {
    if (key === 'logUpstreamResponses') {
      // 日志配置使用专门的API
      if (localConfig[key] !== loggingConfig.logUpstreamResponses) {
        try {
          const result = await updateLoggingConfig(localConfig[key], passwordFromParent);
          if (result.success) {
            individualMessages.push(`日志配置保存成功`);
          } else {
            allSucceeded = false;
            individualMessages.push(`日志配置保存失败: ${result.message}`);
          }
        } catch (error) {
          allSucceeded = false;
          individualMessages.push(`日志配置保存失败: ${error.message || '未知错误'}`);
        }
      }
    } else if (localConfig[key] !== dashboardStore.config[key]) {
      try {
        await dashboardStore.updateConfig(key, localConfig[key], passwordFromParent);
        // 更新store中的值 - 仅在API调用成功后
        dashboardStore.config[key] = localConfig[key];
        individualMessages.push(`${key} 保存成功`);
      } catch (error) {
        allSucceeded = false;
        individualMessages.push(`${key} 保存失败: ${error.message || '未知错误'}`);
      }
    }
  }

  if (allSucceeded && individualMessages.length === 0) {
    // 如果没有任何更改，也算成功，但提示用户
    return { success: true, message: '功能配置: 无更改需要保存' };
  }

  return {
    success: allSucceeded,
    message: `功能配置: ${individualMessages.join('; ')}`
  };
}

// 获取布尔值显示文本
function getBooleanText(value) {
  return value ? '启用' : '禁用'
}

// 获取日志配置
async function refreshLoggingConfig() {
  isRefreshingLogging.value = true
  try {
    const response = await fetch('/api/logging-config', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const data = await response.json()
    if (data.status === 'success' && data.config) {
      loggingConfig.logUpstreamResponses = data.config.log_upstream_responses
      loggingConfig.enableStorage = data.config.enable_storage
      localConfig.logUpstreamResponses = data.config.log_upstream_responses
    }
  } catch (error) {
    console.error('获取日志配置失败:', error)
  } finally {
    isRefreshingLogging.value = false
  }
}

// 更新日志配置
async function updateLoggingConfig(logUpstreamResponses, password) {
  try {
    const response = await fetch('/api/logging-config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        password: password,
        log_upstream_responses: logUpstreamResponses
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }
    
    const data = await response.json()
    if (data.status === 'success' && data.config) {
      loggingConfig.logUpstreamResponses = data.config.log_upstream_responses
      loggingConfig.enableStorage = data.config.enable_storage
      return { success: true, message: data.message }
    }
    
    return { success: false, message: '更新失败' }
  } catch (error) {
    return { success: false, message: error.message }
  }
}

// 组件挂载时获取日志配置
onMounted(() => {
  refreshLoggingConfig()
})

defineExpose({
  saveComponentConfigs,
  localConfig
})
</script>

<template>
  <div class="features-config">
    <h3 class="section-title">功能配置</h3>
    
    <div class="config-form">
      <!-- 布尔值配置项 -->
      <div class="config-row">
        <div class="config-group">
          <label class="config-label">联网搜索</label>
          <div class="toggle-wrapper">
            <input type="checkbox" class="toggle" id="searchMode" v-model="localConfig.searchMode">
            <label for="searchMode" class="toggle-label">
              <span class="toggle-text">{{ getBooleanText(localConfig.searchMode) }}</span>
            </label>
          </div>
        </div>
        
        <div class="config-group">
          <label class="config-label">假流式响应</label>
          <div class="toggle-wrapper">
            <input type="checkbox" class="toggle" id="fakeStreaming" v-model="localConfig.fakeStreaming">
            <label for="fakeStreaming" class="toggle-label">
              <span class="toggle-text">{{ getBooleanText(localConfig.fakeStreaming) }}</span>
            </label>
          </div>
        </div>
        
        <div class="config-group">
          <label class="config-label">伪装信息</label>
          <div class="toggle-wrapper">
            <input type="checkbox" class="toggle" id="randomString" v-model="localConfig.randomString">
            <label for="randomString" class="toggle-label">
              <span class="toggle-text">{{ getBooleanText(localConfig.randomString) }}</span>
            </label>
          </div>
        </div>
      </div>
      
      <!-- 日志配置行 -->
      <div class="config-row">
        <div class="config-group">
          <label class="config-label">上游响应日志</label>
          <div class="toggle-wrapper">
            <input type="checkbox" class="toggle" id="logUpstreamResponses" v-model="localConfig.logUpstreamResponses">
            <label for="logUpstreamResponses" class="toggle-label">
              <span class="toggle-text">{{ getBooleanText(localConfig.logUpstreamResponses) }}</span>
            </label>
          </div>
        </div>
        
        <div class="config-group">
          <div class="log-status">
            <span class="status-label">存储状态:</span>
            <span class="status-value">{{ loggingConfig.enableStorage ? '文件存储' : '控制台输出' }}</span>
          </div>
        </div>
        
        <div class="config-group">
          <button 
            class="refresh-logging-btn" 
            @click="refreshLoggingConfig"
            :disabled="isRefreshingLogging"
          >
            {{ isRefreshingLogging ? '刷新中...' : '刷新状态' }}
          </button>
        </div>
      </div>
      
      <!-- 字符串配置项 -->
      <div class="config-row">
        <div class="config-group full-width">
          <label class="config-label">联网搜索提示</label>
          <input 
            type="text" 
            class="config-input" 
            v-model="localConfig.searchPrompt" 
            placeholder="请输入联网搜索提示"
          >
        </div>
      </div>
      
      <!-- 数值配置项第一行 -->
      <div class="config-row">
        <div class="config-group">
          <label class="config-label">最大重试次数</label>
          <input 
            type="number" 
            class="config-input" 
            v-model.number="localConfig.maxRetryNum" 
            min="0"
          >
        </div>
        
        <div class="config-group">
          <label class="config-label">假流式间隔(秒)</label>
          <input 
            type="number" 
            class="config-input" 
            v-model.number="localConfig.fakeStreamingInterval" 
            min="0"
            step="0.1"
          >
        </div>
        
        <div class="config-group">
          <label class="config-label">伪装信息长度</label>
          <input 
            type="number" 
            class="config-input" 
            v-model.number="localConfig.randomStringLength" 
            min="0"
          >
        </div>
      </div>
      
      <!-- 数值配置项第二行 -->
      <div class="config-row">
        <div class="config-group">
          <label class="config-label">默认并发请求数</label>
          <input 
            type="number" 
            class="config-input" 
            v-model.number="localConfig.concurrentRequests" 
            min="1"
          >
        </div>
        
        <div class="config-group">
          <label class="config-label">失败时增加并发数</label>
          <input 
            type="number" 
            class="config-input" 
            v-model.number="localConfig.increaseConcurrentOnFailure" 
            min="0"
          >
        </div>
        
        <div class="config-group">
          <label class="config-label">最大并发请求数</label>
          <input 
            type="number" 
            class="config-input" 
            v-model.number="localConfig.maxConcurrentRequests" 
            min="1"
          >
        </div>
      </div>
      
      <!-- 数值配置项第三行 -->
      <div class="config-row">
        <div class="config-group">
          <label class="config-label">空响应重试限制</label>
          <input 
            type="number" 
            class="config-input" 
            v-model.number="localConfig.maxEmptyResponses" 
            min="0"
          >
        </div>
        <!-- 可以根据需要在此行添加更多配置项 -->
        <div class="config-group"></div>
        <div class="config-group"></div>
      </div>

      <!-- 移除独立的保存区域 -->
      <!-- 消息提示由父组件处理 -->
    </div>
  </div>
</template>

<style scoped>
.section-title {
  color: var(--color-heading);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 10px;
  margin-bottom: 20px;
  transition: all 0.3s ease;
  position: relative;
  font-weight: 600;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 50px;
  height: 2px;
  background: var(--gradient-primary);
}

.features-config {
  margin-bottom: 25px;
}

.config-form {
  background-color: var(--stats-item-bg);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--card-border);
}

.config-row {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.config-group {
  flex: 1;
  min-width: 120px;
}

.full-width {
  flex-basis: 100%;
}

.config-label {
  display: block;
  font-size: 14px;
  margin-bottom: 5px;
  color: var(--color-text);
  font-weight: 500;
}

.config-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-background);
  color: var(--color-text);
  font-size: 14px;
  transition: all 0.3s ease;
}

.config-input:focus {
  outline: none;
  border-color: var(--button-primary);
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
}

/* 开关样式 */
.toggle-wrapper {
  position: relative;
}

.toggle {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.toggle-label::before {
  content: '';
  display: inline-block;
  width: 36px;
  height: 20px;
  background-color: var(--color-border);
  border-radius: 10px;
  margin-right: 8px;
  position: relative;
  transition: all 0.3s ease;
}

.toggle-label::after {
  content: '';
  position: absolute;
  left: 3px;
  width: 14px;
  height: 14px;
  background-color: white;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.toggle:checked + .toggle-label::before {
  background-color: var(--button-primary);
}

.toggle:checked + .toggle-label::after {
  left: 19px;
}

.toggle-text {
  font-size: 14px;
  color: var(--color-text);
}

/* 日志配置样式 */
.log-status {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 12px;
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  min-height: 42px;
  justify-content: center;
}

.status-label {
  font-size: 12px;
  color: var(--color-text-muted);
  font-weight: 500;
}

.status-value {
  font-size: 13px;
  color: var(--color-text);
  font-weight: 600;
}

.refresh-logging-btn {
  padding: 8px 12px;
  background-color: var(--button-secondary);
  color: var(--button-secondary-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s ease;
  min-height: 42px;
}

.refresh-logging-btn:hover {
  background-color: var(--button-secondary-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.refresh-logging-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .config-row {
    gap: 10px;
  }
  
  .config-group {
    min-width: 100px;
  }
}

/* 小屏幕手机进一步优化 */
@media (max-width: 480px) {
  .config-row {
    flex-direction: column;
    gap: 10px;
  }
  
  .config-group {
    width: 100%;
  }
  
  .config-form {
    padding: 15px;
  }
}
</style> 