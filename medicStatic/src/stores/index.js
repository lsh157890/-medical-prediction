import { createPinia } from 'pinia'
// import { persist } from 'pinia-plugin-persistedstate'
import { createPersistedState } from 'pinia-plugin-persistedstate'
// const pinia = createPinia()
// pinia.use(persist)
const pinia = createPinia()
pinia.use(createPersistedState())  // 注意这里是调用函数
export default pinia
