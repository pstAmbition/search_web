
<template>
  <div class="dashboard-container">
    <h1 class="page-title">数据库指标仪表盘</h1>
    
    <!-- 刷新按钮 -->
    <div class="refresh-container">
      <button 
        @click="fetchDashboardMetrics()"
        class="refresh-button"
        :disabled="loading"
      >
        <i class="fas fa-sync-alt" :class="{ 'animate-spin': loading }"></i> 刷新数据
      </button>
    </div>
    
    <!-- 指标卡片区域 -->
    <div class="metrics-grid">
      <!-- 事件总数卡片 -->
      <div class="metric-card">
        <div class="metric-header">
          <h3 class="metric-title">事件总数</h3>
          <span class="metric-icon"><i class="fas fa-database"></i></span>
        </div>
        <div class="metric-value">
          <span v-if="loading" class="skeleton">加载中...</span>
          <span v-else-if="error" class="error-text">{{ error }}</span>
          <span v-else class="number">{{ formatNumber(metrics.count1 || 0) }}</span>
        </div>
        <div class="metric-description">数据库中所有事件的总数</div>
      </div>
      
      <!-- 风险事件数卡片 -->
      <div class="metric-card risk-card">
        <div class="metric-header">
          <h3 class="metric-title">风险事件数</h3>
          <span class="metric-icon"><i class="fas fa-exclamation-triangle"></i></span>
        </div>
        <div class="metric-value">
          <span v-if="loading" class="skeleton">加载中...</span>
          <span v-else-if="error" class="error-text">{{ error }}</span>
          <span v-else class="number">{{ formatNumber(metrics.risk_count || 0) }}</span>
        </div>
        <div class="metric-description">标记为风险的事件数量</div>
      </div>
      
      <!-- 平台数量卡片 -->
      <div class="metric-card platform-card">
        <div class="metric-header">
          <h3 class="metric-title">平台数量</h3>
          <span class="metric-icon"><i class="fas fa-layer-group"></i></span>
        </div>
        <div class="metric-value">
          <span v-if="loading" class="skeleton">加载中...</span>
          <span v-else-if="error" class="error-text">{{ error }}</span>
          <span v-else class="number">{{ metrics.platforms?.length || 0 }}</span>
        </div>
        <div class="metric-description">支持的不同平台数量</div>
      </div>
      
      <!-- 字段数量卡片 -->
      <div class="metric-card field-card">
        <div class="metric-header">
          <h3 class="metric-title">字段数量</h3>
          <span class="metric-icon"><i class="fas fa-table-columns"></i></span>
        </div>
        <div class="metric-value">
          <span v-if="loading" class="skeleton">加载中...</span>
          <span v-else-if="error" class="error-text">{{ error }}</span>
          <span v-else class="number">{{ metrics.field_count || 0 }}</span>
        </div>
        <div class="metric-description">数据库中事件记录的字段数量</div>
      </div>
      
      <!-- 数据总量卡片 -->
      <div class="metric-card interaction-card">
        <div class="metric-header">
          <h3 class="metric-title">数据总量</h3>
          <span class="metric-icon"><i class="fas fa-database"></i></span>
        </div>
        <div class="metric-value">
          <span v-if="loading" class="skeleton">加载中...</span>
          <span v-else-if="error" class="error-text">{{ error }}</span>
          <span v-else class="number">{{ formatNumber(metrics.total_nums || 0) }}</span>
        </div>
        <div class="metric-description">数据库中存储的数据总量</div>
      </div>
      
      <!-- 语言数量卡片 -->
      <div class="metric-card language-card">
        <div class="metric-header">
          <h3 class="metric-title">语言数量</h3>
          <span class="metric-icon"><i class="fas fa-language"></i></span>
        </div>
        <div class="metric-value">
          <span v-if="loading" class="skeleton">加载中...</span>
          <span v-else-if="error" class="error-text">{{ error }}</span>
          <span v-else class="number">{{ metrics.languages?.length || 0 }}</span>
        </div>
        <div class="metric-description">支持的不同语言数量</div>
      </div>
    </div>
    
    <!-- 数据表格区域 -->
    <div class="charts-container">
      <!-- 平台分布表格 -->
      <div class="chart-card">
        <h3 class="chart-title">平台分布</h3>
        <div v-if="loading" class="chart-loading">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>
        <div v-else-if="error" class="chart-error">
          <p>{{ error }}</p>
        </div>
        <div v-else class="chart-content">
          <div class="distribution-table">
            <table>
              <thead>
                <tr>
                  <th>平台</th>
                  <th>事件数量</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in metrics.platform_counts" :key="index">
                  <td>{{ item.name }}</td>
                  <td>{{ formatNumber(item.value) }}</td>
                </tr>
                <tr v-if="!metrics.platform_counts || metrics.platform_counts.length === 0">
                  <td colspan="2" class="no-data">暂无数据</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      <!-- 语言分布表格 -->
      <div class="chart-card">
        <h3 class="chart-title">语言分布</h3>
        <div v-if="loading" class="chart-loading">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>
        <div v-else-if="error" class="chart-error">
          <p>{{ error }}</p>
        </div>
        <div v-else class="chart-content">
          <div class="distribution-table">
            <table>
              <thead>
                <tr>
                  <th>语言</th>
                  <th>事件数量</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in metrics.language_counts" :key="index">
                  <td>{{ item.name }}</td>
                  <td>{{ formatNumber(item.value) }}</td>
                </tr>
                <tr v-if="!metrics.language_counts || metrics.language_counts.length === 0">
                  <td colspan="2" class="no-data">暂无数据</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 详细信息区域 -->
    <div class="details-container">
      <!-- 字段信息表格 -->
      <div class="details-card">
        <h3 class="details-title">字段信息</h3>
        <div v-if="loading" class="details-loading">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>
        <div v-else-if="error" class="details-error">
          <p>{{ error }}</p>
        </div>
        <div v-else-if="metrics.fields" class="table-container">
          <table class="details-table">
            <thead>
              <tr>
                <th>序号</th>
                <th>字段名称</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(field, index) in metrics.fields" :key="index">
                <td>{{ index + 1 }}</td>
                <td>{{ field }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- 数据分布详情 -->
      <div class="details-card">
        <h3 class="details-title">数据分布详情</h3>
        <div v-if="loading" class="details-loading">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>
        <div v-else-if="error" class="details-error">
          <p>{{ error }}</p>
        </div>
        <div v-else class="distribution-details">
          <div class="distribution-info">
            <p><strong>平台数量:</strong> {{ metrics.platforms?.length || 0 }}</p>
            <p><strong>语言数量:</strong> {{ metrics.languages?.length || 0 }}</p>
            <p><strong>字段数量:</strong> {{ metrics.field_count || 0 }}</p>
            <p><strong>数据总量:</strong> {{ formatNumber(metrics.total_nums || 0) }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick, onUnmounted } from 'vue';
import { getDashboardMetrics } from '../../service/apiManager';


export default {
  name: 'DashboardView',
  setup() {
    const metrics = ref({});
    const loading = ref(false);
    const error = ref('');
    
    // 格式化数字，添加千位分隔符
    const formatNumber = (num) => {
      return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    };
    
    // 获取仪表盘指标数据
    const fetchDashboardMetrics = async () => {
      loading.value = true;
      error.value = '';
      
      try {
        console.log('======================== START FETCH METRICS ========================');
        console.log('使用真实API数据显示仪表盘内容');
        
        // 调用API获取真实数据
        const response = await getDashboardMetrics();
        const realMetrics = response.data;
        
        console.log('获取到的真实数据:', realMetrics);
        
        // 将对象格式的平台数据转换为数组格式
        if (realMetrics.platform_counts && typeof realMetrics.platform_counts === 'object' && !Array.isArray(realMetrics.platform_counts)) {
          const colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#d35400', '#8e44ad'];
          const platformArray = [];
          let index = 0;
          
          for (const [key, value] of Object.entries(realMetrics.platform_counts)) {
            platformArray.push({
              name: key,
              value: value,
              itemStyle: { color: colors[index % colors.length] }
            });
            index++;
          }
          
          realMetrics.platform_counts = platformArray;
        }
        
        // 将对象格式的语言数据转换为数组格式
        if (realMetrics.language_counts && typeof realMetrics.language_counts === 'object' && !Array.isArray(realMetrics.language_counts)) {
          const languageColors = ['#3498db', '#e74c3c', '#2ecc71'];
          const languageArray = [];
          let index = 0;
          
          for (const [key, value] of Object.entries(realMetrics.language_counts)) {
            languageArray.push({
              name: key,
              value: value,
              itemStyle: { color: languageColors[index % languageColors.length] }
            });
            index++;
          }
          
          realMetrics.language_counts = languageArray;
        }
        
        // 更新metrics数据，确保响应式更新
        console.log('======================== BEFORE UPDATE METRICS ========================');
        console.log('更新前的metrics.value:', metrics.value);
        
        Object.assign(metrics.value, realMetrics);
        console.log('======================== AFTER UPDATE METRICS =========================');
        console.log('更新后的metrics.value:', metrics.value);
        console.log('更新后的关键指标值:');
        console.log('- count1:', metrics.value.count1);
        console.log('- risk_count:', metrics.value.risk_count);
        console.log('- total_nums:', metrics.value.total_nums);
        console.log('- platform_counts:', metrics.value.platform_counts);
        console.log('- language_counts:', metrics.value.language_counts);
        
        // 数据更新完成，无需额外渲染图表，Vue的响应式系统会自动更新表格显示
      } catch (err) {
        console.error('Failed to fetch dashboard metrics:', {
          message: err.message,
          stack: err.stack
        });
        error.value = '获取数据失败，请稍后重试';
      } finally {
        loading.value = false;
      }
    };
    
    // 不需要渲染图表函数，已改为直接显示数据表格
    
    // 不需要处理窗口大小变化，已改为表格显示
    
    // 组件卸载时的处理函数
    onUnmounted(() => {
      // 无需特殊处理，Vue会自动清理
    });
    
    // 组件挂载时获取数据
    onMounted(() => {
      // 等待DOM完全渲染后再获取数据
      nextTick(() => {
        setTimeout(() => {
          fetchDashboardMetrics();
        }, 500); // 延迟500ms确保DOM完全渲染
      });
    });
    
    return {
      metrics,
      loading,
      error,
      fetchDashboardMetrics,
      formatNumber
    };
  }
};
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}

