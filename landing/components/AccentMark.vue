<template>
  <span class="accent-mark"><slot /></span>
</template>

<style scoped>
.accent-mark {
  position: relative;
  display: inline-block;
  color: var(--accent);
  white-space: nowrap;
}

.accent-mark::after {
  content: '';
  position: absolute;
  left: -2%;
  right: -2%;
  bottom: -0.08em;
  height: 0.12em;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, var(--accent) 18%, var(--accent) 82%, transparent);
  opacity: 0.55;
}
</style>
