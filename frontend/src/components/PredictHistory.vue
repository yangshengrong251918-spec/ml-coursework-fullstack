<template>
  <el-card>
    <div slot="header">
      预测历史记录
      <el-button size="mini" @click="fetchHistory" style="float:right;">刷新</el-button>
    </div>

    <el-table :data="history" size="mini" max-height="250" v-loading="loading">
      <el-table-column prop="id" label="#" width="40"></el-table-column>
      <el-table-column label="在网月" width="55">
        <template slot-scope="s">{{ s.row.input.tenure }}</template>
      </el-table-column>
      <el-table-column label="月费" width="65">
        <template slot-scope="s">{{ s.row.input.monthly_charges ? s.row.input.monthly_charges.toFixed(0) : '' }}</template>
      </el-table-column>
      <el-table-column label="投诉" width="45">
        <template slot-scope="s">{{ s.row.input.num_complaints }}</template>
      </el-table-column>
      <el-table-column label="合同" width="45">
        <template slot-scope="s">{{ s.row.input.contract_encoded }}</template>
      </el-table-column>
      <el-table-column label="年龄" width="45">
        <template slot-scope="s">{{ s.row.input.age }}</template>
      </el-table-column>
      <el-table-column label="流失概率" width="80">
        <template slot-scope="s">
          {{ (s.row.result.probability * 100).toFixed(1) }}%
        </template>
      </el-table-column>
      <el-table-column label="结果" width="55">
        <template slot-scope="s">
          <el-tag :type="s.row.result.prediction === 1 ? 'danger' : 'success'" size="mini">
            {{ s.row.result.prediction === 1 ? '流失' : '留存' }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="history.length === 0 && !loading" style="text-align:center; color:#999; padding:15px;">
      还没有预测记录
    </div>
  </el-card>
</template>

<script>
import { getPredictHistory } from '@/utils/api'

export default {
  data() {
    return {
      history: [],
      loading: false
    }
  },
  mounted() {
    this.fetchHistory()
    this.$root.$on('predict-done', this.fetchHistory)
  },
  methods: {
    async fetchHistory() {
      this.loading = true
      try {
        const res = await getPredictHistory()
        this.history = res.data
      } catch (e) {
        console.error('获取预测历史失败', e)
      }
      this.loading = false
    }
  }
}
</script>
