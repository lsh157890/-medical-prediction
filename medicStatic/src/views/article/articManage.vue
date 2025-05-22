<template>
  <div class="main-container">
    <!-- 左侧导航 -->
    <el-menu
      class="sidebar-menu"
      default-active="/user"
      router
    >
      <el-menu-item index="/cases">
        <el-icon><Document /></el-icon>
        <span>病例管理</span>
      </el-menu-item>
      <el-sub-menu index="/stats">
        <template #title>
          <el-icon><DataAnalysis /></el-icon>
          <span>统计分析</span>
        </template>
        <!-- 子菜单 -->
      </el-sub-menu>
    </el-menu>

    <!-- 右侧主区域 -->
    <div class="main-content">
      <!-- 顶部操作栏 -->
      <el-header>
        <el-input
          v-model="searchKey"
          placeholder="点此搜索"
          style="width: 300px"
        />

        <!-- 用户信息下拉 -->
        <el-dropdown
          trigger="click"
          placement="bottom-end"
          @command="handleCommand"
        >
          <div class="user-panel">
            <el-avatar :src="userStore.user?.user_pic" />
            <span class="username">{{ userStore.username }}</span>
            <el-icon><ArrowDown /></el-icon>
          </div>

          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>基本资料
              </el-dropdown-item>
              <el-dropdown-item command="avatar">
                <el-icon><Crop /></el-icon>更换头像
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <!-- 病例表单 -->
      <el-main>
        <el-card>
          <!-- 表单内容 -->
        </el-card>
      </el-main>
    </div>
  </div>
</template>

<style scoped>
.main-container {
  display: flex;
  min-height: 100vh;
}

.sidebar-menu {
  width: 200px;
  border-right: 1px solid #e6e6e6;
}

.main-content {
  flex: 1;
}

.el-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.user-panel {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background 0.3s;
}

.user-panel:hover {
  background: #f5f7fa;
}

.username {
  font-weight: 500;
  color: #606266;
}
</style>
