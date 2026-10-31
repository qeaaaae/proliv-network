<script setup lang="ts">
import BroadcastComposer from '~/components/admin/broadcast/BroadcastComposer.vue'
import BroadcastHistory from '~/components/admin/broadcast/BroadcastHistory.vue'

const history = ref<InstanceType<typeof BroadcastHistory>>()
</script>

<template>
  <main class="admin-page">
    <h1>Админка · Рассылка</h1>
    <BroadcastComposer @sent="history?.reload()" />
    <BroadcastHistory ref="history" />
  </main>
</template>
