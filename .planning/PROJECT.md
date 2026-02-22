# FiberQ Platform

## What This Is

Екосистема за управление на FTTX/оптични мрежи, изградена около съществуващ QGIS плъгин и FastAPI бекенд. WebUI (Next.js) осигурява user management, project management, dashboard analytics и достъп до данните на мрежите. QGIS плъгинът остава основният инструмент за проектиране, а уебът — за администрация, наблюдение и координация.

## Core Value

Потребителите могат да се логнат в единна система (Kanidm), да управляват проекти и да работят с оптични мрежи — както от QGIS, така и от уеб браузър.

## Current State

**Shipped:** v1.0 MVP (2026-02-22)
**Source:** ~11,400 LOC (8,068 TypeScript/TSX + 3,319 Python)
**Stack:** Next.js 16 + Auth.js v5 + FastAPI + PostgreSQL/PostGIS + Kanidm + MapLibre GL

v1.0 delivers a fully functional web admin interface:
- Kanidm OIDC authentication with 4 roles (admin, project_manager, designer, field_worker)
- User lifecycle management (create, deactivate, role change, password reset)
- Project management with team assignment and PostGIS mini-maps
- Per-project dashboard with element stats and activity timeline
- Bilingual interface (BG/EN), responsive layout, dark/light theme

## Requirements

### Validated

- ✓ Next.js frontend приложение с Kanidm OIDC login — v1.0
- ✓ 4 роли в системата: Admin, Project Manager, Designer, Field Worker — v1.0
- ✓ WebUI за управление на потребители (admin CRUD via Kanidm API) — v1.0
- ✓ WebUI за управление на проекти (CRUD, team assignment, PostGIS maps) — v1.0
- ✓ WebUI dashboard (stat tiles, activity timeline, per-project analytics) — v1.0
- ✓ Responsive layout за tablets (768px+), bilingual BG/EN — v1.0
- ✓ All 22 v1 requirements delivered — see [v1.0-REQUIREMENTS.md](milestones/v1.0-REQUIREMENTS.md)

### Active

- [ ] QGIS плъгин auth интеграция (login с Kanidm OIDC, същият акаунт като в уеба)

### Out of Scope

- Web карта с визуализация на мрежи — следващ milestone, изисква map library интеграция
- СМР репорти в уеб интерфейса — следващ milestone, зависи от project management
- Генериране на задачи от уеба — следващ milestone, зависи от work orders интеграция
- Mobile app — уебът е web-first, QField покрива полевата работа

## Context

FiberQ е brownfield проект с работещ QGIS плъгин и FastAPI бекенд. v1.0 MVP добави пълен уеб интерфейс за администрация. Текущата система поддържа 4 роли в Kanidm. WebUI покрива user management, project management и dashboard analytics. QGIS плъгинът все още използва urllib за комуникация — auth интеграцията е следващата стъпка.

## Constraints

- **Tech Stack**: Frontend — React/Next.js 16, Auth.js v5
- **Auth Provider**: Kanidm — OIDC с ES256 JWT, group-based roles с fiberq_ prefix
- **Backend**: FastAPI — разширен с user/project/activity endpoints
- **Database**: PostgreSQL 16 + PostGIS 3.4 — project_users, project_activity_log tables added
- **Deployment**: Docker Compose + Nginx + Cloudflare Tunnel
- **UI**: shadcn/ui + Tailwind CSS, oklch green/teal palette, MapLibre GL за карти

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Next.js за WebUI frontend | Потребителско предпочитание, голяма екосистема, SSR/SPA flexibility | ✓ Completed — v1.0 |
| Kanidm за auth | Мигриран от Zitadel, ES256 JWT, group-based roles с fiberq_ prefix | ✓ Completed |
| 4 роли вместо 3 | Добавяне на Project Manager роля за по-фина гранулация на достъпа | ✓ Completed — v1.0 |
| v1 scope: users + projects | Фокус върху фундамента, карта и репорти в следващи milestone-и | ✓ Completed — v1.0 |
| Kanidm list_persons за assignable users | Замяна на user_logins таблицата с Kanidm API за пълен списък | ✓ Completed — Phase 5 |
| Auth.js v5 JWT strategy | Proxy.ts forwards raw Kanidm JWT to FastAPI — cleanest integration | ✓ Completed — Phase 1 |
| Collapsible sidebar navigation | Data-dense UI за tablet/desktop, Sheet за mobile | ✓ Completed — Phase 1 |
| MapLibre GL за mini-maps | Inline OSM raster tiles, без external tile server | ✓ Completed — Phase 3 |
| Denormalized project_users | user_display_name/email в junction table, avoid Kanidm lookups | ✓ Completed — Phase 3 |
| Promise.allSettled за dashboard | Page renders даже ако stats/activity API-та fail-нат | ✓ Completed — Phase 4 |

---
*Last updated: 2026-02-22 after v1.0 milestone*
