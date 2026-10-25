<script setup lang="ts">
</script>

<template>
  <section class="final-cta" aria-labelledby="final-cta-title">
    <LightFlare />
    <div class="cta-inner">
      <h2 id="final-cta-title" class="cta-title" data-reveal >
        Попробуйте Network <AccentMark>3 дня бесплатно</AccentMark>
      </h2>
      <p class="cta-text" data-reveal  style="--delay: 0.08s">
        Пробный период подключается через личный кабинет без привязки банковской карты
      </p>
      <BaseButton class="cta-button" data-reveal  style="--delay: 0.16s">
        Попробовать бесплатно
      </BaseButton>
    </div>
  </section>
</template>

<style scoped>
.final-cta {
  position: relative;
  padding: clamp(40px, 6vw, 72px) 24px;
  text-align: center;
}

.cta-inner {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 640px;
  margin: 0 auto;
}

.cta-title {
  font-family: var(--font-display);
  font-size: clamp(26px, 4vw, 44px);
  font-weight: 600;
  line-height: 1.15;
  letter-spacing: -0.01em;
}

.cta-text {
  margin-top: 16px;
  max-width: 520px;
  color: var(--muted);
  font-size: 17px;
}

.cta-button {
  margin-top: 28px;
}
</style>
