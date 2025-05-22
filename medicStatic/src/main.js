// import './assets/main.css'

import { createApp } from 'vue'
// import pinia from '@/stores/index'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import ElementPlus, {ElMessage} from 'element-plus'
import 'element-plus/dist/index.css'

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(ElementPlus)
app.mount('#app')
app.config.errorHandler = (err, vm, info) => {
  console.error('全局错误:', err);
  // 可以上报到监控系统
  ElMessage.error('发生未预期错误，请联系管理员');
}
