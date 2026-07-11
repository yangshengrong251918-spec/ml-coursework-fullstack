<template>
  <el-card>
    <div slot="header">特征重要性</div>
    <div v-if="loading" style="text-align:center; padding:20px; color:#999;">加载中...</div>
    <div ref="chart" style="height:280px;" v-show="!loading"></div>
  </el-card>
</template>

<script>
import * as echarts from 'echarts'
import { getImportance } from '@/utils/api'

export default {
  data() {
    return {
      loading: true,
      chart: null
    }
  },
  mounted() {
    this.fetchData()
    this.$root.$on('train-done', this.fetchData)
  },
  methods: {
    async fetchData() {
      this.loading = true
      try {
        const res = await getImportance()
        const data = res.data.slice(0, 10)  // Top 10
        this.$nextTick(() => this.renderChart(data))
      } catch (e) {
        console.error('获取特征重要性失败', e)
      }
      this.loading = false
    },
    renderChart(data) {
      if (!this.chart) this.chart = echarts.init(this.$refs.chart)

      const features = data.map(d => d.feature)
      const values = data.map(d => d.importance)

      this.chart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: 100, right: 20, top: 10, bottom: 30 },
        xAxis: { type: 'value', name: '重要性' },
        yAxis: {
          type: 'category',
          data: features.reverse(),
          axisLabel: { fontSize: 10 }
        },
        series: [{
          type: 'bar',
          data: values.reverse(),
          itemStyle: {
            color: function(params) {
              const colors = ['#409EFF', '#67c23a', '#e6a23c', '#f56c6c', '#909399',
                             '#b37feb', '#5cdbd3', '#ff85c0', '#ffc069', '#95de64']
              return colors[params.dataIndex % colors.length]
            }
          },
          label: {
            show: true,
            position: 'right',
            formatter: function(params) {
              return params.value.toFixed(2)
            }
          }
        }]
      })
      window.addEventListener('resize', () => this.chart && this.chart.resize())
    }
  }
}
</script>
