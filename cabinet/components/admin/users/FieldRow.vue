<script setup lang="ts">
defineProps<{ label: string }>()
</script>

<template>
  <div class="adm-users-field">
    <span class="adm-users-field-label">{{ label }}</span>
    <span class="adm-users-field-value"><slot>—</slot></span>
  </div>
</template>

<style scoped>
.adm-users-field {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}
.adm-users-field-label {
  color: var(--adm-muted, #8b95a8);
  flex: 0 0 auto;
}
.adm-users-field-value {
  text-align: right;
  word-break: break-word;
}
</style>
