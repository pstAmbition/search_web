import { defineStore } from 'pinia';

// 创建溯源查询结果的store
export const useTraceStore = defineStore('trace', {
  state: () => ({
    results: [],         // 查询结果数据
    currentPage: 1,      // 当前页码
    itemsPerPage: 10,    // 每页显示数量
    selectedPlatform: '', // 选中的平台筛选条件
    loading: false,      // 加载状态
    errorMessage: ''     // 错误信息
  }),

  getters: {
    // 计算筛选后的结果
    filteredResults(state) {
      if (!state.selectedPlatform) {
        return state.results
      }
      return state.results.filter(item => item.datasource === state.selectedPlatform)
    },

    // 计算总页数
    totalPages(state) {
      return Math.ceil(this.filteredResults.length / state.itemsPerPage)
    },

    // 计算当前页显示的结果
    paginatedResults(state) {
      const startIndex = (state.currentPage - 1) * state.itemsPerPage
      return this.filteredResults.slice(startIndex, startIndex + state.itemsPerPage)
    }
  },

  actions: {
    // 设置查询结果
    setResults(data) {
      this.results = data
      this.currentPage = 1  // 重置到第一页
    },

    // 设置当前页码
    setCurrentPage(page) {
      this.currentPage = page
    },

    // 上一页
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--
      }
    },

    // 下一页
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++
      }
    },

    // 重置分页
    resetPagination() {
      this.currentPage = 1
    },

    // 设置平台筛选条件
    setSelectedPlatform(platform) {
      this.selectedPlatform = platform
      this.currentPage = 1  // 重置到第一页
    },

    // 设置加载状态
    setLoading(loading) {
      this.loading = loading
    },

    // 设置错误信息
    setErrorMessage(message) {
      this.errorMessage = message
    }
  }
})