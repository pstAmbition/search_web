<template>
  <div class="fake-knowledge-detail">
    <h1 class="page-title">虚假信息详情</h1>
    <!-- 错误提示 -->
    <div v-if="errorMessage" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {{ errorMessage }}
    </div>
    
    <div class="bg-white rounded-xl shadow-lg p-6 mb-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xl font-semibold text-gray-800">虚假信息详情</h3>
        <button 
          class="text-gray-500 hover:text-gray-700 transition-colors"
          @click="goBack"
        >
          <i class="fa fa-arrow-left mr-1"></i> 返回虚假信息知识库
        </button>
      </div>
      
      <!-- 加载状态 -->
      <div v-if="loadingDetail" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p class="mt-2 text-gray-500">正在加载虚假信息详情...</p>
      </div>
      
      <!-- 虚假信息详情 -->
      <div v-else-if="fakeDetail" class="space-y-6">
        <div class="flex justify-between items-start">
          <h4 class="text-lg font-medium text-gray-900">{{ fakeDetail.title }}</h4>
          <span class="bg-red-100 text-red-800 text-xs px-2 py-0.5 rounded font-medium">{{ fakeDetail.info_class || '虚假信息' }}</span>
        </div>
        
        <div class="text-gray-700 whitespace-pre-wrap">
          <p>{{ fakeDetail.text || fakeDetail.content }}</p>
        </div>
        
        <div class="space-y-4 text-sm">
          <!-- 来源、发布日期、ID 一行显示 -->
          <div class="flex flex-wrap gap-4">
            <div class="bg-gray-50 p-3 rounded-lg flex-1 min-w-[180px]">
              <div class="text-gray-500 mb-1">来源</div>
              <div class="font-medium text-gray-900">{{ fakeDetail.source || '未知' }}</div>
            </div>
            <div class="bg-gray-50 p-3 rounded-lg flex-1 min-w-[180px]">
              <div class="text-gray-500 mb-1">发布日期</div>
              <div class="font-medium text-gray-900">{{ formatFullDate(fakeDetail.date) || '未知' }}</div>
            </div>
            <div class="bg-gray-50 p-3 rounded-lg flex-1 min-w-[180px]">
              <div class="text-gray-500 mb-1">ID</div>
              <div class="font-medium text-gray-900">{{ fakeDetail.infoId || fakeDetail.id || '未知' }}</div>
            </div>
          </div>
          
          <!-- 新增人物、地点、议题显示，使用不同颜色 -->
          <div class="flex flex-wrap gap-4">
            <div class="bg-purple-50 p-3 rounded-lg flex-1 min-w-[180px]">
              <div class="text-purple-500 mb-1">人物</div>
              <div class="font-medium text-purple-900">{{ fakeDetail.element_character || '未知' }}</div>
            </div>
            <div class="bg-blue-50 p-3 rounded-lg flex-1 min-w-[180px]">
              <div class="text-blue-500 mb-1">地点</div>
              <div class="font-medium text-blue-900">{{ fakeDetail.element_place || '未知' }}</div>
            </div>
            <div class="bg-green-50 p-3 rounded-lg flex-1 min-w-[180px]">
              <div class="text-green-500 mb-1">议题</div>
              <div class="font-medium text-green-900">{{ fakeDetail.element_topic || '未知' }}</div>
            </div>
          </div>
        </div>
        
        <!-- 互动数据 -->
        <div class="grid grid-cols-3 gap-4 text-sm">
          <div class="bg-blue-50 p-3 rounded-lg">
            <div class="text-gray-500 mb-1">转发数</div>
            <div class="font-medium text-blue-700">{{ fakeDetail.reposts_num || '0' }}</div>
          </div>
          <div class="bg-green-50 p-3 rounded-lg">
            <div class="text-gray-500 mb-1">评论数</div>
            <div class="font-medium text-green-700">{{ fakeDetail.comments_num || '0' }}</div>
          </div>
          <div class="bg-orange-50 p-3 rounded-lg">
            <div class="text-gray-500 mb-1">点赞数</div>
            <div class="font-medium text-orange-700">{{ fakeDetail.likes_num || '0' }}</div>
          </div>
        </div>
      </div>
      
      <!-- 无数据状态 -->
      <div v-else class="text-center py-12">
        <i class="fa fa-search-minus text-gray-300 text-4xl mb-2"></i>
        <p class="text-gray-500">未找到该虚假信息的数据</p>
      </div>
    </div>
    
    <!-- 传播图谱 -->
    <div class="bg-white rounded-xl shadow-lg p-6">
      <!-- 多媒体资源展示 -->
      <div class="mb-8">
        <h3 class="text-lg font-semibold text-gray-700 mb-4">相关媒体资源</h3>
        <div v-if="loadingMedia" class="text-center py-4">
          <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
          <p class="mt-2 text-gray-500">正在加载媒体资源...</p>
        </div>
        
        <!-- 图片展示 -->
        <div v-if="!loadingMedia && mediaData.images && mediaData.images.length > 0" class="mb-6">
          <h4 class="text-md font-medium text-gray-600 mb-2">图片</h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            <div v-for="(image, index) in mediaData.images" :key="`img-${index}`" class="relative group">
              <div class="overflow-auto max-h-96 border border-gray-100 rounded-lg">
                <img 
                  :src="image.url" 
                  :alt="`相关图片 ${index + 1}`" 
                  class="w-full object-contain cursor-pointer hover:opacity-90 transition-opacity"
                  style="max-height: 24rem; min-height: 12rem;"
                  @click="openImageViewer(image.url)"
                />
              </div>
              <div class="absolute top-2 right-2 bg-black bg-opacity-50 text-white text-xs px-2 py-0.5 rounded">
                点击查看大图
              </div>
            </div>
          </div>
        </div>
        
        <!-- 视频展示 -->
        <div v-if="!loadingMedia && mediaData.videos && mediaData.videos.length > 0">
          <h4 class="text-md font-medium text-gray-600 mb-2">视频</h4>
          <div class="grid grid-cols-1 gap-4">
            <div v-for="(video, index) in mediaData.videos" :key="`video-${index}`" class="relative">
              <video 
                :src="video.url" 
                controls 
                class="w-full max-h-96 object-contain rounded"
                :alt="`相关视频 ${index + 1}`"
              >
                您的浏览器不支持视频播放
              </video>
            </div>
          </div>
        </div>
        
        <!-- 无媒体资源时的提示 -->
        <div v-if="!loadingMedia && (!mediaData.images || mediaData.images.length === 0) && (!mediaData.videos || mediaData.videos.length === 0)" class="text-center py-4 text-gray-500">
          暂无相关媒体资源
        </div>
      </div>
      
      <!-- 传播图谱部分 -->
      <h3 class="text-xl font-semibold text-gray-800 mb-4">虚假信息传播图谱</h3>
      
      <!-- 图谱加载状态 -->
      <div v-if="loadingGraph" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p class="mt-2 text-gray-500">正在加载传播图谱...</p>
      </div>
      
      <!-- 图谱内容 -->
      <div v-else>
        <!-- 有数据时显示图 -->
          <div v-if="graphData && graphData.results && graphData.results.length > 0">
            <div ref="chartContainer" class="w-full h-[600px] border border-gray-200 rounded-lg my-4"></div>
            

          
          <!-- 节点详情面板 -->
          <div v-if="selectedNode" class="bg-white rounded-xl shadow-md p-6 border border-gray-100">
            <div class="flex justify-between items-start">
              <h4 class="text-lg font-semibold text-gray-900">
                {{ getNodeTitle(selectedNode) }}
              </h4>
            </div>
            
            <div v-if="selectedNode.publishtimestamp" class="text-sm text-gray-500 mt-1">
              {{ formatDate(selectedNode.publishtimestamp) }}
            </div>
            
            <div v-if="selectedNode.content" class="mt-4 text-gray-700">
              <p>{{ selectedNode.content }}</p>
            </div>
            
            <!-- 用户节点特定信息展示 -->
            <div v-if="getNodeType(selectedNode) === 'USER'" class="mt-4 bg-gray-50 p-4 rounded-lg">
              <h5 class="font-medium text-gray-800 mb-2">用户信息</h5>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div class="flex items-start">
                  <span class="font-medium w-24">姓名:</span>
                  <span>{{ selectedNode.user_name || '-' }}</span>
                </div>
                <div class="flex items-start">
                  <span class="font-medium w-24">ID:</span>
                  <span>{{ selectedNode.userId || '-' }}</span>
                </div>
                <div class="flex items-start">
                  <span class="font-medium w-24">关注数:</span>
                  <span>{{ selectedNode.follows_num || '0' }}</span>
                </div>
                <div class="flex items-start">
                  <span class="font-medium w-24">粉丝数:</span>
                  <span>{{ selectedNode.fans_num || '0' }}</span>
                </div>
                <div class="flex items-start">
                  <span class="font-medium w-24">性别:</span>
                  <span>{{ selectedNode.gender || '-' }}</span>
                </div>
                <div class="flex items-start">
                  <span class="font-medium w-24">影响力分数:</span>
                  <span>{{ selectedNode.influence_score || '0' }}</span>
                </div>
                <div class="flex items-start">
                  <span class="font-medium w-24">IP地址:</span>
                  <span>{{ selectedNode.ip_address || '-' }}</span>
                </div>
                <div class="flex items-start">
                  <span class="font-medium w-24">认证信息:</span>
                  <span>{{ selectedNode.verifiedType || '-' }}</span>
                </div>
              </div>
            </div>
            
            <div class="mt-4 bg-gray-50 p-4 rounded-lg">
              <h5 class="font-medium text-gray-800 mb-2">节点属性</h5>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                <div><span class="font-medium">VID:</span> {{ selectedNode.vid || '-' }}</div>
                <div><span class="font-medium">类型:</span> {{ getNodeType(selectedNode) || '-' }}</div>
                <template v-for="(value, key) in selectedNode" :key="key">
                  <div v-if="!['vid', 'e_type', 'title', 'content', 'publishtimestamp', 'isrumor', 'user_name', 'userId', 'follows_num', 'fans_num', 'gender', 'influence_score', 'ip_address', 'verifiedType', 'type'].includes(key)">
                    <span class="font-medium">{{ key }}:</span> {{ value || '-' }}
                  </div>
                </template>
              </div>
            </div>
            
            <button 
              @click="closeNodeDetail" 
              class="mt-4 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200"
            >
              <i class="fa fa-times mr-1"></i> 关闭详情
            </button>
          </div>
        </div>
        
        <!-- 无数据时显示提示 -->
        <div v-else class="text-center py-8 border border-dashed border-gray-200 rounded-lg">
          <i class="fa fa-search-minus text-gray-300 text-4xl mb-2"></i>
          <p class="text-gray-500">未找到该虚假信息的传播图谱数据</p>
          <button 
            @click="loadGraphData()" 
            class="mt-4 px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors duration-200"
          >
            <i class="fa fa-refresh mr-1"></i> 重试加载
          </button>
        </div>
      </div>
    </div>
  </div>
    
    <!-- 图片查看器组件 -->
    <div v-if="showImageViewer" class="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4" @click="closeImageViewer">
      <div class="relative w-full max-w-5xl max-h-[90vh]" @click.stop>
        <img 
          :src="selectedImageUrl" 
          alt="放大图片" 
          class="max-w-full max-h-[90vh] object-contain"
        />
        <button 
          class="absolute top-4 right-4 bg-black bg-opacity-70 text-white text-2xl rounded-full w-12 h-12 flex items-center justify-center hover:bg-black hover:bg-opacity-90 transition-all duration-300 shadow-lg"
          @click="closeImageViewer"
          title="关闭"
        >
          <i class="fa fa-times"></i>
        </button>
      </div>
    </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import * as echarts from 'echarts';
