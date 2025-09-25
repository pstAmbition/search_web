<template>
  <div class="path-view">
    <div class="bg-white rounded-xl shadow-lg p-6 mb-6">
      <h3 class="text-xl font-semibold text-gray-800 mb-4 flex items-center"> 传播图谱
        <!-- 修改：只有加载过数据后才显示查询信息 -->
        <span v-if="hasSearched && currentGraphId" class="ml-2 text-sm text-gray-500">查询:推文_ {{ currentGraphId }}</span>
        <button 
          @click="clearGraph" 
          class="ml-4 text-sm text-gray-500 hover:text-gray-700 transition-colors"
          v-if="hasSearched && currentGraphId"
        >
          <i class="fa fa-times mr-1"></i> 关闭图谱
        </button>
      </h3>
      
      <!-- 图谱ID输入 -->
      <div class="mb-4 flex items-center">
        <label for="graphId" class="block text-sm font-medium text-gray-700 mr-2">查询内容:</label>                  
        <input 
          v-model="currentGraphId" 
          type="text" 
          id="graphId" 
          class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all duration-300"
          placeholder="请输入推文ID查看传播图谱"
        >
        <button 
          @click="loadGraphData(currentGraphId)" 
          class="ml-2 bg-primary hover:bg-primary/90 text-white font-medium py-2 px-4 rounded-lg transition-all duration-300"
          :disabled="!currentGraphId"
        >
          加载
        </button>
      </div>
      

      <!-- 推文/稿件详情板块 -->
      <div v-if="hasSearched && originalTweet && originalTweet.results && originalTweet.results.length > 0" class="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <!-- 根据类型动态显示标题 -->
        <h4 class="text-lg font-semibold text-gray-800 mb-3">
          {{ originalTweet.results[0].node_type === 'Retweet' ? '稿件详情' : '推文详情' }}
        </h4>
        <div class="mb-4 p-2 bg-blue-50 rounded border border-blue-100">
          <span class="font-medium text-blue-800">关联事件：</span>
          <!-- 直接显示，即使为空也显示“无”，方便调试 -->
          <a 
            @click="switchToEventView(currentGraphEvent)"
            class="text-primary hover:text-primary/80 hover:underline cursor-pointer"
          >
            {{ currentGraphEvent || '无关联事件' }}
          </a>
        </div>
        <div class="text-gray-700 mb-3">
          {{ originalTweet.results[0].src_v.content }}
        </div>
        <div class="flex flex-wrap gap-4 text-sm text-gray-500">
          <!-- 根据类型显示不同的发布者属性 -->
          <div><span class="font-medium">发布者:</span> {{ originalTweet.results[0].node_type === 'Retweet' ? originalTweet.results[0].src_v.name : originalTweet.results[0].src_v.uname }}</div>
          <div><span class="font-medium">发布时间:</span> {{ formatDate(originalTweet.results[0].src_v.publishtimestamp) }}</div>
          <div v-if="originalTweet.results[0].src_v.isrumor !== null" class="flex items-center">
            <span class="font-medium">类型:</span>
            <span 
              :class="{
                'bg-green-100 text-green-800 ml-1': !originalTweet.results[0].src_v.isrumor,
                'bg-red-100 text-red-800 ml-1': originalTweet.results[0].src_v.isrumor
              }" 
              class="text-xs px-2 py-0.5 rounded font-medium"
            >
              {{ originalTweet.results[0].src_v.isrumor ? '谣言' : '真实' }}
            </span>
          </div>
        </div>
        <!-- 图片展示 -->
        <div v-if="originalTweet.results[0].src_v.pics_url" class="mt-4">
          <h5 class="text-sm font-medium text-gray-700 mb-2">图片:</h5>
          <div class="flex flex-wrap gap-2">
            <img 
              v-for="(url, index) in originalTweet.results[0].src_v.pics_url.split(', ')" 
              :key="index" 
              :src="url" 
              class="max-h-40 max-w-40 object-cover rounded-md border border-gray-200 cursor-pointer hover:opacity-90 transition-opacity"
              alt="推文图片"
              @click="handleImageClick(url)"
            >
          </div>
        </div>
      </div>

      <!-- 图谱加载状态 -->
      <div v-if="loadingGraph" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p class="mt-2 text-gray-500">正在加载传播图谱...</p>
      </div>
      
      <!-- 图谱内容 -->
      <div v-else>
        <!-- 有数据时显示图 -->
        <div v-if="hasSearched && relatedData && relatedData.results && relatedData.results.length > 0">
          <div ref="chartContainer" class="w-full h-[500px] border border-gray-200 rounded-lg mb-6"></div>
          
          <!-- 节点详情面板 -->
          <div v-if="selectedNode" class="bg-white rounded-xl shadow-md p-6 border border-gray-100">
            <div class="flex justify-between items-start">
              <h4 class="text-lg font-semibold text-gray-900">
                {{ getNodeTitle(selectedNode) }}
              </h4>
              <span 
                v-if="selectedNode.isrumor !== null" 
                :class="{
                  'bg-green-100 text-green-800': !selectedNode.isrumor,
                  'bg-red-100 text-red-800': selectedNode.isrumor
                }" 
                class="text-xs px-2 py-0.5 rounded font-medium"
              >
                {{ selectedNode.isrumor ? '谣言' : '真实' }}
              </span>
            </div>
            
            <div v-if="selectedNode.publishtimestamp || selectedNode.republishtime" class="text-sm text-gray-500 mt-1">
                {{ formatDate(selectedNode.publishtimestamp || selectedNode.republishtime) }}
            </div>
            
            <div v-if="selectedNode.content" class="mt-4 text-gray-700">
              <p>{{ selectedNode.content }}</p>
            </div>
            
            <div class="mt-4 bg-gray-50 p-4 rounded-lg">
              <h5 class="font-medium text-gray-800 mb-2">节点属性</h5>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                <div><span class="font-medium">VID:</span> {{ selectedNode.vid || '-' }}</div>
                <div><span class="font-medium">类型:</span> {{ getNodeType(selectedNode) || '-' }}</div>
                <template v-for="(value, key) in selectedNode" :key="key">
                  <div v-if="!['vid', 'e_type', 'title', 'content', 'publishtimestamp', 'isrumor'].includes(key)">
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
        
        <!-- 无数据时显示提示 - 修改：只有加载过数据后才显示 -->
        <div v-if="hasSearched && (!relatedData || !relatedData.results || relatedData.results.length === 0)" class="text-center py-8 border border-dashed border-gray-200 rounded-lg">
          <i class="fa fa-search-minus text-gray-300 text-4xl mb-2"></i>
          <p class="text-gray-500">未找到与 "{{ currentGraphId }}" 相关的图谱数据</p>
        </div>
      </div>
    </div>
  </div>

  <!-- 新增：图片放大模态框 -->
  <div 
    v-if="showImageModal" 
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
    @click="closeImageModal"
  >
    <div class="relative max-w-4xl max-h-[90vh]" @click.stop>
      <button 
        class="absolute -top-12 right-0 text-white text-2xl hover:text-gray-300 transition-colors"
        @click="closeImageModal"
      >
        <i class="fa fa-times"></i>
      </button>
      <img 
        :src="selectedImageUrl" 
        class="max-w-full max-h-[90vh] object-contain"
        alt="放大图片"
      >
    </div>
  </div>
