<template>
  <div class="page-container">
    <h1 class="page-title">风险传播事件库</h1>
    
    <!-- 标签页选择 -->
    <div class="tab-container">
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'all' }"
        @click="switchTab('all')"
      >
        传播事件库
      </div>
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'risk' }"
        @click="switchTab('risk')"
      >
        风险事件库
      </div>
    </div>
    
    <!-- 搜索和筛选区域 -->
    <div class="search-filter-container">
      <div class="platform-filter mb-4">
        <label class="filter-label">平台筛选：</label>
        <select 
          v-model="selectedPlatform" 
          class="platform-select"
          @change="handlePlatformChange"
        >
          <option value="">全部平台</option>
          <option value="微博">微博</option>
          <option value="百度">百度</option>
          <option value="推特">推特</option>
          <option value="中国互联网联合辟谣平台">中国互联网联合辟谣平台</option>
          <option value="人民日报">人民日报</option>
          <option value="人民网">人民网</option>
          <option value="微信">微信</option>
          <option value="腾讯新闻">腾讯新闻</option>
        </select>
      </div>
      
      <!-- 搜索框和筛选条件 -->
      <div class="search-filters">
        <div class="search-item">
          <label class="filter-label">关键词：</label>
          <input 
            type="text" 
            v-model="searchKeyword"
            placeholder="输入关键词搜索"
            class="search-input"
          />
        </div>
        
        <div class="search-item">
          <label class="filter-label">地区：</label>
          <select 
            v-model="selectedRegion" 
            class="platform-select"
          >
            <option value="">全部地区</option>
            <option v-for="region in availableRegions" :key="region" :value="region">
              {{ region }}
            </option>
          </select>
        </div>
        
        <div class="search-item">
          <label class="filter-label">发生年月：</label>
          <input 
            type="month" 
            v-model="selectedMonth"
            class="datetime-input"
          />
        </div>
        
        <div class="search-item">
          <button 
            @click="handleSearch"
            class="search-button"
          >
            搜索
          </button>
          <button 
            @click="handleReset"
            class="reset-button"
          >
            重置
          </button>
          <button 
            @click="handleExport"
            class="export-button"
          >
            导出数据
          </button>
        </div>
      </div>
    </div>
    
    <!-- 事件列表表格 -->
    <div class="table-container bg-white rounded-lg shadow-sm overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              事件ID
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              事件内容
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              发布者
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              时间
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              平台
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              操作
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <template v-if="events.length > 0">
            <tr v-for="event in events" :key="event._id">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ event._id }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 max-w-xs truncate">{{ event.Event }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ event.account }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ event.Time }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ event.platform }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button @click="viewEventDetail(event)" class="text-blue-600 hover:text-blue-900">
                  查看详情
                </button>
              </td>
            </tr>
          </template>
          <tr v-else>
            <td colspan="6" class="px-6 py-10 text-center text-gray-500">
              暂无数据
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- 分页控件 -->
    <div class="pagination-container flex justify-between items-center mt-4">
      <div class="text-sm text-gray-500">
        共 {{ total }} 条数据，第 {{ page }}/{{ totalPages }} 页
      </div>
      <div class="flex space-x-2">
        <button 
          @click="changePage(page - 1)" 
          :disabled="page <= 1"
          class="px-4 py-2 border rounded text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          上一页
        </button>
        <button 
          @click="changePage(page + 1)" 
          :disabled="page >= totalPages"
          class="px-4 py-2 border rounded text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          下一页
        </button>
      </div>
    </div>
    
    <!-- 详情弹窗 -->
    <div v-if="showDetail" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h3 class="text-lg font-medium text-gray-900">事件详情</h3>
          <button @click="closeDetail" class="text-gray-400 hover:text-gray-500 focus:outline-none">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="px-6 py-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="col-span-2">
              <p class="text-sm font-medium text-gray-500">事件内容</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.Event }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">事件ID</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent._id }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">发布者</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.account }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">发布时间</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.Time }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">平台</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.platform }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">类型</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.Type }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">语言</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.language }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">风险类型</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.isRisk }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">评论数</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.Comment }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">点赞数</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.Praise }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">转发数</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.Reblog }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">模态</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.Modal }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">IP</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.IP }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">工具</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.Tool }}</p>
            </div>
            <div class="col-span-2">
              <p class="text-sm font-medium text-gray-500">链接</p>
              <a :href="selectedEvent.Link" target="_blank" rel="noopener noreferrer" class="mt-1 text-base text-blue-600 hover:text-blue-800 break-all">
                {{ selectedEvent.Link }}
              </a>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">地区</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.region }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">前置节点</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent.Pre_node }}</p>
            </div>
          </div>
        </div>
        <div class="px-6 py-4 bg-gray-50 rounded-b-lg flex justify-end">
          <button @click="closeDetail" class="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none">
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getRiskEvents, getAllEvents, exportEvents, getDashboardMetrics } from '../../service/apiManager'

