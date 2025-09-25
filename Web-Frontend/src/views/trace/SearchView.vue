<template>
  <div class="search-view">
    <!-- 溯源查询区域 -->
    <div class="bg-white rounded-xl shadow-lg p-6 mb-6">
      <h3 class="text-xl font-semibold text-gray-800 mb-4"> 溯源查询</h3>
      
      <div class="space-y-6">
        <!-- 查询框 -->
        <div class="w-full">
          <label for="queryContent" class="block text-base font-medium text-gray-700 mb-1">查询内容</label>
          <div class="relative">
            <textarea 
              v-model="queryContent" 
              id="queryContent" 
              class="w-full px-4 py-3 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all duration-300 resize-y"
              placeholder="请输入查询内容"
              rows="3"
              style="min-height: 100px;"
            ></textarea>
            <!-- 添加清除按钮 -->
            <button 
              v-if="queryContent"
              @click="queryContent = ''"
              class="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
            >
              <i class="fa fa-times"></i>
            </button>
          </div>
        </div>

        <!-- 上传文件按钮和拖拽区域 -->
        <div class="relative">
          <!-- 上传区域 -->
          <label 
            class="flex flex-col items-center justify-center w-full mx-auto border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors duration-300 py-2 min-h-[100px]"
            @dragover.prevent="onDragOver"
            @dragleave.prevent="onDragLeave"
            @drop.prevent="onDrop"
          >
            <!-- 图标和提示文字 -->
            <i class="fa fa-cloud-upload text-gray-500 mb-3 text-2xl"></i>
            <span 
              :class="{
                'text-green-600': uploadStatus.includes('✅'),
                'text-red-600': uploadStatus.includes('❌'),
                'text-gray-600': !uploadStatus
              }"
              class="text-center"
            >
              {{ uploadStatus || '点击上传文件或拖放文件至此处' }}
            </span>
            
            <!-- 文件输入（隐藏） -->
            <input 
              type="file" 
              class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              @change="handleFileUpload" 
              :accept="contentType === 'image' ? 'image/*' : contentType === 'video' ? 'video/*' : '*'"
            />
          </label>
          
          <!-- 移除按钮（放在label外部） -->
          <button
            v-if="selectedFile"
            @click="selectedFile = null; uploadStatus = ''"
            class="absolute -top-3 -right-3 bg-white px-2 py-1 rounded-full shadow-md text-red-500 hover:text-red-700"
          >
            <i class="fa fa-times-circle"></i>
          </button>
        </div>
        
        <!-- 内容类型选择和查询按钮 -->
        <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div class="flex items-center gap-6 flex-wrap">
            <div class="flex items-center">
              <input type="radio" id="textType" v-model="contentType" value="text" class="mr-2">
              <label for="textType" class="text-gray-700">文本</label>
            </div>
            <div class="flex items-center">
              <input type="radio" id="imageType" v-model="contentType" value="image" class="mr-2">
              <label for="imageType" class="text-gray-700">图片</label>
            </div>
            <div class="flex items-center">
              <input type="radio" id="videoType" v-model="contentType" value="video" class="mr-2">
              <label for="videoType" class="text-gray-700">视频</label>
            </div>
          </div>
          
          <button 
            @click="executeSearch" 
            class="query-button"
          >
            <i class="fa fa-search mr-2"></i> 查询
          </button>
        </div>
        <!-- 添加错误信息显示 -->
        <div v-if="traceStore.errorMessage" class="text-red-500 text-sm mt-2 animate-fade-in">
          <i class="fa fa-exclamation-circle mr-1"></i>{{ traceStore.errorMessage }}
        </div>
      </div>
    </div>
    
    <!-- 结果展示区域 -->
    <div class="bg-white rounded-xl shadow-lg p-6 mb-6">
      <!-- 添加筛选控件和标题容器 -->
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xl font-semibold text-gray-800">查询结果</h3>
        <div class="platform-filter">
          <select v-model="traceStore.selectedPlatform" class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all">
              <option value="">全部平台</option>
              <option value="微博">微博</option>
              <option value="百家号">百家号</option>
              <option value="网易新闻">网易新闻</option>
              <option value="今日头条">今日头条</option>
          </select>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="traceStore.loading" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p class="mt-2 text-gray-500">正在查询数据...</p>
      </div>
      
      <!-- 结果表格 -->
      <div v-else>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-center text-sm font-medium text-gray-500 uppercase tracking-wider">序号</th>
                <th class="px-6 py-3 text-center text-sm font-medium text-gray-500 uppercase tracking-wider">稿件(推文)</th>
                <th class="px-6 py-3 text-center text-sm font-medium text-gray-500 uppercase tracking-wider">平台</th>
                <th class="px-6 py-3 text-center text-sm font-medium text-gray-500 uppercase tracking-wider">作者</th>
                <th class="px-6 py-3 text-center text-sm font-medium text-gray-500 uppercase tracking-wider">发布时间</th>
                <!-- <th class="px-6 py-3 text-center text-sm font-medium text-gray-500 uppercase tracking-wider">图片</th>
                <th class="px-6 py-3 text-center text-sm font-medium text-gray-500 uppercase tracking-wider">视频</th> -->
                <th class="px-6 py-3 text-center text-sm font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">是否为源头</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="(item, index) in traceStore.paginatedResults" :key="item.id || index" class="hover:bg-gray-50 transition-colors">
                <!-- 添加序号列 -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-center">{{ (traceStore.currentPage - 1) * 10 + index + 1 }}</td>
                
                <!-- 修改稿件列为全部可点击跳转 -->
                <td class="px-6 py-4 text-sm text-gray-700 max-w-xs truncate">
                  <a 
                    @click="switchToPathWithId({ id: item.id, event: item.event })" 
                    class="text-primary hover:text-primary/80 hover:underline cursor-pointer font-medium"
                  >
                    {{ item.content }}
                  </a>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-center">{{ item.datasource }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-center">{{ item.uname }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-center">{{ formatDate(item.publishtime) }}</td>
                <!-- <td class="px-6 py-4 whitespace-nowrap text-sm text-center">
                  <a v-if="item.imageUrl" href="#" @click.prevent="viewImage(item.imageUrl)"  target="_blank" class="text-primary hover:underline flex items-center justify-center">
                    <i class="fa fa-image mr-1"></i> 查看
                  </a>
                  <span v-else class="text-gray-400">Null</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-center">
                  <a v-if="item.videoUrl" href="#" @click.prevent="viewVideo(item.videoUrl)"  target="_blank" class="text-primary hover:underline flex items-center justify-center">
                    <i class="fa fa-video-camera mr-1"></i> 查看
                  </a>
                  <span v-else class="text-gray-400">Null</span>
                </td> -->
                <td class="px-6 py-4 whitespace-nowrap text-center">
                  <span 
                    :class="item.isSource ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'"
                    class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                  >
                    {{ item.isSource ? '是' : '否' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 添加分页控件 -->
        <div class="flex justify-center mt-4 pagination-controls items-center space-x-2">
          <span class="text-sm text-gray-500 leading-none">10条/页</span>
          <button 
            @click="traceStore.prevPage()"
            :disabled="traceStore.currentPage === 1"
            class="px-2 py-1 border rounded disabled:opacity-50 text-sm flex items-center justify-center"
          >
            <i class="fa fa-chevron-left"></i>
          </button>
          <span class="px-2 py-1 text-sm text-gray-500 leading-none">
            {{ traceStore.currentPage }} / {{ traceStore.totalPages }}
          </span>
          <button 
            @click="traceStore.nextPage()"
            :disabled="traceStore.currentPage === traceStore.totalPages"
            class="px-2 py-1 border rounded disabled:opacity-50 text-sm flex items-center justify-center"
          >
            <i class="fa fa-chevron-right"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 添加媒体查看模态框 -->
    <div v-if="showImageModal" class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto">
        <button @click="showImageModal = false" class="absolute top-4 right-4 text-white text-2xl">×</button>
        <ImageShow :imageUrl="currentMediaUrl" @close="showImageModal = false" />
      </div>
    </div>

    <div v-if="showVideoModal" class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto">
        <button @click="showVideoModal = false" class="absolute top-4 right-4 text-white text-2xl">×</button>
        <VideoShow :videoUrl="currentMediaUrl" @close="showVideoModal = false" />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useTraceStore } from '../../store/traceStore';
import ImageShow from './ImageShow.vue';
import VideoShow from './VideoShow.vue';
import { 
  searchTraceByText, 
  searchTraceByImage, 
  searchTraceByVideo, 
  uploadFile 
} from '../../service/apiManager.js';
import { formatDate } from '../../utils/date.js';

export default {
  name: 'SearchView',
  components: {
    ImageShow,
    VideoShow
  },
  setup() {
    const router = useRouter();
    const traceStore = useTraceStore();
    
    // 溯源查询相关变量
    const queryContent = ref('');
    const contentType = ref('text'); // text, image, video
    const selectedFile = ref(null);
    const uploadStatus = ref(''); // 上传状态提示
    const threshold = ref(0.5); // 文本查询阈值
    const topK = ref(5); // 图片/视频查询Top k数量

    const showImageModal = ref(false);
    const showVideoModal = ref(false);
    const currentMediaUrl = ref('')
    
    // 计算属性：根据内容类型返回当前值
    const currentValue = computed({
      get() {
        return contentType.value === 'text' ? threshold.value : topK.value;
      },
      set(newValue) {
        if (contentType.value === 'text') {
          threshold.value = newValue;
        } else {
          topK.value = newValue;
        }
      }
    });
    
    // 监听筛选条件变化
    watch(() => traceStore.selectedPlatform, () => {
      traceStore.setCurrentPage(1);
    });
    
    // 文件拖拽处理函数
    const onDragOver = (e) => {
      e.target.classList.add('border-blue-400', 'bg-blue-50');
    };
    const onDragLeave = (e) => {
      e.target.classList.remove('border-blue-400', 'bg-blue-50');
    };
    const onDrop = (e) => {
      const files = e.dataTransfer.files;
      if (files.length === 0) return;
      // 模拟 input 的 change 事件
      const fakeEvent = {
        target: { files }
      };
      handleFileUpload(fakeEvent);
    };



    // 溯源查询方法
    const executeSearch = async () => {
      // 重置错误信息和分页
      traceStore.setErrorMessage('');
      traceStore.resetPagination(); // 新增：重置分页到第一页
      // 开始加载状态
      traceStore.setLoading(true);

      try {
        let responseData = null;

        // 验证查询类型与文件匹配
        if ((contentType.value === 'image' || contentType.value === 'video') && !selectedFile.value) {
          traceStore.setErrorMessage(`请上传${contentType.value === 'image' ? '图片' : '视频'}文件`);
          traceStore.setLoading(false);
          return;
        }
        if (contentType.value === 'image' && selectedFile.value?.type.split('/')[0] !== 'image') {
          traceStore.setErrorMessage("当前选择的是图片查询，请上传图片文件"); 
          traceStore.setLoading(false);
          return;
        }
        if (contentType.value === 'video' && selectedFile.value?.type.split('/')[0] !== 'video') {
          traceStore.setErrorMessage("当前选择的是视频查询，请上传视频文件"); 
          traceStore.setLoading(false);
          return;
        }

        // 1. 文本查询
        if (contentType.value === 'text') {
          if (!queryContent.value.trim()) {
            traceStore.setErrorMessage("请输入查询文本");
            traceStore.setLoading(false);
            return;
          }
          const textResponse = await searchTraceByText(queryContent.value, currentValue.value);
          responseData = textResponse.data.search_results;
        } 
        // 2. 图片查询
        else if (contentType.value === 'image') {
          const imgResponse = await searchTraceByImage(selectedFile.value, currentValue.value);
          responseData = imgResponse.data.search_results;
        }
        // 3. 视频查询
        else if (contentType.value === 'video') {
          const videoResponse = await searchTraceByVideo(selectedFile.value, currentValue.value, {timeout: 60000});
          responseData = videoResponse.data.search_results;
        }
        // 统一处理所有类型查询结果中的平台名称替换
        const formattedResults = responseData.map(item => ({
          ...item,
          datasource: item.datasource === 'weibo' ? '微博' : item.datasource
        }));

        // 存储结果到store
        traceStore.setResults(formattedResults);
        
      } catch (error) {
        console.error('查询失败:', error);
        traceStore.setErrorMessage(error.response?.data?.error || '查询过程中发生错误，请重试');
      } finally {
        traceStore.setLoading(false);
      }
    };

    // 查看媒体方法
    const viewImage = (url) => {
      currentMediaUrl.value = url;
      showImageModal.value = true;
    };
    const viewVideo = (url) => {
      currentMediaUrl.value = url;
      showVideoModal.value = true;
    };
    const closeModal = () => {
      showImageModal.value = false;
      showVideoModal.value = false;
    };
    
    // 修改原ID列的切换函数，明确指定接口类型
    const switchToPathWithId = async (params) => {
      const { id, event } = params;
      console.log('SearchView点击事件触发，ID:', id, 'Event:', event);
      // 仅验证ID
      if (!id) {
        traceStore.setErrorMessage("ID不存在");
        return;
      }
      // 发射事件，event可选
      router.push({ path: '/path', query: { id, event } });
    };

    // 文件上传处理函数
    const handleFileUpload = async (e) => {
      const file = e.target?.files?.[0];
      if (!file) return;

      // 重置状态
      traceStore.setErrorMessage('');
      uploadStatus.value = '';

      // 类型验证
      const fileType = file.type.split('/')[0];
      if (contentType.value === 'image' && fileType !== 'image') {
        uploadStatus.value = '❌ 请上传图片文件';
        return;
      }
      if (contentType.value === 'video' && fileType !== 'video') {
        uploadStatus.value = '❌ 请上传视频文件';
        return;
      }
      selectedFile.value = file;
      uploadStatus.value = '📤 正在上传...';

      try {
        const response = await uploadFile(file);
        if (response.status === 200) {
          uploadStatus.value = `✅ 上传成功：${file.name}`;
        } else {
          uploadStatus.value = `❌ 上传失败：${response.data.message || '服务器错误'}`;
        }
      } catch (error) {
        uploadStatus.value = `❌ 网络错误：${error.message}`;
      }
    };

    return {
      queryContent,
      contentType,
      selectedFile,
      uploadStatus,
      threshold,
      topK,
      currentValue,  // 计算属性：用于v-model绑定
      executeSearch,
      onDragOver,
      onDragLeave,
      onDrop,
      handleFileUpload,
      formatDate,
      viewImage,
      viewVideo,
      switchToPathWithId,
      showImageModal,  // 控制图片模态框显示
      showVideoModal,  // 控制视频模态框显示
      currentMediaUrl, // 存储当前预览的媒体URL
      closeModal,
      traceStore, // 添加store引用
      // 从store中解构所需的状态和方法
      ...traceStore
    };
  }
};
</script>

<style scoped>
/* 原内容样式适配 */
.search-view {
  width: 100%;
}

.query-button {
  background-color: var(--primary-color); /* 使用主题色 */
  color: #fff;
  font-weight: 500;
  padding: 0.5rem 1.5rem;
  border-radius: 0.5rem;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: linear-gradient(to bottom, #1890ff, #1479e6);
}

.query-button:hover {
  background-color: #1479e6;
  box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15), 0 2px 4px rgba(0, 0, 0, 0.1);
}

.query-button:active {
  transform: scale(0.98); /* 点击时缩小按钮 */
}

.query-button i {
  margin-right: 0.5rem; /* 图标与文字的间距 */
}

/* 确保表格在侧边栏切换时能正确适应宽度 */
.overflow-x-auto {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

/* 按钮和交互元素样式统一 */
button {
  cursor: pointer;
}

/* 动画效果 */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 定义主题色变量 */
:root {
  --primary-color: #1890ff;
}

.text-primary {
  color: #1890ff !important;
}

.border-primary {
  border-color: #1890ff !important;
}

.bg-primary {
  background-color: #1890ff !important;
}

.focus\:ring-primary\/50:focus {
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.5) !important;
}

.focus:border-primary:focus {
  border-color: #1890ff !important;
}

/* 自定义标题字体大小 */
.search-view h3 {
  font-size: 22px !important; /* 覆盖text-xl */
}

/* 自定义查询内容标签字体大小 */
.search-view label[for="queryContent"] {
  font-size: 15px !important; /* 覆盖text-sm */
}

/* 自定义表格表头字体大小 */
.search-view thead th {
  font-size: 13px !important; /* 覆盖text-xs */
}

/* 分页控件样式 */
.pagination-controls {
  color: #4B5563; /* 文本颜色 */
  align-items: center; /* 确保内容垂直居中 */
}

.pagination-controls span {
  line-height: 1; /* 确保文字垂直居中 */
}

.pagination-controls button {
  color: #4B5563; /* 按钮文本颜色 */
  background-color: #F3F4F6; /* 按钮背景色 */
  border-color: #D1D5DB; /* 按钮边框色 */
  display: flex;
  align-items: center; /* 图标和文字垂直居中 */
  justify-content: center;
}

.pagination-controls button:hover:not(:disabled) {
  color: #1F2937; /* 悬停时文本颜色 */
  background-color: #E5E7EB; /* 悬停时背景色 */
}

.pagination-controls button:disabled {
  color: #9CA3AF; /* 禁用状态文本颜色 */
}
</style>