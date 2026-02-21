# Technology Stack

**Analysis Date:** 2026-02-21

## Languages

**Primary:**
- Python 3.12 - Backend API and server-side logic
- QGIS Python - Desktop plugin for QGIS 3.22+

**Secondary:**
- SQL - PostgreSQL/PostGIS database schema and queries
- JavaScript - QGIS PyQt plugin UI components

## Runtime

**Environment:**
- Python 3.12.3 - Server runtime in Docker containers
- Node.js v22.21.0 - Available in development environment

**Package Manager:**
- pip - Python package management
- Lockfile: Present (requirements.txt with pinned versions)

## Frameworks

**Core:**
- FastAPI 0.115.6 - REST API framework
- Uvicorn 0.34.0 - ASGI web server
- QGIS 3.22+ - Desktop GIS application framework

**Async & Database:**
- asyncpg 0.30.0 - PostgreSQL async driver
- SQLAlchemy (implicit via asyncpg URL format) - ORM patterns

**Spatial Data:**
- GeoPandas 1.0.1 - Geospatial data analysis
- Shapely 2.0.6 - Geometric object operations
- Fiona 1.10.1 - Vector data I/O (GeoPackage, shapefiles)
- PyProj 3.7.0 - Coordinate reference system transformations
- PostGIS 16 extension - Spatial database capabilities

**Configuration:**
- Pydantic 2.10.4 - Data validation and settings
- Pydantic-settings 2.7.1 - Environment-based configuration

**Testing:**
- pytest - Test runner (implied by .pytest_cache)

**Build/Dev:**
- Docker & Docker Compose - Containerization
- Nginx (Alpine) - Reverse proxy and static file serving

## Key Dependencies

**Critical:**
- fastapi 0.115.6 - REST API server (all endpoints depend on this)
- asyncpg 0.30.0 - Database connection pooling and queries
- PostGIS 16 - Geospatial queries and storage
- Pydantic 2.10.4 - Request/response validation

**Infrastructure:**
- python-jose[cryptography] 3.3.0 - JWT token validation for Zitadel OIDC
- httpx 0.28.1 - Async HTTP client for external API calls (Zitadel, JWKS)
- python-multipart 0.0.20 - File upload handling
- aiofiles 24.1.0 - Async file operations

**Data Processing:**
- geopandas 1.0.1 - Vector data manipulation
- fiona 1.10.1 - GeoPackage export/import
- shapely 2.0.6 - WKB geometry parsing

## Configuration

**Environment:**
- `.env` file in `/home/rosen/fiberq/server/` - Loaded via Pydantic BaseSettings
- Environment variables (`POSTGRES_PASSWORD`, `ZITADEL_DOMAIN`, `API_SECRET_KEY`, etc.) required
- Config file: `fiberq/config.ini` - QGIS plugin PostGIS and server settings

**Build:**
- `docker-compose.yml` - Production multi-container setup
- `docker-compose.dev.yml` - Development lightweight setup
- Dockerfiles for `djok/fiberq-api` image

**Logging:**
- Python logging module - Configurable via `LOG_LEVEL` env var (default: info)

## Platform Requirements

**Development:**
- Python 3.12+
- PostgreSQL 16 + PostGIS 3.4
- Docker & Docker Compose
- QGIS 3.22+ (for plugin development)

**Production:**
- Docker containers
- Nginx reverse proxy
- Cloudflare Tunnel for remote access (optional)
- 100MB max request body size (configurable in nginx)

---

*Stack analysis: 2026-02-21*
