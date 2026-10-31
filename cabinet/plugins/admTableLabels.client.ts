// Авто-подписи для адаптивных таблиц: берём текст из thead > th и ставим
// data-label на каждый td. На узких экранах CSS (admin.css) раскладывает
// строки таблицы в карточки, где подписью служит attr(data-label).
// MutationObserver покрывает и динамически подгружаемые таблицы.
export default defineNuxtPlugin(() => {
  function labelTables() {
    document.querySelectorAll<HTMLTableElement>('.admin-table').forEach((table) => {
      const heads = [...table.querySelectorAll('thead th')].map(
        (th) => th.textContent?.trim() || '',
      )
      if (!heads.length) return
      table.querySelectorAll('tbody > tr').forEach((tr) => {
        ;[...tr.children].forEach((cell, i) => {
          if (
            cell instanceof HTMLElement &&
            cell.tagName === 'TD' &&
            !cell.dataset.label &&
            heads[i]
          ) {
            cell.dataset.label = heads[i]
          }
        })
      })
    })
  }

  const observer = new MutationObserver(labelTables)
  onNuxtReady(() => {
    labelTables()
    observer.observe(document.body, { childList: true, subtree: true })
  })
})
