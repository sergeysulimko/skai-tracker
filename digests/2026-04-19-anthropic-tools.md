<b>🔧 Anthropic Tools · 19 апр</b>
<i>за 18 апр–19 апр</i>

<b>Claude API</b>

<blockquote><b>[19 апр] ⚠️ Breaking: claude-3-haiku-20240307 уходит завтра</b>
Сегодня последний день — <code>claude-3-haiku-20240307</code> официально выводится из эксплуатации 20 апреля 2026. После этого все запросы вернут ошибку без автоматического перенаправления. Замена: <code>claude-haiku-4-5-20251001</code>. Breaking-нюансы миграции: temperature и top_p нельзя передавать одновременно; добавьте обработку нового stop_reason <code>refusal</code>.
<a href="https://platform.claude.com/docs/en/about-claude/model-deprecations">официальная документация →</a></blockquote>

<blockquote><b>[14 апр] Обновление: claude-sonnet-4 и claude-opus-4 — дедлайн 15 июня</b>
<code>claude-sonnet-4-20250514</code> и <code>claude-opus-4-20250514</code> объявлены устаревшими 14 апреля. Retirement: 15 июня 2026. Замены: <code>claude-sonnet-4-6</code> и <code>claude-opus-4-7</code> соответственно — совместимость промптов и tool use сохраняется, смена одной строки.
<a href="https://platform.claude.com/docs/en/about-claude/model-deprecations">официальная документация →</a></blockquote>

<blockquote expandable><b>💡 Как применить</b>
· Найти все упоминания сегодня: <code>grep -r "claude-3-haiku-20240307" . --include="*.{ts,js,py,env}"</code>
· В Next.js API routes и Vercel AI SDK: проверь env vars и захардкоженные model strings в route handlers
· В grammY bot: обнови model в обработчике перед деплоем на сервер
· Haiku 4.5 даёт 64K output (вместо 4K у Haiku 3) — убери chunking если делал его ради лимита
· Sonnet 4 / Opus 4: запланируй миграцию до 15 июня, Mastra workflows обновляй по одному с тестами</blockquote>

<i>2 обновления · источники проверены</i>
