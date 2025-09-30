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
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.Event ? selectedEvent.Event : '暂无数据' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">事件ID</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent._id ? selectedEvent._id : '暂无数据' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">发布者</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.account ? selectedEvent.account : '暂无数据' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">发布时间</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.Time ? selectedEvent.Time : '暂无数据' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">平台</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.platform ? selectedEvent.platform : '暂无数据' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">类型</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.Type ? selectedEvent.Type : '暂无数据' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">语言</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.language ? selectedEvent.language : '暂无数据' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">风险类型</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.isRisk ? selectedEvent.isRisk : '暂无数据' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">评论数</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.Comment ? selectedEvent.Comment : '暂无数据' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">点赞数</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.Praise ? selectedEvent.Praise : '暂无数据' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">转发数</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.Reblog ? selectedEvent.Reblog : '暂无数据' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">模态</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.Modal ? selectedEvent.Modal : '暂无数据' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">IP</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.IP ? selectedEvent.IP : '暂无数据' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">工具</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.Tool ? selectedEvent.Tool : '暂无数据' }}</p>
            </div>
            <div class="col-span-2">
              <p class="text-sm font-medium text-gray-500">链接</p>
              <a v-if="selectedEvent && selectedEvent.Link" :href="selectedEvent.Link" target="_blank" rel="noopener noreferrer" class="mt-1 text-base text-blue-600 hover:text-blue-800 break-all">
                {{ selectedEvent.Link }}
              </a>
              <p v-else class="mt-1 text-base text-gray-900">暂无数据</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">地区</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.region ? selectedEvent.region : '暂无数据' }}</p>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-500">前置节点</p>
              <p class="mt-1 text-base text-gray-900">{{ selectedEvent && selectedEvent.Pre_node ? selectedEvent.Pre_node : '暂无数据' }}</p>
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
      availableRegions: ['中国', '美国', '日本', '韩国', '英国', '德国', '法国', '以色列', '巴勒斯坦','哥伦比亚','其他'] // 可用地区列表‘
    }
  },
  mounted() {
    // 获取核心的事件数据
    this.fetchEvents();
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
        
        // 检查响应数据并处理
        if (response && response.data) {
          // 确保results是数组类型
          if (Array.isArray(response.data.results)) {
            this.events = response.data.results
          } else {
            console.warn('响应数据格式异常，results不是数组:', response.data.results)
            this.events = []
          }
          // 确保total是数字类型
          this.total = typeof response.data.total === 'number' ? response.data.total : 0
          this.totalPages = Math.ceil(this.total / this.pageSize)
          console.log(`数据更新完成 - 事件列表: ${this.events.length} 条, 总页数: ${this.totalPages}`);
        } else {
          console.warn('响应数据为空');
          this.events = []
          this.total = 0
          this.totalPages = 0
        }
      } catch (error) {
        // 首先检查error是否存在
        if (!error) {
          console.error('获取事件数据失败: 未知错误');
          // 使用通用方法安全地显示错误消息
          this.showMessage('获取数据失败: 未知错误', 'error');
          this.events = [];
          this.total = 0;
          this.totalPages = 0;
          return;
        }
        
        console.error('获取事件数据失败:', error);
        
        // 更安全的错误详情日志记录
        try {
          console.error('错误详情:', {
            message: error ? (error.message || '无错误消息') : '无错误对象',
            response: error && error.response ? {
              status: error.response.status || '未知状态',
              statusText: error.response.statusText || '未知状态文本',
              data: error.response.data || '无响应数据'
            } : '无响应',
            request: error && error.request ? '请求已发送但未收到响应' : '无请求',
            config: error && error.config ? {
              url: error.config.url || '无URL',
              method: error.config.method || '无方法',
              params: error.config.params || '无参数'
            } : '无配置'
          });
        } catch (logError) {
          console.warn('记录错误详情时出错:', logError);
        }
        
        // 清空事件列表，避免显示旧数据
        this.events = [];
        this.total = 0;
        this.totalPages = 0;
        
        // 显示错误提示 - 增强的防御性编程
        let errorMsg = '获取数据失败';
        
        try {
          if (error && error.response) {
            // 服务器返回了错误状态码
            errorMsg = `获取数据失败: ${error.response.status || '未知状态'} - ${error.response.statusText || '未知错误'}`;
            
            // 用try-catch包裹所有对error.response.data的访问
            try {
              // 检查response.data是否存在
              if (error.response.data) {
                // 尝试获取更具体的错误信息
                if (typeof error.response.data === 'object') {
                  // 使用可选链操作符和安全检查
                  if ('error' in error.response.data && error.response.data.error) {
                    errorMsg = `获取数据失败: ${error.response.data.error}`;
                  } else if ('message' in error.response.data && error.response.data.message) {
                    errorMsg = `获取数据失败: ${error.response.data.message}`;
                  }
                } else if (typeof error.response.data === 'string') {
                  errorMsg = `获取数据失败: ${error.response.data}`;
                }
              }
            } catch (dataError) {
              console.warn('解析错误响应数据时出错:', dataError);
            }
          } else if (error && error.request) {
            // 请求已发出但没有收到响应
            errorMsg = '网络错误，请检查您的网络连接';
          } else if (error && error.message) {
            // 其他错误
            errorMsg = `获取数据失败: ${error.message || '未知错误'}`;
          }
        } catch (e) {
          console.warn('构建错误消息时出错:', e);
          errorMsg = '获取数据失败: 处理错误时发生异常';
        }
        
        // 使用通用方法安全地显示错误消息
        this.showMessage(errorMsg, 'error');
      }
    },
    
    // 安全显示消息的通用方法
    showMessage(message, type = 'error') {
      try {
        if (this.$message && typeof this.$message[type] === 'function') {
          this.$message[type](message);
        } else {
          console.warn(`无法使用this.$message.${type}显示消息`);
          // 使用浏览器原生alert替代
          alert(message);
        }
      } catch (error) {
        console.error('显示消息失败:', error);
        // 即使try-catch失败也尝试显示alert
        try {
          alert(message);
        } catch (alertError) {
          console.error('显示alert也失败:', alertError);
        }
      }
    },
    
    // 独立获取仪表盘数据的方法（非核心功能）
    async fetchDashboardMetrics() {
      try {
        console.log('开始获取仪表盘数据...');
        const response = await getDashboardMetrics();
        console.log('仪表盘数据获取成功:', response.status || '默认数据');
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
      console.log('执行搜索操作');
      console.log('搜索参数:', {
        keyword: this.searchKeyword,
        platform: this.selectedPlatform,
        region: this.selectedRegion,
        month: this.selectedMonth,
        page: 1,
        pageSize: this.pageSize
      });
      
      // 重置页码为1
      this.page = 1;
      // 重新获取数据
      this.fetchEvents();
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
        
        // 加强防御性编程 - 首先检查response是否存在
        if (!response) {
          console.error('导出请求未返回响应');
          // 安全显示错误消息
          this.showMessage('导出失败: 未收到响应', 'error');
          return;
        }
        
        // 检查响应是否为Blob类型
        try {
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
            
            // 安全显示成功消息
            this.showMessage('数据导出成功', 'success')
          } else {
            // 尝试将响应数据解析为JSON（兼容旧版本）
            try {
              // 多层安全检查
              if (response.data && typeof response.data === 'object') {
                const data = response.data
                if (data && data.results && Array.isArray(data.results)) {
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
                  
                  this.$message.success('数据导出成功')
                } else {
                  console.warn('导出数据格式不支持:', data)
                  // 安全显示错误消息
                  this.showMessage('导出失败: 数据格式不支持', 'error')
                }
              } else {
                console.warn('导出响应数据类型异常:', typeof response.data)
                // 安全显示错误消息
                this.showMessage('导出失败: 响应数据异常', 'error')
              }
            } catch (jsonError) {
              console.error('解析导出数据失败:', jsonError)
              // 安全显示错误消息
              this.showMessage('导出失败: 数据解析错误', 'error')
            }
          }
        } catch (downloadError) {
          console.error('处理下载过程中出错:', downloadError)
          // 安全显示错误消息
          this.showMessage('导出失败: 下载处理错误', 'error')
        }
      } catch (error) {
        console.error('导出数据失败:', error);
        // 更安全的错误信息获取逻辑
        try {
          let errorMsg = '未知错误';
          
          try {
            if (error) {
              if (error.response) {
                // 服务器返回了错误状态码
                errorMsg = `服务器错误: ${error.response.status || '未知状态'}`;
                
                // 使用try-catch包裹所有对error.response.data的访问
                try {
                  // 安全地检查error.response.data中的详细信息
                  if (error.response.data) {
                    if (typeof error.response.data === 'object') {
                      if ('error' in error.response.data && error.response.data.error) {
                        errorMsg = error.response.data.error;
                      } else if ('message' in error.response.data && error.response.data.message) {
                        errorMsg = error.response.data.message;
                      }
                    } else if (typeof error.response.data === 'string') {
                      errorMsg = error.response.data;
                    }
                  }
                } catch (dataError) {
                  console.warn('解析错误响应数据时出错:', dataError);
                }
              } else if (error.request) {
                // 请求已发出但没有收到响应
                errorMsg = '网络错误: 请求超时';
              } else if (error.message) {
                // 其他错误
                errorMsg = error.message;
              }
            }
            
            // 安全地显示错误消息
            try {
              this.$message.error(`导出失败: ${errorMsg}`);
            } catch (msgError) {
              console.error('显示错误消息失败:', msgError);
            }
          } catch (errMsgError) {
            console.error('构建错误消息时出错:', errMsgError);
            try {
              this.$message.error('导出失败: 处理错误时发生异常');
            } catch (msgError) {
              console.error('显示错误消息失败:', msgError);
            }
          }
        } catch (errMsgError) {
          console.error('构建错误消息时出错:', errMsgError);
          this.$message.error('导出失败: 处理错误时发生异常');
        }
      }
    },
    changePage(newPage) {
      if (newPage >= 1 && newPage <= this.totalPages) {
        this.page = newPage
        this.fetchEvents()
      }
    },
    viewEventDetail(event) {
      // 增强防御性编程，确保event存在且为对象
      try {
        if (!event || typeof event !== 'object') {
          console.warn('尝试查看详情的事件数据无效:', event);
          this.$message.warning('事件数据无效，无法查看详情');
          return;
        }
        // 创建一个深拷贝，避免直接修改原事件对象
        this.selectedEvent = JSON.parse(JSON.stringify(event));
        this.showDetail = true;
        console.log('成功显示事件详情');
      } catch (error) {
        console.error('显示事件详情失败:', error);
        this.$message.error('显示详情时发生错误');
        // 确保selectedEvent始终是一个安全的对象
        this.selectedEvent = {};
        this.showDetail = false;
      }
    },
    closeDetail() {
      this.showDetail = false;
      // 重置为安全的空对象
      this.selectedEvent = {};
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