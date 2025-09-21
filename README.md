# search_web项目说明文档

## 项目概述

search_web是一个集成多模态搜索、图数据库分析和事件管理的Web应用系统，旨在提供高效的数据检索、可视化分析和事件监控功能。

## 项目结构

项目采用前后端分离架构，分为Web-Backend（Python后端）和Web-Frontend（Vue前端）两个主要部分。

```
search_web/
├── Web-Backend/              # Python Flask后端服务
│   ├── app.py                # Flask应用主入口
│   ├── routes.py             # API路由定义
│   ├── config.py             # 应用配置文件
│   ├── services/             # 服务层实现
│   │   ├── nebula_service.py # NebulaGraph图数据库服务
│   │   ├── search_service.py # Milvus、ES数据库近似检索服务
│   │   └── mongodb_service.py # MongoDB数据库服务
│   ├── utils.py              # 工具函数
│   └── uploads/              # 上传文件存储目录
└── Web-Frontend/             # Vue 3前端应用
    ├── public/               # 静态资源文件
    ├── src/                  # 源代码目录
    │   ├── App.vue           # 应用根组件
    │   ├── main.js           # 应用入口
    │   ├── router/           # 路由配置
    │   ├── components/       # Vue组件
    │   ├── views/            # 页面视图
    │   ├── store/            # Pinia状态管理
    │   └── service/          # API请求服务
    ├── package.json          # 项目依赖配置
    └── vue.config.js         # Vue配置文件
```

## 技术栈

### 后端技术栈
- **编程语言**: Python 3.x
- **Web框架**: Flask
- **数据库**: 
  - MongoDB（事件数据存储）
  - NebulaGraph（图数据库，关系分析）
  - Milvus（向量数据库，多模态搜索）
  - Elasticsearch（搜索引擎，全文检索）
- **第三方库**: 
  - flask-cors（跨域支持）
  - towhee（多模态处理）
  - pymilvus（Milvus客户端）
  - elasticsearch（ES客户端）
  - nebula3（NebulaGraph客户端）
  - pillow（图像处理）

### 前端技术栈
- **框架**: Vue 3
- **路由**: Vue Router 4
- **状态管理**: Pinia
- **HTTP客户端**: Axios
- **可视化**: 
  - ECharts（数据图表）
  - Vis-network（关系图可视化）
- **样式**: Tailwind CSS
- **构建工具**: Vue CLI

## 功能模块

### 1. 多模态搜索

#### 文本搜索
- 通过关键词搜索相关事件和内容
- 支持相关性分数过滤

#### 图片搜索
- 上传图片进行相似图片检索
- 返回相关事件信息

#### 视频搜索
- 上传视频进行相似视频检索
- 支持视频转码和特征提取

### 2. 图数据库分析

基于NebulaGraph实现的图数据查询功能：
- 通过事件名称查询相关节点和关系
- 通过ID查询相关推文和关联信息
- 支持自定义图查询语句执行

### 3. 事件管理

基于MongoDB的事件数据管理：
- 获取所有事件（支持分页、排序和多条件过滤）
- 获取风险事件（isRisk=true）
- 导出事件数据（支持JSON和JSONL格式）
- 数据库统计信息查询

### 4. 数据可视化

基于ECharts和Vis-network的数据可视化功能：
- 事件趋势分析图表
- 关系网络图展示
- 仪表盘指标统计

## 核心API端点

### 搜索API
```
POST /api/search/text       # 文本搜索
POST /api/search/picture    # 图片搜索
POST /api/search/video      # 视频搜索
```

### 图数据库API
```
POST /api/executeCustomQuery  # 执行自定义NebulaGraph查询
GET /api/getRelatedByEvent    # 通过事件名称获取相关节点
GET /api/getRelatedById       # 通过ID获取相关节点
GET /api/getOriginalTweetById # 获取原始推文信息
```

### 事件管理API
```
GET /api/getAllEvents         # 获取所有事件（支持分页和过滤）
GET /api/getRiskEvents        # 获取风险事件
GET /api/getDatabaseStats     # 获取数据库统计信息
GET /api/exportEvents         # 导出事件数据
GET /api/getDashboardMetrics  # 获取仪表盘指标
```

### 文件上传API
```
POST /api/upload              # 通用文件上传接口
```

## 配置与部署

### 后端配置

Web-Backend需要配置以下环境变量或配置文件参数：
- NebulaGraph连接信息
- MongoDB连接信息
- Milvus连接信息
- Elasticsearch连接信息
- 日志级别
- 上传目录路径

### 前端配置

前端通过vue.config.js配置开发服务器代理，将API请求转发到后端服务：
```javascript
proxy: {
  '/api': {
    target: 'http://localhost:5000',
    changeOrigin: true,
    ws: true,
    secure: false
  }
}
```

### 启动流程

1. **启动后端服务**
```bash
cd Web-Backend
python app.py
# 或使用gunicorn/uwsgi部署
# gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. **启动前端服务**
```bash
cd Web-Frontend
npm install
npm run serve
# 或构建生产版本
# npm run build
```

## 开发说明

### 后端开发
- 遵循Flask应用工厂模式
- 服务层采用模块化设计，分离不同数据源的操作
- 使用Blueprint组织API路由

### 前端开发
- 采用Vue 3 Composition API
- 使用Pinia进行状态管理
- 组件化开发UI界面
- API请求封装在service目录

## 注意事项
1. 确保所有依赖服务（MongoDB、NebulaGraph、Milvus、Elasticsearch）正常运行
2. 开发环境中使用的是前端代理，生产环境需要配置正确的API地址
3. 文件上传功能支持图片和视频，保存在uploads目录
4. 服务启动时会自动初始化各数据库连接池

## License

[MIT](LICENSE)