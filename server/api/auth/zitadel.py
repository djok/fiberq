import logging

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config import settings
from auth.models import UserInfo

logger = logging.getLogger("fiberq.auth")

security = HTTPBearer()

_jwks_cache: dict | None = None
_openid_config_cache: dict | None = None


async def _get_openid_config() -> dict:
    global _openid_config_cache
    if _openid_config_cache:
        return _openid_config_cache

    url = f"https://{settings.zitadel_domain}/.well-known/openid-configuration"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        _openid_config_cache = resp.json()
    return _openid_config_cache


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache

    config = await _get_openid_config()
    jwks_uri = config["jwks_uri"]
    async with httpx.AsyncClient() as client:
        resp = await client.get(jwks_uri)
        resp.raise_for_status()
        _jwks_cache = resp.json()
    return _jwks_cache


def _find_key(jwks: dict, kid: str) -> dict | None:
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    return None


async def validate_token(token: str) -> dict:
    """Validate a Zitadel OIDC Bearer token and return claims."""
    if not settings.zitadel_domain:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zitadel not configured",
        )

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
        )

    jwks = await _get_jwks()
    key = _find_key(jwks, unverified_header.get("kid", ""))

    if not key:
        # Refresh JWKS cache in case keys rotated
        global _jwks_cache
        _jwks_cache = None
        jwks = await _get_jwks()
        key = _find_key(jwks, unverified_header.get("kid", ""))
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token signing key not found",
            )

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.zitadel_client_id,
            issuer=f"https://{settings.zitadel_domain}",
        )
    except JWTError as e:
        logger.warning("Token validation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {e}",
        )

    return claims


def _extract_roles(claims: dict) -> list[str]:
    """Extract FiberQ roles from Zitadel token claims."""
    roles = []

    # Zitadel stores project roles in urn:zitadel:iam:org:project:roles
    project_roles = claims.get("urn:zitadel:iam:org:project:roles", {})
    if isinstance(project_roles, dict):
        roles.extend(project_roles.keys())

    # Also check urn:zitadel:iam:org:project:{id}:roles
    if settings.zitadel_project_id:
        key = f"urn:zitadel:iam:org:project:{settings.zitadel_project_id}:roles"
        project_specific = claims.get(key, {})
        if isinstance(project_specific, dict):
            for role in project_specific.keys():
                if role not in roles:
                    roles.append(role)

    return roles


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserInfo:
    """FastAPI dependency that validates token and returns user info."""
    claims = await validate_token(credentials.credentials)

    return UserInfo(
        sub=claims.get("sub", ""),
        email=claims.get("email", claims.get("preferred_username", "")),
        name=claims.get("name", claims.get("given_name", "")),
        roles=_extract_roles(claims),
    )
