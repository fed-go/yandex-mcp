"""Yandex Webmaster API tools."""

import json
from datetime import date, timedelta
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from ..client import api_client
from ..models.common import ResponseFormat
from ..models.webmaster import (
    WebmasterAddRecrawlBatchInput,
    WebmasterGetExcludedSamplesInput,
    WebmasterGetExternalLinksSummaryInput,
    WebmasterGetIndexingStatsInput,
    WebmasterGetInsearchSamplesInput,
    WebmasterGetRecrawlQuotaInput,
    WebmasterGetSearchQueriesInput,
    WebmasterGetSiteInfoInput,
    WebmasterGetSitemapsInput,
    WebmasterGetSqiHistoryInput,
    WebmasterListSitesInput,
    WebmasterRecrawlUrlInput,
)
from ..formatters.webmaster import (
    format_external_links_summary_markdown,
    format_hosts_markdown,
    format_indexing_stats_markdown,
    format_recrawl_quota_markdown,
    format_search_queries_markdown,
    format_site_info_markdown,
    format_sitemaps_markdown,
    format_sqi_history_markdown,
    format_url_samples_markdown,
    format_search_queries_markdown as _fmt_q,  # noqa: F401
)
from ..utils import handle_api_error


def _default_dates(date_from: str | None, date_to: str | None) -> tuple[str, str]:
    today = date.today()
    df = date_from or (today - timedelta(days=7)).isoformat()
    dt = date_to or today.isoformat()
    return df, dt


def _as_output(payload: Any, markdown: str, fmt: ResponseFormat) -> str:
    if fmt == ResponseFormat.JSON:
        return json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    return markdown


