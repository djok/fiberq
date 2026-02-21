# Codebase Concerns

**Analysis Date:** 2026-02-21

## Tech Debt

**Overly broad exception handling in QGIS plugin:**
- Issue: Extensive use of bare `except Exception:` blocks (50+ occurrences) that silently swallow all errors
- Files: `fiberq/main_plugin.py` (lines 30, 38, 44, 53, 60, 83, 93, 104, 149, 225, 234, 244, 253, 255, 297, 303, 310, 319, 324, 330, 345, 409, 415, 420, 436, 448, 454, 456, 462, 467, 471, 493, 597, 603, 613, 618, 621, 636, 652, 656+)
- Impact: Makes debugging extremely difficult; errors propagate silently with no logging, leaving users confused about failures
- Fix approach: Replace with specific exception types and add logging. Use `logger.exception()` to capture stack traces for debugging

**Silent exception handlers in addon system:**
- Issue: Many signal handlers and initialization routines in `fiberq/addons/reserve_hook.py` use `except Exception: pass` (20+ instances)
- Files: `fiberq/addons/reserve_hook.py` (lines 29, 37, 47, 51, 55, 59, 68, 93, 123, 138, 143, 163, 183, 200, 271)
- Impact: Critical layer synchronization failures go unnoticed; users don't know when calculations fail
- Fix approach: Log all exceptions at minimum; consider user-facing warnings for critical paths

**Monolithic main plugin file (12,991 lines, 423 functions):**
- Issue: `fiberq/main_plugin.py` contains all UI logic, data operations, styling, and toolbar management in a single file
- Files: `fiberq/main_plugin.py`
- Impact: Extremely difficult to maintain, test, or modify; high risk of regressions; violates single responsibility principle
- Fix approach: Split into modules: `ui/dialogs.py`, `ui/styles.py`, `ui/toolbar.py`, `operations/`, `core/licensing.py`

**Hardcoded shared license key:**
- Issue: Pro license validation uses a hardcoded master key `_FIBERQ_PRO_MASTER_KEY = "FIBERQ-PRO-2025"` in source code
- Files: `fiberq/main_plugin.py` (line 74)
- Impact: Anyone with access to code can enable Pro features; key rotation requires code update and redeployment
- Fix approach: Move key to secure backend service, implement time-limited license tokens with expiration

**Global state caching without invalidation:**
- Issue: JWT JWKS and OpenID config cached globally without TTL or cache invalidation mechanism
- Files: `server/api/auth/zitadel.py` (lines 15-16, 73-76)
- Impact: Key rotation at Zitadel won't be picked up for duration of container runtime; old keys may be accepted
- Fix approach: Add 1-hour TTL to cache; implement cache invalidation on key lookup failure

**Global database pool without proper lifecycle:**
- Issue: Database connection pool is global mutable state; no guarantee it's properly initialized before use
- Files: `server/api/database.py`, `server/api/main.py`
- Impact: Concurrent module imports can race on pool initialization; missing pool throws cryptic RuntimeError
- Fix approach: Use context manager pattern; validate pool exists at route entry point with explicit error message

---

## Known Bugs

**SQL injection vulnerability in dynamic table names:**
- Symptoms: Queries with table names interpolated directly into SQL strings; column names from user input
- Files: `server/api/sync/exporter.py` (lines 83, 85), `server/api/sync/merger.py` (line 224), `server/api/sync/differ.py` (line 183)
- Trigger: Any user-provided data that reaches table/column name variables
- Workaround: Currently mitigated by hardcoded table mappings, but pattern is unsafe for future extensions
- Fix: Use parameterized queries with identifier arrays in asyncpg; never interpolate table/column names

**License key validation accepts any master key:**
- Symptoms: Function `_fiberq_validate_pro_key()` only checks if key equals the hardcoded master key
- Files: `fiberq/main_plugin.py` (lines 97-105)
- Trigger: User enters the hardcoded key which is in source code
- Impact: License protection is trivial to bypass
- Fix: Implement cryptographic signature validation or backend license check

**Docker health check uses hardcoded port without validation:**
- Symptoms: Health check calls localhost:8000 which may fail if API actually listens on different interface
- Files: `server/docker-compose.yml` (line 40)
- Trigger: Container startup; will mark service unhealthy if port mismatch
- Fix: Use environment variable or service name (api:8000) instead of localhost:8000

---

## Security Considerations

**CORS allow-all policy in production:**
- Risk: API accepts requests from any origin with `allow_origins=["*"]`
- Files: `server/api/main.py` (lines 41-46)
- Current mitigation: Token validation still required (good), but CSRF attacks possible
- Recommendations: Restrict to known frontend domains; at minimum exclude credentials exposure. Example: `allow_origins=["https://app.example.com"]`

