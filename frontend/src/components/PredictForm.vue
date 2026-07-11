<template>
  <el-card>
    <div slot="header">在线客户流失预测</div>

    <el-tabs v-model="activeTab">
      <!-- 单条预测 -->
      <el-tab-pane label="单条预测" name="single">
        <el-form label-width="120px" size="mini">
          <el-row :gutter="10">
            <el-col :span="12">
              <el-form-item label="在网时长(月)">
                <el-input-number v-model="form.tenure" :min="1" :max="72"></el-input-number>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="月消费(元)">
                <el-input-number v-model="form.monthly_charges" :min="20" :max="120"></el-input-number>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="总消费(元)">
                <el-input-number v-model="form.total_charges" :min="100" :max="10000"></el-input-number>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="投诉次数">
                <el-input-number v-model="form.num_complaints" :min="0" :max="10"></el-input-number>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="合同类型">
                <el-select v-model="form.contract_encoded">
                  <el-option label="按月" :value="0"></el-option>
                  <el-option label="一年" :value="1"></el-option>
                  <el-option label="两年" :value="2"></el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="在线安全">
                <el-switch v-model="form.has_online_security" :active-value="1" :inactive-value="0"></el-switch>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="技术支持">
                <el-switch v-model="form.has_tech_support" :active-value="1" :inactive-value="0"></el-switch>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="电子账单">
                <el-switch v-model="form.paperless_billing" :active-value="1" :inactive-value="0"></el-switch>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="年龄">
                <el-input-number v-model="form.age" :min="18" :max="70"></el-input-number>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="月均流量(GB)">
                <el-input-number v-model="form.avg_monthly_gb" :min="1" :max="50"></el-input-number>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item>
            <el-button type="primary" @click="doPredict" :loading="singleLoading">预测</el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-form-item>

          <!-- 预测结果 -->
          <el-form-item v-if="singleResult">
            <el-alert :title="singleResult.text" type="success" show-icon></el-alert>
            <el-progress
              :percentage="singleResult.probability * 100"
              :color="singleResult.probability > 0.7 ? '#f56c6c' : '#67c23a'"
              style="margin-top:8px;">
            </el-progress>
            <div style="margin-top:5px; font-size:13px; color:#666;">
              建议：{{ singleResult.suggestion }}
            </div>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 批量预测 -->
      <el-tab-pane label="批量预测" name="batch">
        <el-upload
          ref="upload"
          :auto-upload="false"
          :on-change="handleFileChange"
          :limit="1"
          accept=".csv">
          <el-button slot="trigger" size="small" type="primary">选择 CSV 文件</el-button>
          <div slot="tip" class="el-upload__tip" style="color:#999; font-size:12px;">
            上传包含所有特征列的 CSV 文件
          </div>
        </el-upload>

        <el-button
          type="success"
          size="small"
          @click="doBatchPredict"
          :loading="batchLoading"
          :disabled="!selectedFile"
          style="margin-top:10px;">
          开始批量预测
        </el-button>

        <!-- 批量结果表格 -->
        <el-table
          v-if="batchResults.length > 0"
          :data="batchResults"
          size="mini"
          max-height="300"
          style="margin-top:10px;">
          <el-table-column type="index" label="#" width="40"></el-table-column>
          <el-table-column prop="tenure" label="在网月" width="60"></el-table-column>
          <el-table-column prop="monthly_charges" label="月费" width="70"></el-table-column>
          <el-table-column prop="num_complaints" label="投诉" width="60"></el-table-column>
          <el-table-column prop="contract_encoded" label="合同" width="50"></el-table-column>
          <el-table-column prop="predicted_prob" label="流失概率" width="90">
            <template slot-scope="scope">
              {{ (scope.row.predicted_prob * 100).toFixed(1) }}%
            </template>
          </el-table-column>
          <el-table-column prop="prediction" label="预测" width="50">
            <template slot-scope="scope">
              <el-tag :type="scope.row.prediction === 1 ? 'danger' : 'success'" size="mini">
                {{ scope.row.prediction === 1 ? '流失' : '留存' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>

        <el-button
          v-if="batchResults.length > 0"
          size="small"
          @click="downloadResults"
          style="margin-top:10px;">
          下载结果 CSV
        </el-button>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script>
import { predict, predictBatch, exportResults } from '@/utils/api'

export default {
  data() {
    return {
      activeTab: 'single',
      form: {
        tenure: 12,
        monthly_charges: 60,
        total_charges: 720,
        num_complaints: 0,
        contract_encoded: 0,
        has_online_security: 0,
        has_tech_support: 0,
        paperless_billing: 0,
        age: 30,
        avg_monthly_gb: 20
      },
      singleResult: null,
      singleLoading: false,
      selectedFile: null,
      batchLoading: false,
      batchResults: []
    }
  },
  methods: {
    // 单条预测
    async doPredict() {
      this.singleLoading = true
      try {
        const res = await predict(this.form)
        const d = res.data
        this.singleResult = {
          probability: d.probability,
          prediction: d.prediction,
          suggestion: d.suggestion,
          text: `预测流失概率：${(d.probability * 100).toFixed(2)}%  (${d.prediction === 1 ? '⚠️ 可能流失' : '✅ 稳定客户'})`
        }
        // 通知刷新历史
        this.$emit('predict-done')
      } catch (e) {
        this.$message.error('预测失败，检查后端启动了没')
      }
      this.singleLoading = false
    },
    resetForm() {
      this.form = {
        tenure: 12,
        monthly_charges: 60,
        total_charges: 720,
        num_complaints: 0,
        contract_encoded: 0,
        has_online_security: 0,
        has_tech_support: 0,
        paperless_billing: 0,
        age: 30,
        avg_monthly_gb: 20
      }
      this.singleResult = null
    },

    // 批量预测
    handleFileChange(file) {
      this.selectedFile = file.raw
    },
    async doBatchPredict() {
      if (!this.selectedFile) return
      this.batchLoading = true
      try {
        const res = await predictBatch(this.selectedFile)
        this.batchResults = res.data.results
        this.$message.success(`预测完成，共 ${res.data.count} 条`)
        this.$emit('predict-done')
      } catch (e) {
        this.$message.error('批量预测出错')
      }
      this.batchLoading = false
    },
    async downloadResults() {
      try {
        const res = await exportResults()
        if (res.data.status === 'success') {
          this.$message.success('结果已导出到服务端 data/ 目录')
        }
      } catch (e) {
        console.error('导出失败', e)
      }
    }
  }
}
</script>
