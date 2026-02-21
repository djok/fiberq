# Testing Patterns

**Analysis Date:** 2026-02-21

## Test Framework

**Status:** No active testing framework configured or in use

**Evidence:**
- No `pytest.ini`, `pyproject.toml`, `conftest.py`, or `vitest.config.js` found
- `tests/` directory exists but is empty (no `.py` test files)
- `.pytest_cache/` directory present but contains only cache metadata
- No test files in root or module directories (pattern `*.test.py`, `*.spec.py` not found)
- No assertions or test code in codebase

**Observation:**
This is a mature project (v1.1.1) without automated testing infrastructure. All validation appears to be manual or through staging deployments.

## Documentation of Expected Patterns (If Tests Were to Be Added)

### Recommended Framework
**pytest** would be natural choice for this project because:
- Async support via `pytest-asyncio`
- Works well with FastAPI (FastAPI docs recommend pytest)
- Simple, Pythonic API
- Good coverage tools

### Suggested Test Structure
```
tests/
├── conftest.py              # Shared fixtures, pytest configuration
├── unit/
│   ├── test_config.py       # Settings loading
│   ├── test_auth/
│   │   ├── test_zitadel.py  # Token validation, role extraction
│   │   └── test_models.py   # UserInfo properties
│   ├── test_database.py     # Pool creation, connection helpers
│   └── test_sync/
│       ├── test_differ.py   # Diff computation logic
│       ├── test_merger.py   # Merge operations
│       └── test_exporter.py # GPKG export
├── integration/
│   ├── test_auth_routes.py  # GET /auth/me, /auth/roles
│   ├── test_project_routes.py
│   ├── test_work_orders_routes.py
│   └── test_sync_routes.py
└── qgis/                    # Separate QGIS plugin UI tests (if applicable)
    └── test_api_client.py
```

## Code Organization Implications for Tests

**Units to test (by file):**

| File | Type | Test Focus |
|------|------|-----------|
| `config.py` | Settings | Env var loading, defaults, validation |
| `database.py` | Pool management | Initialization, cleanup, connection context managers |
| `auth/models.py` | Pydantic models | Role inference (`is_admin`, `is_engineer` properties) |
| `auth/zitadel.py` | OAuth integration | Token validation, JWKS caching, role extraction |
| `sync/differ.py` | Business logic | Feature comparison, timestamp conflict resolution |
| `sync/merger.py` | Data merge | Layer mapping, insert/update/conflict handling |
| `sync/exporter.py` | Data export | GPKG layer creation, geometry handling |
| `dependencies.py` | FastAPI dependencies | Role-based access control |
| Route handlers | Integration | Request validation, response models, status codes |

## Testing Patterns (Hypothetical Best Practices)

### Async Test Pattern
```python
import pytest
from httpx import AsyncClient
from fastapi import FastAPI

@pytest.mark.asyncio
async def test_health_check(app: FastAPI):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "db": True}
```

### Fixture Pattern (Would use pytest)
```python
# conftest.py
import pytest
from config import Settings

@pytest.fixture
async def test_settings():
    """Override with test database URL."""
    return Settings(
        database_url="postgresql+asyncpg://test:test@localhost:5432/fiberq_test"
    )

@pytest.fixture
async def db_pool(test_settings):
    """Create isolated test pool."""
    pool = await asyncpg.create_pool(dsn=test_settings.asyncpg_dsn)
    yield pool
    await pool.close()
```

### Mock Pattern (Would use unittest.mock)
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_token_validation_failure():
    with patch('auth.zitadel._get_jwks') as mock_jwks:
        mock_jwks.return_value = {"keys": []}
        with pytest.raises(HTTPException) as exc_info:
            await validate_token("invalid.token.here")
        assert exc_info.value.status_code == 401
```

### Database Testing Pattern
```python
@pytest.mark.asyncio
async def test_sync_merge(db_pool, gpkg_fixture):
    """Test merge operation with real database transaction."""
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            result = await merge_gpkg_to_postgis(
                gpkg_path=gpkg_fixture,
                project_id=1,
                user_sub="user123",
                pool=db_pool
            )
            assert result["features_merged"] > 0

            # Verify features were inserted
            rows = await conn.fetch("SELECT * FROM ftth_trase WHERE _modified_by_sub = 'user123'")
            assert len(rows) > 0
```

## Coverage Expectations (If Tests Were Implemented)

**Critical paths to cover (High Priority):**
1. Authentication flow: Token validation, role checks, permission enforcement
2. Data sync: GPKG merge logic, conflict resolution, transaction handling
3. API boundaries: Request validation, error responses, status codes

**Secondary paths (Medium Priority):**
1. Settings/configuration loading and validation
2. Database pool lifecycle (create, close, error recovery)
3. Data export (GPKG generation from PostGIS)

**Lower priority:**
1. QGIS plugin UI dialogs (manual testing sufficient due to framework constraints)
2. Icon/resource loading helpers
3. Language/translation functions

## QGIS Plugin Testing (Special Considerations)

**Challenge:** QGIS plugins require QGIS environment (cannot run in CI easily)

**Strategies:**
1. **Unit test logic separately:** Extract business logic into standalone modules
   - Example: Move API client code (`FiberQApiClient`) to testable module without QGIS dependencies
   - Test sync/merge logic without QGIS imports

2. **Manual testing checklist** (if no automated framework):
   - Addon loading and initialization
   - Dialog UI responsiveness
   - Token refresh and auth flow
   - File upload success/failure handling

3. **Example testable extraction from `addons/api_client.py`:**
   - `FiberQApiClient` class has no QGIS dependencies → fully testable
   - `_load_server_config()` reads config.ini → testable with fixture files
   - `_request()` method handles HTTP → mockable with unittest.mock

## Current State

**No tests exist.** To add testing:

1. Create `tests/conftest.py` with pytest configuration and shared fixtures
2. Create `tests/unit/` for unit tests of sync logic, auth, models
3. Create `tests/integration/` for FastAPI route tests
4. Add `pytest` and `pytest-asyncio` to dependencies
5. Add CI step to run tests on push (GitHub Actions already configured)

**Recommended first tests to add:**
1. `tests/unit/test_config.py` – Settings loading
2. `tests/unit/test_database.py` – Pool initialization
3. `tests/integration/test_auth_routes.py` – OAuth flow
4. `tests/integration/test_sync_routes.py` – Data merge endpoint

---

*Testing analysis: 2026-02-21*
