<template>
  <div id="app">
    <el-container>
      <el-header style="background:#409EFF; color:white; font-size:24px; line-height:60px; padding-left:20px;">
        YangShengRong 客户流失预测系统 (TensorFlow)
      </el-header>
      <el-main>
        <router-view/>
      </el-main>
    </el-container>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
body { margin: 0; }
.el-main { background: #f0f2f5; min-height: 90vh; }
</style>