</template>

<script>
  import { ref, watch, nextTick, onMounted } from 'vue';
  import * as echarts from 'echarts';
  import { getGraphDataById } from '../../service/apiManager.js';
  import { getOriginalTweetById } from '../../service/apiManager.js';
  import { getStartNodeInfo } from '../../service/apiManager.js';
  import { formatDate } from '../../utils/date.js';
  import { useRouter } from 'vue-router';
  export default {
    name: 'PathView',
    props: {
      initialGraphId: {
        type: String,
        default: ''
      },
      // 新增：接收事件名称prop
      initialGraphEvent: {
        type: String,
        default: ''
      }
    },
    
    emits: ['clearGraph'],
    setup(props, { emit }) {
      // 新增：标记是否已执行过搜索
      const hasSearched = ref(false);
      // 图谱相关变量
      const currentGraphId = ref(props.initialGraphId);
      const currentGraphEvent = ref(props.initialGraphEvent);
      const relatedData = ref(null);
      const loadingGraph = ref(false);
      const chart = ref(null);
      const selectedNode = ref(null);
      const chartContainer = ref(null);
      const isDataReady = ref(false);
      const isContainerReady = ref(false);
      const errorMessage = ref('');
      const originalTweet = ref(null);
      const router = useRouter();
      // 新增：图片放大相关变量
      const showImageModal = ref(false);
      const selectedImageUrl = ref('');
      // 监听初始图谱ID变化
      watch(() => props.initialGraphId, (newId) => {
        if (newId && newId !== currentGraphId.value) {
          console.log('从路由参数接收推文ID:', newId);
          currentGraphId.value = newId;
          loadGraphData(newId); // 自动加载数据
        }
      },
      { immediate: true } // 初始化时立即执行
      );

      // 确保在组件挂载时执行一次查询
      onMounted(() => {
        if (props.initialGraphId) {
          console.log('组件挂载时检测到初始ID:', props.initialGraphId);
          loadGraphData(props.initialGraphId);
        }
      });
      // 新增：监听初始事件名称变化
      watch(() => props.initialGraphEvent, (newEvent) => {
        currentGraphEvent.value = newEvent;
      });

      // 点击关联事件跳转方法
      const switchToEventView = (newEvent) => {
        console.log('点击关联事件，事件数据:', newEvent);
        if (!newEvent) return; // 确保事件名称存在
        // 跳转到EventView，携带事件ID和必要参数
        router.push({
          path: '/event',
          query:{ event: newEvent }
        });
      };

      // 时间格式化
      const formatDate = (timestamp) => {
        if (!timestamp) return '';
        let msTimestamp = timestamp;
        if (String(timestamp).length < 13) {
          msTimestamp = Number(timestamp) * 1000;
        }
        const date = new Date(msTimestamp);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        return `${year}/${month}/${day} ${hours}:${minutes}:${seconds}`;
      };
      
      // 节点详细信息变量
      const startNodeInfo = ref(null);
      // 所有节点的详细信息Map
      const allNodesInfo = ref(new Map());
      
      // 加载图谱数据和推文原文
      const loadGraphData = async (Id) => {
        if (!Id) return;
        
        loadingGraph.value = true;
        errorMessage.value = '';
        // 标记为已搜索
        hasSearched.value = true;
        try {
          // 首先获取图谱数据和推文原文
          const [graphResponse, tweetResponse] = await Promise.all([
            getGraphDataById(Id),
            getOriginalTweetById(Id)
          ]);
          
          // 清空旧数据
          relatedData.value = null;
          originalTweet.value = null;
          startNodeInfo.value = null;
          allNodesInfo.value.clear();
          await nextTick();
          
          // 更新数据
          relatedData.value = graphResponse.data;
          originalTweet.value = tweetResponse.data;
          
          // 收集所有需要查询的未知类型节点ID
          const unknownTypeNodeIds = new Set();
          
          // 添加起始节点（无论类型如何，始终获取其详细信息）
          unknownTypeNodeIds.add(Id);
          
          // 从图谱数据中提取类型为未知的节点ID
          if (relatedData.value && relatedData.value.results) {
            relatedData.value.results.forEach(item => {
              // 检查源节点类型
              if (item.e_src && (item.src_type === 'Unknown' || !item.src_type)) {
                unknownTypeNodeIds.add(item.e_src);
              }
              // 检查目标节点类型
              if (item.e_dst && item.e_type === 'forwarded' && (item.dst_type === 'Unknown' || !item.dst_type)) {
                unknownTypeNodeIds.add(item.e_dst);
              }
            });
          }
          
          // 批量查询所有未知类型节点的详细信息
          const allNodesInfoPromises = Array.from(unknownTypeNodeIds).map(nodeId => 
            getStartNodeInfo(nodeId).catch(error => {
              console.warn(`获取节点 ${nodeId} 信息失败:`, error);
              return { data: { results: null } };
            })
          );
          
          const allNodesInfoResponses = await Promise.all(allNodesInfoPromises);
          
          // 存储所有节点的详细信息
          Array.from(unknownTypeNodeIds).forEach((nodeId, index) => {
            const response = allNodesInfoResponses[index];
            if (response && response.data && response.data.results) {
              allNodesInfo.value.set(nodeId, response.data.results);
              // 设置起始节点信息
              if (nodeId === Id) {
                startNodeInfo.value = response.data.results;
              }
            }
          });
          
          // 强制重绘
          isDataReady.value = false;
          nextTick(() => {
            isDataReady.value = true;
            tryDrawGraph();
          });
        } catch (error) {
          console.error('查询关联内容失败:', error);
          handleError(error);
        } finally {
          loadingGraph.value = false;
        }
      };
      
      // 清除图谱显示
      const clearGraph = () => {
        currentGraphId.value = '';
        relatedData.value = null;
        selectedNode.value = null;
        originalTweet.value = null;
        // 重置搜索状态
        hasSearched.value = false;
        // 销毁图表实例
        if (chart.value) {
          chart.value.dispose();
          chart.value = null;
        }
        
        // 通知父组件清除图谱
        emit('clearGraph');
      };
      
      // 其余代码保持不变...
      watch(chartContainer, (newValue) => {
        if (newValue) {
          isContainerReady.value = true;
          tryDrawGraph();
        }
      });
      
      watch(relatedData, () => {
        if (relatedData.value && relatedData.value.results && relatedData.value.results.length > 0) {
          isDataReady.value = true;
          tryDrawGraph();
        }
      });
      
      const tryDrawGraph = () => {
        if (isDataReady.value && isContainerReady.value) {
          drawGraph();
        }
      };
      
      const handleError = (error) => {
        if (error.response) {
          console.error(`请求失败 (${error.response.status}):`, error.response.data);
        } else if (error.request) {
          console.error("没有收到服务器响应:", error.request);
        } else {
          console.error("请求错误:", error.message);
        }
      };
      
      const drawGraph = () => {
        if (!chartContainer.value || !relatedData.value?.results || !currentGraphId.value) {
          console.error('Chart container or data not found');
          return;
        }
        
        if (chart.value) {
          chart.value.dispose();
        }
        
        chart.value = echarts.init(chartContainer.value);
        
        const nodes = new Map();
        const links = [];
        const nodeTypes = new Map();
        let nextCategoryId = 0;
        
        const centerId = currentGraphId.value;
        
        // 获取起始节点的详细信息 - 仅使用API返回的数据
        const centerNodeInfo = allNodesInfo.value.get(centerId);
        const nodeName = centerNodeInfo?.all_properties?.text?.substring(0, 20) || '当前查询';
        // 优化节点类型获取逻辑，处理不同格式的node_type数据
        let finalNodeType = 'Unknown';
        if (centerNodeInfo && centerNodeInfo.node_type) {
          if (Array.isArray(centerNodeInfo.node_type) && centerNodeInfo.node_type.length > 0) {
            finalNodeType = centerNodeInfo.node_type[0];
          } else if (typeof centerNodeInfo.node_type === 'string') {
            finalNodeType = centerNodeInfo.node_type;
          }
        }
        
        nodes.set(centerId, {
          id: centerId,
          name: nodeName,
          symbolSize: getNodeSizeByType(finalNodeType), // 使用动态大小
          itemStyle: { color: getNodeColorByType(finalNodeType) }, // 使用动态颜色
          category: 0,
          originalData: {
            vid: centerId,
            type: finalNodeType,
            ...centerNodeInfo?.all_properties
          },
          draggable: true,
        });
        nodeTypes.set(finalNodeType, 0); // 使用API返回的节点类型
        nextCategoryId = 1;
        
        relatedData.value.results.forEach((item) => {
          if (!item.e_src) {
            console.warn('跳过无效边数据:', item);
            return;
          }

          let source = item.e_src;
          let target;
          
          if (item.e_type === 'belong') {
            target = centerId;
          } else if (item.e_type === 'forwarded') {
            if (!item.e_dst) return;
            target = item.e_dst;
          } else {
            return;
          }

          if (!nodes.has(source)) {
            // 获取节点信息：优先使用API获取的信息，如果没有则使用item中的信息
            const nodeInfo = allNodesInfo.value.get(source);
            const srcNodeType = item.src_type || 'Unknown';
            const srcNodeProps = item.src_props || {};
            
            // 确定最终节点类型 - 处理不同格式的node_type数据
            let finalSrcType = srcNodeType || 'Unknown';
            if (nodeInfo && nodeInfo.node_type) {
              if (Array.isArray(nodeInfo.node_type) && nodeInfo.node_type.length > 0) {
                finalSrcType = nodeInfo.node_type[0];
              } else if (typeof nodeInfo.node_type === 'string') {
                finalSrcType = nodeInfo.node_type;
              }
            }
            const nodeProps = nodeInfo?.all_properties || srcNodeProps;

            if (!nodeTypes.has(finalSrcType)) {
              nodeTypes.set(finalSrcType, nextCategoryId);
              nextCategoryId++;
            }
            
            let nodeName;
            if (nodeProps.content) {
              nodeName = nodeProps.content.substring(0, 8) + '...';
            } else if (nodeProps.retext) {
              nodeName = nodeProps.retext.substring(0, 8) + '...';
            } else if (nodeProps.title) {
              nodeName = nodeProps.title.substring(0, 8) + '...';
            } else if (nodeProps.text) {
              nodeName = nodeProps.text.substring(0, 8) + '...';
            } else if (srcNodeProps.name) {
              nodeName = srcNodeProps.name.substring(0, 8) + '...';
            } else {
              nodeName = '节点';
            }
                    
            nodes.set(source, {
              id: source,
              name: nodeName,
              symbolSize: getNodeSizeByType(finalSrcType),
              itemStyle: { color: getNodeColorByType(finalSrcType) },
              category: nodeTypes.get(finalSrcType),
              draggable: true,
              originalData: {
                vid: source,
                type: finalSrcType,
                ...nodeProps
              }
            });
          }

          if (item.e_type === 'forwarded' && !nodes.has(target)) {
            // 获取节点信息：优先使用API获取的信息，如果没有则使用item中的信息
            const nodeInfo = allNodesInfo.value.get(target);
            const dstNodeType = item.dst_type || 'Unknown';
            const dstNodeProps = item.dst_props || {};
            
            // 确定最终节点类型 - 处理不同格式的node_type数据
            let finalDstType = dstNodeType || 'Unknown';
            if (nodeInfo && nodeInfo.node_type) {
              if (Array.isArray(nodeInfo.node_type) && nodeInfo.node_type.length > 0) {
                finalDstType = nodeInfo.node_type[0];
              } else if (typeof nodeInfo.node_type === 'string') {
                finalDstType = nodeInfo.node_type;
              }
            }
            const nodeProps = nodeInfo?.all_properties || dstNodeProps;

            if (!nodeTypes.has(finalDstType)) {
              nodeTypes.set(finalDstType, nextCategoryId);
              nextCategoryId++;
            }
            
            let nodeName;
            if (nodeProps.content) {
              nodeName = nodeProps.content.substring(0, 8) + '...';
            } else if (nodeProps.retext) {
              nodeName = nodeProps.retext.substring(0, 8) + '...';
            } else if (nodeProps.title) {
              nodeName = nodeProps.title.substring(0, 8) + '...';
            } else if (nodeProps.text) {
              nodeName = nodeProps.text.substring(0, 8) + '...';
            } else if (dstNodeProps.name) {
              nodeName = dstNodeProps.name.substring(0, 8) + '...';
            } else {
              nodeName = '节点';
            }
            
            nodes.set(target, {
              id: target,
              name: nodeName,
              symbolSize: getNodeSizeByType(finalDstType),
              itemStyle: { color: getNodeColorByType(finalDstType) },
              category: nodeTypes.get(finalDstType),
              draggable: true,
              originalData: {
                vid: target,
                type: finalDstType,
                ...nodeProps
              }
            });
          }

          links.push({
            source: source,
            target: target,
            name: item.e_type,
            lineStyle: {
              width: item.e_type === 'belong' ? 3 : 2,
              curveness: item.e_type === 'belong' ? 0.1 : 0.2,
              color: item.e_type === 'belong' ? '#52c41a' : '#faad14',
              opacity: 0.9
            }
          });
        });
        
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
                repulsion: 350,
                edgeLength: 120
              },
              roam: true,
              label: {
                show: true,
                fontSize: 12,
                overflow: 'truncate'
              },
              edgeSymbol: ['none', 'arrow'],
              edgeSymbolSize: [0, 8],
              edgeLabel: {
                fontSize: 10,
                formatter: '{b}'
              },
              data: Array.from(nodes.values()),
              links: links,
              categories: Array.from(nodeTypes.entries()).map(([type]) => ({ 
                name: type,
                itemStyle: { color: getNodeColorByType(type) }
              }))
            }
          ]
        };
        
        chart.value.setOption(option);
        
        chart.value.on('click', async (params) => {
          if (params.dataType === 'node') {
            if (params.data.originalData?.type === 'Original_Tweet') {
              window.scrollTo({ top: 0, behavior: 'smooth' });
            } else {
              const nodeId = params.data.id;
              // 优先使用allNodesInfo中已有的完整节点信息
              let nodeInfo = allNodesInfo.value.get(nodeId);
              
              // 如果没有完整信息，则调用API获取
              if (!nodeInfo) {
                loadingGraph.value = true;
                try {
                  const response = await getStartNodeInfo(nodeId);
                  if (response && response.data && response.data.results) {
                    nodeInfo = response.data.results;
                    allNodesInfo.value.set(nodeId, nodeInfo);
                  }
                } catch (error) {
                  console.warn(`获取节点 ${nodeId} 信息失败:`, error);
                } finally {
                  loadingGraph.value = false;
                }
              }
              
              // 设置选中节点信息，合并原始数据和API获取的数据
              selectedNode.value = {
                ...params.data.originalData,
                ...nodeInfo?.all_properties
              };
            }
          }
        });
        
        window.addEventListener('resize', () => {
          if (chart.value) {
            chart.value.resize();
          }
        });
      };

      const getNodeColorByType = (type) => {
        const colorMap = {
          'Event': '#1890ff',
          'Article': '#34A853',
          'Original_Tweet': '#FBBC05',
          'Retweet': '#F2994A',
          'User': '#9B51E0',
          'Comment': '#EA4335',
          'Unknown': '#8884d8'
        };
        return colorMap[type] || colorMap['Unknown'];
      };
      
      const getNodeSizeByType = (type) => {
        const sizeMap = {
          'Event': 50,
          'Article': 40,
          'Original_Tweet': 40,
          'Retweet': 30,
          'User': 30,
          'Comment': 30,
          'Unknown': 35
        };
        return sizeMap[type] || sizeMap['Unknown'];
      };

      const closeNodeDetail = () => {
        selectedNode.value = null;
      };
      
      const getNodeTitle = (node) => {
        return node.title ||  '转发节点';
      };
      
      const getNodeType = (node) => {
        return node.type || node.e_type || '未知类型';
      }

      // 新增：图片点击放大方法
      const handleImageClick = (url) => {
        selectedImageUrl.value = url;
        showImageModal.value = true;
      }

      // 新增：关闭图片模态框方法
      const closeImageModal = () => {
        showImageModal.value = false;
        selectedImageUrl.value = '';
      };


      
      return {
        currentGraphId,
        relatedData,
        loadingGraph,
        chart,
        selectedNode,
        chartContainer,
        errorMessage,
        loadGraphData,
        clearGraph,
        closeNodeDetail,
        getNodeTitle,
        getNodeType,
        formatDate,
        originalTweet,
        currentGraphEvent,  // 导出事件名称变量
        switchToEventView,
        hasSearched,  // 导出新增的状态变量
        startNodeInfo,  // 导出节点详细信息
        // 导出新增的图片放大相关变量和方法
        showImageModal,
        selectedImageUrl,
        handleImageClick,
        closeImageModal
      };
    }
  };
</script>