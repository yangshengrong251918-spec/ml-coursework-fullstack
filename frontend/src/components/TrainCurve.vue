<template>
  <el-card v-if="show">
    <div slot="header">训练曲线</div>
    <div ref="lossChart" style="height:200px;"></div>
    <div ref="accChart" style="height:200px; margin-top:10px;"></div>
  </el-card>
</template>

<script>
import * as echarts from 'echarts'
import { getTrainCurves } from '@/utils/api'

export default {
  props: {
    // 由父组件控制什么时候刷新
    refreshKey: {
      type: Number,
      default: 0
    }
  },
  data() {
    return {
      show: false,
      lossChart: null,
      accChart: null
    }
  },
  watch: {
    refreshKey() {
      this.fetchCurves()
    }
  },
  methods: {
    async fetchCurves() {
      try {
        const res = await getTrainCurves()
        if (res.data.status === 'done') {
          this.show = true
          const history = res.data.history
          const epochs = Array.from({length: history.loss.length}, (_, i) => i + 1)

          this.$nextTick(() => {
            this.renderLossCurve(epochs, history.loss, history.val_loss)
            this.renderAccCurve(epochs, history.accuracy, history.val_accuracy)
          })
        }
      } catch (e) {
        console.error('获取训练曲线失败', e)
      }
    },
    renderLossCurve(epochs, loss, valLoss) {
      if (!this.lossChart) this.lossChart = echarts.init(this.$refs.lossChart)
      this.lossChart.setOption({
        title: { text: '损失曲线', left: 'center', textStyle: { fontSize: 12 } },
        tooltip: { trigger: 'axis' },
        legend: { data: ['训练集', '验证集'], bottom: 0 },
        xAxis: { type: 'category', data: epochs, name: 'Epoch' },
        yAxis: { type: 'value', name: 'Loss' },
        series: [
          { name: '训练集', type: 'line', data: loss, smooth: true, lineStyle: { color: '#409EFF' } },
          { name: '验证集', type: 'line', data: valLoss, smooth: true, lineStyle: { color: '#f56c6c' } }
        ]
      })
      window.addEventListener('resize', () => this.lossChart && this.lossChart.resize())
    },
    renderAccCurve(epochs, acc, valAcc) {
      if (!this.accChart) this.accChart = echarts.init(this.$refs.accChart)
      this.accChart.setOption({
        title: { text: '准确率曲线', left: 'center', textStyle: { fontSize: 12 } },
        tooltip: { trigger: 'axis' },
        legend: { data: ['训练集', '验证集'], bottom: 0 },
        xAxis: { type: 'category', data: epochs, name: 'Epoch' },
        yAxis: { type: 'value', name: 'Accuracy', min: 0, max: 1 },
        series: [
          { name: '训练集', type: 'line', data: acc, smooth: true, lineStyle: { color: '#67c23a' } },
          { name: '验证集', type: 'line', data: valAcc, smooth: true, lineStyle: { color: '#e6a23c' } }
        ]
      })
      window.addEventListener('resize', () => this.accChart && this.accChart.resize())
    }
  }
}
</script>
