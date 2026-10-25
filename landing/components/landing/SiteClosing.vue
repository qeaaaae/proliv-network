<script setup lang="ts">
import FinalCta from './FinalCta.vue'
import SiteFooter from './SiteFooter.vue'
</script>

<template>
  <div class="site-closing">
    <div class="content-frame">
      <DotField class="dot-field--left closing-field" />
      <div class="closing-sheet sheet">
        <FinalCta />
        <SiteFooter />
      </div>
    </div>
  </div>
</template>

<style scoped>
.site-closing {
  padding-top: 56px;
}

.closing-sheet {
  padding: 0;
}
</style>