import { getFakeKnowledgeDetail, getFakeGraphData, getFakeKnowledgeMedia } from '../../service/apiManager.js';

// 定义默认的formatDate函数
const formatDate = (timestamp) => {
  if (!timestamp) return '未知日期';
  try {
    const date = new Date(timestamp);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  } catch (error) {
    console.error('格式化日期失败:', error);
    return timestamp;
  }
};

// 定义完整的日期时间格式化函数
const formatFullDate = (dateStr) => {
  if (!dateStr) return '未知日期';
  try {
    // 如果已经包含时间，直接返回
    if (dateStr.includes(' ')) return dateStr;
    
    // 否则尝试解析为日期并添加时间
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  } catch (error) {
    console.error('格式化完整日期失败:', error);
    return dateStr;
  }
};

export default {
  name: 'FakeKnowledgeDetail',
  props: {
    id: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const router = useRouter();
    const route = useRoute();
    // 优先使用props中的id，如果没有则从route中获取
    // 确保fakeId始终是字符串类型，以兼容Neo4j数据库的存储方式
  const fakeId = ref(String(props.id || route.params.id || route.query.id || ''));
    const fakeDetail = ref(null);
    const graphData = ref(null);
    const loadingDetail = ref(false);
    const loadingGraph = ref(false);
    const errorMessage = ref('');
    const chart = ref(null);
    const selectedNode = ref(null);
    const chartContainer = ref(null);
    const isContainerReady = ref(false);
    const isDataReady = ref(false);
    const mediaData = ref({ images: [], videos: [] });
    const loadingMedia = ref(false);
    const showImageViewer = ref(false);
    const selectedImageUrl = ref('');
    
    console.log('初始化组件，props.id:', props.id, 'route.params.id:', route.params.id, '最终fakeId:', fakeId.value);
    

    
    // 加载虚假信息详情
      const loadFakeDetail = async () => {
        if (!fakeId.value) return;
        
        try {
          loadingDetail.value = true;
          console.log(`尝试获取虚假信息详情，ID: ${fakeId.value}`);
          // 直接从后端获取指定ID的虚假信息详情
          const response = await getFakeKnowledgeDetail(fakeId.value);
          console.log(`获取详情响应完整数据:`, response);
          
          // 兼容不同的响应格式
          if (response && response.data && (response.data.data || response.data.results)) {
            fakeDetail.value = response.data.data || response.data.results;
            console.log(`成功设置虚假信息详情数据:`, fakeDetail.value);
          } else if (response && (response.data || response.results)) {
            // 兼容直接返回数据的情况
            fakeDetail.value = response.data || response.results;
            console.log(`使用备用路径设置虚假信息详情数据:`, fakeDetail.value);
          } else {
            // 如果没找到或失败，使用默认示例数据
            console.warn('未找到指定的虚假信息，使用模拟数据:', fakeId.value);
            fakeDetail.value = {
              id: fakeId.value,
              title: '示例虚假信息 - ' + fakeId.value,
              content: '这是一条关于' + fakeId.value + '的示例虚假信息内容。虚假信息通常具有误导性，缺乏可靠来源支持，可能对公众认知造成负面影响。',
              source: '社交媒体',
              date: '2023-01-15'
            };
          }
        } catch (error) {
          console.error('加载虚假信息详情失败:', error);
          errorMessage.value = '加载虚假信息详情失败';
          // 设置默认数据
          fakeDetail.value = {
            id: fakeId.value,
            title: '示例虚假信息 - ' + fakeId.value,
            content: '这是一条关于' + fakeId.value + '的示例虚假信息内容。',
            source: '社交媒体',
            date: '2023-01-15'
          };
        } finally {
          loadingDetail.value = false;
          // 加载多媒体资源
          loadMediaData();
        }
      };
    
    // 加载多媒体资源
    const loadMediaData = async () => {
      if (!fakeId.value) return;

      try {
        loadingMedia.value = true;
        console.log(`尝试获取多媒体资源，ID: ${fakeId.value}`);
        const response = await getFakeKnowledgeMedia(fakeId.value);
        
        // 更健壮的响应处理逻辑
        console.log('多媒体资源API响应:', response);
        
        // 检查不同的响应格式
        if (response && response.data) {
          if (response.data.data) {
            // 标准格式: { data: { images: [], videos: [] } }
            mediaData.value = response.data.data;
          } else if (response.data.images || response.data.videos) {
            // 直接格式: { images: [], videos: [] }
            mediaData.value = response.data;
          } else {
            // 其他格式，尝试使用整个data
            mediaData.value = response.data;
          }
        } else if (response) {
          // 直接使用响应作为数据
          mediaData.value = response;
        }
        
        // 确保mediaData结构正确，处理pictures和images字段的映射
        if (mediaData.value.pictures && !mediaData.value.images) {
          // 将pictures字段映射到images字段，并转换为前端期望的格式
          mediaData.value.images = mediaData.value.pictures.map(url => ({ url, name: '相关图片' }));
        } else if (!mediaData.value.images) {
          mediaData.value.images = [];
        }
        
        if (!mediaData.value.videos) {
          mediaData.value.videos = [];
        }
        // 处理videos字段，转换为前端期望的格式
        if (mediaData.value.videos && Array.isArray(mediaData.value.videos)) {
          mediaData.value.videos = mediaData.value.videos.map(url => ({ url, name: '相关视频' }));
        }
        
        console.log(`最终多媒体资源数据:`, mediaData.value);
        console.log(`图片数量: ${mediaData.value.images.length}, 视频数量: ${mediaData.value.videos.length}`);
      } catch (error) {
        console.error('加载多媒体资源失败:', error);
        // 出错时设置默认数据，包含一些模拟媒体资源以便调试
        mediaData.value = {
          images: [
            { url: '/uploads/0.png', name: '测试图片1' },
            { url: '/uploads/0d503c196a8a229f60e2e039cf92e8a9.png', name: '测试图片2' }
          ],
          videos: [
            { url: '/uploads/douyin_raw_1.mp4', name: '测试视频1' }
          ]
        };
        console.log('使用默认模拟媒体资源进行调试');
      } finally {
        loadingMedia.value = false;
      }
    };
    
    // 加载传播图谱数据
    const loadGraphData = async () => {
      if (!fakeId.value) return;

      try {
        loadingGraph.value = true;
        console.log(`尝试获取传播图谱数据，ID: ${fakeId.value}`);
        const response = await getFakeGraphData(fakeId.value);
        console.log(`获取图谱数据响应完整数据:`, response);
        
        // 处理正确的响应格式
        if (response && response.data && response.data.data) {
          // 后端API返回格式: {success: true, data: {results: [...]}}
          graphData.value = response.data.data;
          console.log(`成功设置传播图谱数据(标准API格式):`, graphData.value);
        } else if (response && response.data) {
          // 兼容直接返回数据的情况
          graphData.value = response.data;
          console.log(`使用备用路径设置传播图谱数据(兼容格式):`, graphData.value);
        } else {
          // 保留原始响应
          graphData.value = response;
          console.log(`使用原始响应设置传播图谱数据:`, graphData.value);
        }
        
        // 确保数据和容器都准备好后绘制图表
        isDataReady.value = true;
        if (chartContainer.value) {
          isContainerReady.value = true;
          drawGraph();
        }
      } catch (error) {
        console.error('加载传播图谱数据失败:', error);
        errorMessage.value = '加载传播图谱数据失败';
        
        // 即使出错也设置isDataReady为true，并提供默认的模拟数据
        isDataReady.value = true;
        graphData.value = {
          results: [
            {
              e_src: 'source_' + fakeId.value,
              e_dst: 'node_1',
              e_type: 'spread_to',
              src_type: 'Fake_Article',
              src_props: {
                title: '虚假信息源头',
                content: '这是虚假信息的原始来源文章',
                isrumor: true,
                datasource: '社交媒体',
                publishtimestamp: '1680000000000'
              }
            },
            {
              e_src: 'node_1',
              e_dst: 'node_2',
              e_type: 'forwarded',
              src_type: 'User',
              src_props: {
                name: '用户A',
                followers: 1250,
                verified: false
              },
              dst_type: 'User',
              dst_props: {
                name: '用户B',
                followers: 3400,
                verified: true
              }
            },
            {
              e_src: 'node_2',
              e_dst: 'node_3',
              e_type: 'forwarded',
              src_type: 'User',
              src_props: {
                name: '用户B',
                followers: 3400,
                verified: true
              },
              dst_type: 'User',
              dst_props: {
                name: '用户C',
                followers: 8900,
                verified: false
              }
            }
          ]
        };
        
        // 确保容器就绪后绘制图表
        if (chartContainer.value) {
          isContainerReady.value = true;
          drawGraph();
        }
        
        // 加载多媒体资源
        loadMediaData();
      } finally {
        loadingGraph.value = false;
      }
    };

    // 组件挂载时加载数据
    onMounted(() => {
      // 等待DOM完全渲染后再初始化容器检查
      setTimeout(() => {
        // 检查容器是否就绪
        if (chartContainer.value) {
          isContainerReady.value = true;
        }
        
        // 确保fakeId有值再加载数据
        if (fakeId.value) {
          loadFakeDetail();
          loadGraphData();
        } else {
          console.warn('组件挂载时fakeId为空');
          // 如果没有ID，尝试使用默认示例数据
          useDefaultData();
        }
      }, 100);
    });
    
    // 使用默认示例数据
    const useDefaultData = () => {
      fakeDetail.value = {
        id: 'default',
        title: '示例虚假信息',
        content: '这是一条示例虚假信息内容，用于展示虚假信息详情页面的布局和功能。虚假信息通常具有误导性，缺乏可靠来源支持。',
        source: '社交媒体',
        date: '2023-01-15',
        category: '社会热点谣言'
      };
      
      // 设置默认图谱数据
      graphData.value = {
        results: [
          {              
            e_src: 'source_default',
            e_dst: 'user_1',
            e_type: 'spread_to',
            src_type: 'Fake_Article',
            src_props: {
              title: '示例虚假信息源',
              content: '这是示例虚假信息的原始内容',
              isrumor: true,
              datasource: '社交媒体',
              publishtimestamp: '1680000000000'
            },
            dst_type: 'User',
            dst_props: {
              name: '用户A',
              followers: 1250,
              verified: false
            }
          },
          {
            e_src: 'user_1',
            e_dst: 'user_2',
            e_type: 'forwarded',
            src_type: 'User',
            src_props: {
              name: '用户A',
              followers: 1250,
              verified: false
            },
            dst_type: 'User',
            dst_props: {
              name: '用户B',
              followers: 3400,
              verified: true
            }
          },
          {
            e_src: 'user_2',
            e_dst: 'user_3',
            e_type: 'forwarded',
            src_type: 'User',
            src_props: {
              name: '用户B',
              followers: 3400,
              verified: true
            },
            dst_type: 'User',
            dst_props: {
              name: '用户C',
              followers: 8900,
              verified: false
            }
          }
        ]
      };
      
      // 绘制默认图表
      if (chartContainer.value) {
        isContainerReady.value = true;
        isDataReady.value = true;
        drawGraph();
      }
    };
    
    // 尝试绘制图表
    const tryDrawGraph = () => {
      console.log('tryDrawGraph - 开始尝试绘制图谱');
      
      // 确保数据和容器准备就绪
      if (isDataReady.value && isContainerReady.value) {
        // 增强容器尺寸检查逻辑
        if (chartContainer.value) {
          const { clientWidth, clientHeight } = chartContainer.value;
          
          console.log(`tryDrawGraph - 当前容器尺寸: ${clientWidth}x${clientHeight}`);
          
          // 检查容器高度是否为0，需要修复
          if (clientHeight === 0) {
            console.warn('tryDrawGraph - 检测到容器高度为0，尝试修复容器尺寸');
            
            // 强制设置容器的最小高度和高度为600px
            try {
              // 设置内联样式
              chartContainer.value.style.minHeight = '600px';
              chartContainer.value.style.height = '600px';
              chartContainer.value.style.display = 'block'; // 确保容器不是隐藏的
              chartContainer.value.style.position = 'relative'; // 确保相对定位
              
              console.log('tryDrawGraph - 已设置容器强制尺寸: minHeight=600px, height=600px');
              
              // 访问offsetHeight触发浏览器重排，确保样式立即生效
              const offsetHeight = chartContainer.value.offsetHeight;
              console.log('tryDrawGraph - 触发浏览器重排后容器offsetHeight:', offsetHeight);
            } catch (error) {
              console.error('tryDrawGraph - 设置容器尺寸时出错:', error);
            }
            
            // 立即重新检查尺寸
            setTimeout(() => {
              const newClientHeight = chartContainer.value.clientHeight;
              console.log(`tryDrawGraph - 尺寸修复后新高度: ${newClientHeight}px`);
              
              if (newClientHeight > 0) {
                // 修复成功，调用drawGraph
                drawGraph();
              } else {
                // 修复失败，记录警告并计划重试
                console.warn('tryDrawGraph - 容器尺寸修复失败，计划重试');
                setTimeout(tryDrawGraph, 300);
              }
            }, 50); // 短暂延迟等待DOM更新
          } else if (clientWidth > 0 && clientHeight > 0) {
            // 容器尺寸有效，直接调用drawGraph
            console.log('tryDrawGraph - 容器尺寸有效，调用drawGraph');
            drawGraph();
          } else {
            // 容器尺寸无效但高度不为0，记录警告并计划重试
            console.warn(`tryDrawGraph - 容器尺寸无效 (${clientWidth}x${clientHeight})，计划重试`);
            setTimeout(tryDrawGraph, 300);
          }
        } else {
          console.warn('tryDrawGraph - 容器不存在，计划重试');
          setTimeout(tryDrawGraph, 300);
        }
      } else {
        // 数据或容器未准备好
        const missing = !isDataReady.value ? '数据未准备好' : '容器未准备好';
        console.log(`tryDrawGraph - 条件不满足: ${missing}`);
      }
    };
    
    // 绘制关系图
    const drawGraph = () => {
      if (!chartContainer.value) {
        console.warn('Chart container not found, retrying...');
        // 添加重试逻辑
        setTimeout(() => {
          if (chartContainer.value) {
            drawGraph();
          }
        }, 100);
        return;
      }
      
      // Check if container has valid dimensions
      const { clientWidth, clientHeight } = chartContainer.value;
      if (!clientWidth || !clientHeight) {
        console.warn(`Container dimensions invalid (${clientWidth}x${clientHeight}), retrying...`);
        // Implement exponential backoff for retries
        setTimeout(() => {
          drawGraph();
        }, 300);
        return;
      }
      
      if (!graphData.value?.results || !fakeId.value) {
        console.warn('Graph data or fakeId not available yet');
        return;
      }
      
      // 确保graphData.results是数组
      if (!Array.isArray(graphData.value.results)) {
        console.error('Invalid graph data format');
        return;
      }
    
      // 销毁旧的图表实例
      if (chart.value) {
        chart.value.dispose();
      }
    
      // 初始化图表
      try {
        chart.value = echarts.init(chartContainer.value);
      } catch (error) {
        console.error('Failed to initialize echarts:', error);
        return;
      }
      
      // 准备数据
      const nodes = new Map();
      const links = [];
      const nodeTypes = new Map();
      let nextCategoryId = 0;
    
      // 中心虚假信息节点ID
      let centerFakeId = 'source_' + fakeId.value;
      
      // 查找实际的INFO节点ID
      graphData.value.results.forEach((item) => {
        if (item.dst_type === 'INFO' && item.e_type === 'post') {
          centerFakeId = item.e_dst;
        }
      });
    
      // 识别需要保留的USER节点 - 只保留用POST指向INFO节点的USER
      const validUserNodes = new Set();
      const repostNodes = new Map(); // 用于限制REPOST节点数量
      const commentNodes = new Map(); // 用于限制COMMENT节点数量
      const review2Links = []; // 存储有review2关系的边，优先展示
      const firstLevelCommentsWithReplies = new Set(); // 存储有二级评论的一级评论节点ID
    
      // 第一次遍历：识别有效的USER节点和review2关系
      graphData.value.results.forEach((item) => {
        // 识别用POST指向INFO节点的USER
        if (item.e_type === 'post' && item.dst_type === 'INFO' && item.src_type === 'USER') {
          validUserNodes.add(item.e_src);
        }
        
        // 识别review2关系的边
        if (item.e_type === 'review2' && item.dst_type === 'COMMENT') {
          review2Links.push(item);
          // 记录有二级评论的一级评论节点
          firstLevelCommentsWithReplies.add(item.e_dst);
        }
      });
    
      // 处理结果数据，提取节点和边
      // 先处理review2关系的边，优先展示
      review2Links.forEach((item) => {
        processGraphItem(item);
      });
      
      // 然后处理其他边
      graphData.value.results.forEach((item) => {
        if (!review2Links.includes(item)) {
          processGraphItem(item);
        }
      });
    
      // 处理单个图数据项的函数
      function processGraphItem(item) {
        // 必须存在源节点ID才处理
        if (!item.e_src) {
          console.warn('跳过无效边数据:', item);
          return;
        }
    
        // 获取节点类型和属性
        const srcNodeType = item.src_type || 'Unknown';
        const srcNodeProps = item.src_props || {};
    
        // 初始化源和目标节点
        let source = item.e_src;
        let target;
    
        // 处理传播关系
        if (item.e_type === 'spread_to') {
          target = item.e_dst || centerFakeId;
        } else {
          if (!item.e_dst) return; // 过滤无效目标
          target = item.e_dst;
        }
        
        // 特殊处理review1关系，确保target是正确的INFO节点
        if (item.e_type === 'review1' && item.dst_type === 'INFO') {
          target = centerFakeId;
        }
    
        // 处理源节点
        if (!nodes.has(source)) {
          // 过滤USER节点，只保留有效的USER节点
          if (srcNodeType === 'USER' && !validUserNodes.has(source)) {
            return;
          }
          
          // 对COMMENT节点限制数量
          if (srcNodeType === 'COMMENT') {
            // 优先保留有二级评论的一级评论节点
            if (commentNodes.size >= 20 && !commentNodes.has(source) && !firstLevelCommentsWithReplies.has(source)) {
              return;
            }
            commentNodes.set(source, true);
          }
          
          // 对REPOST节点限制数量
          if (srcNodeType === 'REPOST') {
            if (repostNodes.size >= 20 && !repostNodes.has(source)) {
              return;
            }
            repostNodes.set(source, true);
          }
          
          if (!nodeTypes.has(srcNodeType)) {
            nodeTypes.set(srcNodeType, nextCategoryId);
            nextCategoryId++;
          }
      
          // 处理节点名称
          let nodeName = srcNodeProps.title || srcNodeProps.name;
          if (!nodeName && srcNodeProps.content) {
            nodeName = srcNodeProps.content.substring(0, 8) + '...';
          } else if (!nodeName) {
            nodeName = source.slice(0, 8) + '...';
          }
      
          // 确保使用正确的源节点属性，不会被子节点覆盖
          nodes.set(source, {
            id: source,
            name: nodeName,
            symbolSize: getNodeSizeByType(srcNodeType, nodes.size + 1),
            itemStyle: { color: getNodeColorByType(srcNodeType) },
            category: nodeTypes.get(srcNodeType),
            draggable: true,
            // 使用真正的深拷贝确保数据不被共享和覆盖
            originalData: JSON.parse(JSON.stringify({
              ...srcNodeProps,
              vid: source,
              type: srcNodeType
            }))
          });
        }
      
        // 处理目标节点
        if (!nodes.has(target)) {
          const dstNodeType = item.dst_type || 'Unknown';
          const dstNodeProps = item.dst_props || {};
      
          // 过滤USER节点，只保留有效的USER节点
          if (dstNodeType === 'USER' && !validUserNodes.has(target)) {
            return;
          }
          
          // 对COMMENT节点限制数量
          if (dstNodeType === 'COMMENT') {
            // 优先保留有二级评论的一级评论节点
            if (commentNodes.size >= 20 && !commentNodes.has(target) && !firstLevelCommentsWithReplies.has(target)) {
              return;
            }
            commentNodes.set(target, true);
          }
          
          // 对REPOST节点限制数量
          if (dstNodeType === 'REPOST') {
            if (repostNodes.size >= 20 && !repostNodes.has(target)) {
              return;
            }
            repostNodes.set(target, true);
          }
          
          if (!nodeTypes.has(dstNodeType)) {
            nodeTypes.set(dstNodeType, nextCategoryId);
            nextCategoryId++;
          }
      
          let nodeName = dstNodeProps.title || dstNodeProps.name;
          if (!nodeName && dstNodeProps.content) {
            nodeName = dstNodeProps.content.substring(0, 8) + '...';
          } else if (!nodeName) {
            nodeName = target.slice(0, 8) + '...';
          }
      
          // 确保使用正确的目标节点属性
          nodes.set(target, {
            id: target,
            name: nodeName,
            symbolSize: getNodeSizeByType(dstNodeType, nodes.size + 1),
            itemStyle: { color: getNodeColorByType(dstNodeType) },
            category: nodeTypes.get(dstNodeType),
            draggable: true,
            // 使用真正的深拷贝确保数据不被共享和覆盖
            originalData: JSON.parse(JSON.stringify({
              ...dstNodeProps,
              vid: target,
              type: dstNodeType
            }))
          });
        }
    
        // 添加边
        links.push({
          source: source,
          target: target,
          name: item.e_type,
          lineStyle: {
            width: getEdgeWidthByType(item.e_type),
            curveness: 0.2,
            color: getEdgeColorByType(item.e_type),
            opacity: 0.9
          }
        });
      }
    
      // 检查是否有节点，如果没有节点，使用默认的中心节点
      if (nodes.size === 0) {
        // 添加中心虚假信息节点
        nodes.set(centerFakeId, {
          id: centerFakeId,
          name: fakeDetail.value?.title || '虚假信息源',
          symbolSize: 40,
          itemStyle: { color: '#ff4d4f' },
          category: 0,
          draggable: true,
          originalData: { 
            title: fakeDetail.value?.title || '虚假信息源',
            content: fakeDetail.value?.content || '虚假信息内容',
            vid: centerFakeId,
            type: 'Fake_Article'
          }
        });
        nodeTypes.set('Fake_Article', 0);
      }
    
      // 图表配置
          const option = {
            tooltip: {
              formatter: function(params) {
                if (params.dataType === 'node') {
                  return `${params.data.name}<br/>类型: ${params.data.originalData.type}`;
                } else if (params.dataType === 'edge') {
                  return `关系: ${params.data.name}`;
                }
                return params.name;
              }
            },
            legend: {
              data: Array.from(nodeTypes.entries())
                .filter(([type]) => type)
                .map(([type]) => type),
              bottom: 10
            },
            series: [
              {
                type: 'graph',
                layout: 'force',
                force: {
                  repulsion: 1200,  // 增加节点间排斥力，让节点分布更开
                  edgeLength: 300,  // 增加边的长度，让整体图谱更大
                  gravity: 0.05,     // 减小重力，让节点更容易散开
                  layoutAnimation: true  // 启用布局动画
                },
                roam: true,  // 允许缩放和平移
                scaleLimit: {
                  min: 0.1,  // 降低最小缩放比例，便于查看大量节点
                  max: 10    // 提高最大缩放比例，便于查看细节
                },
                label: {
                  show: false,  // 不显示节点名称
                  fontSize: 14,
                  overflow: 'truncate',
                  position: 'right',
                  formatter: function(params) {
                    // 节点过多时优化标签显示
                    const nodeCount = Array.from(nodes.values()).length;
                    if (nodeCount > 50 && chart.value && chart.value.getOption().series[0].zoom < 1) {
                      return ''; // 缩小视图时隐藏标签
                    }
                    return params.name;
                  }
                },
                edgeSymbol: ['none', 'arrow'],
                edgeSymbolSize: [0, 8],
                edgeLabel: {
                  show: false, // 不显示边上的关系名称
                  fontSize: 10,
                  formatter: '{b}',
                  showAbove: true
                },
                data: Array.from(nodes.values()),
                links: links,
                categories: Array.from(nodeTypes.entries()).map(([type]) => ({ 
                  name: type,
                  itemStyle: { color: getNodeColorByType(type) }
                })),
                emphasis: {
                  focus: 'adjacency',
                  lineStyle: {
                    width: 5  // 鼠标悬停时边变粗
                  }
                }
              }
            ]
          };

          chart.value.setOption(option);

          // 节点点击事件
          chart.value.on('click', (params) => {
            if (params.dataType === 'node') {
              console.log('点击节点:', params.data.id, '节点类型:', params.data.originalData.type);
              // 创建一个新的对象，确保使用节点的id作为vid，避免数据混淆
              const nodeData = {
                ...params.data.originalData,
                vid: params.data.id  // 确保vid始终等于节点的id
              };
              // 使用深拷贝确保数据不被共享和覆盖
              selectedNode.value = JSON.parse(JSON.stringify(nodeData));
            }
          });

          // 窗口大小变化时重绘图表
          window.addEventListener('resize', () => {
            if (chart.value) {
              chart.value.resize();
            }
          });

          // 当节点数量较多时，自动调整初始缩放比例
          const nodeCount = Array.from(nodes.values()).length;
          if (nodeCount > 30) {
            // 根据节点数量设置初始缩放比例
            const initialZoom = Math.min(1, 30 / nodeCount);
            chart.value.dispatchAction({
              type: 'graphRoam',
              animation: true,
              roam: 'scale',
              zoom: initialZoom
            });
          }
    };
    
    // 辅助函数：根据节点类型获取颜色
    const getNodeColorByType = (type) => {
      const colorMap = {
        'REPOST': '#ff4d4f',     // 虚假信息源用红色
        'Original_Article': '#ff7a45', // 原始文章用橙色
        'INFO': '#34A853',          // 普通文章用绿色
        'USER': '#9B51E0',             // 用户用紫色
        'COMMENT': '#2196F3',          // 评论用蓝色
        'Unknown': '#8884d8'           // 未知类型用深紫色
      };
      return colorMap[type] || colorMap['Unknown'];
    };
    
    // 辅助函数：根据节点类型和数量获取大小
    const getNodeSizeByType = (type, nodeCount = 0) => {
      // 基础大小配置
      const baseSizeMap = {
        'Fake_Article': 40,     // 中心节点
        'Original_Article': 40, // 保持兼容性
        'Article': 30,          // 文章节点
        'User': 25,             // 用户节点
        'Comment': 20,          // 评论节点
        'Unknown': 25           // 未知类型节点
      };
      
      let size = baseSizeMap[type] || baseSizeMap['Unknown'];
      
      // 根据节点数量动态调整大小
      if (nodeCount > 20) {
        // 节点数量越多，大小越小
        const scaleFactor = Math.max(0.5, 1 - (nodeCount - 20) / 100);
        size = Math.round(size * scaleFactor);
      }
      
      return size;
    };
    
    // 辅助函数：根据边类型获取宽度
    const getEdgeWidthByType = (type) => {
      const widthMap = {
        'spread_to': 3,
        'forwarded': 2,
        'commented': 1.5,
        'follow': 1,
        'issue': 1.5,
        'perform': 1.5,
        'post': 2,
        'review1': 1.5,
        'review2': 1.2,
        'review3': 1.5,
        'Unknown': 2
      };
      return widthMap[type] || widthMap['Unknown'];
    };
    
    // 辅助函数：根据边类型获取颜色
    const getEdgeColorByType = (type) => {
      const colorMap = {
        'spread_to': '#ff4d4f',
        'forwarded': '#faad14',
        'commented': '#52c41a',
        'follow': '#1890ff',
        'issue': '#f5222d',
        'perform': '#722ed1',
        'post': '#fa8c16',
        'review1': '#52c41a',
        'review2': '#1890ff',
        'review3': '#faad14',
        'Unknown': '#8884d8'
      };
      return colorMap[type] || colorMap['Unknown'];
    };
    
    // 关闭节点详情
    const closeNodeDetail = () => {
      selectedNode.value = null;
    };

    // 打开图片查看器
    const openImageViewer = (imageUrl) => {
      selectedImageUrl.value = imageUrl;
      showImageViewer.value = true;
    };

    // 关闭图片查看器
    const closeImageViewer = () => {
      showImageViewer.value = false;
      selectedImageUrl.value = '';
    };

    // 聚焦到特定节点
    const focusOnNode = (nodeVid) => {
      if (!chart.value || !nodeVid) return;
      
      const nodes = chart.value.getOption().series[0].data;
      const targetNode = nodes.find(node => node.id === nodeVid);
      
      if (targetNode) {
        chart.value.dispatchAction({
          type: 'showTip',
          seriesIndex: 0,
          dataIndex: nodes.indexOf(targetNode)
        });
        
        // 设置中心到目标节点并放大
        chart.value.dispatchAction({
          type: 'graphRoam',
          animation: true,
          roam: 'drag',
          dx: 0,
          dy: 0,
          originX: chart.value.getWidth() / 2,
          originY: chart.value.getHeight() / 2,
          targetX: targetNode.x || chart.value.getWidth() / 2,
          targetY: targetNode.y || chart.value.getHeight() / 2
        });
        
        // 放大显示该节点
        setTimeout(() => {
          chart.value.dispatchAction({
            type: 'graphRoam',
            animation: true,
            roam: 'scale',
            zoom: 2
          });
        }, 300);
      }
    };


    
    // 获取节点标题
    const getNodeTitle = (node) => {
      if (node.type === 'COMMENT') {
        return '评论节点';
      } else if (node.type === 'USER') {
        return '用户节点';
      } else if (node.type === 'INFO' || node.type === 'Fake_Article' || node.type === 'Original_Article') {
        return '虚假信息源';
      } else if (node.type === 'REPOST') {
        return '转发节点';
      }
      return node.title || '节点';
    };
    
    // 获取节点类型
    const getNodeType = (node) => {
      return node.type || node.e_type || '未知类型';
    };
    
    // 返回虚假信息知识库
    const goBack = () => {
      router.push('/fake');
    };
    
    // 监听路由参数变化
    watch(() => route.query.id, (newId) => {
      if (newId && newId !== fakeId.value) {
        fakeId.value = newId;
        loadFakeDetail();
        loadGraphData();
      }
    });
    
    // 监听容器变化
    watch(chartContainer, (newValue) => {
      if (newValue) {
        isContainerReady.value = true;
        tryDrawGraph();
      }
    });
    
    watch(graphData, () => {
      if (graphData.value && graphData.value.results && graphData.value.results.length > 0) {
        isDataReady.value = true;
        tryDrawGraph();
      }
    });
    
    return {
      fakeDetail,
      graphData,
      loadingDetail,
      loadingGraph,
      chart,
      selectedNode,
      chartContainer,
      errorMessage,
      loadFakeDetail,
      loadGraphData,
      loadMediaData,
      closeNodeDetail,
      getNodeTitle,
      getNodeType,
      formatDate,
      formatFullDate,
      goBack,
      focusOnNode,
      mediaData,
      loadingMedia,
      showImageViewer,
      selectedImageUrl,
      openImageViewer,
      closeImageViewer
    };
  }
};
</script>

<style scoped>
.fake-knowledge-detail {
  width: 100%;
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
</style>