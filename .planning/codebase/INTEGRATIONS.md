# External Integrations

**Analysis Date:** 2026-02-21

## APIs & External Services

**Zitadel OIDC:**
- Zitadel Identity Provider - Central authentication and role management
  - SDK/Client: python-jose (JWT validation), httpx (JWKS/OIDC config fetching)
  - Auth: Configured via `ZITADEL_DOMAIN`, `ZITADEL_CLIENT_ID`, `ZITADEL_PROJECT_ID`
  - Implementation: `server/api/auth/zitadel.py` validates RS256-signed JWT tokens
  - Token claims parsed for user roles (urn:zitadel:iam:org:project:roles)

**QField Integration:**
- QField mobile GIS app - Field data collection
  - Integration: Sync endpoints download/upload GeoPackage files
  - Storage: Synced data stored in `gpkg_sync` volume
  - Format: `.gpkg` (GeoPackage)

## Data Storage

**Databases:**
- PostgreSQL 16 with PostGIS 3.4
  - Connection: `postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}`
  - Env vars: `DATABASE_URL` (async), `DATABASE_SYNC_URL` (sync fallback)
  - Client: asyncpg (async) for API, psycopg2-style URLs accepted
  - Schema: `fiberq` schema for project data, public for PostGIS functions
  - Connection pool: Min 2, Max 20 connections per `database.py`

**File Storage:**
- Local filesystem volumes
  - `photos` volume - Stored at `/app/storage/photos` (served via nginx at `/storage/photos/`)
  - `gpkg_sync` volume - GeoPackage exports/imports at `/app/storage/gpkg`
  - Cache headers: 7-day expiry for photo files

**Caching:**
- In-memory Python dicts - JWKS and OpenID config cached in `auth/zitadel.py` (global `_jwks_cache`, `_openid_config_cache`)

## Authentication & Identity

**Auth Provider:**
- Zitadel (OIDC/OAuth2)
  - Implementation: Bearer token validation via JWT
  - Endpoint: `{zitadel_domain}/.well-known/openid-configuration` fetches issuer config
  - JWKS endpoint: Dynamically fetched from OpenID config, cached globally
  - Token validation: RS256 signature verification against public keys
  - User roles extracted from custom Zitadel claims in token
  - Defined roles: `admin`, `engineer`, `field_worker` (role-based access in `dependencies.py`)

## Monitoring & Observability

**Error Tracking:**
- None detected - Application relies on logging

**Logs:**
- Python logging module - Configured in `server/api/main.py` lifespan
  - Log level: Configurable via `LOG_LEVEL` env var (default: info)
  - Format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
  - Loggers: `fiberq`, `fiberq.auth`, `fiberq.sync.exporter` etc.
  - Healthcheck logging: API and database startup events logged

## CI/CD & Deployment

**Hosting:**
- Docker containers (cloud-agnostic)
- Cloudflare Tunnel - Remote access and DNS management
  - Tunnel token: `CLOUDFLARE_TUNNEL_TOKEN` env var
  - Container: cloudflare/cloudflared latest image

**Reverse Proxy:**
- Nginx (Alpine) - Routes all traffic
  - API endpoints: `/api/*` prefix proxied to FastAPI backend
  - Health checks: `/health` routed directly (no `/api/` prefix)
  - Photo storage: `/storage/photos/*` served as static files
  - CORS: Enabled at application level (allow_origins=["*"])

**CI Pipeline:**
- None detected - Manual deployment via Docker Compose

## Environment Configuration

**Required env vars:**
- `POSTGRES_DB` - Database name (default: fiberq)
- `POSTGRES_USER` - Database user (default: fiberq)
- `POSTGRES_PASSWORD` - Database password (REQUIRED)
- `ZITADEL_DOMAIN` - Zitadel tenant domain (REQUIRED)
- `ZITADEL_CLIENT_ID` - Zitadel application client ID (REQUIRED)
- `ZITADEL_PROJECT_ID` - Zitadel project ID (optional, for role extraction)
- `API_SECRET_KEY` - JWT secret for internal signing (REQUIRED)
- `LOG_LEVEL` - Logging level (default: info)
- `FIBERQ_API_VERSION` - Docker image version tag (default: latest)
- `HTTP_PORT` - Nginx HTTP port (default: 80)
- `HTTPS_PORT` - Nginx HTTPS port (default: 443)
- `CLOUDFLARE_TUNNEL_TOKEN` - Cloudflare Tunnel auth token (REQUIRED in production)
- `SERVER_DOMAIN` - Server domain for SSL/Nginx config

**Secrets location:**
- `.env` file in `server/` directory (not committed, example at `server/.env.example`)
- Environment variables injected by Docker Compose or Portainer

## Webhooks & Callbacks

**Incoming:**
- None detected - Stateless REST API only

**Outgoing:**
- None detected - API is pull-based for external services

## Data Export Formats

**GeoPackage (.gpkg):**
- Format: OGC GeoPackage (SQLite-based)
- Export handler: `server/api/sync/exporter.py` exports PostGIS tables to GPKG layers
- Layers: OKNA, Stubovi, Kablovi_podzemni, Kablovi_vazdusni, Trasa, PE cevi, Nastavci, Prekid vlakna, Elements, Splice_closures, Work_orders, SMR_reports
- CRS: EPSG:4326 (WGS84)
- Geometry handling: ST_AsText() conversion in SQL, Shapely WKB parsing in Python

---

*Integration audit: 2026-02-21*
