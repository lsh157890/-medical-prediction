
// import { createRouter, createWebHistory } from 'vue-router'
// import { userUserStore } from '@/stores/user'
// const router = createRouter({
//   history: createWebHistory(import.meta.env.BASE_URL),
//   routes: [
//     {
//       path: '/login',
//       component: () => import('@/views/login/loginPage.vue') // 使用别名
//     },
//     {
//       path: '/',
//       component: () => import('@/views/layout/layoutContainer.vue'),
//       redirect: '/artic/channel',
//       children: [
//         {
//           path: '/artic/manage', // 保持绝对路径
//           component: () => import('@/views/artic/articManage.vue')
//         },
//         {
//           path: '/artic/channel',
//           component: () => import('@/views/artic/articChannel.vue')
//         },
//         {
//           path: '/user/profile',
//           component: () => import('@/views/user/userProfile.vue')
//         },
//         {
//           path: '/user/avatar', // 修正拼写
//           component: () => import('@/views/user/userAvatar.vue')
//         },
//         {
//           path: '/user/password',
//           component: () => import('@/views/user/userPassword.vue')
//         }
//       ]
//     }
//   ]
// })
// router.beforeEach((to, from, next) => {
//   // 在回调内部获取 Store
//   const userStore = userUserStore()
//
//   if (to.path !== '/login' && !userStore.isLoggedIn) {
//     next('/login')
//   } else {
//     next()
//   }
// })
// export default router

import { createRouter, createWebHistory } from 'vue-router'
import { userUserStore } from '@/stores/user' // 确保导入正确的 Store

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      component: () => import('@/views/login/loginPage.vue')
    },
    {
      path: '/',
      component: () => import('@/views/layout/layoutContainer.vue'),
      redirect: '/article/channel',
      children: [
        { path: '/article/manage', component: () => import('@/views/article/articManage.vue') },
        { path: '/article/channel', component: () => import('@/views/article/articleChannel.vue') },
        { path: '/user/profile', component: () => import('@/views/user/UserProfile.vue')},
        { path: '/prediction_result', component: () => import('@/views/user/UserAvatar.vue')},
        { path: '/user/password', component: () => import('@/views/user/UserPassword.vue')}
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  const userStore = userUserStore()

  // 豁免登录页
  if (to.path === '/login') {
    return next()
  }

  // 未登录跳转
  if (!userStore.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
