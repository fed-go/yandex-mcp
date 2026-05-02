"""Yandex Wordstat tools backed by Yandex Search API (AI Studio)."""

import json
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from ..client import api_client
from ..models.common import ResponseFormat
from ..models.wordstat import (
    WordstatTopRequestsInput,
    WordstatDynamicsInput,
    WordstatRegionsInput,
    WordstatRegionsTreeInput,
    WordstatUserInfoInput,
)
from ..formatters.wordstat import (
    format_wordstat_top_requests_markdown,
    format_wordstat_dynamics_markdown,
    format_wordstat_regions_markdown,
)
from ..utils import handle_api_error


_DEVICE_MAP = {
    "all": "DEVICE_ALL",
    "desktop": "DEVICE_DESKTOP",
    "phone": "DEVICE_PHONE",
    "mobile": "DEVICE_PHONE",
    "tablet": "DEVICE_TABLET",
}

_PERIOD_MAP = {
    "monthly": "PERIOD_MONTHLY",
    "weekly": "PERIOD_WEEKLY",
    "daily": "PERIOD_DAILY",
}

_REGION_TYPE_MAP = {
    "cities": "REGION_CITIES",
    "regions": "REGION_REGIONS",
    "all": "REGION_ALL",
}


def _normalize_devices(values: Optional[List[str]]) -> Optional[List[str]]:
    if not values:
        return None
    return [_DEVICE_MAP.get(v.lower(), v) for v in values]


def _normalize_regions(values: Optional[List[Any]]) -> Optional[List[str]]:
    if not values:
        return None
    return [str(v) for v in values]


def _to_rfc3339(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    return value if "T" in value else f"{value}T00:00:00Z"


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def register(mcp: FastMCP) -> None:
    """Register Wordstat tools."""

    @mcp.tool(
        name="wordstat_top_requests",
        annotations={
            "title": "Get Wordstat Top Requests",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def wordstat_top_requests(params: WordstatTopRequestsInput) -> str:
        """Get popular search queries from Yandex Wordstat (Search API GetTop).

        Returns top requests and associated queries for given phrases.
        Provide either 'phrase' (single) or 'phrases' (multiple — fanned out
        into one request per phrase, since Search API accepts a single phrase).
        """
        try:
            phrases = params.phrases or ([params.phrase] if params.phrase else [])
            if not phrases:
                return "Error: provide either 'phrase' or 'phrases' parameter."

            results: List[Dict[str, Any]] = []
            for phrase in phrases:
                data: Dict[str, Any] = {
                    "phrase": phrase,
                    "numPhrases": params.num_phrases,
                }
                regions = _normalize_regions(params.regions)
                if regions is not None:
                    data["regions"] = regions
                devices = _normalize_devices(params.devices)
                if devices is not None:
                    data["devices"] = devices

                try:
                    raw = await api_client.wordstat_request(
                        "/v2/wordstat/topRequests", data
                    )
                except Exception as e:  # noqa: BLE001
                    results.append({"requestPhrase": phrase, "error": str(e)})
                    continue

                results.append(
                    {
                        "requestPhrase": phrase,
                        "totalCount": _safe_int(raw.get("totalCount")),
                        "topRequests": [
                            {
                                "phrase": x.get("phrase"),
                                "count": _safe_int(x.get("count")),
                            }
                            for x in raw.get("results", [])
                        ],
                        "associations": [
                            {
                                "phrase": x.get("phrase"),
                                "count": _safe_int(x.get("count")),
                            }
                            for x in raw.get("associations", [])
                        ],
                    }
                )

            payload: Any = results[0] if len(results) == 1 else results

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(payload, indent=2, ensure_ascii=False)
            return format_wordstat_top_requests_markdown(payload)

        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="wordstat_dynamics",
        annotations={
            "title": "Get Wordstat Query Dynamics",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def wordstat_dynamics(params: WordstatDynamicsInput) -> str:
        """Get query frequency dynamics over time (Search API GetDynamics).

        Only the + operator is allowed when period is weekly/monthly; daily
        supports all operators. Dates accepted as YYYY-MM-DD (converted to
        RFC3339 automatically) or as RFC3339 strings.
        """
        try:
            data: Dict[str, Any] = {
                "phrase": params.phrase,
                "period": _PERIOD_MAP.get(
                    params.period.lower(), params.period
                ),
                "fromDate": _to_rfc3339(params.from_date),
            }
            if params.to_date is not None:
                data["toDate"] = _to_rfc3339(params.to_date)
            regions = _normalize_regions(params.regions)
            if regions is not None:
                data["regions"] = regions
            devices = _normalize_devices(params.devices)
            if devices is not None:
                data["devices"] = devices

            raw = await api_client.wordstat_request("/v2/wordstat/dynamics", data)
            normalized = {
                "dynamics": [
                    {
                        "date": item.get("date"),
                        "count": _safe_int(item.get("count")),
                        "share": item.get("share", 0),
                    }
                    for item in raw.get("results", [])
                ]
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(normalized, indent=2, ensure_ascii=False)
            return format_wordstat_dynamics_markdown(normalized)

        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="wordstat_regions",
        annotations={
            "title": "Get Wordstat Regional Distribution",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def wordstat_regions(params: WordstatRegionsInput) -> str:
        """Get regional distribution of search queries (Search API GetRegionsDistribution).

        Region granularity: 'cities', 'regions', or 'all' (default).
        """
        try:
            data: Dict[str, Any] = {
                "phrase": params.phrase,
                "region": _REGION_TYPE_MAP.get(
                    params.region_type.lower(), params.region_type
                ),
            }
            devices = _normalize_devices(params.devices)
            if devices is not None:
                data["devices"] = devices

            raw = await api_client.wordstat_request("/v2/wordstat/regions", data)
            normalized = {
                "regions": [
                    {
                        "regionId": item.get("region"),
                        "count": _safe_int(item.get("count")),
                        "share": item.get("share", 0),
                        "affinityIndex": item.get("affinityIndex", 0),
                    }
                    for item in raw.get("results", [])
                ]
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(normalized, indent=2, ensure_ascii=False)
            return format_wordstat_regions_markdown(normalized)

        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="wordstat_regions_tree",
        annotations={
            "title": "Get Wordstat Regions Tree",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def wordstat_regions_tree(params: WordstatRegionsTreeInput) -> str:
        """Return hierarchical list of region codes supported by Wordstat."""
        try:
            result = await api_client.wordstat_request(
                "/v2/wordstat/getRegionsTree", {}
            )
            return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="wordstat_user_info",
        annotations={
            "title": "Get Wordstat User Info",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def wordstat_user_info(params: WordstatUserInfoInput) -> str:
        """Wordstat quotas are managed in Yandex Cloud Console — no API endpoint."""
        return (
            "Yandex Search API не предоставляет отдельный userInfo-эндпоинт. "
            "Квоты и остаток лимитов смотрите в консоли Yandex Cloud: "
            "https://console.yandex.cloud/ → Квоты."
        )
