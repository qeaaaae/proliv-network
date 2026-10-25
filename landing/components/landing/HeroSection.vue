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
  padding-top: 16px;
}

.hero-stage {
  min-height: 480px;
  padding: 28px clamp(32px, 5vw, 64px) clamp(32px, 5vw, 64px);
}

.hero-header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.hero-copy {
  position: relative;
  margin-top: 64px;
}

.hero-title {
  max-width: 700px;
  font-family: var(--font-display);
  font-size: clamp(30px, 5vw, 56px);
  font-weight: 700;
  line-height: 1.12;
  letter-spacing: -0.01em;
  text-wrap: balance;
}

.hero-lead {
  margin-top: 20px;
  max-width: 560px;
  color: var(--muted);
  font-size: 18px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 36px;
}

@media (max-width: 640px) {
  .hero-stage {
    padding-top: 24px;
  }

  .hero-copy {
    margin-top: 48px;
  }

  .hero-actions {
    flex-direction: column;
  }

  .hero-actions :deep(.base-button) {
    width: 100%;
  }
}
</style>