def register_webmaster_tools(mcp: FastMCP) -> None:
    """Register Webmaster tools (mcp__yandex__webmaster_*)."""

    @mcp.tool(
        name="webmaster_list_sites",
        annotations={
            "title": "List sites in Yandex Webmaster",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def webmaster_list_sites(params: WebmasterListSitesInput) -> str:
        """List all hosts (verified or not) in the connected Yandex Webmaster account."""
        try:
            uid = await api_client.webmaster_user_id()
            data = await api_client.webmaster_request(f"/user/{uid}/hosts/")
            hosts = data.get("hosts", [])
            api_client._wm_hosts_cache = hosts  # refresh cache
            return _as_output(hosts, format_hosts_markdown(hosts), params.response_format)
        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="webmaster_get_site_info",
        annotations={
            "title": "Get site info",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def webmaster_get_site_info(params: WebmasterGetSiteInfoInput) -> str:
        """Get general info about a host (verification status, mirror)."""
        try:
            uid = await api_client.webmaster_user_id()
            host_id = await api_client.webmaster_resolve_host_id(params.host)
            data = await api_client.webmaster_request(f"/user/{uid}/hosts/{host_id}/")
            return _as_output(data, format_site_info_markdown(data), params.response_format)
        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="webmaster_get_search_queries",
        annotations={
            "title": "Get search queries (Top)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def webmaster_get_search_queries(params: WebmasterGetSearchQueriesInput) -> str:
        """Top search queries from Yandex Webmaster (clicks/shows/CTR/position)."""
        try:
            uid = await api_client.webmaster_user_id()
            host_id = await api_client.webmaster_resolve_host_id(params.host)
            df, dt = _default_dates(params.date_from, params.date_to)
            qp: Dict[str, Any] = {
                "date_from": df,
                "date_to": dt,
                "query_indicator": params.query_indicator,
                "order_by": params.order_by,
                "limit": params.limit,
                "offset": params.offset,
            }
            if params.device_type:
                qp["device_type_indicator"] = params.device_type
            data = await api_client.webmaster_request(
                f"/user/{uid}/hosts/{host_id}/search-queries/popular/",
                params=qp,
            )
            return _as_output(
                data,
                format_search_queries_markdown(data, params.host),
                params.response_format,
            )
        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="webmaster_get_indexing_stats",
        annotations={
            "title": "Get indexing stats",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def webmaster_get_indexing_stats(params: WebmasterGetIndexingStatsInput) -> str:
        """Indexing summary: counts of insearch / excluded URLs and history."""
        try:
            uid = await api_client.webmaster_user_id()
            host_id = await api_client.webmaster_resolve_host_id(params.host)
            data = await api_client.webmaster_request(
                f"/user/{uid}/hosts/{host_id}/summary/"
            )
            return _as_output(
                data,
                format_indexing_stats_markdown(data, params.host),
                params.response_format,
            )
        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="webmaster_get_insearch_samples",
        annotations={
            "title": "Get sample of in-search URLs",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def webmaster_get_insearch_samples(params: WebmasterGetInsearchSamplesInput) -> str:
        """Sample of URLs currently present in Yandex search index."""
        try:
            uid = await api_client.webmaster_user_id()
            host_id = await api_client.webmaster_resolve_host_id(params.host)
            data = await api_client.webmaster_request(
                f"/user/{uid}/hosts/{host_id}/search-urls/in-search/samples/",
                params={"limit": params.limit, "offset": params.offset},
            )
            return _as_output(
                data,
                format_url_samples_markdown(data, params.host, "in-search"),
                params.response_format,
            )
        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="webmaster_get_excluded_samples",
        annotations={
            "title": "Get sample of excluded URLs",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def webmaster_get_excluded_samples(params: WebmasterGetExcludedSamplesInput) -> str:
        """Sample of URLs excluded from Yandex search (with reasons)."""
        try:
            uid = await api_client.webmaster_user_id()
            host_id = await api_client.webmaster_resolve_host_id(params.host)
            data = await api_client.webmaster_request(
                f"/user/{uid}/hosts/{host_id}/search-urls/excluded/samples/",
                params={"limit": params.limit, "offset": params.offset},
            )
            return _as_output(
                data,
                format_url_samples_markdown(data, params.host, "excluded"),
                params.response_format,
            )
        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="webmaster_get_sitemaps",
        annotations={
            "title": "List sitemaps",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def webmaster_get_sitemaps(params: WebmasterGetSitemapsInput) -> str:
        """List sitemaps registered for the host with status and counts."""
        try:
            uid = await api_client.webmaster_user_id()
            host_id = await api_client.webmaster_resolve_host_id(params.host)
            data = await api_client.webmaster_request(
                f"/user/{uid}/hosts/{host_id}/sitemaps/"
            )
            return _as_output(
                data,
                format_sitemaps_markdown(data, params.host),
                params.response_format,
            )
        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="webmaster_recrawl_url",
        annotations={
            "title": "Submit URL for recrawl",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def webmaster_recrawl_url(params: WebmasterRecrawlUrlInput) -> str:
        """Submit a single URL to Yandex recrawl queue. Consumes daily quota."""
        try:
            uid = await api_client.webmaster_user_id()
            host_id = await api_client.webmaster_resolve_host_id(params.host)
            data = await api_client.webmaster_request(
                f"/user/{uid}/hosts/{host_id}/recrawl/queue/",
                method="POST",
                data={"url": params.url},
            )
            md = (
                f"✅ Submitted `{params.url}` for recrawl.\n\n"
                f"Task ID: `{data.get('task_id', '?')}`"
            )
            return _as_output(data, md, params.response_format)
        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="webmaster_recrawl_batch",
        annotations={
            "title": "Submit URLs for recrawl (batch)",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def webmaster_recrawl_batch(params: WebmasterAddRecrawlBatchInput) -> str:
        """Submit several URLs to Yandex recrawl queue. Each URL consumes 1 quota."""
        try:
            uid = await api_client.webmaster_user_id()
            host_id = await api_client.webmaster_resolve_host_id(params.host)
            results = []
            for u in params.urls:
                try:
                    r = await api_client.webmaster_request(
                        f"/user/{uid}/hosts/{host_id}/recrawl/queue/",
                        method="POST",
                        data={"url": u},
                    )
                    results.append({"url": u, "status": "ok", "task_id": r.get("task_id")})
                except Exception as inner:  # noqa: BLE001
                    results.append({"url": u, "status": "error", "error": str(inner)})
            md_lines = [f"# Recrawl batch — {params.host}", ""]
            md_lines.append("| URL | Status | task_id / error |")
            md_lines.append("|---|:-:|---|")
            for r in results:
                if r["status"] == "ok":
                    md_lines.append(f"| {r['url']} | ✅ | `{r.get('task_id', '?')}` |")
                else:
                    md_lines.append(f"| {r['url']} | ❌ | {r.get('error', '')} |")
            return _as_output(results, "\n".join(md_lines), params.response_format)
        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="webmaster_get_recrawl_quota",
        annotations={
            "title": "Get recrawl quota",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def webmaster_get_recrawl_quota(params: WebmasterGetRecrawlQuotaInput) -> str:
        """Get daily recrawl-queue quota: total, remaining, used."""
        try:
            uid = await api_client.webmaster_user_id()
            host_id = await api_client.webmaster_resolve_host_id(params.host)
            data = await api_client.webmaster_request(
                f"/user/{uid}/hosts/{host_id}/recrawl/quota/"
            )
            return _as_output(
                data,
                format_recrawl_quota_markdown(data, params.host),
                params.response_format,
            )
        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="webmaster_get_sqi_history",
        annotations={
            "title": "Get ИКС history",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def webmaster_get_sqi_history(params: WebmasterGetSqiHistoryInput) -> str:
        """ИКС (Site Quality Index) history points."""
        try:
            uid = await api_client.webmaster_user_id()
            host_id = await api_client.webmaster_resolve_host_id(params.host)
            data = await api_client.webmaster_request(
                f"/user/{uid}/hosts/{host_id}/sqi-history/"
            )
            return _as_output(
                data,
                format_sqi_history_markdown(data, params.host),
                params.response_format,
            )
        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)

    @mcp.tool(
        name="webmaster_get_external_links_summary",
        annotations={
            "title": "Get external links summary",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def webmaster_get_external_links_summary(
        params: WebmasterGetExternalLinksSummaryInput,
    ) -> str:
        """Total external links and unique domains pointing to the host."""
        try:
            uid = await api_client.webmaster_user_id()
            host_id = await api_client.webmaster_resolve_host_id(params.host)
            data = await api_client.webmaster_request(
                f"/user/{uid}/hosts/{host_id}/links/external/main/"
            )
            return _as_output(
                data,
                format_external_links_summary_markdown(data, params.host),
                params.response_format,
            )
        except Exception as e:  # noqa: BLE001
            return handle_api_error(e)
