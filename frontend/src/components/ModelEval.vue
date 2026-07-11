<template>
  <el-card>
    <div slot="header">模型评估</div>

    <!-- 没训练时 -->
    <div v-if="status === 'pending'" style="color:#999; text-align:center; padding:30px 0;">
      还没训练模型，去左边训练一下
    </div>

    <!-- 训练出错 -->
    <div v-else-if="status === 'error'" style="color:#f56c6c; text-align:center; padding:30px 0;">
      {{ errorMsg }}
    </div>

    <!-- 评估结果显示 -->
    <template v-else-if="metrics">
      <!-- 指标卡片 -->
      <el-row :gutter="10">
        <el-col :span="4"><el-statistic title="准确率" :value="metrics.accuracy * 100" :precision="2" suffix="%"/></el-col>
        <el-col :span="5"><el-statistic title="精确率" :value="metrics.precision * 100" :precision="2" suffix="%"/></el-col>
        <el-col :span="5"><el-statistic title="召回率" :value="metrics.recall * 100" :precision="2" suffix="%"/></el-col>
        <el-col :span="5"><el-statistic title="F1" :value="metrics.f1" :precision="4"/></el-col>
        <el-col :span="5"><el-statistic title="AUC" :value="aucValue * 100" :precision="2" suffix="%"/></el-col>
      </el-row>

      <el-row :gutter="10" style="margin-top:15px;">
        <!-- 混淆矩阵 -->
        <el-col :span="12">
          <div ref="cmChart" style="height:220px;"></div>
        </el-col>
        <!-- ROC 曲线 -->
        <el-col :span="12">
          <div ref="rocChart" style="height:220px;"></div>
        </el-col>
      </el-row>
    </template>
  </el-card>
</template>

<script>
import * as echarts from 'echarts'
import { getEvaluate } from '@/utils/api'

export default {
  data() {
    return {
      status: 'pending',  // pending | done | error
      errorMsg: '',
      metrics: null,
      cmData: null,
      rocData: null,
      cmChart: null,
      rocChart: null
    }
  },
  computed: {
    aucValue() {
      return this.rocData ? this.rocData.auc : 0
    }
  },
  mounted() {
    this.$root.$on('train-done', this.fetchEval)
  },
  methods: {
    async fetchEval() {
      try {
        const res = await getEvaluate()
        if (res.data.status === 'done') {
          this.status = 'done'
          this.metrics = res.data.metrics
          this.cmData = res.data.confusionMatrix
          this.rocData = res.data.roc

          this.$nextTick(() => {
            this.renderConfusionMatrix()
            this.renderROC()
          })
        } else if (res.data.status === 'error') {
          this.status = 'error'
          this.errorMsg = res.data.message
        }
      } catch (e) {
        console.error('获取评估结果失败', e)
      }
    },

    // 混淆矩阵热力图
    renderConfusionMatrix() {
      if (!this.cmData) return
      if (!this.cmChart) this.cmChart = echarts.init(this.$refs.cmChart)

      const labels = this.cmData.labels
      const matrix = this.cmData.matrix

      const data = []
      for (let i = 0; i < labels.length; i++) {
        for (let j = 0; j < labels.length; j++) {
          data.push([j, i, matrix[i][j]])
        }
      }

      this.cmChart.setOption({
        title: { text: '混淆矩阵', left: 'center', textStyle: { fontSize: 12 } },
        tooltip: {
          formatter: function(params) {
            return '真实: ' + labels[params.value[1]] + '<br/>预测: ' + labels[params.value[0]] + '<br/>数量: ' + params.value[2]
          }
        },
        grid: { left: 80, right: 30, top: 40, bottom: 30 },
        xAxis: {
          type: 'category',
          data: labels,
          name: '预测值',
          nameLocation: 'center',
          nameGap: 25
        },
        yAxis: {
          type: 'category',
          data: labels,
          name: '真实值',
          nameLocation: 'center',
          nameGap: 35
        },
        visualMap: {
          min: 0,
          max: Math.max(...matrix.flat()),
          inRange: { color: ['#e8f4f8', '#409EFF'] },
          calculable: false,
          show: false
        },
        series: [{
          type: 'heatmap',
          data: data,
          label: {
            show: true,
            color: '#333',
            fontWeight: 'bold',
            fontSize: 14
          }
        }]
      })
      window.addEventListener('resize', () => this.cmChart && this.cmChart.resize())
    },

    // ROC 曲线
    renderROC() {
      if (!this.rocData) return
      if (!this.rocChart) this.rocChart = echarts.init(this.$refs.rocChart)

      const fpr = this.rocData.fpr
      const tpr = this.rocData.tpr

      this.rocChart.setOption({
        title: {
          text: 'ROC 曲线 (AUC=' + this.rocData.auc.toFixed(3) + ')',
          left: 'center',
          textStyle: { fontSize: 12 }
        },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'value', name: 'FPR', min: 0, max: 1 },
        yAxis: { type: 'value', name: 'TPR', min: 0, max: 1 },
        series: [
          {
            name: 'ROC',
            type: 'line',
            data: fpr.map((v, i) => [v, tpr[i]]),
            smooth: true,
            lineStyle: { color: '#409EFF', width: 2 },
            areaStyle: { color: 'rgba(64,158,255,0.1)' }
          },
          {
            name: '随机线',
            type: 'line',
            data: [[0, 0], [1, 1]],
            lineStyle: { type: 'dashed', color: '#ccc' },
            silent: true
          }
        ]
      })
      window.addEventListener('resize', () => this.rocChart && this.rocChart.resize())
    }
  }
}
</script>
