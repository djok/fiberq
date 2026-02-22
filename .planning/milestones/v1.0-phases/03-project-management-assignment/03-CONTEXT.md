# Phase 3: Project Management & Assignment - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Manage projects and assign team members from the WebUI. Projects have CRUD operations, user-to-project assignment with project-level roles, and visibility scoped by global role and assignment. Dashboard stats and activity feed are Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Списък с проекти (Project list)
- Card-based layout (не таблица) — grid от карти за визуален преглед
- Всяка карта показва: име на проекта, статус, мини карта (географска визуализация от PostGIS данни)
- Мини картата извлича bounding box / геометрия от съществуващите PostGIS данни на проекта
- Статуси: Планиране / В изпълнение / Завършен / Паузиран / Архивиран (5 нива)
- Филтриране и търсене по име, статус, назначен потребител (от success criteria)

### Назначаване на потребители (Assignment)
- Inline combobox директно в секцията с членове (не диалог)
- Премахване чрез бутон X до името на члена с потвърждение
- Роли на ниво проект: Мениджър / Специалист / Наблюдател (3 нива)
- При назначаване се избира и ролята в проекта
- Един потребител може да е в много проекти с различни роли

### Създаване на проект
- Модален диалог (modal) — като при създаване на потребител във Фаза 2

### Видимост и достъп по роли
- Admin вижда всички проекти
- Project Manager (глобална роля) вижда всички проекти (но с по-малко права от Admin)
- Specialist и Field Worker виждат само проекти, в които са назначени
- Назначаване на членове: Admin + проектни мениджъри (с роля Мениджър в конкретния проект)
- Създаване на проекти: Admin + Project Manager (глобална роля)
- Empty state за non-admin без проекти: съобщение "Нямаш назначени проекти. Обърни се към администратор."

### Claude's Discretion
- Layout на детайлната страница на проект (карта + sidebar, секции, или tabs)
- Съдържание на детайлната страница (основна информация + карта + членове като минимум)
- Полета при създаване на проект (като минимум: име + описание от success criteria)
- Точен дизайн на картите и мини картата
- Технически детайли на PostGIS интеграцията за мини картата

</decisions>

<specifics>
## Specific Ideas

- Проектите са свързани с QGIS и PostGIS — имат географски елементи, мини картата е от реални GIS данни
- Потребителят иска да вижда визуално къде се намират обектите на проекта директно от списъка с карти
- Card layout е съзнателен избор — повече визуална информация от таблица благодарение на мини картата

</specifics>

<deferred>
## Deferred Ideas

- Пълна map view на всички проекти — отделна фаза или допълнение (потребителят спомена идея за визуализация на всички проекти върху обща карта)

</deferred>

---

*Phase: 03-project-management-assignment*
*Context gathered: 2026-02-21*
