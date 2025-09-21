<template>
  <div :class="['app-sidebar', { 'sidebar-closed': !sidebarOpened }]">
    <nav class="sidebar-menu">
      <ul>
        <!-- 多模态传播模型工具 -->
        <li class="menu-item" :class="{ 'active': activeTab === 'tool' }">
          <a href="#" @click.prevent="switchTab('tool')">
            <i class="fas fa-project-diagram"></i>
            <span>多模态传播模型工具</span>
            <!-- 展开/收起箭头 -->
            <i
              class="expand-arrow fas fa-chevron-right"
              :style="{ transform: isToolExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }"
            ></i>
          </a>

          <!-- 子菜单：v-show 控制显示，不销毁 -->
          <ul v-show="showSubmenu" class="submenu">
            <li class="submenu-item" :class="{ 'active': subTab === 'trace' }">
              <a href="#" @click.prevent="switchSubTab('trace')">
                <i class="fas fa-search"></i>
                <span>溯源</span>
              </a>
            </li>
            <li class="submenu-item" :class="{ 'active': subTab === 'path' }">
              <a href="#" @click.prevent="switchSubTab('path')">
                <i class="fas fa-road"></i>
                <span>路径</span>
              </a>
            </li>
            <li class="submenu-item" :class="{ 'active': subTab === 'event' }">
              <a href="#" @click.prevent="switchSubTab('event')">
                <i class="fas fa-file-alt"></i>
                <span>事件详情</span>
              </a>
            </li>
          </ul>
        </li>

        <!-- 风险传播事件库 -->
        <li class="menu-item" :class="{ 'active': activeTab === 'risk' || activeTab === 'dashboard' }">
          <a href="#" @click.prevent="switchTab('risk')">
            <i class="fas fa-exclamation-triangle"></i>
            <span>风险传播事件库</span>
          </a>

          <!-- 子菜单 - 始终显示 -->
          <div class="submenu-container" style="display: block !important; overflow: visible !important; height: auto !important; max-height: 1000px !important;">
            <ul class="submenu" style="display: block !important;">
              <li class="submenu-item" :class="{ 'active': activeTab === 'dashboard' }">
                <a href="#" @click.prevent="switchSubTab('dashboard')">
                  <i class="fas fa-chart-pie"></i>
                  <span>数据库指标仪表盘</span>
                </a>
              </li>
            </ul>
          </div>
        </li>
        <li class="menu-item" :class="{ 'active': activeTab === 'fake' }">
          <a href="#" @click.prevent="switchTab('fake')">
            <i class="fas fa-ban"></i>
            <span>虚假信息知识库</span>
          </a>
        </li>
        <li class="menu-item" :class="{ 'active': activeTab === 'bad' }">
          <a href="#" @click.prevent="switchTab('bad')">
            <i class="fas fa-times-circle"></i>
            <span>不良内容知识库</span>
          </a>
        </li>
      </ul>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  sidebarOpened: {
    type: Boolean,
    default: true
  },
  activeTab: {
    type: String,
    default: 'tool'
  }
});
const emit = defineEmits(['switchTab']);

// 当前子标签
const subTab = ref('trace');

// 是否展开 "多模态" 子菜单
const isToolExpanded = ref(false);

// 风险传播事件库子菜单总是展开，不再需要这个状态
// const isRiskExpanded = ref(false);

// 计算：是否显示子菜单（仅当 sidebar 展开 + tool 菜单激活 + 显式展开）
const showSubmenu = computed(() => {
  return isToolExpanded.value;
});

// 切换主菜单
const switchTab = (tab) => {
  if (tab === 'tool') {
    // 切换多模态菜单的展开/收起状态
    isToolExpanded.value = !isToolExpanded.value;
  } else if (tab === 'risk') {
    // 风险传播事件库子菜单始终显示，无需切换状态
    isToolExpanded.value = false;
  } else {
    // 点击其他菜单时收起多模态子菜单
    isToolExpanded.value = false;
  }
  // 发出事件通知父组件当前激活的菜单
  emit('switchTab', tab);
};

// 切换子菜单
const switchSubTab = (sub) => {
  subTab.value = sub;
  if (sub === 'trace' || sub === 'path' || sub === 'event') {
    emit('switchTab', `tool-${sub}`);
  } else if (sub === 'dashboard') {
    emit('switchTab', sub);
  }
};

