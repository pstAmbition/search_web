const { defineConfig } = require('@vue/cli-service')
module.exports = {
  lintOnSave: false,
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        ws: true,
        secure: false,
        pathRewrite: {
          '^/api': '/api'
        },
        // 添加更多的代理配置以确保请求正确转发
        headers: {
          Connection: 'keep-alive'
        },
        onProxyReq: function(proxyReq, req, res) {
          console.log('Proxying request:', req.method, req.url);
        },
        onProxyRes: function(proxyRes, req, res) {
          console.log('Proxy response status:', proxyRes.statusCode, 'for', req.url);
        }
      }
    },
    port: 8080,
    host: '0.0.0.0',
    // 禁用HMR可能会解决一些请求中断问题
    hot: true,
    // 启用静态资源压缩
    compress: true
  },
  // 其他配置保持不变
}