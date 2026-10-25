<template>
  <section class="hero">
    <div class="content-frame">
      <DotField class="dot-field--left" />
      <div class="hero-stage sheet">
        <LightFlare />
        <header class="hero-header">
          <ProlivLogo />
          <BaseButton variant="primary" size="small">Кабинет</BaseButton>
        </header>
        <div class="hero-copy">
          <h1 class="hero-title" data-reveal>
            Proliv Network — быстро и <AccentMark>без сложностей</AccentMark>
          </h1>
          <p class="hero-lead" data-reveal style="--delay: 0.08s">
            Быстрая приватная сеть для всех устройств. Российские сервисы работают без отключения
          </p>
          <div class="hero-actions" data-reveal style="--delay: 0.16s">
            <BaseButton>Попробовать бесплатно</BaseButton>
            <BaseButton variant="secondary" href="#pricing">Выбрать срок</BaseButton>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  padding-top: clamp(12px, 1.6vw, 20px);
}

.hero-stage {
  min-height: var(--stage-height);
  display: grid;
  place-items: center;
  text-align: center;
  padding: clamp(100px, 14vh, 160px) 24px clamp(150px, 22vh, 220px);
}

.hero-header {
  position: absolute;
  inset: clamp(18px, 2.4vw, 28px) clamp(18px, 2.4vw, 28px) auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.hero-copy {
  position: relative;
  display: grid;
  justify-items: center;
  gap: 26px;
  max-width: 780px;
}

.hero-title {
  max-width: 16ch;
  font-family: var(--font-display);
  font-size: clamp(34px, 6vw, 76px);
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.045em;
  text-wrap: balance;
}

.hero-lead {
  max-width: 52ch;
  color: var(--fg-secondary);
  font-size: 18px;
  text-wrap: pretty;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

@media (max-width: 640px) {
  .hero-actions {
    flex-direction: column;
    width: 100%;
  }

  .hero-actions :deep(.base-button) {
    width: 100%;
  }
}
</style>