// 监听外部 activeTab 变化（比如路由切换），同步展开状态和子菜单选中
watch(
  () => props.activeTab,
  (newTab) => {
    // 解析工具子标签并更新 subTab
    if (newTab.startsWith('tool-')) {
      const sub = newTab.split('-')[1];
      subTab.value = sub;
      isToolExpanded.value = true;
    } else if (newTab === 'dashboard') {
      subTab.value = newTab;
      isToolExpanded.value = false;
    } else if (newTab === 'risk') {
      isToolExpanded.value = false;
    } else {
      isToolExpanded.value = false;
    }
  }
);
</script>

<style scoped>
/* 左侧侧边栏 */
.app-sidebar {
  width: 256px;
  background-color: #2f2f2f; /* 修改为灰色背景 */
  color: #fff;
  transition: width 0.3s ease, box-shadow 0.3s ease;
  overflow-y: auto;
  height: 100%;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5); /* 添加深色阴影 */
}

.sidebar-closed {
  width: 64px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5); /* 缩小状态下的阴影 */
}

.sidebar-menu ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.menu-item {
  margin-bottom: 2px;
}

.menu-item a {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 20px 20px;
  color: rgba(255, 255, 255, 0.8); /* 提高文字对比度 */
  text-decoration: none;
  transition: all 0.3s;
  border-radius: 4px; /* 添加圆角 */
  font-size: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.6); /* 深色阴影 */
}

.menu-item a:hover {
  background-color: #3a3a3a; /* 悬停时背景色稍微变亮 */
  color: #fff;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.8); /* 悬停时阴影加深 */
}

.menu-item.active a {
  background-color: #4f4f4f;
  color: #fff;
  border-radius: 0;
}

/* 主菜单图标样式 */
.menu-item i {
  width: 20px;
  margin-right: 20px;
  text-align: center;
  font-size: 16px;
}

.menu-item a .expand-arrow {
  margin-right: auto; /* 确保箭头在最右侧 */
}

/* 展开箭头 */
.expand-arrow {
  margin-left: auto;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  transition: transform 0.2s ease; /* 添加旋转动画 */
}

.expand-arrow:hover {
  transform: scale(1.2); /* 悬停时放大箭头 */
}

/* 缩小侧边栏时隐藏箭头和文字 */
.sidebar-closed .expand-arrow,
.sidebar-closed span {
  display: none;
}

.sidebar-closed .menu-item a {
  justify-content: center;
  padding: 18px 0;
}

.sidebar-closed .menu-item i {
  margin-right: 0;
}

/* 子菜单容器 - 确保始终可见 */
.submenu-container {
  display: block !important;
  overflow: visible !important;
  height: auto !important;
  max-height: 1000px !important;
  transition: none !important;
  background-color: rgba(47, 47, 47, 0.8); /* 半透明背景 */
  border-left: 3px solid #2a85da;
  margin-top: 4px;
}

/* 子菜单 - 确保始终可见 */
.submenu {
  list-style: none;
  padding-left: 20px; /* 增加缩进 */
  margin: 0;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  transform: none !important;
  transition: none !important;
  height: auto !important;
  max-height: 1000px !important;
}

.submenu-item a {
  font-size: 14px; /* 子菜单项字体稍小 */
  padding: 10px 30px; /* 调整内边距 */
  color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: flex-start;
  border-radius: 4px;
  background-color: rgba(60, 60, 60, 0.7); /* 子菜单项背景色 */
  margin-bottom: 2px;
  border-left: 3px solid transparent;
  transition: all 0.3s ease;
}

.submenu-item a:hover {
  background-color: rgba(74, 74, 74, 0.8);
  color: #fff;
  border-left-color: #2a85da;
  transform: translateX(5px); /* 鼠标悬停时轻微右移 */
}

.submenu-item.active a {
  background-color: #2a85da;
  color: #fff;
  font-weight: 500;
  border-left-color: #fff;
  transform: translateX(5px); /* 激活时轻微右移 */
}

.submenu-item a:hover {
  background-color: #3a3a3a; /* 悬停时背景色稍微变亮 */
  color: #fff;
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.8); /* 悬停时阴影加深 */
}

.submenu-item.active a {
  background-color: #2a85da;
  color: #fff;
  font-weight: 500;
}

/* 缩小状态下隐藏子菜单 */
.sidebar-closed .submenu {
  display: none;
}

/* 响应式 */
@media (max-width: 768px) {
  .app-sidebar {
    position: fixed;
    top: 50px;
    left: 0;
    height: calc(100% - 50px);
    z-index: 99;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
  }

  .sidebar-closed {
    transform: translateX(-100%);
    width: 192px;
  }
}
</style>