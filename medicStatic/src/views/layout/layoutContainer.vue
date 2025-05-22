<template>
  <el-container class="main-container">
    <!-- 侧边栏 -->
    <el-aside width="200px">
      <div class="logo">临床病例系统</div>
      <el-menu
        :default-active="$route.path"
        router
      >
        <el-menu-item index="/article/channel">
          <el-icon><document /></el-icon>
          <span>病例管理</span>
        </el-menu-item>
        <el-menu-item index="/prediction_result">
          <el-icon><data-analysis /></el-icon>
          <span>统计分析</span>
        </el-menu-item>
        <el-menu-item index="/user/profile">
          <el-icon><user /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { Document, DataAnalysis, User } from '@element-plus/icons-vue'
import { userUserStore } from '@/stores/user' // 导入 Store

const userStore = userUserStore() // 获取用户信息
</script>

<style scoped>
.main-container {
  height: 100vh;
}
.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  font-size: 18px;
  font-weight: bold;
  background: #409eff;
  color: white;
}
</style>
