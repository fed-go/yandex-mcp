"""Pydantic models for Yandex Webmaster tools."""

from typing import List, Optional

from pydantic import BaseModel, Field

from .common import ResponseFormat


class WebmasterListSitesInput(BaseModel):
    """No parameters — list all sites in the Webmaster account."""
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' (default) or 'json'.",
    )


class _HostScopedInput(BaseModel):
    """Common base for tools scoped to a single host."""
    host: str = Field(
        ...,
        description=(
            "Host: domain ('applause-pc.ru'), full URL ('https://applause-pc.ru/'), "
            "or raw Webmaster host_id ('https:applause-pc.ru:443')."
        ),
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' (default) or 'json'.",
    )


class WebmasterGetSiteInfoInput(_HostScopedInput):
    """Get general info about a host (verification status, mirror, etc)."""


class WebmasterGetSearchQueriesInput(_HostScopedInput):
    """Search performance queries (POPULAR by default)."""
    date_from: Optional[str] = Field(
        default=None,
        description="ISO date YYYY-MM-DD. Defaults to 7 days ago.",
    )
    date_to: Optional[str] = Field(
        default=None,
        description="ISO date YYYY-MM-DD. Defaults to today.",
    )
    query_indicator: str = Field(
        default="TOTAL_SHOWS",
        description=(
            "Sort indicator: TOTAL_SHOWS, TOTAL_CLICKS, AVG_SHOW_POSITION, "
            "AVG_CLICK_POSITION, CTR."
        ),
    )
    order_by: str = Field(
        default="TOTAL_SHOWS",
        description="Sort field. Same values as query_indicator.",
    )
    limit: int = Field(default=20, ge=1, le=500, description="Max queries to return.")
    offset: int = Field(default=0, ge=0)
    device_type: Optional[str] = Field(
        default=None,
        description="DESKTOP / MOBILE_AND_TABLET / MOBILE / TABLET. Default: all.",
    )


class WebmasterGetIndexingStatsInput(_HostScopedInput):
    """Indexing summary (counts of insearch, excluded, errors)."""


class WebmasterGetInsearchSamplesInput(_HostScopedInput):
    """Sample of URLs currently in Yandex search index."""
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class WebmasterGetExcludedSamplesInput(_HostScopedInput):
    """Sample of URLs excluded from search."""
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class WebmasterGetSitemapsInput(_HostScopedInput):
    """List sitemaps known for the host with status."""


class WebmasterRecrawlUrlInput(_HostScopedInput):
    """Submit a URL for re-crawl (consumes daily quota)."""
    url: str = Field(..., description="Full URL to recrawl.")


class WebmasterGetRecrawlQuotaInput(_HostScopedInput):
    """Daily recrawl-queue quota info."""


class WebmasterGetSqiHistoryInput(_HostScopedInput):
    """ИКС (SQI) history."""


class WebmasterGetExternalLinksSummaryInput(_HostScopedInput):
    """Summary of external links pointing to the host."""


class WebmasterAddRecrawlBatchInput(_HostScopedInput):
    """Submit several URLs for re-crawl in a batch (each consumes 1 quota)."""
    urls: List[str] = Field(..., description="List of full URLs to recrawl.")
