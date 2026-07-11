<template>
  <el-card>
    <div slot="header">数据探索 (EDA)</div>

    <!-- 数据摘要 -->
    <el-row v-if="summary" :gutter="10" style="margin-bottom:10px;">
      <el-col :span="6"><el-statistic title="样本总数" :value="summary.totalSamples"></el-statistic></el-col>
      <el-col :span="6"><el-statistic title="特征数量" :value="summary.featureCount"></el-statistic></el-col>
      <el-col :span="6"><el-statistic title="流失率" :value="summary.churnRate * 100" :precision="1" suffix="%"></el-statistic></el-col>
      <el-col :span="6">
        <el-button size="mini" @click="showStats = !showStats" style="margin-top:18px;">
          {{ showStats ? '收起统计' : '查看详细统计' }}
        </el-button>
      </el-col>
    </el-row>

    <!-- 详细统计表 -->
    <el-table v-if="showStats && summary.featureStats" :data="statsTable" size="mini" max-height="200" style="margin-bottom:10px;">
      <el-table-column prop="feature" label="特征" width="100"></el-table-column>
      <el-table-column prop="mean" label="均值" width="70"></el-table-column>
      <el-table-column prop="median" label="中位数" width="70"></el-table-column>
      <el-table-column prop="min" label="最小" width="70"></el-table-column>
      <el-table-column prop="max" label="最大" width="70"></el-table-column>
      <el-table-column prop="std" label="标准差" width="70"></el-table-column>
      <el-table-column prop="missing" label="缺失值" width="60"></el-table-column>
    </el-table>

    <!-- 相关性热力图 -->
    <div ref="heatmapChart" style="height:280px;"></div>

    <el-row :gutter="10" style="margin-top:10px;">
      <!-- 目标分布 -->
      <el-col :span="12">
        <div ref="pieChart" style="height:200px;"></div>
      </el-col>
      <!-- 箱线图 -->
      <el-col :span="12">
        <div ref="boxChart" style="height:200px;"></div>
      </el-col>
    </el-row>
  </el-card>
</template>

<script>
import * as echarts from 'echarts'
import { getDataSummary, getEdaData, getBoxplotData } from '@/utils/api'

export default {
  data() {
    return {
      summary: null,
      showStats: false,
      chart1: null,
      chart2: null,
      chart3: null
    }
  },
  computed: {
    // 把 featureStats 转成表格数组
    statsTable() {
      if (!this.summary || !this.summary.featureStats) return []
      const stats = this.summary.featureStats
      return Object.keys(stats).map(key => ({
        feature: key,
        mean: stats[key].mean,
        median: stats[key].median,
        min: stats[key].min,
        max: stats[key].max,
        std: stats[key].std,
        missing: stats[key].missing
      }))
    }
  },
  mounted() {
    this.fetchAll()
  },
  methods: {
    async fetchAll() {
      try {
        const [sumRes, edaRes, boxRes] = await Promise.all([
          getDataSummary(),
          getEdaData(),
          getBoxplotData()
        ])
        this.summary = sumRes.data

        const eda = edaRes.data
        const boxData = boxRes.data

        this.$nextTick(() => {
          this.renderHeatmap(eda.correlationMatrix)
          this.renderPie(eda.targetDistribution)
          this.renderBoxplot(boxData)
        })
      } catch (e) {
        console.error('加载 EDA 数据失败', e)
      }
    },

    // 热力图
    renderHeatmap(corrMatrix) {
      if (!this.chart1) this.chart1 = echarts.init(this.$refs.heatmapChart)

      const features = corrMatrix.features
      const values = corrMatrix.values

      // 转成 ECharts heatmap 需要的格式
      const data = []
      for (let i = 0; i < features.length; i++) {
        for (let j = 0; j < features.length; j++) {
          data.push([j, i, values[i][j]])
        }
      }

      this.chart1.setOption({
        title: { text: '特征相关性热力图', left: 'center', textStyle: { fontSize: 12 } },
        tooltip: {
          formatter: function(params) {
            return params.value[0] + '~' + params.value[1] + ': ' + params.value[2].toFixed(3)
          }
        },
        grid: { left: 100, right: 30, top: 40, bottom: 60 },
        xAxis: {
          type: 'category',
          data: features,
          axisLabel: { rotate: 45, fontSize: 9 }
        },
        yAxis: {
          type: 'category',
          data: features,
          axisLabel: { fontSize: 9 }
        },
        visualMap: {
          min: -1,
          max: 1,
          inRange: {
            color: ['#f56c6c', '#fff', '#409EFF']
          },
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: 0
        },
        series: [{
          type: 'heatmap',
          data: data,
          label: {
            show: true,
            fontSize: 9,
            formatter: function(p) {
              return p.value[2].toFixed(1)
            }
          },
          emphasis: {
            itemStyle: { shadowBlur: 10 }
          }
        }]
      })
      window.addEventListener('resize', () => this.chart1 && this.chart1.resize())
    },

    // 饼图
    renderPie(dist) {
      if (!this.chart2) this.chart2 = echarts.init(this.$refs.pieChart)
      this.chart2.setOption({
        title: { text: '流失分布', left: 'center', textStyle: { fontSize: 12 } },
        tooltip: { trigger: 'item' },
        series: [{
          type: 'pie',
          radius: ['30%', '60%'],
          label: { formatter: '{b}\n{d}%' },
          data: [
            { value: dist['0'] || 0, name: '未流失' },
            { value: dist['1'] || 0, name: '流失' }
          ],
          color: ['#67c23a', '#f56c6c']
        }]
      })
      window.addEventListener('resize', () => this.chart2 && this.chart2.resize())
    },

    // 箱线图
    renderBoxplot(data) {
      if (!this.chart3) this.chart3 = echarts.init(this.$refs.boxChart)

      // 取前 3 个特征画箱线图（数据太多挤不下）
      const features = Object.keys(data).slice(0, 3)
      const seriesData = []
      const xAxisData = []

      features.forEach(feat => {
        const groups = data[feat]
        if (groups['0']) {
          seriesData.push(groups['0'])
          xAxisData.push(feat + '(未流失)')
        }
        if (groups['1']) {
          seriesData.push(groups['1'])
          xAxisData.push(feat + '(流失)')
        }
      })

      this.chart3.setOption({
        title: { text: '关键特征箱线图', left: 'center', textStyle: { fontSize: 12 } },
        tooltip: { trigger: 'axis' },
        xAxis: {
          type: 'category',
          data: xAxisData,
          axisLabel: { fontSize: 9, rotate: 20 }
        },
        yAxis: { type: 'value' },
        series: [{
          type: 'boxplot',
          data: seriesData,
          itemStyle: { color: '#409EFF' }
        }]
      })
      window.addEventListener('resize', () => this.chart3 && this.chart3.resize())
    }
  }
}
</script>
