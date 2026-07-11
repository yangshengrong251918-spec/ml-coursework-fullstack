// Vue CLI 2.0 风格的配置文件
'use strict'

const path = require('path')

module.exports = {
  dev: {
    // 开发环境配置
    env: require('./dev.env'),
    port: 8080,
    autoOpenBrowser: true,
    assetsSubDirectory: 'static',
    assetsPublicPath: '/',
    proxyTable: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    },
    cssSourceMap: false
  },
  build: {
    // 生产环境配置
    env: require('./prod.env'),
    index: path.resolve(__dirname, '../dist/index.html'),
    assetsRoot: path.resolve(__dirname, '../dist'),
    assetsSubDirectory: 'static',
    assetsPublicPath: '/',
    productionSourceMap: true,
    productionGzip: false,
    productionGzipExtensions: ['js', 'css'],
    bundleAnalyzerReport: false
  }
}
