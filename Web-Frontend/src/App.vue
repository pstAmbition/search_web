
<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <HeaderBar 
      :sidebar-opened="sidebarOpened" 
      @toggle-sidebar="toggleSidebar"
    />

    <div class="app-main">
      <!-- 左侧侧边栏 -->
      <Sidebar 
        :sidebar-opened="sidebarOpened" 
        :active-tab="activeTab"
        @switch-tab="switchTab"
      />

      <!-- 右侧内容区 -->
      <main class="app-content">
        <!-- 标签页导航 - 仅在"多模态传播工具"菜单时显示 -->
        <Tabs @tab-change="handleTabChange" v-if="isToolMenuActive" />
        <div class="content-wrapper">
          <!-- 使用keep-alive缓存需要保留状态的路由组件 -->
          <!-- 为SearchView使用固定key以确保状态保留 -->
          <router-view v-slot="{ Component }">
            <keep-alive :include="['SearchView', 'PathView', 'EventView']">
              <component 
                :is="Component" 
                :key="$route.name === 'Search' ? 'search-view' : ($route.name === 'Event' ? 'event-view' : $route.fullPath)" 
              />
            </keep-alive>
          </router-view>
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import { ref, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import HeaderBar from './components/Header.vue';
import Sidebar from './components/Sidebar.vue';
import Tabs from './components/Tabs.vue';

export default {
  name: 'App',
  components: {
    HeaderBar,
    Sidebar,
    Tabs
  },
  setup() {
    const route = useRoute();
    const router = useRouter();
    // 侧边栏状态
    const sidebarOpened = ref(true);
    // 活动标签
    const activeTab = ref('trace');

    const cachedViews = ref(['SearchView', 'PathView', 'EventView']);
    // 添加路由变化监听
    watch(() => route.name, (newName, oldName) => {
      console.log('路由变化:', oldName, '->', newName);
    });

    // 计算属性：判断是否为"多模态传播工具"菜单
    const isToolMenuActive = computed(() => {
      return activeTab.value.startsWith('tool-') || activeTab.value === 'trace' || activeTab.value === 'tool';
    });
    
    // 切换侧边栏显示状态
    const toggleSidebar = () => {
      sidebarOpened.value = !sidebarOpened.value;
    };
    
    // 切换菜单
    const switchTab = (tab) => {
      activeTab.value = tab;
      // 添加路由跳转逻辑
      if (tab === 'trace' || tab === 'tool-trace' || tab === 'tool') {
        router.push('/trace'); // 溯源页面
      } else if (tab === 'path' || tab === 'tool-path') {
        router.push('/path'); // 路径页面
      } else if (tab === 'event' || tab === 'tool-event') {
        router.push('/event'); // 事件详情页面
      } else if (tab === 'risk') {
        router.push('/risk'); // 风险传播事件库
      } else if (tab === 'fake') {
        router.push('/fake'); // 虚假信息知识库
      } else if (tab === 'bad') {
        router.push('/bad'); // 不良内容知识库
      } else if (tab === 'dashboard') {
        router.push('/dashboard'); // 数据库指标仪表盘
      } else if (tab === 'detection') {  // 新增这一行
        router.push('/detection'); // 虚假信息检测  // 新增这一行
      }
    };
    
    // 监听路由变化，更新活动标签
    watch(() => route.name, (newRouteName) => {
      if (newRouteName === 'Search' || newRouteName === 'Trace') {
        activeTab.value = newRouteName === 'Search' ? 'trace' : 'tool-trace';
      } else if (newRouteName === 'Path') {
        activeTab.value = 'tool-path';
      } else if (newRouteName === 'Event') {
        activeTab.value = 'tool-event';
      } else if (newRouteName === 'Detection') {  // 新增这一行
        activeTab.value = 'detection';  // 新增这一行
      } else {
        activeTab.value = newRouteName ? newRouteName.toLowerCase() : '';
      }
    });
    
    // 处理标签页切换
    const handleTabChange = (tab) => {
      console.log('切换到标签:', tab);
    };

    return {
      sidebarOpened,
      activeTab,
      cachedViews,
      isToolMenuActive,
      toggleSidebar,
      switchTab,
      handleTabChange
    };
  }
};
</script>

<style>
/* 基础样式 */
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background-color: #f5f7fa;
}

/* 主内容区 */
.app-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 右侧内容区 */
.app-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  box-sizing: border-box;
}

/* 标签页样式调整 */
.tabs-container {
  border-bottom: 1px solid #e8e8e8;
  background-color: #fff;
  z-index: 10;
  width: 100%;
}

.content-wrapper {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  padding: 15px 20px;
  min-height: calc(100% - 40px);
}

/* 调整内容区域的样式，使没有标签页时内容紧贴顶部 */
.content-wrapper {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  padding: 15px 20px;
  min-height: calc(100% - 40px);
  margin-top: 0; /* 确保没有上外边距 */
}

/* 响应式调整 */
@media (max-width: 768px) {
  .app-content {
    padding: 10px;
  }
  
  .content-wrapper {
    padding: 15px;
  }
}
</style>
