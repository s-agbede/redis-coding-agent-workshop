const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: process.env.VUE_APP_BASE_PATH || '/',
  outputDir: 'dist',
  assetsDir: 'assets',
  devServer: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VUE_APP_API_URL || 'http://localhost:8080',
        changeOrigin: true
      },
      '/terminal': {
        target: process.env.VUE_APP_API_URL || 'http://localhost:8080',
        changeOrigin: false,
        ws: true
      },
      '/app/': {
        target: process.env.VUE_APP_API_URL || 'http://localhost:8080',
        changeOrigin: true
      }
    }
  }
})