export default {
  name: 'RiskView',
  data() {
    return {
      events: [],
      page: 1,
      pageSize: 10,
      total: 0,
      totalPages: 0,
      showDetail: false,
      selectedEvent: {},
      activeTab: 'all', // 'all' 表示传播事件库，'risk' 表示风险事件库
      selectedPlatform: '', // 选中的平台，空字符串表示全部平台
      searchKeyword: '', // 搜索关键词
      selectedRegion: '', // 选中的地区，空字符串表示全部地区
      selectedMonth: '', // 发生年月
      availableRegions: ['中国', '美国', '日本', '韩国', '英国', '德国', '法国', '其他'] // 可用地区列表
    }
  },
  mounted() {
    // 首先获取核心的事件数据
    this.fetchEvents();
    // 然后独立获取仪表盘数据，使用Promise.all确保即使失败也不影响主功能
    Promise.all([
      this.fetchDashboardMetrics()
    ]).catch(error => {
      console.warn('部分非核心数据获取失败，但页面仍可正常使用:', error);
    });
  },
  methods: {
    // 获取事件数据（核心功能）
    async fetchEvents() {
      try {
        console.log('开始获取事件数据...');
        console.log(`当前标签页: ${this.activeTab}, 页码: ${this.page}, 每页数量: ${this.pageSize}`);
        console.log(`筛选条件 - 平台: ${this.selectedPlatform}, 关键词: ${this.searchKeyword}, 地区: ${this.selectedRegion}`);
        
        // 将选中的月份同时作为开始和结束时间传递给后端
        let formattedStartTime = ''
        let formattedEndTime = ''
        
        if (this.selectedMonth) {
          formattedStartTime = this.selectedMonth
          formattedEndTime = this.selectedMonth
          console.log(`时间筛选: ${formattedStartTime}`);
        }
        
        // 记录请求开始时间
        const startTime = Date.now();
        
        // 根据当前选中的标签页决定调用哪个API
        let response
        if (this.activeTab === 'risk') {
          console.log('调用getRiskEvents API');
          response = await getRiskEvents(
            this.page, 
            this.pageSize, 
            this.selectedPlatform,
            this.searchKeyword,
            this.selectedRegion,
            formattedStartTime,
            formattedEndTime
          )
        } else {
          console.log('调用getAllEvents API');
          response = await getAllEvents(
            this.page, 
            this.pageSize, 
            this.selectedPlatform,
            this.searchKeyword,
            this.selectedRegion,
            formattedStartTime,
            formattedEndTime
          )
        }
        
        // 记录请求结束时间
        const endTime = Date.now();
        console.log(`事件数据请求成功，耗时: ${endTime - startTime}ms`);
        console.log(`返回数据量: ${response.data?.results?.length || 0} 条, 总数据量: ${response.data?.total || 0} 条`);
        
        if (response.data) {
          this.events = response.data.results || []
          this.total = response.data.total || 0
          this.totalPages = Math.ceil(this.total / this.pageSize)
          console.log(`数据更新完成 - 事件列表: ${this.events.length} 条, 总页数: ${this.totalPages}`);
        }
      } catch (error) {
        console.error('获取事件数据失败:', error);
        console.error('错误详情:', {
          message: error.message,
          response: error.response ? {
            status: error.response.status,
            statusText: error.response.statusText,
            data: error.response.data
          } : undefined,
          request: error.request ? '请求已发送但未收到响应' : undefined,
          config: error.config ? {
            url: error.config.url,
            method: error.config.method,
            params: error.config.params
          } : undefined
        });
        
        // 清空事件列表，避免显示旧数据
        this.events = [];
        this.total = 0;
        this.totalPages = 0;
        
        // 显示错误提示
        if (error.response) {
          // 服务器返回了错误状态码
          this.$message.error(`获取数据失败: ${error.response.status} - ${error.response.statusText}`);
        } else if (error.request) {
          // 请求已发出但没有收到响应
          this.$message.error('网络错误，请检查您的网络连接');
        } else {
          // 其他错误
          this.$message.error(`获取数据失败: ${error.message}`);
        }
      }
    },
    
    // 独立获取仪表盘数据的方法（非核心功能）
    async fetchDashboardMetrics() {
      try {
        console.log('开始获取仪表盘数据...');
        const response = await getDashboardMetrics();
        console.log('仪表盘数据获取成功:', response.status);
        // 如果需要使用仪表盘数据，可以在这里处理
      } catch (error) {
        console.warn('获取仪表盘数据失败，但不影响页面主要功能:', error ? error.message || error : '未知错误');
        // 不抛出错误，允许页面继续加载
      }
    },
    
    switchTab(tab) {
      if (this.activeTab !== tab) {
        this.activeTab = tab
        this.page = 1 // 切换标签页时重置到第一页
        this.fetchEvents()
      }
    },
    
    handlePlatformChange() {
      this.page = 1 // 切换平台时重置到第一页
      this.fetchEvents()
    },
    
    // 处理搜索
    handleSearch() {
      this.page = 1 // 搜索时重置到第一页
      this.fetchEvents()
    },
    
    // 重置搜索条件
    handleReset() {
      this.searchKeyword = ''
      this.selectedRegion = ''
      this.selectedMonth = ''
      this.selectedPlatform = ''
      this.page = 1
      this.fetchEvents()
    },

    // 导出数据
    async handleExport() {
      try {
        // 将选中的月份同时作为开始和结束时间传递给后端
        let formattedStartTime = ''
        let formattedEndTime = ''
        
        if (this.selectedMonth) {
          formattedStartTime = this.selectedMonth
          formattedEndTime = this.selectedMonth
        }
        
        // 获取要导出的数据
        const response = await exportEvents(
          this.searchKeyword, 
          this.selectedRegion, 
          formattedStartTime, 
          formattedEndTime, 
          this.activeTab === 'risk' ? 'true' : '', 
          this.selectedPlatform
        )
        
        // 检查响应是否为Blob类型
        if (response.data instanceof Blob) {
          // 创建下载链接
          const url = URL.createObjectURL(response.data)
          const link = document.createElement('a')
          link.href = url
          // 设置文件名，包含导出时间
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
          link.download = `events_export_${timestamp}.json`
          // 触发下载
          document.body.appendChild(link)
          link.click()
          // 清理
          document.body.removeChild(link)
          URL.revokeObjectURL(url)
          
          alert('数据导出成功')
        } else {
          // 尝试将响应数据解析为JSON（兼容旧版本）
          try {
            const data = response.data
            if (data && data.results) {
              const dataStr = JSON.stringify(data.results, null, 2)
              const dataBlob = new Blob([dataStr], { type: 'application/json' })
              const url = URL.createObjectURL(dataBlob)
              const link = document.createElement('a')
              link.href = url
              const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
              link.download = `events_export_${timestamp}.json`
              document.body.appendChild(link)
              link.click()
              document.body.removeChild(link)
              URL.revokeObjectURL(url)
              
              alert(`成功导出 ${data.total || 0} 条数据`)
            }
          } catch (jsonError) {
            console.error('解析响应数据失败:', jsonError)
            alert('导出数据失败，请稍后重试')
          }
        }
      } catch (error) {
        console.error('导出数据失败:', error)
        alert('导出数据失败，请稍后重试')
      }
    },
    changePage(newPage) {
      if (newPage >= 1 && newPage <= this.totalPages) {
        this.page = newPage
        this.fetchEvents()
      }
    },
    viewEventDetail(event) {
      this.selectedEvent = event
      this.showDetail = true
    },
    closeDetail() {
      this.showDetail = false
      this.selectedEvent = {}
    }
  }
}
</script>

