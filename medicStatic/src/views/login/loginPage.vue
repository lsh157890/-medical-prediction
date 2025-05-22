<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { userUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
const userStore = userUserStore()
const router = useRouter()
// 登录表单数据
const loginForm = ref({
  username: '',
  password: ''
})

// 注册表单数据
const registerForm = ref({
  username: '',
  password: '',
  confirmPassword: ''
})

// 当前激活的标签页
const activeTab = ref('login')

// 登录表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

// 注册表单验证规则
const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.value.password) {
          callback(new Error('两次输入密码不一致!'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 登录表单引用
const loginFormRef = ref(null)
// 注册表单引用
const registerFormRef = ref(null)

// 登录提交


// 注册提交
const handleRegister = async () => {
  try {
    await registerFormRef.value.validate()
    console.log('注册提交', registerForm.value)
    // 这里可以添加实际的注册请求
  } catch (error) {
    console.log('表单验证失败', error)
  }
}


// 修改后的登录逻辑
const handleLogin = async () => {
  try {
    await loginFormRef.value.validate()

    // 模拟API返回数据
    const mockResponse = {
      token: 'mock_token_123',
      user: {
        username: loginForm.value.username,
        nickname: '张医生',
        user_pic: 'https://example.com/avatar.jpg'
      }
    }

    // 更新store
    userStore.setToken(mockResponse.token)
    userStore.setUser(mockResponse.user)  // 使用统一的setUser方法

    router.push('/article/channel')
  } catch (error) {
    ElMessage.error('登录失败：' + error.message)
  }
}
</script>

<template>
  <div class="auth-container">
    <el-card class="auth-card">
      <el-tabs v-model="activeTab" stretch>
        <!-- 登录标签页 -->
        <el-tab-pane label="登录" name="login">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-width="80px"
             @submit.native.prevent="handleLogin"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="loginForm.username" placeholder="请输入用户名"  @blur="loginFormRef.validateField('username')"/>
            </el-form-item>

            <el-form-item label="密码" prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="handleLogin"
                style="width: 100%"
              >
                登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 注册标签页 -->
        <el-tab-pane label="注册" name="register">
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-width="100px"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="registerForm.username" placeholder="请输入用户名" />
            </el-form-item>

            <el-form-item label="密码" prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入密码"
                show-password
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="success"
                @click="handleRegister"
                style="width: 100%"
              >
                注册
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.auth-card {
  width: 400px;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,.1);
}

.el-tabs {
  margin-top: 10px;
}

.el-form-item {
  margin-bottom: 22px;
}
</style>
