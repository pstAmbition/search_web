import axios from 'axios';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: '/api', // 后端 API 基础 URL
  timeout: 120000 // 请求超时时间增加到120秒
});

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    // 在发送请求之前做些什么，例如添加认证 token
    // config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  error => {
    // 对请求错误做些什么
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    // 对响应数据做些什么
    return response;
  },
  error => {
    // 对响应错误做些什么
    if (error.response) {
      // 服务器返回了错误状态码
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('Network Error:', error.request);
    } else {
      // 其他错误
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// API 请求函数
// 文本溯源查询
export const searchTraceByText = (queryContent, threshold) => {
  return apiClient.post('/search/text', new URLSearchParams({
    queryContent,
    threshold
  }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
};

// 图片溯源查询
export const searchTraceByImage = (file, topk) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('topk', topk);
  return apiClient.post('/search/picture', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

// 视频溯源查询
export const searchTraceByVideo = (file, topk, config = {}) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('topk', topk);
  return apiClient.post('/search/video', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...config  // 添加配置参数
  });
};

// 上传文件
export const uploadFile = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

// 通过 ID 获取推文数据
export const getOriginalTweetById = (id, space_name = 'Social_Network_1') => {
  return apiClient.get('/getOriginalTweetById', {
    params: { id, space_name }
  });
};

// 通过 ID 获取关联图谱数据
export const getGraphDataById = (id, space_name = 'Social_Network_1') => {
  return apiClient.get('/getRelatedById', {
    params: { id, space_name }
  });
};

// 获取节点详细信息
export const getStartNodeInfo = (node_id, space_name = 'Social_Network_1') => {
  return apiClient.get('/getStartNodeInfo', {
    params: { node_id, space_name }
  });
};

// 通过事件名称获取关联图谱数据
export const getGraphDataByEvent = (event, space_name = 'Social_Network_1') => {
  return apiClient.get('/getRelatedByEvent', {
    params: { event, space_name }
  });
};

// 获取所有事件列表（支持分页和按platform、region、Time和关键字过滤）
export const getAllEvents = async (page = 1, pageSize = 10, platform = '', keyword = '', region = '', start_time = '', end_time = '', sortBy = 'Time', sortOrder = -1) => {
  try {
    console.log('正在请求事件数据...');
    const startTime = Date.now();
    // 增加超时时间到120秒，因为这个请求可能处理大量数据
    const response = await apiClient.get('/getAllEvents', {
      params: { page, page_size: pageSize, platform: platform, keyword: keyword, region: region, start_time: start_time, end_time: end_time, sort_by: sortBy, sort_order: sortOrder },
      timeout: 120000 // 120秒超时
    });
    const endTime = Date.now();
    console.log(`事件数据请求成功，耗时: ${endTime - startTime}ms`);
    return response;
  } catch (error) {
    console.error('获取事件数据失败:', error);
    // 增强错误处理，返回更友好的错误信息
    if (error.code === 'ECONNABORTED') {
      // 请求超时
      console.error('请求超时(ERR_ABORTED): 服务器处理时间过长，请稍后重试');
    } else if (error.response) {
      // 服务器返回了错误状态码
      console.error('服务器错误:', error.response.status, error.response.data);
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('网络错误: 服务器未响应 (net::ERR_ABORTED)');
    }
    // 保留原始错误信息，不返回模拟数据，以便前端能够正确处理实际错误
    throw error;
  }
};

// 获取风险事件列表（isRisk="true"，支持分页和按platform、region、Time和关键字过滤）
export const getRiskEvents = async (page = 1, pageSize = 10, platform = '', keyword = '', region = '', start_time = '', end_time = '', sortBy = 'Time', sortOrder = -1) => {
  try {
    console.log('正在请求风险事件数据...');
    const startTime = Date.now();
    // 增加超时时间到120秒，因为这个请求可能处理大量数据
    const response = await apiClient.get('/getRiskEvents', {
      params: { page, page_size: pageSize, platform: platform, keyword: keyword, region: region, start_time: start_time, end_time: end_time, sort_by: sortBy, sort_order: sortOrder },
      timeout: 120000 // 120秒超时
    });
    const endTime = Date.now();
    console.log(`风险事件数据请求成功，耗时: ${endTime - startTime}ms`);
    return response;
  } catch (error) {
    console.error('获取风险事件数据失败:', error);
    // 增强错误处理，返回更友好的错误信息
    if (error.code === 'ECONNABORTED') {
      // 请求超时
      console.error('请求超时(ERR_ABORTED): 服务器处理时间过长，请稍后重试');
    } else if (error.response) {
      // 服务器返回了错误状态码
      console.error('服务器错误:', error.response.status, error.response.data);
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('网络错误: 服务器未响应 (net::ERR_ABORTED)');
    }
    // 保留原始错误信息，不返回模拟数据，以便前端能够正确处理实际错误
    throw error;
  }
};

// 导出事件数据
export const exportEvents = (keyword = '', region = '', start_time = '', end_time = '', is_risk = '', platform = '', format = 'json') => {
  return apiClient.get('/exportEvents', {
    params: { keyword, region, start_time, end_time, is_risk, platform, format },
    responseType: 'blob'  // 设置响应类型为blob以支持文件下载
  });
};

// 获取仪表盘指标数据
export const getDashboardMetrics = async () => {
  try {
    console.log('正在请求仪表盘数据...');
    const startTime = Date.now();
    // 增加超时时间到120秒，因为这个请求可能处理大量数据
    const response = await apiClient.get('/getDashboardMetrics', {
      timeout: 120000 // 120秒超时
    });
    const endTime = Date.now();
    console.log(`仪表盘数据请求成功，耗时: ${endTime - startTime}ms`);
    console.log('响应状态码:', response.status);
    console.log('响应数据大小:', JSON.stringify(response.data).length, 'bytes');
    return response;
  } catch (error) {
    console.error('获取仪表盘数据失败:', error);
    // 增强错误处理，返回更友好的错误信息
    if (error.code === 'ECONNABORTED') {
      // 请求超时
      console.error('请求超时(ERR_ABORTED): 服务器处理时间过长，请稍后重试');
    } else if (error.response) {
      // 服务器返回了错误状态码
      console.error('服务器错误:', error.response.status, error.response.data);
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('网络错误: 服务器未响应 (net::ERR_ABORTED)');
    }
    // 保留原始错误信息，不返回模拟数据，以便前端能够正确处理实际错误
    throw error;
  }
};

// 虚假信息知识库相关 API

// 获取虚假信息列表
export const getAllFakeKnowledge = async () => {
  try {
    console.log('正在请求虚假信息列表...');
    // 添加较短的超时设置，避免长时间等待
    const response = await apiClient.get('/fake-knowledge/all', {
      timeout: 30000 // 30秒超时
    });
    console.log('虚假信息列表请求成功，返回完整响应对象');
    // 返回完整响应对象，与其他API函数保持一致
    return response;
  } catch (error) {
    console.error('获取虚假信息列表失败:', error);
    // 重新抛出错误，保留原始错误信息
    throw error;
  }
};

// 获取虚假信息知识库统计数据
export const getFakeKnowledgeStats = async () => {
  try {
    const response = await apiClient.get('/fake-knowledge/stats');
    return response.data;
  } catch (error) {
    console.error('获取统计数据失败:', error);
    throw error;
  }
};

// 获取虚假信息详情
export const getFakeKnowledgeDetail = async (fakeId) => {
  console.log(`开始获取虚假信息详情，ID: ${fakeId}`);
  
  try {
    const response = await apiClient.get(`/fake-knowledge/detail/${encodeURIComponent(fakeId)}`);
    return response;
  } catch (error) {
    console.error('获取虚假信息详情失败:', error);
    throw error;
  }
};

// 获取虚假信息传播图谱数据
export const getFakeGraphData = async (fakeId) => {
  try {
    const response = await apiClient.get(`/fake-knowledge/graph/${encodeURIComponent(fakeId)}`);
    return response;
  } catch (error) {
    console.error('获取虚假信息图谱数据失败:', error);
    throw error;
  }
};

// 获取虚假信息多媒体资源
export const getFakeKnowledgeMedia = async (fakeId) => {
  try {
    console.log(`开始获取虚假信息多媒体资源，ID: ${fakeId}`);
    const response = await apiClient.get(`/fake-knowledge/media/${encodeURIComponent(fakeId)}`);
    return response;
  } catch (error) {
    console.error('获取虚假信息多媒体资源失败:', error);
    throw error;
  }
};

// 导出 axios 实例以供直接使用
export default apiClient;