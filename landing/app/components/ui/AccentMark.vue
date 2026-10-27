<template>
  <span class="accent-mark plate"><slot /></span>
</template>

<style scoped>
.accent-mark {
  display: inline;
  padding: .02em .2em .1em;
  white-space: nowrap;
  border-radius: .16em;
  box-decoration-break: clone;
  -webkit-box-decoration-break: clone;
}

@media (max-width: 480px) {
  .accent-mark {
    white-space: normal;
  }
}
</style>
