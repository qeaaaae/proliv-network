<template>
  <span class="accent-mark"><slot /></span>
</template>

<style scoped>
.accent-mark {
  display: inline-block;
  padding: 0.02em 0.24em 0.08em;
  margin: 0 0.04em;
  color: var(--accent);
  background: rgba(125, 211, 252, 0.1);
  border: 1px solid rgba(125, 211, 252, 0.22);
  border-radius: 0.32em;
  white-space: nowrap;
}
</style>
