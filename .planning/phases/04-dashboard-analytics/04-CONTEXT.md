# Phase 4: Dashboard & Analytics - Context

**Gathered:** 2026-02-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Project detail pages provide at-a-glance intelligence about project health and recent activity. Stats and activity feed are added to the existing project detail page built in Phase 3. No new pages — only enrichment of the existing detail view.

</domain>

<decisions>
## Implementation Decisions

### Stat tiles
- Stat карти (tiles) — всяка метрика в отделна карта с икона и голямо число (admin dashboard стил)
- Метрики: closures, poles, cables, обща дължина на кабели, team size, last sync
- Тотали + delta: показва текущ общ брой с малък индикатор за промяна спрямо предишен sync (ако е достъпно)
- Last sync показва релативно време като основен текст ("Преди 2 часа"), точна дата при hover/tooltip

### Activity feed
- Вертикален timeline с икони по тип действие (визуално богат)
- Типове действия (само от DASH-02): sync uploads, user assignments, status changes
- Първоначално 20 записа + бутон "Зареди още" за по-стари
- Записи групирани по ден ("Днес", "Вчера", "20 фев 2026")

### Празни състояния
- Stat tiles показват "—" (тире) когато няма данни — не "0"
- Last sync без данни: тире "—" (консистентно с останалите tiles)
- Activity feed без записи: илюстрация/икона + приятелско текстово съобщение
- Нов проект без никакви данни: нормална страница с тирета и празен feed (без специален банер)

### Claude's Discretion
- Layout интеграция: как да се вградят stats и feed в съществуващата detail page (секции, табове, подредба)
- Позиция на stat tiles спрямо картата и членовете
- Дали feed-ът е винаги видим или collapsible
- Claude може да преподреди съществуващите секции от Phase 3 за по-добър UX
- Дизайн на timeline иконите и стиловете

</decisions>

<specifics>
## Specific Ideas

- Delta индикатор за промяна — "+5 нови муфи" стил, малък текст под или до основното число
- Timeline стил подобен на GitHub activity feed — вертикална линия, цветни икони по тип
- Данните идват от съществуващи таблици в БД (не се създават нови данни, само се агрегират)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-dashboard-analytics*
*Context gathered: 2026-02-22*
