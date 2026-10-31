<script setup lang="ts">
// Одно сообщение в треде тикета. body_format='html' приходит с Telegram-разметкой:
// экранируем всё и возвращаем только белый список тегов (b/i/u/s/code/pre/a[http]).
interface MsgButton {
  label: string
  url: string
  kind?: string
}

interface SupportMessage {
  message_id: number
  author_role: string
  author_name?: string | null
  author_label?: string | null
  body: string
  body_format?: string
  buttons?: MsgButton[]
  image_id?: string | null
  is_internal_note: boolean
  created_at: string | null
  read_by_user_at?: string | null
  connector_source?: string | null
}

const props = defineProps<{ message: SupportMessage }>()

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const bodyHtml = computed(() => {
  const m = props.message
  const esc = escapeHtml(m.body || '')
  if (m.body_format !== 'html') return esc
  let out = esc
  for (const tag of ['b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del', 'code', 'pre', 'blockquote']) {
    out = out.split(`&lt;${tag}&gt;`).join(`<${tag}>`)
    out = out.split(`&lt;/${tag}&gt;`).join(`</${tag}>`)
    // Теги с атрибутами (<code class="...">): тег оставляем, атрибуты срезаем
    out = out.replace(new RegExp(`&lt;${tag} [^&]*?&gt;`, 'g'), `<${tag}>`)
  }
  out = out.replace(/&lt;a href=&quot;(.+?)&quot;&gt;/g, (_m, u: string) => {
    const url = u.replace(/&amp;/g, '&')
    return /^https?:\/\//i.test(url)
      ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">`
      : ''
  })
  out = out.split('&lt;/a&gt;').join('</a>')
  // Спойлеры и прочие контейнеры - просто срезаем, текст остаётся
  out = out.replace(/&lt;\/?(span|tg-spoiler)[^&]*?&gt;/g, '')
  return out
})

const authorLabel = computed(() => {
  const m = props.message
  if (m.is_internal_note) return m.author_name ? `Заметка · ${m.author_name}` : 'Внутренняя заметка'
  if (m.author_role === 'user') return 'Клиент'
  if (m.author_role === 'connector') return m.author_label || 'Коннектор'
  return m.author_name || 'Поддержка'
})

const bubbleClass = computed(() => {
  const m = props.message
  if (m.is_internal_note) return 'note'
  return m.author_role === 'user' ? 'user' : 'admin'
})

function fmtTime(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function safeUrl(url: string): string | null {
  return /^https?:\/\//i.test(url) ? url : null
}
</script>

<template>
  <div class="msg" :class="bubbleClass">
    <div class="msg-head">
      <strong>{{ authorLabel }}</strong>
      <span class="msg-time">{{ fmtTime(message.created_at) }}</span>
      <span v-if="message.is_internal_note" class="msg-flag">скрыто от клиента</span>
      <span v-else-if="message.author_role !== 'user' && message.read_by_user_at" class="msg-flag">прочитано</span>
    </div>
    <!-- eslint-disable-next-line vue/no-v-html -- разметка санитизирована белым списком выше -->
    <div class="msg-body" v-html="bodyHtml" />
    <div v-if="message.image_id" class="admin-note">Вложение: изображение ({{ message.image_id.slice(0, 8) }}...)</div>
    <div v-if="message.buttons?.length" class="msg-buttons">
      <template v-for="(b, i) in message.buttons" :key="i">
        <a v-if="safeUrl(b.url)" :href="safeUrl(b.url)!" target="_blank" rel="noopener noreferrer" class="msg-btn">
          {{ b.label }}
        </a>
      </template>
    </div>
  </div>
</template>

<style scoped>
.msg {
  display: grid;
  gap: 6px;
  max-width: 85%;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--adm-border);
  background: var(--adm-card-2);
}
.msg.user {
  align-self: flex-start;
}
.msg.admin {
  align-self: flex-end;
  border-color: var(--adm-accent);
}
.msg.note {
  align-self: stretch;
  max-width: 100%;
  border-style: dashed;
  border-color: var(--adm-warning);
  background: rgba(251, 191, 36, 0.06);
}
.msg-head {
  display: flex;
  gap: 8px;
  align-items: baseline;
  font-size: 12px;
}
.msg-time {
  color: var(--adm-muted);
}
.msg-flag {
  color: var(--adm-muted);
  font-size: 11px;
}
.msg-body {
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}
.msg-body :deep(a) {
  color: var(--adm-accent);
}
.msg-body :deep(code),
.msg-body :deep(pre) {
  background: var(--adm-bg);
  border-radius: 6px;
  padding: 1px 5px;
  font-size: 12px;
}
.msg-body :deep(blockquote) {
  margin: 0;
  padding-left: 8px;
  border-left: 2px solid var(--adm-border);
  color: var(--adm-muted);
}
.msg-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.msg-btn {
  padding: 5px 10px;
  border-radius: 8px;
  border: 1px solid var(--adm-border);
  color: var(--adm-accent);
  font-size: 12px;
  text-decoration: none;
}
</style>
