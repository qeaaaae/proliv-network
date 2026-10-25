<template>
  <section class="landing-block" aria-labelledby="routes-title">
    <div class="content-frame">
      <DotField class="dot-field--left" />

      <header class="block-head" data-reveal>
        <p class="block-kicker">02 — Маршруты</p>
        <h2 id="routes-title">Как Network <AccentMark>направляет трафик</AccentMark></h2>
        <p>Маршрут выбирается сам. Менять настройки не нужно.</p>
      </header>

      <ul class="routes card">
        <li class="route" data-reveal style="--delay: 0s">
          <span class="route-service">YouTube</span>
          <span class="route-leader" aria-hidden="true" />
          <span class="route-path">через Европу</span>
          <p class="route-note">Видео идёт через выбранную европейскую локацию без рекламы</p>
        </li>
        <li class="route" data-reveal style="--delay: 0.1s">
          <span class="route-service">Российские сайты</span>
          <span class="route-leader" aria-hidden="true" />
          <span class="route-path">напрямую</span>
          <p class="route-note">Network остаётся включённым для остальных сервисов</p>
        </li>
        <li class="route" data-reveal style="--delay: 0.2s">
          <span class="route-service">Нейросети</span>
          <span class="route-leader" aria-hidden="true" />
          <span class="route-path">через Европу</span>
          <p class="route-note">Соединение идёт через выбранную европейскую локацию</p>
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.routes {
  padding: clamp(8px, 1.6vw, 16px) clamp(24px, 4vw, 56px);
}

.route {
  display: grid;
  grid-template-columns: auto minmax(40px, 1fr) auto;
  align-items: center;
  gap: 12px clamp(16px, 2vw, 28px);
  padding-block: clamp(28px, 3.4vw, 44px);
}

.route + .route {
  border-top: 1px solid var(--line);
}

.route-service,
.route-path {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: clamp(24px, 3.4vw, 48px);
  line-height: 1;
  letter-spacing: -0.04em;
  white-space: nowrap;
}

.route-path {
  color: var(--accent);
}

.route-leader {
  position: relative;
  height: 10px;
  transform-origin: 0;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.22) 1.6px, transparent 2.1px) 0 0 / 14px
    10px repeat-x;
  transition: transform 1.4s var(--ease-out) 0.25s;
}

.route-leader::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle, var(--accent) 1.8px, transparent 2.3px) 0 50% / 14px 10px
    repeat-x;
  filter: drop-shadow(0 0 4px rgba(125, 211, 252, 0.6));
  -webkit-mask-image: linear-gradient(90deg, transparent, #000 45% 55%, transparent);
  mask-image: linear-gradient(90deg, transparent, #000 45% 55%, transparent);
  -webkit-mask-position: -45% 0;
  mask-position: -45% 0;
  -webkit-mask-size: 28% 100%;
  mask-size: 28% 100%;
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  animation: route-flow 2.6s cubic-bezier(0.45, 0, 0.55, 1) infinite;
}

.route:nth-child(2) .route-leader::after {
  animation-delay: 0.7s;
}

.route:nth-child(3) .route-leader::after {
  animation-delay: 1.4s;
}

.route:not([data-shown]) .route-leader {
  transform: scaleX(0);
}

.route-note {
  grid-column: 2;
  justify-self: center;
  max-width: 52ch;
  color: var(--fg-secondary);
  text-align: center;
  text-wrap: balance;
  font-size: 16px;
}

@keyframes route-flow {
  to {
    -webkit-mask-position: 145% 0;
    mask-position: 145% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .route-leader,
  .route-leader::after {
    transition: none;
    animation: none;
  }

  .route:not([data-shown]) .route-leader {
    transform: none;
  }
}

@media (max-width: 720px) {
  .routes {
    padding-inline: 20px;
  }

  .route {
    grid-template-columns: auto minmax(16px, 1fr) auto;
    gap: 10px 12px;
    padding-block: 24px;
  }

  .route-service,
  .route-path {
    letter-spacing: -0.03em;
    font-size: clamp(15px, 4.6vw, 24px);
  }

  .route-leader,
  .route-leader::after {
    background-size: 10px 10px;
  }

  .route-note {
    grid-column: 1 / -1;
    font-size: 14px;
  }
}
</style>