.refresh-container {
  margin-bottom: 20px;
  text-align: right;
}

.refresh-button {
  padding: 8px 16px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  transition: background-color 0.3s;
}

.refresh-button:hover:not(:disabled) {
  background-color: #2980b9;
}

.refresh-button:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.metric-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;
  overflow: hidden;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  height: 4px;
  width: 100%;
  background-color: #3498db;
}

.metric-card.risk-card::before {
  background-color: #e74c3c;
}

.metric-card.platform-card::before {
  background-color: #2ecc71;
}

.metric-card.field-card::before {
  background-color: #f39c12;
}

.metric-card.interaction-card::before {
  background-color: #9b59b6;
}

.metric-card.language-card::before {
  background-color: #1abc9c;
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.metric-title {
  font-size: 16px;
  font-weight: 500;
  color: #666;
  margin: 0;
}

.metric-icon {
  font-size: 20px;
  color: #3498db;
}

.risk-card .metric-icon {
  color: #e74c3c;
}

.platform-card .metric-icon {
  color: #2ecc71;
}

.field-card .metric-icon {
  color: #f39c12;
}

.interaction-card .metric-icon {
  color: #9b59b6;
}

.language-card .metric-icon {
  color: #1abc9c;
}

.metric-value {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.metric-description {
  font-size: 14px;
  color: #999;
}

.skeleton {
  display: inline-block;
  width: 100px;
  height: 36px;
  background-color: #ecf0f1;
  border-radius: 4px;
  animation: skeleton-loading 1.5s infinite;
}

.error-text {
  color: #e74c3c;
  font-size: 16px;
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.chart-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.chart-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}

.chart-content {
  position: relative;
}

.distribution-table {
  width: 100%;
}

.distribution-table table {
  width: 100%;
  border-collapse: collapse;
}

.distribution-table th,
.distribution-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.distribution-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #666;
}

.distribution-table tr:hover {
  background-color: #f8f9fa;
}

.no-data {
  text-align: center;
  color: #999;
  padding: 20px;
}

.chart-loading,
.chart-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #999;
}

.details-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.details-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  max-height: 400px;
  overflow-y: auto;
}

.details-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}

.table-container {
  overflow-x: auto;
}

.details-table {
  width: 100%;
  border-collapse: collapse;
}

.details-table th,
.details-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.details-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #666;
}

.details-table tr:hover {
  background-color: #f8f9fa;
}

.distribution-details {
  padding: 10px 0;
}

.distribution-info p {
  margin: 10px 0;
  color: #666;
  font-size: 15px;
}

.distribution-info strong {
  color: #333;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes skeleton-loading {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 0.9; }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .metrics-grid,
  .charts-container,
  .details-container {
    grid-template-columns: 1fr;
  }
  
  .chart-card,
  .details-card {
    width: 100%;
  }
}
</style>
