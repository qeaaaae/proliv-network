<template>
  <section class="landing-block" aria-labelledby="routes-title">
    <div class="content-frame">
      <DotField side="left" />
      <header class="block-head" data-reveal>
        <p class="block-kicker">02 — Маршруты</p>
        <h2 id="routes-title">Как Network <AccentMark>направляет трафик</AccentMark></h2>
        <p>Маршрут выбирается сам. Менять настройки не нужно.</p>
      </header>

      <ul class="routes card">
        <li class="route" data-reveal style="--delay: 0s">
          <div class="route-service">
            <span class="route-name">YouTube</span>
            <p class="route-note">Видео идёт через выбранную европейскую локацию без рекламы</p>
          </div>
          <span class="route-leader" aria-hidden="true">
            <span class="route-node">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="5.5" y="10.5" width="13" height="9.5" rx="2" /><path d="M8.5 10.5V7.5a3.5 3.5 0 0 1 7 0v3" /></svg>
            </span>
            <span class="route-pkt" />
          </span>
          <span class="route-path">через Европу</span>
        </li>
        <li class="route" data-reveal style="--delay: 0.1s">
          <div class="route-service">
            <span class="route-name">Российские сайты</span>
            <p class="route-note">Network остаётся включённым для остальных сервисов</p>
          </div>
          <span class="route-leader" aria-hidden="true">
            <span class="route-node">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="5.5" y="10.5" width="13" height="9.5" rx="2" /><path d="M8.5 10.5V7.5a3.5 3.5 0 0 1 7 0v3" /></svg>
            </span>
            <span class="route-pkt" />
          </span>
          <span class="route-path">напрямую</span>
        </li>
        <li class="route" data-reveal style="--delay: 0.2s">
          <div class="route-service">
            <span class="route-name">Нейросети</span>
            <p class="route-note">Соединение идёт через выбранную европейскую локацию</p>
          </div>
          <span class="route-leader" aria-hidden="true">
            <span class="route-node">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="5.5" y="10.5" width="13" height="9.5" rx="2" /><path d="M8.5 10.5V7.5a3.5 3.5 0 0 1 7 0v3" /></svg>
            </span>
            <span class="route-pkt" />
          </span>
          <span class="route-path">через Европу</span>
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
  grid-template-columns: minmax(0, 1.15fr) minmax(80px, 0.7fr) auto;
  align-items: center;
  gap: 14px clamp(16px, 2.6vw, 36px);
  padding-block: clamp(26px, 3vw, 40px);
}

.route + .route {
  border-top: 1px solid var(--line);
}

.route-name,
.route-path {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: clamp(22px, 3vw, 40px);
  line-height: 1;
  letter-spacing: -0.04em;
  white-space: nowrap;
}

.route-name {
  display: block;
}

.route-path {
  color: var(--accent);
  text-align: right;
}

.route-note {
  margin-top: 10px;
  max-width: 44ch;
  color: var(--fg-secondary);
  font-size: 14px;
  line-height: 1.45;
  text-wrap: pretty;
}

.route-leader {
  position: relative;
  height: 58px;
  overflow: hidden;
  transform-origin: 0;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.22) 1.6px, transparent 2.1px) 0 50% / 14px
    10px repeat-x;
  transition:
    transform 1.4s var(--ease-out) 0.25s,
    filter 0.3s ease;
}

/* encrypted half of the channel lights once the packet exits the lock */
.route-leader::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  right: 0;
  height: 2px;
  margin-top: -1px;
  background: linear-gradient(90deg, rgba(125, 211, 252, 0.7), rgba(125, 211, 252, 0.1) 75%, transparent);
  opacity: 0;
  animation: route-seg 3.2s linear infinite;
}

/* lock node the packet passes through */
.route-node {
  position: absolute;
  left: 50%;
  top: 50%;
  z-index: 2;
  transform: translate(-50%, -50%);
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  color: var(--muted);
  animation: node-arm 3.2s linear infinite;
}

.route-node svg {
  width: 22px;
  height: 22px;
}

/* flying packet: plain dot with a trail, becomes a glowing diamond after the lock */
.route-pkt {
  position: absolute;
  top: 50%;
  left: 0;
  z-index: 1;
  width: 34px;
  height: 10px;
  margin-top: -5px;
  animation: route-pkt 3.2s linear infinite;
}

.route-pkt::before {
  content: '';
  position: absolute;
  top: 50%;
  right: 0;
  width: 6px;
  height: 6px;
  margin-top: -3px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.92);
  animation: pkt-body 3.2s linear infinite;
}

.route-pkt::after {
  content: '';
  position: absolute;
  top: 50%;
  right: 8px;
  width: 26px;
  height: 2px;
  margin-top: -1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5));
  animation: pkt-trail 3.2s linear infinite;
}

/* staggered cascade down the rows; same duration keeps packet/lock/glow in sync */
.route:nth-child(2) .route-pkt,
.route:nth-child(2) .route-pkt::before,
.route:nth-child(2) .route-pkt::after,
.route:nth-child(2) .route-leader::after,
.route:nth-child(2) .route-node {
  animation-delay: 1s;
}

.route:nth-child(3) .route-pkt,
.route:nth-child(3) .route-pkt::before,
.route:nth-child(3) .route-pkt::after,
.route:nth-child(3) .route-leader::after,
.route:nth-child(3) .route-node {
  animation-delay: 2s;
}

.route:not([data-shown]) .route-leader {
  transform: scaleX(0);
}

@keyframes route-pkt {
  0% {
    left: -36px;
    opacity: 0;
  }

  6% {
    opacity: 1;
  }

  94% {
    opacity: 1;
  }

  100% {
    left: 100%;
    opacity: 0;
  }
}

/* body hides inside the lock ~45-49%, morphs to encrypted while hidden */
@keyframes pkt-body {
  0%,
  45% {
    border-radius: 2px;
    background: rgba(255, 255, 255, 0.92);
    box-shadow: none;
    transform: rotate(0deg);
  }

  52%,
  100% {
    border-radius: 1px;
    background: var(--accent);
    box-shadow: 0 0 9px rgba(125, 211, 252, 0.85);
    transform: rotate(45deg);
  }
}

@keyframes pkt-trail {
  0%,
  45% {
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5));
  }

  52%,
  100% {
    background: linear-gradient(90deg, transparent, rgba(125, 211, 252, 0.75));
  }
}

@keyframes route-seg {
  0%,
  54% {
    opacity: 0;
  }

  62% {
    opacity: 0.55;
  }

  88%,
  100% {
    opacity: 0;
  }
}

@keyframes node-arm {
  0%,
  44% {
    border-color: var(--border);
    color: var(--muted);
    box-shadow: none;
  }

  52%,
  62% {
    border-color: var(--accent);
    color: var(--accent);
    box-shadow: 0 0 12px rgba(125, 211, 252, 0.4);
  }

  74%,
  100% {
    border-color: var(--border);
    color: var(--muted);
    box-shadow: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .route-leader,
  .route-leader::after,
  .route-node,
  .route-pkt,
  .route-pkt::before,
  .route-pkt::after {
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
    grid-template-columns: 1fr;
    gap: 12px;
    padding-block: 22px;
  }

  .route-name,
  .route-path {
    letter-spacing: -0.03em;
    font-size: 22px;
    white-space: normal;
  }

  .route-path {
    text-align: left;
  }

  .route-leader {
    order: 3;
    width: 100%;
  }

  .route-leader {
    background-size: 10px 10px;
  }
}
</style>
