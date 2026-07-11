<template>
  <el-card>
    <div slot="header">模型训练控制</div>

    <el-form label-width="100px" size="mini">
      <el-form-item label="训练轮次">
        <el-input-number v-model="params.epochs" :min="5" :max="200"></el-input-number>
      </el-form-item>

      <el-form-item label="隐藏层数">
        <el-select v-model="layerCount">
          <el-option :label="'1 层'" :value="1"></el-option>
          <el-option :label="'2 层'" :value="2"></el-option>
          <el-option :label="'3 层'" :value="3"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="每层神经元">
        <el-input v-model="params.layersStr" placeholder="逗号分隔, 如 128,64"></el-input>
      </el-form-item>

      <el-form-item label="激活函数">
        <el-select v-model="params.activation">
          <el-option label="ReLU" value="relu"></el-option>
          <el-option label="Tanh" value="tanh"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="优化器">
        <el-select v-model="params.optimizer">
          <el-option label="Adam" value="adam"></el-option>
          <el-option label="RMSprop" value="rmsprop"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="handleTrain" :loading="training">
          {{ training ? '训练中...' : '开始训练' }}
        </el-button>
        <el-button @click="refreshProgress" :disabled="!training">刷新进度</el-button>
      </el-form-item>
    </el-form>

    <el-progress :percentage="progressPercent" :format="formatProgress"></el-progress>

    <el-table :data="logTable" size="mini" max-height="180" style="margin-top:10px;">
      <el-table-column prop="epoch" label="Epoch" width="55"></el-table-column>
      <el-table-column prop="loss" label="Loss" width="80"></el-table-column>
      <el-table-column prop="val_loss" label="Val Loss" width="80"></el-table-column>
      <el-table-column prop="accuracy" label="Acc" width="80"></el-table-column>
      <el-table-column prop="val_accuracy" label="Val Acc"></el-table-column>
    </el-table>
  </el-card>
</template>

<script>
import { startTraining, getTrainProgress } from '@/utils/api'

export default {
  data() {
    return {
      training: false,
      layerCount: 2,
      params: {
        epochs: 30,
        layersStr: '128,64',
        activation: 'relu',
        optimizer: 'adam'
      },
      progress: 0,
      totalEpochs: 30,
      logs: [],
      timer: null
    }
  },
  computed: {
    progressPercent() {
      return this.totalEpochs > 0 ? Math.round((this.progress / this.totalEpochs) * 100) : 0
    },
    logTable() {
      // 取最近 10 条倒序显示
      return this.logs.slice(-10).reverse()
    }
  },
  methods: {
    formatProgress() {
      return `${this.progress}/${this.totalEpochs}`
    },
    async handleTrain() {
      let layers = this.params.layersStr.split(',').map(s => parseInt(s.trim())).filter(n => n > 0)
      if (layers.length === 0) {
        layers = [128, 64]
      }

      // 根据隐藏层数调整
      if (this.layerCount === 1) {
        layers = [layers[0] || 64]
      } else if (this.layerCount === 3) {
        while (layers.length < 3) layers.push(64)
        layers = layers.slice(0, 3)
      } else {
        while (layers.length < 2) layers.push(64)
        layers = layers.slice(0, 2)
      }

      const payload = {
        epochs: this.params.epochs,
        batchSize: 32,
        layers: layers,
        activation: this.params.activation,
        optimizer: this.params.optimizer
      }

      this.training = true
      this.logs = []
      this.progress = 0
      this.totalEpochs = this.params.epochs

      try {
        await startTraining(payload)
        this.timer = setInterval(this.refreshProgress, 1000)
        this.$message.success('训练启动了，稍等一下...')
      } catch (e) {
        this.$message.error('启动训练失败')
        this.training = false
      }
    },
    async refreshProgress() {
      try {
        const res = await getTrainProgress()
        const data = res.data
        this.progress = data.progress || 0
        this.totalEpochs = data.totalEpochs || this.params.epochs
        if (data.logs && data.logs.length > 0) {
          this.logs = data.logs
        }

        if (!data.isTraining) {
          this.training = false
          if (this.timer) {
            clearInterval(this.timer)
            this.timer = null
          }
          if (data.result && data.result.accuracy) {
            this.$message.success(`训练完成！准确率: ${(data.result.accuracy * 100).toFixed(2)}%`)
            this.$emit('train-done')
          } else if (data.result && data.result.error) {
            this.$message.error('训练出错: ' + data.result.error)
          }
        }
      } catch (e) {
        console.error('刷新进度失败', e)
      }
    }
  },
  beforeDestroy() {
    if (this.timer) clearInterval(this.timer)
    // 移除事件监听
  }
}
</script>