<style scoped>
.page-container {
  padding: 20px;
  min-height: 100vh;
  background-color: #f9fafb;
}
.page-title {
    font-size: 24px;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 24px;
  }
  
  /* 标签页样式 */
  .tab-container {
    display: flex;
    margin-bottom: 20px;
    border-bottom: 1px solid #e2e8f0;
  }
  
  .tab-item {
    padding: 10px 20px;
    cursor: pointer;
    color: #4a5568;
    font-size: 16px;
    border-bottom: 2px solid transparent;
    transition: all 0.2s ease;
  }
  
  .tab-item:hover {
    color: #2c5282;
  }
  
  .tab-item.active {
    color: #2c5282;
    font-weight: 600;
    border-bottom-color: #2c5282;
  }
  
  /* 搜索和筛选区域样式 */
  .search-filter-container {
    margin-bottom: 20px;
    padding: 15px;
    background-color: #f7fafc;
    border-radius: 8px;
  }
  
  .platform-filter {
    display: flex;
    align-items: center;
  }
  
  /* 搜索和筛选区域样式 */
  .search-filters {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    align-items: flex-end;
  }
  
  .search-item {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
  }
  
  .search-input,
  .datetime-input {
    padding: 8px 12px;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    font-size: 14px;
    width: 200px;
  }
  
  .search-input:focus,
  .datetime-input:focus {
    outline: none;
    border-color: #2c5282;
    box-shadow: 0 0 0 2px rgba(44, 82, 130, 0.1);
  }
  
  .search-button,
  .reset-button,
  .export-button {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    margin-left: 5px;
  }
  
  .search-button {
    background-color: #2c5282;
    color: white;
  }
  
  .search-button:hover {
    background-color: #2a4365;
  }
  
  .reset-button {
    background-color: #718096;
    color: white;
  }
  
  .reset-button:hover {
    background-color: #4a5568;
  }
  
  .export-button {
    background-color: #38a169;
    color: white;
  }
  
  .export-button:hover {
    background-color: #2f855a;
  }
  
  .filter-label {
    margin-right: 10px;
    font-size: 14px;
    color: #4a5568;
    font-weight: 500;
  }
  
  .platform-select {
    padding: 8px 12px;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    font-size: 14px;
    background-color: white;
    cursor: pointer;
    min-width: 120px;
  }
  
  .platform-select:focus {
    outline: none;
    border-color: #2c5282;
    box-shadow: 0 0 0 2px rgba(44, 82, 130, 0.1);
  }
.table-container {
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}
.pagination-container {
  margin-top: 1.5rem;
}
</style>