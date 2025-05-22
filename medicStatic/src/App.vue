<script setup>
 import { userUserStore } from '@/stores/user'

  const userStore = userUserStore()
</script>


<template>
  <router-view></router-view>

</template>

<style scoped>
   .dev {
        color: red;
    }
</style>
