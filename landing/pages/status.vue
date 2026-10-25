<script setup lang="ts">
useHead({ title: 'Состояние сервиса - Proliv Network' })

const nodes = [
  {
    country: 'Эстония',
    city: 'Таллин',
    flag: 'ee',
    state: 'Работает',
    uptime: '99,98% за 30 дней',
    load: 'Порт 10 Гбит/с, загрузка низкая',
  },
  {
    country: 'Великобритания',
    city: 'Лондон',
    flag: 'gb',
    state: 'Работает',
    uptime: '99,96% за 30 дней',
    load: 'Порт 10 Гбит/с, загрузка низкая',
  },
]
</script>

<template>
  <main class="status-page">
    <div class="content-frame status-frame">
      <div class="status-sheet sheet">
        <header class="status-head">
          <div class="status-topline">
            <NuxtLink to="/" class="status-brand" aria-label="Proliv Network">
              <ProlivLogo />
            </NuxtLink>
            <NuxtLink to="/" class="status-back">На главную</NuxtLink>
          </div>
          <h1 class="status-title">Состояние сервиса</h1>
          <p class="status-updated">Проверки узлов выполняются автоматически каждую минуту</p>
        </header>

        <ul class="node-list">
          <li v-for="node in nodes" :key="node.flag" class="node-card card" data-reveal>
            <div class="node-id">
              <img class="node-flag" :src="`/images/flags/${node.flag}.svg`" alt="" width="26" height="18">
              <div>
                <h2>{{ node.country }}</h2>
                <span class="node-city">{{ node.city }}</span>
              </div>
            </div>
            <div class="node-side">
              <span class="node-state"><i class="node-dot" aria-hidden="true" />{{ node.state }}</span>
              <span class="node-meta">{{ node.uptime }}</span>
              <span class="node-meta">{{ node.load }}</span>
            </div>
          </li>
        </ul>

        <p class="status-note">
          Страница пока работает в демо-режиме: метрики подключатся к Remnawave после запуска нод.
        </p>
      </div>
    </div>
  </main>
</template>

<style scoped>
.status-page {
  flex: 1;
  padding: 40px 0 96px;
}

.status-frame {
  max-width: 820px;
}

.status-sheet {
  padding: clamp(24px, 4vw, 48px);
}

.status-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.status-brand {
  display: inline-flex;
  color: var(--text);
}

.status-back {
  color: var(--muted);
  font-size: 14px;
  transition: color 0.18s ease;
}

.status-back:hover {
  color: var(--accent);
}

.status-title {
  margin-top: 40px;
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 34px);
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: -0.01em;
}

.status-updated {
  margin-top: 12px;
  color: var(--muted);
  font-size: 14px;
}

.node-list {
  display: grid;
  gap: 14px;
  margin-top: 36px;
}

.node-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 20px 22px;
}

.node-id {
  display: flex;
  align-items: center;
  gap: 14px;
}

.node-flag {
  border-radius: 4px;
}

.node-id h2 {
  font-size: 17px;
  font-weight: 600;
  line-height: 1.3;
}

.node-city {
  color: var(--muted);
  font-size: 13px;
}

.node-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  text-align: right;
}

.node-state {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #3ddc84;
  font-size: 14px;
  font-weight: 600;
}

.node-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3ddc84;
  box-shadow:
    0 0 6px rgba(61, 220, 132, 0.8),
    0 0 14px rgba(61, 220, 132, 0.4);
}

.node-meta {
  color: var(--muted);
  font-size: 13px;
}

.status-note {
  margin-top: 28px;
  padding: 12px 16px;
  color: var(--muted);
  font-size: 13px;
  background: var(--accent-soft);
  border: 1px solid var(--border);
  border-radius: var(--radius-control);
}

@media (max-width: 720px) {
  .node-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .node-side {
    align-items: flex-start;
    text-align: left;
  }
}
</style>
