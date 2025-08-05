from __future__ import annotations
import os
import time
from typing import Any, Dict, Optional, List

import httpx
from fastapi import HTTPException, status, Request
from jose import jwt
from jose.utils import base64url_decode


class OIDCConfig:
    def __init__(self) -> None:
        self.issuer: str = os.getenv("OIDC_ISSUER", "")
        self.audience: str = os.getenv("OIDC_AUDIENCE", "")
        # If OIDC_JWKS_URL is not provided, default to {issuer}/.well-known/jwks.json
        self.jwks_url: str = os.getenv("OIDC_JWKS_URL", "").strip() or (
            (self.issuer.rstrip("/") + "/.well-known/jwks.json") if self.issuer else ""
        )
        # Role enforcement
        self.required_role_claim: str = os.getenv("OIDC_ROLE_CLAIM", "role")
        self.required_role_value: str = os.getenv("OIDC_REQUIRED_ROLE", "generator")

        if not self.issuer or not self.audience or not self.jwks_url:
            raise RuntimeError(
                "OIDC_ISSUER, OIDC_AUDIENCE and OIDC_JWKS_URL (or issuer-based default) must be set"
            )


class JWKSCache:
    def __init__(self) -> None:
        self.keys: Optional[Dict[str, Any]] = None
        self.expires_at: float = 0.0

    def get(self) -> Optional[Dict[str, Any]]:
        if self.expires_at and time.time() < self.expires_at:
            return self.keys
        return None

    def set(self, keys: Dict[str, Any], ttl_seconds: int = 300) -> None:
        self.keys = keys
        self.expires_at = time.time() + ttl_seconds


class OIDCValidator:
    def __init__(self, config: OIDCConfig) -> None:
        self.config = config
        self._jwks_cache = JWKSCache()

    async def _fetch_jwks(self) -> Dict[str, Any]:
        cached = self._jwks_cache.get()
        if cached:
            return cached
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(self.config.jwks_url)
            resp.raise_for_status()
            data = resp.json()
            # Cache for 5 minutes
            self._jwks_cache.set(data, ttl_seconds=300)
            return data

    async def _get_signing_key(self, kid: str) -> Dict[str, Any]:
        jwks = await self._fetch_jwks()
        keys: List[Dict[str, Any]] = jwks.get("keys", []) if isinstance(jwks, dict) else []
        for key in keys:
            if key.get("kid") == kid:
                return key
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signing key not found for token kid",
        )

    async def validate_request(self, request: Request) -> Dict[str, Any]:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = auth.split(" ", 1)[1].strip()
        try:
            # Decode headers to get kid
            header_b64 = token.split(".")[0]
            header_data = base64url_decode(header_b64.encode("utf-8"))
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing kid header",
                )

            signing_key = await self._get_signing_key(kid)

            claims = jwt.decode(
                token,
                signing_key,
                algorithms=[signing_key.get("alg", "RS256")],
                audience=self.config.audience,
                issuer=self.config.issuer,
                options={"verify_at_hash": False},
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {exc}",
            )

        # Role enforcement
        role_claim = claims.get(self.config.required_role_claim)
        if isinstance(role_claim, list):
            ok = self.config.required_role_value in role_claim
        else:
            ok = role_claim == self.config.required_role_value
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )

        return claims