**Credentials stored in QSettings (local storage):**
- Risk: Access tokens and refresh tokens stored in QGIS user settings directory (QSettings) without encryption
- Files: `fiberq/addons/zitadel_auth.py` (lines 215-223, 238-245)
- Current mitigation: None - tokens readable by any process with user permissions
- Recommendations: Use OS keyring (python-keyring) for credential storage; encrypt tokens at rest with user password

**Config file with plain text database password:**
- Risk: `config.ini` in plugin folder contains PostgreSQL credentials
- Files: `fiberq/addons/fiberq_preview.py` (lines 39-73)
- Current mitigation: Only readable by file permissions
- Recommendations: Use environment variables only; never commit config with secrets; add to .gitignore

**API secret key default is "dev-secret-key":**
- Risk: Default configuration uses hardcoded insecure value
- Files: `server/api/config.py` (line 15)
- Current mitigation: Requires override in production
- Recommendations: Make secret required with no default; fail loudly on startup if not set

**Cloudflare Tunnel token required but not validated for format:**
- Risk: `CLOUDFLARE_TUNNEL_TOKEN` env var is required but never validated; typos/wrong token fail silently at runtime
- Files: `server/docker-compose.yml` (line 63)
- Current mitigation: Service restart loop on failure
- Recommendations: Pre-validate token format in startup script; provide clear error message

---

## Performance Bottlenecks

**Unoptimized reserve layer update algorithm:**
- Problem: Recalculates cable slack for entire reserve layer on any edit event
- Files: `fiberq/addons/reserve_hook.py` (lines 186-205, 226-232)
- Cause: `_on_editing_stopped()` scans all features; `_on_geom_changed()` does full layer traversal
- Improvement path: Track only modified feature IDs; defer updates until editing stops; use spatial index for cable lookups

**GPKG export reads all features into memory before writing:**
- Problem: Entire table contents loaded with `conn.fetch()` before fiona write
- Files: `server/api/sync/exporter.py` (line 88)
- Cause: No streaming/pagination; all rows held in Python memory simultaneously
- Improvement path: Use asyncpg cursor for streaming; write features batch-by-batch (1000 at a time)

**JWT JWKS refetch on every key rotation check:**
- Problem: On key lookup failure, fetches entire JWKS again; blocks token validation
- Files: `server/api/auth/zitadel.py` (lines 73-82)
- Cause: Synchronous HTTP call in async context; no timeout protection
- Improvement path: Add timeout; implement backoff; cache JWKS with versioning instead of cache invalidation

**Sync differ compares all DB features for each GPKG row:**
- Problem: `_fetch_db_features()` called once but then O(n) iteration for conflict detection
- Files: `server/api/sync/differ.py` (lines 79-100)
- Cause: No indexing on feature IDs in memory
- Improvement path: Build dict of db_features by ID (already done); ensure no N² iteration on conflicts

---

## Fragile Areas

**QGIS plugin depends on hardcoded field names:**
- Files: `fiberq/addons/reserve_hook.py` (indexFromName('tip'), indexFromName('kabl_layer_id'), indexFromName('kabl_fid'), etc.)
- Why fragile: Field rename in database breaks all layer interaction silently
- Safe modification: Add layer schema validation at startup; raise informative error if required fields missing
- Test coverage: No automated tests for addon signal handlers; no field name validation tests

**Fiber plan tracer algorithm with no validation:**
- Files: `server/api/fiber_plan/tracer.py` (158 lines)
- Why fragile: Complex geometric calculations with no intermediate validation or bounds checking
- Safe modification: Add unit tests with known good traces; validate geometry at each step
- Test coverage: No unit tests visible in repository

**Database transaction handling in merger:**
- Files: `server/api/sync/merger.py` (204 lines)
- Why fragile: Updates database with no transaction wrapper; partial failures leave data inconsistent
- Safe modification: Wrap entire merge in `async with conn.transaction():` block
- Test coverage: No merge integration tests found

**GeoPackage file handling with no locking:**
- Files: `server/api/sync/exporter.py` (lines 35-36), `server/api/sync/merger.py`
- Why fragile: GPKG file deleted/overwritten during concurrent sync operations
- Safe modification: Implement file-level locking or unique temp files with atomic rename
- Test coverage: No concurrent sync tests

---

## Scaling Limits

