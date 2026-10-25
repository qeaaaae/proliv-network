<script setup lang="ts">
import LocationScene from './LocationScene.vue'
</script>

<template>
  <section class="landing-block" aria-labelledby="locations-title">
    <div class="content-frame">
      <DotField class="dot-field--right" />
      <header class="block-head" data-reveal >
        <h2 id="locations-title">
          Две локации<br><AccentMark>Порт 10 Гбит/с</AccentMark> на каждой
        </h2>
        <p>Обе локации входят в тариф. Переключайтесь между ними в приложении</p>
      </header>
      <ul class="locations">
        <li class="location card" data-reveal  style="--delay: 0s">
          <LocationScene seed="ee" />
          <div class="location-meta">
            <img class="location-flag" src="/images/flags/ee.svg" width="26" height="18" alt="" />
            <h3>Эстония</h3>
            <span class="location-city">Таллин</span>
          </div>
        </li>
        <li class="location card" data-reveal  style="--delay: 0.08s">
          <LocationScene seed="gb" />
          <div class="location-meta">
            <img class="location-flag" src="/images/flags/gb.svg" width="26" height="18" alt="" />
            <h3>Великобритания</h3>
            <span class="location-city">Лондон</span>
          </div>
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.locations {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.location {
  padding: 20px;
}

.location-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

.location-meta h3 {
  font-weight: 600;
  font-size: 17px;
}

.location-city {
  margin-left: auto;
  color: var(--muted);
  font-size: 14px;
}

.location-flag {
  display: block;
  border-radius: 3px;
}

@media (max-width: 639px) {
  .locations {
    grid-template-columns: 1fr;
  }
}
</style>
