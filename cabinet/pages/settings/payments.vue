<script setup lang="ts">
// Диплинк из бота («История платежей») - история живёт секцией на /purchases
useHead({ title: 'История платежей - Proliv Network' })
await navigateTo('/purchases#orders', { replace: true })
</script>

<template>
  <div />
</template>
