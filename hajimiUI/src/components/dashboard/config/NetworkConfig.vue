<script setup>
import { useDashboardStore } from '../../../stores/dashboard'
import { ref, reactive, watch } from 'vue'

const dashboardStore = useDashboardStore()

// Initialize localConfig with default structure
const localConfig = reactive({
  proxyUrl: '',
  geminiApiBaseUrl: '',
  vertexApiBaseUrl: ''
})

const populatedFromStore = ref(false)

// Watch for store changes to populate localConfig ONCE when config is loaded
watch(
  () => ({
    storeProxyUrl: dashboardStore.config.proxyUrl,
    storeGeminiApiBaseUrl: dashboardStore.config.geminiApiBaseUrl,
    storeVertexApiBaseUrl: dashboardStore.config.vertexApiBaseUrl,
    configIsActuallyLoaded: dashboardStore.isConfigLoaded,
  }),
  (newValues) => {
    if (newValues.configIsActuallyLoaded && !populatedFromStore.value) {
      localConfig.proxyUrl = newValues.storeProxyUrl || '';
      localConfig.geminiApiBaseUrl = newValues.storeGeminiApiBaseUrl || '';
      localConfig.vertexApiBaseUrl = newValues.storeVertexApiBaseUrl || '';
      populatedFromStore.value = true;
    }
  },
  { deep: true, immediate: true }
)

// 保存组件配置
async function saveComponentConfigs(passwordFromParent) {
  if (!passwordFromParent) {
    return { success: false, message: '网络配置: 密码未提供' }
  }

  let allSucceeded = true;
  let individualMessages = [];

  // 逐个保存配置项
  const configKeys = Object.keys(localConfig);
  for (const key of configKeys) {
    if (localConfig[key] !== dashboardStore.config[key]) {
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
    return { success: true, message: '网络配置: 无更改需要保存' };
  }

  return {
    success: allSucceeded,
    message: `网络配置: ${individualMessages.join('; ')}`
  };
}

// 检测代理类型
function getProxyType(url) {
  if (!url) return '未设置'
  const lower = url.toLowerCase()
  if (lower.startsWith('http://')) return 'HTTP代理'
  if (lower.startsWith('https://')) return 'HTTPS代理'
  if (lower.startsWith('socks5://')) return 'SOCKS5代理'
  if (lower.startsWith('socks5h://')) return 'SOCKS5H代理'
  return '其他代理'
}

defineExpose({
  saveComponentConfigs,
  localConfig
})
</script>

<template>
  <div class="network-config">
    <h3 class="section-title">网络配置</h3>
    
    <div class="config-form">
      <!-- 代理配置 -->
      <div class="config-row">
        <div class="config-group full-width">
          <label class="config-label">代理配置</label>
          <input 
            type="text" 
            class="config-input" 
            v-model="localConfig.proxyUrl" 
            placeholder="http://proxy.com:8080 或 socks5://user:pass@proxy.com:1080"
          >
          <small class="config-help">
            {{ getProxyType(localConfig.proxyUrl) }}
            <br>支持格式：http://proxy:8080, https://proxy:8080, socks5://proxy:1080, socks5h://user:pass@proxy:1080
          </small>
        </div>
      </div>
      
      <!-- API基础URL配置 -->
      <div class="config-row">
        <div class="config-group">
          <label class="config-label">Gemini API基础URL</label>
          <input 
            type="text" 
            class="config-input" 
            v-model="localConfig.geminiApiBaseUrl" 
            placeholder="https://generativelanguage.googleapis.com"
          >
        </div>
        
        <div class="config-group">
          <label class="config-label">Vertex API基础URL</label>
          <input 
            type="text" 
            class="config-input" 
            v-model="localConfig.vertexApiBaseUrl" 
            placeholder="https://aiplatform.googleapis.com"
          >
        </div>
      </div>
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

.network-config {
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

.config-help {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.4;
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