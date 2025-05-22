//
// import { defineStore } from 'pinia'
// import { ref, computed } from 'vue'
//
// export const userUserStore = defineStore('user', () => {
//   state: () => ({
//     user: JSON.parse(localStorage.getItem('userInfo')) || null,
//     token: localStorage.getItem('token') || ''
//   })
//
//   const token = ref('')
//   const userName = ref('')
//   const setToken = (newToken) => {
//     token.value = newToken
//     localStorage.setItem('token', newToken)
//   }
//     const user = ref({})
//     const setUserInfo = (newToken, userData) => {
//       token.value = newToken
//       user.value = userData || {}
//       localStorage.setItem('userInfo', JSON.stringify(userData))
//   }
//   const setUserName = (newUserName) => {
//     userName.value = newUserName
//     localStorage.setItem('userName', newUserName)
//   }
//   const removeToken = () => {
//     token.value = ''
//     localStorage.removeItem('token')
//     localStorage.removeItem('userInfo')
//   }
//   const isLoggedIn = computed(() => !!token.value) // 关键状态
//
//   return { token, setToken,userName, setUserName, removeToken,setUserInfo, user, isLoggedIn }
// }, { persist: true })

// stores/user.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const userUserStore = defineStore('user', () => {
  // 状态定义
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user')) || null)
  const setAvatar = (avatarUrl) => {
    user.value.user_pic = avatarUrl
    localStorage.setItem('user', JSON.stringify(user.value))
  }
  // 操作方法
  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const setUser = (userData) => {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const removeToken = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => user.value?.username || '未登录用户')

  return {
    token,
    user,
    setToken,
    setUser,
    removeToken,
    isLoggedIn,
    username,
    setAvatar
  }
}, {
  persist: true  // 需要安装持久化插件
})
