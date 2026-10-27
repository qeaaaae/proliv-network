<script setup lang="ts">
import FinalCta from './FinalCta.vue'
import SiteFooter from './SiteFooter.vue'
</script>

<template>
  <div class="site-closing">
    <div class="content-frame">
      <DotField side="left" />
      <div class="closing-sheet sheet">
        <FinalCta />
        <SiteFooter />
      </div>
    </div>
  </div>
</template>

<style scoped>
.site-closing {
  padding: 56px 0 clamp(12px, 1.6vw, 20px);
}

.closing-sheet {
  padding: 0;
}
</style>