**Global database connection pool (max 20 connections):**
- Current capacity: 20 concurrent connections
- Limit: With FastAPI workers=4 and typical request handling, supports ~5 concurrent users
- Scaling path: Increase `max_size=20` in `server/api/database.py` (line 14); monitor connection churn; consider connection pooler (pgBouncer)

**Photo storage on Docker volume:**
- Current capacity: Limited by volume size (typically 10-100GB container default)
- Limit: No cleanup; photos accumulate forever
- Scaling path: Implement S3/cloud storage; add photo retention policy; implement cleanup cronjob

**GPKG sync file accumulation:**
- Current capacity: `STORAGE_GPKG_DIR` unlimited; files never deleted
- Limit: Disk space fills up; large GPKG files slow down sync
- Scaling path: Delete GPKG files after successful merge; implement 7-day retention policy

**PostGIS schema hardcoded as "fiberq":**
- Current capacity: Single schema; multi-tenant not possible
- Limit: Organizational isolation requires separate database instances
- Scaling path: Add tenant_id to all tables; implement schema/database routing per tenant

---

## Dependencies at Risk

**python-jose (PyJWT alternative):**
- Risk: Older library; python-jose hasn't had security updates since 2021; JWT libraries frequently have CVEs
- Impact: Token validation vulnerability could grant unauthorized access
- Migration plan: Evaluate PyJWT (more maintained); implement token signature verification unit tests

**Fiona/GDAL stack for spatial I/O:**
- Risk: GDAL has history of buffer overflows in raster processing; Fiona wraps it
- Impact: Malformed GeoPackage could crash API
- Migration plan: Add GeoPackage validation before processing; catch and log GDAL errors gracefully

**Zitadel OIDC dependency:**
- Risk: Hard dependency on external service; no fallback authentication
- Impact: Zitadel outage = entire API down
- Migration plan: Implement local auth fallback; cache token validity; add circuit breaker pattern

**PostGIS 16:**
- Risk: PostGIS has SQL injection risks if not careful with table/column names (already identified above)
- Impact: Database compromise
- Migration plan: Migrate to ORM with parameterized table names; implement database permission restrictions

---

## Missing Critical Features

**No encryption for data at rest:**
- Problem: Database and photo storage completely unencrypted
- Blocks: GDPR compliance, healthcare data handling, classified infrastructure mapping
- Recommendation: Implement database encryption (PostgreSQL pgcrypto or Transparent Encryption); encrypt photo storage

**No audit logging:**
- Problem: No log of who changed what and when in sync/merge operations
- Blocks: Compliance reporting, incident investigation, rollback capability
- Recommendation: Add audit table; log all sync operations with user_sub, timestamp, operation type

**No soft delete / historical versioning:**
- Problem: Deleted features are gone; no way to view or restore history
- Blocks: Compliance, infrastructure archaeology, accident recovery
- Recommendation: Add deleted_at timestamp; implement view with version history

**No API rate limiting:**
- Problem: No protection against brute force or DoS attacks
- Blocks: Production deployment security checklist
- Recommendation: Add rate limiting middleware; implement per-user quotas

**No backup/disaster recovery procedure:**
- Problem: PostGIS container volume is ephemeral; data loss on host failure
- Blocks: Production deployment viability
- Recommendation: Implement daily PostgreSQL backups; document restore procedure; test regularly

---

## Test Coverage Gaps

**QGIS addon signal handling untested:**
- What's not tested: Reserve layer updates, fiber plan tracing, work order synchronization
- Files: `fiberq/addons/reserve_hook.py`, `fiberq/addons/fiber_plan.py`, `fiberq/addons/work_orders.py`
- Risk: Signal handler bugs cause silent failures in layer synchronization
- Priority: High - core functionality

**No integration tests for sync pipeline:**
- What's not tested: Full cycle of GPKG export → edit → merge back to PostGIS
- Files: `server/api/sync/*` (exporter, differ, merger, routes)
- Risk: Sync data loss or corruption undetected
- Priority: High - data integrity critical

**Auth token validation not unit tested:**
- What's not tested: Token expiry, key rotation, invalid signatures
- Files: `server/api/auth/zitadel.py`
- Risk: Authentication bypass due to incorrect validation logic
- Priority: Critical - security-sensitive

**Database migration tests missing:**
- What's not tested: Schema changes, backwards compatibility
- Files: `server/db/init.sql`
- Risk: Breaking changes go undetected
- Priority: Medium - deployment safety

**No tests for error handling paths:**
- What's not tested: Network failures, malformed GPKG, database connection loss
- Files: All route handlers
- Risk: Unhandled exceptions crash API
- Priority: High - reliability

---

*Concerns audit: 2026-02-21*
