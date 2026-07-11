<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- 左列 -->
      <el-col :span="14">
        <TrainControl ref="trainControl" @train-done="onTrainDone" />

        <TrainCurve ref="trainCurve" :refresh-key="curveRefreshKey" style="margin-top:20px;" />

        <EDACharts style="margin-top:20px;" />

        <FeatureImportance style="margin-top:20px;" />
      </el-col>

      <!-- 右列 -->
      <el-col :span="10">
        <ModelEval ref="modelEval" />

        <PredictForm style="margin-top:20px;" @predict-done="onPredictDone" />

        <PredictHistory style="margin-top:20px;" />
      </el-col>
    </el-row>
  </div>
</template>

<script>
import TrainControl from '@/components/TrainControl'
import TrainCurve from '@/components/TrainCurve'
import EDACharts from '@/components/EDACharts'
import ModelEval from '@/components/ModelEval'
import FeatureImportance from '@/components/FeatureImportance'
import PredictForm from '@/components/PredictForm'
import PredictHistory from '@/components/PredictHistory'

export default {
  name: 'Dashboard',
  components: {
    TrainControl,
    TrainCurve,
    EDACharts,
    ModelEval,
    FeatureImportance,
    PredictForm,
    PredictHistory
  },
  data() {
    return {
      curveRefreshKey: 0
    }
  },
  methods: {
    onTrainDone() {
      // 训练完成，触发曲线组件刷新
      this.curveRefreshKey++
      // 通知评估组件刷新
      this.$root.$emit('train-done')
      // 特征重要性也刷新
    },
    onPredictDone() {
      this.$root.$emit('predict-done')
    }
  }
}
</script>

<style scoped>
.dashboard { padding: 10px; }
</style>
