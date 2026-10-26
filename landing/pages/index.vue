<script setup lang="ts">
useHead({ title: 'Proliv Network' })
</script>

<template>
  <DotField side="left" />
  <DotField side="right" />
  <main>
    <LandingHeroSection />
    <LandingLocationsSection />
    <LandingRoutesSection />
    <LandingPricingSection />
  </main>
  <LandingSiteClosing />
</template>
