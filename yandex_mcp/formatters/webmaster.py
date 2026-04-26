"""Markdown formatters for Yandex Webmaster tool responses."""

from typing import Any, Dict, List


def format_hosts_markdown(hosts: List[Dict[str, Any]]) -> str:
    if not hosts:
        return "No verified hosts in account."
    lines = [f"# Webmaster: {len(hosts)} host(s)", ""]
    lines.append("| URL | Verified | host_id |")
    lines.append("|---|:-:|---|")
    for h in hosts:
        url = h.get("ascii_host_url", "")
        verified = "✅" if h.get("verified") else "❌"
        hid = h.get("host_id", "")
        lines.append(f"| {url} | {verified} | `{hid}` |")
    return "\n".join(lines)


def format_site_info_markdown(data: Dict[str, Any]) -> str:
    return (
        f"# {data.get('ascii_host_url', '?')}\n\n"
        f"- **host_id:** `{data.get('host_id', '?')}`\n"
        f"- **Verified:** {'✅' if data.get('verified') else '❌'}\n"
        f"- **Main mirror:** {data.get('main_mirror') or '—'}\n"
    )


def format_search_queries_markdown(data: Dict[str, Any], host: str) -> str:
    queries = data.get("queries") or data.get("indicators", {}).get("queries") or []
    total = data.get("count", len(queries))
    if not queries:
        # API might return aggregated indicators only
        ind = data.get("indicators") or data.get("indicator") or {}
        if ind:
            return f"# {host} — search-queries summary\n\n```json\n{ind}\n```"
        return f"# {host}\n\nNo queries returned."

    lines = [f"# {host} — top search queries ({len(queries)} of {total})", ""]
    lines.append("| # | Query | Shows | Clicks | CTR | Avg pos. |")
    lines.append("|--:|---|--:|--:|--:|--:|")
    for i, q in enumerate(queries, 1):
        text = q.get("query_text") or q.get("text") or "—"
        ind = q.get("indicators", {})
        shows = ind.get("TOTAL_SHOWS", "—")
        clicks = ind.get("TOTAL_CLICKS", "—")
        ctr = ind.get("CTR")
        ctr_s = f"{ctr:.2%}" if isinstance(ctr, (int, float)) else (ctr or "—")
        pos = ind.get("AVG_CLICK_POSITION") or ind.get("AVG_SHOW_POSITION") or "—"
        lines.append(f"| {i} | {text} | {shows} | {clicks} | {ctr_s} | {pos} |")
    return "\n".join(lines)


def format_indexing_stats_markdown(data: Dict[str, Any], host: str) -> str:
    counts = data.get("counts") or {}
    history = data.get("history") or []
    lines = [f"# {host} — indexing stats", ""]
    if counts:
        lines.append("## Counts")
        for k, v in counts.items():
            lines.append(f"- **{k}:** {v}")
        lines.append("")
    if history:
        lines.append(f"## History ({len(history)} points)")
        lines.append("| Date | Searchable | Total |")
        lines.append("|---|--:|--:|")
        for p in history[-30:]:  # last 30 points
            d = p.get("date") or p.get("dt") or "?"
            sr = p.get("value") or p.get("searchable") or p.get("count") or "?"
            tot = p.get("total") or "—"
            lines.append(f"| {d} | {sr} | {tot} |")
    return "\n".join(lines)


def format_url_samples_markdown(data: Dict[str, Any], host: str, kind: str) -> str:
    samples = data.get("samples") or data.get("urls") or []
    count = data.get("count", len(samples))
    if not samples:
        return f"# {host} — {kind} samples\n\nNo URLs returned."
    lines = [f"# {host} — {kind} ({len(samples)} of {count})", ""]
    for s in samples:
        url = s.get("url") or s
        extra = ""
        if isinstance(s, dict):
            status = s.get("status") or s.get("state")
            if status:
                extra = f" — *{status}*"
        lines.append(f"- {url}{extra}")
    return "\n".join(lines)


def format_sitemaps_markdown(data: Dict[str, Any], host: str) -> str:
    items = data.get("sitemaps") or []
    if not items:
        return f"# {host} — sitemaps\n\nNo sitemaps registered."
    lines = [f"# {host} — sitemaps ({len(items)})", ""]
    lines.append("| URL | Last access | Searchable URLs | Errors |")
    lines.append("|---|---|--:|--:|")
    for s in items:
        url = s.get("sitemap_url") or s.get("url") or "?"
        last = s.get("last_access_date") or "—"
        searchable = s.get("searchable_urls_count", "—")
        errors = s.get("errors_count", "—")
        lines.append(f"| {url} | {last} | {searchable} | {errors} |")
    return "\n".join(lines)


def format_recrawl_quota_markdown(data: Dict[str, Any], host: str) -> str:
    return (
        f"# {host} — recrawl quota\n\n"
        f"- **Quota total:** {data.get('quota_total', data.get('quota', '?'))}\n"
        f"- **Quota remainder:** {data.get('quota_remainder', '?')}\n"
        f"- **Daily quota:** {data.get('daily_quota', '?')}\n"
    )


def format_sqi_history_markdown(data: Dict[str, Any], host: str) -> str:
    points = data.get("points") or data.get("history") or []
    if not points:
        return f"# {host} — ИКС history\n\nNo data returned."
    lines = [f"# {host} — ИКС history ({len(points)} points)", ""]
    lines.append("| Date | ИКС |")
    lines.append("|---|--:|")
    for p in points[-50:]:
        lines.append(f"| {p.get('date', '?')} | {p.get('value', '?')} |")
    return "\n".join(lines)


def format_external_links_summary_markdown(data: Dict[str, Any], host: str) -> str:
    links = data.get("links_count")
    domains = data.get("hosts_count") or data.get("domains_count")
    return (
        f"# {host} — external links summary\n\n"
        f"- **Total links:** {links if links is not None else '?'}\n"
        f"- **Unique domains:** {domains if domains is not None else '?'}\n"
    )
