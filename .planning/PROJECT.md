# FiberQ Platform

## What This Is

Екосистема за управление на FTTX/оптични мрежи, изградена около съществуващ QGIS плъгин и FastAPI бекенд. WebUI (Next.js) осигурява user management, project management и достъп до данните на мрежите. QGIS плъгинът остава основният инструмент за проектиране, а уебът — за администрация, наблюдение и координация.

## Core Value

Потребителите могат да се логнат в единна система (Zitadel), да управляват проекти и да работят с оптични мрежи — както от QGIS, така и от уеб браузър.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ FastAPI REST API бекенд с async PostgreSQL/PostGIS — existing
- ✓ QGIS плъгин с addon архитектура за fiber optic network management — existing
- ✓ Zitadel OIDC автентикация с JWT валидация и role-based access — existing
- ✓ Project CRUD операции (create, list, get, update) — existing
- ✓ GeoPackage sync за QField мобилно приложение — existing
- ✓ Fiber plan management (splice closures, tracing) — existing
- ✓ Work orders и SMR reports — existing
- ✓ Docker контейнеризация с Nginx reverse proxy и Cloudflare Tunnel — existing
- ✓ Photo storage и serving — existing

### Active

<!-- Current scope. Building toward these. -->

- [ ] WebUI за управление на потребители (admin създава, деактивира, задава роли)
- [ ] WebUI за управление на проекти (CRUD, присвояване на потребители)
- [ ] WebUI dashboard за потребителите (виждат проектите си, навигират между тях)
- [ ] 4 роли в системата: Admin, Project Manager, Designer, Field Worker
- [ ] QGIS плъгин auth интеграция (login със Zitadel OIDC, същият акаунт като в уеба)
- [ ] Next.js frontend приложение с Zitadel OIDC login

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Web карта с визуализация на мрежи — следващ milestone, изисква map library интеграция
- СМР репорти в уеб интерфейса — следващ milestone, зависи от project management
- Генериране на задачи от уеба — следващ milestone, зависи от work orders интеграция
- Mobile app — уебът е web-first, QField покрива полевата работа

## Context

FiberQ е brownfield проект с работещ QGIS плъгин и FastAPI бекенд. Текущата система поддържа 3 роли (admin, engineer, field_worker) в Zitadel. Плъгинът използва urllib за комуникация със сървъра и конфигурационен файл (config.ini) за настройки. Бекендът обслужва REST API на /api/ prefix зад Nginx reverse proxy.

Текущо няма WebUI — целият потребителски интерфейс е в QGIS плъгина. Потребителите се управляват директно в Zitadel console. Проектите се създават и управляват от QGIS.

Следващата стъпка е да се изгради уеб приложение, което да поеме административните функции и да предостави достъп на потребители, които не използват QGIS.

## Constraints

- **Tech Stack**: Frontend трябва да е React/Next.js — решение на потребителя
- **Auth Provider**: Zitadel остава — вече интегриран в бекенда, не се мигрира
- **Backend**: FastAPI остава — работещ бекенд, разширяваме го с нови endpoints
- **Database**: PostgreSQL 16 + PostGIS 3.4 — съществуваща схема, разширяваме
- **Deployment**: Docker Compose + Nginx + Cloudflare Tunnel — запазваме модела

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Next.js за WebUI frontend | Потребителско предпочитание, голяма екосистема, SSR/SPA flexibility | — Pending |
| Zitadel остава за auth | Вече интегриран, работи, не мигрираме | — Pending |
| 4 роли вместо 3 | Добавяне на Project Manager роля за по-фина гранулация на достъпа | — Pending |
| v1 scope: users + projects | Фокус върху фундамента, карта и репорти в следващи milestone-и | — Pending |

---
*Last updated: 2026-02-21 after initialization*
