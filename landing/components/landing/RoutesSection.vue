<template>
  <section class="landing-block" aria-labelledby="routes-title">
    <div class="content-frame">
      <DotField class="dot-field--left" />

      <header class="block-head">
        <h2 id="routes-title">Как Network <AccentMark>направляет трафик</AccentMark></h2>
        <p>Маршрут выбирается сам. Менять настройки не нужно.</p>
      </header>

      <ul class="routes card">
        <li class="route" data-reveal  style="--delay: 0s">
          <span class="route-service">YouTube</span>
          <span class="route-leader" aria-hidden="true" />
          <span class="route-path">через Европу</span>
          <p class="route-note">Видео идёт через выбранную европейскую локацию без рекламы</p>
        </li>
        <li class="route" data-reveal  style="--delay: 0.1s">
          <span class="route-service">Российские сайты</span>
          <span class="route-leader" aria-hidden="true" />
          <span class="route-path">напрямую</span>
          <p class="route-note">Network остаётся включённым для остальных сервисов</p>
        </li>
        <li class="route" data-reveal  style="--delay: 0.2s">
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
  padding: 8px;
}

.route {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  column-gap: 16px;
  padding: 20px 24px;
}

.route + .route {
  border-top: 1px solid var(--border);
}

.route-service {
  font-weight: 600;
  font-size: 16px;
}

.route-leader {
  min-width: 40px;
  height: 1px;
  align-self: center;
  border-bottom: 2px dotted var(--border-strong);
}

.route-path {
  color: var(--accent);
  font-weight: 600;
  font-size: 14px;
}

.route-note {
  grid-column: 1 / -1;
  margin-top: 6px;
  color: var(--muted);
  font-size: 14px;
}

@media (max-width: 560px) {
  .route {
    display: flex;
    flex-wrap: wrap;
    column-gap: 12px;
    row-gap: 8px;
  }

  .route-leader {
    flex: 1 1 40px;
    min-width: 24px;
  }

  .route-note {
    flex-basis: 100%;
    margin-top: 0;
  }
}
</style>
