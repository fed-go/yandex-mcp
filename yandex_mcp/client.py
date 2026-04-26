"""Unified API client for Yandex Direct and Metrika APIs."""

import os
from typing import Any, Dict, Optional

import httpx

from .config import (
    DEFAULT_TIMEOUT,
    YANDEX_DIRECT_API_URL,
    YANDEX_DIRECT_API_URL_V501,
    YANDEX_DIRECT_SANDBOX_URL,
    YANDEX_METRIKA_API_URL,
)


class YandexAPIClient:
    """Unified client for Yandex Direct and Metrika APIs."""

    def __init__(self):
        self.direct_token = os.environ.get("YANDEX_DIRECT_TOKEN", "")
        self.metrika_token = os.environ.get("YANDEX_METRIKA_TOKEN", "")
        # Allow single token for both services
        self.unified_token = os.environ.get("YANDEX_TOKEN", "")
        self.client_login = os.environ.get("YANDEX_CLIENT_LOGIN", "")
        self.use_sandbox = os.environ.get("YANDEX_USE_SANDBOX", "false").lower() == "true"
        # Yandex Cloud AI Studio (Search API) — used for Wordstat since Yandex
        # retired api.wordstat.yandex.net in favour of searchapi.api.cloud.yandex.net.
        self.ai_studio_key = os.environ.get("YANDEX_AI_STUDIO_KEY", "")
        self.cloud_folder_id = os.environ.get("YANDEX_CLOUD_FOLDER_ID", "")

    def _get_direct_token(self) -> str:
        """Get token for Direct API."""
        return self.direct_token or self.unified_token

    def _get_metrika_token(self) -> str:
        """Get token for Metrika API."""
        return self.metrika_token or self.unified_token

    def _get_direct_url(self, use_v501: bool = False) -> str:
        """Get Direct API URL based on configuration."""
        if self.use_sandbox:
            return YANDEX_DIRECT_SANDBOX_URL
        return YANDEX_DIRECT_API_URL_V501 if use_v501 else YANDEX_DIRECT_API_URL

    async def direct_request(
        self,
        service: str,
        method: str,
        params: Dict[str, Any],
        use_v501: bool = False,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Make a request to Yandex Direct API."""
        token = self._get_direct_token()
        if not token:
            raise ValueError(
                "Yandex Direct API token not configured. "
                "Set YANDEX_DIRECT_TOKEN or YANDEX_TOKEN environment variable."
            )

        url = f"{self._get_direct_url(use_v501)}/{service}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept-Language": "ru",
            "Content-Type": "application/json"
        }

        if self.client_login:
            headers["Client-Login"] = self.client_login

        payload = {
            "method": method,
            "params": params
        }

        req_timeout = timeout or DEFAULT_TIMEOUT
        async with httpx.AsyncClient(timeout=req_timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def metrika_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to Yandex Metrika API."""
        token = self._get_metrika_token()
        if not token:
            raise ValueError(
                "Yandex Metrika API token not configured. "
                "Set YANDEX_METRIKA_TOKEN or YANDEX_TOKEN environment variable."
            )

        url = f"{YANDEX_METRIKA_API_URL}{endpoint}"
        headers = {
            "Authorization": f"OAuth {token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            if method == "GET":
                response = await client.get(url, params=params, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=data, params=params, headers=headers)
            elif method == "PUT":
                response = await client.put(url, json=data, params=params, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            if response.status_code == 204:
                return {"success": True}

            return response.json()

    async def webmaster_request(
        self,
        path: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to Yandex Webmaster API v4.

        `path` may be either an absolute path under /v4 (e.g. "/user/")
        or a relative one (e.g. "user/123/hosts/"). The leading slash
        is normalized.
        """
        from .config import YANDEX_WEBMASTER_API_URL

        token = self.unified_token or os.environ.get("YANDEX_WEBMASTER_TOKEN", "")
        if not token:
            raise ValueError(
                "Yandex Webmaster API token not configured. "
                "Set YANDEX_TOKEN or YANDEX_WEBMASTER_TOKEN environment variable."
            )

        path = path if path.startswith("/") else f"/{path}"
        url = f"{YANDEX_WEBMASTER_API_URL}{path}"
        headers = {
            "Authorization": f"OAuth {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            if method == "GET":
                response = await client.get(url, params=params, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=data, params=params, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                return {"success": True}
            return response.json()

    async def webmaster_user_id(self) -> int:
        """Resolve & cache Webmaster user_id (required in every subsequent path)."""
        if getattr(self, "_wm_user_id", None):
            return self._wm_user_id  # type: ignore[return-value]
        data = await self.webmaster_request("/user/")
        uid = data.get("user_id")
        if not uid:
            raise ValueError(f"Cannot resolve Webmaster user_id from response: {data!r}")
        self._wm_user_id = int(uid)
        return self._wm_user_id

    async def webmaster_resolve_host_id(self, host: str) -> str:
        """Resolve host_id from a domain or URL.

        Yandex host_id format is 'https:domain:443' (or http:domain:80).
        If the input already looks like a host_id, it's returned as-is.
        Otherwise, list_hosts is queried and matched by ascii_host_url.
        """
        if ":" in host and not host.startswith("http"):
            return host  # already a host_id

        if not getattr(self, "_wm_hosts_cache", None):
            uid = await self.webmaster_user_id()
            data = await self.webmaster_request(f"/user/{uid}/hosts/")
            self._wm_hosts_cache = data.get("hosts", [])

        needle = host.lower().rstrip("/")
        if needle.startswith("http"):
            candidates = [needle + "/" if not needle.endswith("/") else needle]
        else:
            candidates = [f"https://{needle}/", f"http://{needle}/"]

        for h in self._wm_hosts_cache:  # type: ignore[union-attr]
            ascii_url = h.get("ascii_host_url", "").lower()
            if ascii_url in candidates:
                return h.get("host_id", "")

        available = [h.get("ascii_host_url") for h in self._wm_hosts_cache]  # type: ignore[union-attr]
        raise ValueError(
            f"Host '{host}' not found in Yandex Webmaster account. "
            f"Available ({len(available)}): {available}"
        )

    async def wordstat_request(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call Yandex Search API Wordstat (AI Studio).

        `folderId` is injected automatically if absent.
        """
        if not self.ai_studio_key:
            raise ValueError(
                "Yandex AI Studio API key not configured. "
                "Set YANDEX_AI_STUDIO_KEY environment variable."
            )
        if not self.cloud_folder_id:
            raise ValueError(
                "Yandex Cloud folder ID not configured. "
                "Set YANDEX_CLOUD_FOLDER_ID environment variable."
            )

        from .config import YANDEX_SEARCH_API_URL
        url = f"{YANDEX_SEARCH_API_URL}{endpoint}"
        payload = dict(data or {})
        payload.setdefault("folderId", self.cloud_folder_id)

        headers = {
            "Authorization": f"Api-Key {self.ai_studio_key}",
            "Content-Type": "application/json;charset=utf-8",
        }

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()


# Global API client instance
api_client = YandexAPIClient()
