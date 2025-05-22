<template>
  <el-card>
    <el-table :data="users" stripe>
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="role" label="角色" />
      <el-table-column prop="lastLogin" label="最后登录时间" />
      <el-table-column label="操作">
        <template #default>
          <el-button size="small">编辑</el-button>
          <el-button type="danger" size="small">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
const users = ref([
  { username: 'doctor1', role: '主治医师', lastLogin: '2024-03-15 09:30' },
  { username: 'student1', role: '实习生', lastLogin: '2024-03-14 16:45' }
])
</script>
