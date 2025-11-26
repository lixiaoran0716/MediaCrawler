<template>
  <div class="app-container">
    <h1>媒体爬虫工具</h1>
    <div class="input-section">
      <div class="form-group">
        <label>平台:</label>
        <select v-model="selectedPlatform" class="form-control">
          <option v-for="platform in platforms" :key="platform" :value="platform">{{ platformLabels[platform] }}</option>
        </select>
      </div>
      <div class="form-group">
        <label>爬取类型:</label>
        <select v-model="crawlType" class="form-control">
          <option value="search">搜索</option>
          <option value="detail">详情</option>
        </select>
      </div>
      <div class="form-group" v-if="crawlType === 'search'">
        <label>关键词:</label>
        <input v-model="keywords" type="text" class="form-control" placeholder="输入搜索关键词">
      </div>
      <button @click="fetchData" :disabled="loading" class="btn-crawl">
        <span v-if="loading">爬取中...</span>
        <span v-else>开始爬取</span>
      </button>
    </div>

    <div v-if="error" class="error-message">{{ error }}</div>

    <!-- 移除了原来的result-section，改为弹窗提示 -->
    
    <div v-if="debugInfo.error" class="debug-section">
      <h3>调试信息:</h3>
      <pre>{{ JSON.stringify(debugInfo, null, 2) }}</pre>
    </div>
    
    <!-- 添加模态弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>爬取结果</h2>
          <button class="modal-close" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <p v-if="!error">爬取任务已成功提交！</p>
          <p v-else>爬取任务提交失败，请查看调试信息。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-confirm" @click="closeModal">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import axios from 'axios';

export default {
  name: 'App',
  setup() {
    const platforms = ["xhs", "dy", "ks", "bili", "wb", "tieba", "zhihu", "nytimes", "qqnews"];
    const platformLabels = {
      "xhs": "小红书",
      "dy": "抖音",
      "ks": "快手",
      "bili": "哔哩哔哩",
      "wb": "微博",
      "tieba": "贴吧",
      "zhihu": "知乎",
      "nytimes": "纽约时报",
      "qqnews": "腾讯新闻"
    };
    const selectedPlatform = ref('xhs');
    const crawlType = ref('search');
    const keywords = ref('');
    const saveOption = ref('db');
    const result = ref(null);
    const loading = ref(false);
    const error = ref(null);
    const debugInfo = ref({});
    const showModal = ref(false); // 控制模态弹窗显示

    const fetchData = async () => {
      console.log('触发爬取数据函数');
      loading.value = true;
      error.value = null;
      result.value = null;

      try {
        debugInfo.value = { url: 'http://localhost:8000/api/crawl', data: {
          platform: selectedPlatform.value,
          type: crawlType.value,
          keywords: keywords.value,
          save_data_option: saveOption.value
        }};
        console.log('发送爬取请求:', debugInfo.value);
        const response = await axios.post('http://127.0.0.1:8000/api/crawl', {
          platform: selectedPlatform.value,
          type: crawlType.value,
          keywords: keywords.value,
          save_data_option: saveOption.value,
          start_page: 1,
          get_comment: false,
          get_sub_comment: false,
          login_type: 'qrcode'
        }, { headers: { 'Content-Type': 'application/json' } });
        result.value = response.data;
        // 显示模态弹窗
        showModal.value = true;
      } catch (err) {
        console.error('爬取错误详情:', {
          message: err.message,
          status: err.response?.status,
          statusText: err.response?.statusText,
          url: err.config?.url,
          method: err.config?.method,
          data: err.config?.data
        });
        debugInfo.value = {
          ...debugInfo.value,
          error: {
            message: err.message,
            status: err.response?.status,
            statusText: err.response?.statusText,
            data: err.response?.data
          }
        };
        error.value = `爬取失败: ${err.response?.status || ''} ${err.response?.data?.message || err.message || '未知错误'}。请查看浏览器控制台获取详细信息。`;
      } finally {
        loading.value = false;
      }
    };

    // 关闭模态弹窗的方法
    const closeModal = () => {
      showModal.value = false;
    };

    // 移除 formattedResult 计算属性，因为我们不再需要显示详细内容

    return {
      platforms,
      platformLabels,
      selectedPlatform,
      crawlType,
      keywords,
      saveOption,
      result,
      loading,
      error,
      debugInfo,
      showModal,
      fetchData,
      closeModal
    };
  }
};
</script>

<style scoped>
.app-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
  font-family: 'Arial', sans-serif;
  color: #333;
}

.input-section {
  background-color: #f5f5f5;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
  color: #555;
}

.form-control {
  width: 100%;
  padding: 0.8rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.btn-crawl {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 0.8rem 1.5rem;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-crawl:hover:not(:disabled) {
  background-color: #359469;
}

.btn-crawl:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.result-section {
  margin-top: 2rem;
}

pre {
  background-color: #f8f8f8;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  max-height: 400px;
}

.error-message {
  color: #ff4444;
  background-color: #ffebee;
  padding: 1rem;
  border-radius: 4px;
  margin: 1rem 0;
}

.debug-section {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #e3f2fd;
  border-radius: 4px;
}

h1 {
  color: #2c3e50;
  border-bottom: 2px solid #42b983;
  padding-bottom: 0.5rem;
  margin-bottom: 2rem;
  text-align: center;
}


.platform-select {
  flex: 1;
  min-width: 200px;
  padding: 0.8rem;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  background-color: #fff;
}

.crawl-btn {
  padding: 0.8rem 1.5rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.crawl-btn:hover:not(:disabled) {
  background-color: #359469;
}


.crawl-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.result-section {
  margin-top: 2rem;
}

.result-card {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.error-card {
  background-color: #fff0f0;
  color: #dc3545;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: auto;
  padding: 1rem;
  background-color: #fff;
  border-radius: 4px;
  border: 1px solid #eee;
}

/* 模态弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  max-width: 80%;
  max-height: 80%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  color: #2c3e50;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  color: #333;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.modal-body pre {
  max-height: 500px;
  margin: 0;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #eee;
  text-align: right;
}

.btn-confirm {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 0.5rem 1.5rem;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-confirm:hover {
  background-color: #359469;
}
</style>
