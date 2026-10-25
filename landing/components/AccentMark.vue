<template>
  <span class="accent-mark"><slot /></span>
</template>

<style scoped>
.accent-mark {
  display: inline-block;
  padding: 0.02em 0.24em 0.08em;
  margin: 0 0.04em;
  background: #26292f;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 0.32em;
  white-space: nowrap;
}
</style>
