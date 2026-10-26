<script setup lang="ts">
import LocationScene from './LocationScene.vue'
</script>

<template>
  <section class="landing-block" aria-labelledby="locations-title">
    <div class="content-frame">
      <header class="block-head" data-reveal>
        <p class="block-kicker">01 — Локации</p>
        <h2 id="locations-title">
          Две локации<br /><AccentMark>Порт 10 Гбит/с</AccentMark> на каждой
        </h2>
        <p>Обе локации входят в тариф. Переключайтесь между ними в приложении</p>
      </header>
      <ul class="locations">
        <li class="location card" data-reveal style="--delay: 0s">
          <LocationScene seed="ee" />
          <div class="location-meta">
            <img class="location-flag" src="/images/flags/ee.svg" width="26" height="18" alt="" />
            <h3>Эстония</h3>
            <span class="location-city">Таллин</span>
          </div>
        </li>
        <li class="location card" data-reveal style="--delay: 0.08s">
          <LocationScene seed="gb" />
          <div class="location-meta">
            <img class="location-flag" src="/images/flags/gb.svg" width="26" height="18" alt="" />
            <h3>Великобритания</h3>
            <span class="location-city">Лондон</span>
          </div>
        </li>
      </ul>
      <NuxtLink to="/status" class="status-strip" data-reveal>
        <span class="strip-dot" aria-hidden="true" />
        <span class="strip-text">онлайн 2 из 2 узлов</span>
        <span class="strip-sep" aria-hidden="true">·</span>
        <span class="strip-muted">канал 10 Гбит/с на каждом</span>
        <span class="strip-sep" aria-hidden="true">·</span>
        <span class="strip-muted">обновлено только что</span>
        <span class="strip-more">Статус →</span>
      </NuxtLink>
    </div>
  </section>
</template>

<style scoped>
.locations {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.location {
  position: relative;
  display: grid;
  align-content: end;
  min-height: 300px;
  padding: 22px;
  overflow: hidden;
}

.location :deep(.location-scene) {
  position: absolute;
  inset: 0 0 auto;
  height: 74%;
  transition:
    filter 0.5s ease,
    transform 0.7s var(--ease-out);
}

.location:hover :deep(.location-scene) {
  filter: brightness(1.3);
  transform: scale(1.02);
}

.location-meta {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
}

.location-meta h3 {
  font-size: 21px;
  font-weight: 600;
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.location-city {
  margin-left: auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--muted);
  font-size: 14px;
}

.location-flag {
  display: block;
  flex: none;
  border-radius: 5px;
  object-fit: cover;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.14);
}

.status-strip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 16px;
  padding: 12px 18px;
  font-family: ui-monospace, 'Cascadia Mono', Menlo, monospace;
  font-size: 13px;
  color: var(--fg-secondary);
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.02);
  transition:
    border-color 0.2s ease,
    color 0.2s ease;
}

.status-strip:hover {
  border-color: var(--border-strong);
  color: var(--text);
}

.strip-dot {
  position: relative;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #3ddc84;
  box-shadow: 0 0 8px rgba(61, 220, 132, 0.7);
}

.strip-dot::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 1px solid rgba(61, 220, 132, 0.6);
  animation: status-ping 2.4s var(--ease-out) infinite;
}

@keyframes status-ping {
  0% {
    transform: scale(0.6);
    opacity: 0.9;
  }

  70%,
  100% {
    transform: scale(2);
    opacity: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .strip-dot::after {
    animation: none;
    opacity: 0;
  }
}

.strip-text {
  color: var(--text);
}

.strip-sep,
.strip-muted {
  color: var(--muted);
}

.strip-more {
  margin-left: 6px;
  color: var(--accent);
  transition: transform 0.3s var(--ease-out);
}

.status-strip:hover .strip-more {
  transform: translateX(4px);
}

@media (max-width: 620px) {
  .locations {
    grid-template-columns: 1fr;
  }

  .status-strip {
    flex-wrap: wrap;
  }
}
</style>
