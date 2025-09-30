# search_web项目说明文档

## 项目概述

search_web是一个集成多模态搜索、图数据库分析、事件管理和虚假信息检测的Web应用系统，旨在提供高效的数据检索、可视化分析、事件监控和内容真实性验证功能。

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
│   ├── algorithms/           # 虚假信息检测算法模块
│   │   ├── text_detection/   # 文本谣言检测
│   │   ├── image_detection/  # 图像伪造检测
│   │   ├── audio_video_detection/ # 音视频伪造检测
│   │   ├── entity_identification/ # 实体识别
│   │   └── multimodal_detection/  # 多模态假信息检测
│   ├── scripts/              # 服务管理脚本
│   │   ├── start_all_algorithms.sh  # 启动所有算法服务
│   │   ├── stop_all_algorithms.sh   # 停止所有算法服务
│   │   └── check_services.sh        # 检查服务状态
│   ├── utils.py              # 工具函数
│   ├── uploads/              # 上传文件存储目录
│   └── 算法配置文档.md        # 算法配置详细文档
└── Web-Frontend/             # Vue 3前端应用
    ├── public/               # 静态资源文件
    ├── src/                  # 源代码目录
    │   ├── App.vue           # 应用根组件
    │   ├── main.js           # 应用入口
    │   ├── router/           # 路由配置
    │   ├── components/       # Vue组件
    │   ├── views/            # 页面视图
    │   │   └── detection/    # 虚假信息检测页面
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
- **深度学习框架**:
  - PyTorch（模型推理）
  - Transformers（预训练模型）
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

### 5. 虚假信息检测 ⭐ 新增

基于深度学习的多模态虚假信息检测系统，包含5个独立的检测模块：

#### 文本谣言检测
- 基于RoBERTa预训练模型的文本分类
- 检测文本内容的真实性
- 返回真假判断和置信度
- API端口: 5013

#### 图像伪造检测
- 基于Xception网络的图像真伪鉴别
- 检测图像是否被篡改或伪造
- 支持多种图像格式（PNG、JPG、GIF）
- API端口: 5014

#### 音视频伪造检测
- 音频深度伪造检测（基于Wav2Vec2）
- 视频深度伪造检测（基于Xception）
- 支持MP3、WAV、MP4等格式
- API端口: 5015

#### 实体识别
- 基于BERT的命名实体识别
- 识别文本中的人名、地名、组织等实体
- 支持中文实体识别
- API端口: 5016

#### 多模态假新闻检测
- 综合文本和图像进行联合检测
- 基于BERT文本编码和图像特征融合
- 提供更准确的真伪判断
- API端口: 5017

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

### 虚假信息检测API ⭐ 新增
```
POST /api/text/detect         # 文本谣言检测
POST /api/image/detect        # 图像伪造检测
POST /api/audiovideo/detect   # 音视频伪造检测
POST /api/entity/extract      # 实体识别
POST /api/multimodal/detect   # 多模态假信息检测
```

### 文件上传API
```
POST /api/upload              # 通用文件上传接口
```

## 配置与部署

### 后端配置

#### 主服务配置
Web-Backend需要配置以下环境变量或配置文件参数：
- NebulaGraph连接信息
- MongoDB连接信息
- Milvus连接信息
- Elasticsearch连接信息
- 日志级别
- 上传目录路径

#### 虚假信息检测算法配置 ⭐ 新增
详细配置请参考 [算法配置文档.md](Web-Backend/算法配置文档.md)

**环境要求**:
- Python 3.8+
- Conda或Miniconda
- CUDA 11.0+（推荐，用于GPU加速）

**虚拟环境配置**:
```bash
# 为每个算法创建独立的虚拟环境
conda create -n text_detection python=3.8 -y
conda create -n image_detection python=3.8 -y
conda create -n audio_video_detection python=3.8 -y
conda create -n entity_identification python=3.8 -y
conda create -n multimodal_detection python=3.8 -y

# 激活环境并运行安装脚本
conda activate text_detection
cd Web-Backend/algorithms/text_detection
bash install_step_by_step.sh
# 其他模块类似...
```

**模型文件下载**:
由于GitHub对大文件有限制，模型权重文件（总计约3GB）需要从百度网盘下载。

**🔗 百度网盘下载链接**
- **虚假信息检测算法** 
- 链接: https://pan.baidu.com/s/1TtCq0jE30N22Y7AmGBp4ig?pwd=jxy2 
- 提取码: jxy2

**📋 下载说明**
- 所有模型文件已打包上传至百度网盘
- 包含5个算法模块的所有必需模型文件
- 详细列表和路径请参考[算法配置文档.md](Web-Backend/算法配置文档.md)

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

1. **启动主后端服务**
```bash
cd Web-Backend
python app.py
# 或使用gunicorn/uwsgi部署
# gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. **启动虚假信息检测算法服务** ⭐ 新增
```bash
# 进入后端目录
cd Web-Backend

# 启动所有算法服务（会自动激活各自的虚拟环境）
bash scripts/start_all_algorithms.sh

# 检查服务状态
bash scripts/check_services.sh

# 停止所有服务
bash scripts/stop_all_algorithms.sh
```

3. **启动前端服务**
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
- 算法服务采用独立进程部署，通过HTTP API调用

### 前端开发
- 采用Vue 3 Composition API
- 使用Pinia进行状态管理
- 组件化开发UI界面
- API请求封装在service目录

### 算法开发 ⭐ 新增
- 每个算法模块独立部署在各自的Conda虚拟环境中
- 使用Flask提供统一的RESTful API接口
- 支持GPU加速推理
- 日志统一存储在`Web-Backend/logs/`目录

## 服务端口说明

| 服务名称 | 端口 | 说明 |
|---------|------|------|
| 主后端服务 | 5000 | Flask主应用 |
| 文本谣言检测 | 5013 | 独立算法服务 |
| 图像伪造检测 | 5014 | 独立算法服务 |
| 音视频伪造检测 | 5015 | 独立算法服务 |
| 实体识别 | 5016 | 独立算法服务 |
| 多模态假信息检测 | 5017 | 独立算法服务 |

## 注意事项
1. 确保所有依赖服务（MongoDB、NebulaGraph、Milvus、Elasticsearch）正常运行
2. 开发环境中使用的是前端代理，生产环境需要配置正确的API地址
3. 文件上传功能支持图片和视频，保存在uploads目录
4. 服务启动时会自动初始化各数据库连接池
5. **虚假信息检测服务需要预先下载模型文件并配置虚拟环境** ⭐
6. **建议使用GPU服务器部署算法服务以获得更好的性能** ⭐
7. **算法服务日志存储在`Web-Backend/logs/`目录，便于问题排查** ⭐

## 性能建议

- **GPU加速**: 所有算法模块均支持CUDA加速，推荐使用GPU服务器
- **内存要求**: 建议至少16GB内存，所有算法服务同时运行需要约8-10GB内存
- **磁盘空间**: 模型文件总计约3GB，建议预留10GB以上空间
- **并发处理**: 可通过增加Flask worker数量提升并发能力

## License

[MIT](LICENSE)
