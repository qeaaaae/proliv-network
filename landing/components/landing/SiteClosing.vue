<script setup lang="ts">
import FinalCta from './FinalCta.vue'
import SiteFooter from './SiteFooter.vue'
</script>

<template>
  <div class="site-closing">
    <div class="content-frame">
      <div class="closing-sheet sheet">
        <FinalCta />
        <SiteFooter />
      </div>
    </div>
  </div>
</template>

<style scoped>
.site-closing {
  padding: 56px 0 clamp(40px, 6vw, 72px);
}

.closing-sheet {
  padding: 0;
}
</style>
