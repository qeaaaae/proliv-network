<script setup lang="ts">
const props = defineProps<{
  page: number
  pageCount: number
  total?: number | null
  busy?: boolean
}>()
const emit = defineEmits<{ go: [page: number] }>()

const count = computed(() => Math.max(1, props.pageCount || 1))
</script>

<template>
  <div class="admin-pager">
    <button
      type="button"
      class="admin-btn ghost"
      :disabled="busy || page <= 0"
      @click="emit('go', page - 1)"
    >
      Назад
    </button>
    <span class="admin-note">
      Страница {{ page + 1 }} из {{ count
      }}<template v-if="total !== null && total !== undefined"> · всего {{ total }}</template>
    </span>
    <button
      type="button"
      class="admin-btn ghost"
      :disabled="busy || page + 1 >= count"
      @click="emit('go', page + 1)"
    >
      Вперёд
    </button>
    <slot />
  </div>
</template>
