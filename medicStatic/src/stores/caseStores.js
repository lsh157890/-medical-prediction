import { defineStore } from 'pinia'

export const useCaseStore = defineStore('cases', {
  state: () => ({
    cases: [],
    currentCase: null
  }),
  actions: {
    async fetchCases() {
      // 获取病例列表
    },
    async addCase(newCase) {
      // 添加新病例
    }
  },
  persist: true
})
