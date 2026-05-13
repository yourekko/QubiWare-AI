"""Per-table AI 'wow' insights: OpenAI when configured, else deterministic rules."""

from __future__ import annotations

import hashlib
import html as html_lib
import os
import re
from typing import Optional

import pandas as pd
import streamlit as st


def _fmt_int(x) -> str:
    try:
        return f"{int(float(x)):,}"
    except (TypeError, ValueError):
        return str(x)


def _safe_col(df: pd.DataFrame, *names: str) -> Optional[pd.Series]:
    for n in names:
        if n in df.columns:
            return df[n]
    return None


def _apply_bold_escape(s) -> str:
    """Turn **label** into <strong> after escaping each segment."""
    if s is None:
        return ""
    s = str(s)
    parts = re.split(r"\*\*(.+?)\*\*", s)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append("<strong>" + html_lib.escape(part) + "</strong>")
        else:
            out.append(html_lib.escape(part))
    return "".join(out)


def format_wow_html(body: str) -> str:
    """Wrap plain-text insight (possibly with • bullets) in branded HTML."""
    t = (body or "").strip()
    if not t:
        t = "Review this table with your operations lead to validate next steps."
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    parts = []
    bullets = []
    for ln in lines:
        if ln.startswith("•") or (ln.startswith("-") and not ln.startswith("--")):
            inner = ln.lstrip("•").lstrip("-").strip()
            inner_html = _apply_bold_escape(inner)
            bullets.append(f'<li style="margin:4px 0;line-height:1.45;">{inner_html}</li>')
        else:
            if bullets:
                parts.append(
                    '<ul style="margin:8px 0 0 0;padding-left:18px;">' + "".join(bullets) + "</ul>"
                )
                bullets = []
            parts.append(f'<p style="margin:0 0 8px 0;line-height:1.5;">{_apply_bold_escape(ln)}</p>')
    if bullets:
        parts.append('<ul style="margin:8px 0 0 0;padding-left:18px;">' + "".join(bullets) + "</ul>")
    inner = "".join(parts) if parts else f'<p style="margin:0;">{html_lib.escape(t)}</p>'
    return (
        '<div class="qw-wow-insight">'
        '<div class="qw-wow-insight-head">'
        '<span class="qw-wow-dot"></span>'
        "<span>AI insight</span></div>"
        f'<div class="qw-wow-insight-body">{inner}</div></div>'
    )


def rule_based_wow(table_key: str, df: pd.DataFrame, title: str, subtitle: str) -> str:
    """Deterministic insight when OpenAI is off or fails."""
    if df is None or len(df) == 0:
        return (
            "This slice is empty — either your filters exclude everything or the dataset has no rows here. "
            "• **Next step:** widen filters or confirm upstream sync so intelligence can attach to live SKUs and orders."
        )

    n = len(df)
    key = table_key

    if key == "inv_low_stock":
        sku = _safe_col(df, "SKU", "sku_id")
        stc = _safe_col(df, "Stock", "current_stock")
        sup = _safe_col(df, "Supplier", "supplier_name")
        z = _safe_col(df, "Zone", "warehouse_zone")
        line1 = f"{n} SKUs sit at or below reorder — stockout risk is elevated until purchase orders land."
        b1 = f"**Procurement:** prioritize {sup.iloc[0] if sup is not None else 'top suppliers'} for the lowest on-hand SKUs (e.g. {sku.iloc[0] if sku is not None else 'see table'})."
        b2 = f"**Floor:** rebalance picks in {z.iloc[0] if z is not None else 'hot zones'} so fast movers do not stall outbound."
        if stc is not None and sku is not None:
            nums = pd.to_numeric(stc.astype(str).str.replace(",", "", regex=False), errors="coerce")
            if nums.notna().any():
                try:
                    i = nums.idxmin()
                    line1 = (
                        f"Tightest line is **{sku.loc[i]}** at about **{_fmt_int(stc.loc[i])}** units on hand — "
                        f"that SKU should headline today's buy list alongside {max(0, n - 1)} other low-stock lines."
                    )
                except (ValueError, TypeError, KeyError):
                    pass
        return f"{line1}\n• {b1}\n• {b2}"

    if key == "inv_overstock":
        line1 = f"{n} SKUs exceed ~85% of max stock — carrying cost and slot lock-in rise until you release units."
        return (
            f"{line1}\n"
            "• **Commercial:** run targeted promos or bundle offers on the heaviest overstock lines first.\n"
            "• **Network:** consider inter-facility transfer before ordering more inbound capacity."
        )

    if key == "inv_dead_stock":
        di = _safe_col(df, "Days Inactive", "days_inactive")
        mx = 0
        if di is not None and len(di):
            raw_mx = pd.to_numeric(di, errors="coerce").max()
            mx = int(raw_mx) if pd.notna(raw_mx) else 0
        return (
            f"{n} SKUs show no meaningful movement; longest idle stretch in view is about **{mx}** days.\n"
            "• **Cash:** freeze discretionary buys on these SKUs until disposition is agreed.\n"
            "• **Velocity:** pair liquidation with slotting changes so the same pattern does not repeat."
        )

    if key == "inv_fast_moving":
        ads = _safe_col(df, "Avg Daily Sales", "avg_daily_sales")
        sku = _safe_col(df, "SKU", "sku_id")
        top = sku.iloc[0] if sku is not None else "Top SKU"
        rate = ads.iloc[0] if ads is not None else "—"
        return (
            f"Velocity leaders like **{top}** (~**{rate}** units/day in this view) pull the warehouse rhythm — protect their inbound lane.\n"
            "• **Supply:** shorten review cycles for the top five movers so replenishment matches demand spikes.\n"
            "• **Labor:** stage pick faces closer to dispatch for these SKUs to compress cycle time."
        )

    if key == "inv_reorder":
        rq = _safe_col(df, "Reorder Qty", "recommended_reorder_qty")
        tot = int(pd.to_numeric(rq, errors="coerce").fillna(0).sum()) if rq is not None else 0
        return (
            f"Aggregate recommended buy is about **{_fmt_int(tot)}** units across **{n}** SKUs — capital and dock windows need alignment.\n"
            "• **Finance:** sequence POs by estimated cost and margin contribution in the table.\n"
            "• **Inbound:** book receiving slots before cut-offs so low-stock picks do not idle."
        )

    if key == "inv_dead_reason":
        r = _safe_col(df, "Reason", "dead_stock_reason")
        c = _safe_col(df, "Count", "count")
        if r is not None and c is not None and len(r):
            j = int(pd.to_numeric(c, errors="coerce").fillna(0).values.argmax())
            top = str(r.iloc[j])
            return (
                f"Root-cause concentration points to **{top}** as the dominant dead-stock driver in this cohort.\n"
                "• **Merch:** attack the top reason with pricing, kitting, or assortment fixes before generic clearance.\n"
                "• **Supplier:** where supplier quality appears, tighten inbound QC and returns clauses."
            )

    if key == "inv_dead_detail":
        return (
            f"{n} dead-stock lines carry measurable holding drag — use storage cost columns to rank burn-down.\n"
            "• **Ops:** start with highest total storage cost SKUs to free space and power spend.\n"
            "• **Expiry:** if perishables appear, calendar markdowns before write-offs hit margin."
        )

    if key == "inv_liquidation":
        return (
            f"{n} liquidation paths are modeled — recovery and strategy columns show where cash can be unlocked fastest.\n"
            "• **Sales:** assign owners to the largest recovery opportunities this week.\n"
            "• **Inventory:** track strategy execution so dead units do not quietly return to quiet corners."
        )

    if key == "inv_liquidation_strat_dist":
        return (
            "Strategy mix shows how you plan to exit dead capital — keep the portfolio balanced between speed and margin.\n"
            "• **Governance:** cap share of deep-discount routes if margin erosion is a board concern.\n"
            "• **Reporting:** revisit this distribution monthly as sell-through proves out."
        )

    if key == "inv_resource_zones":
        st_col = _safe_col(df, "Status", "status")
        crit = int((st_col == "Critical").sum()) if st_col is not None else 0
        return (
            f"{crit} zone(s) in this table show **Critical** utilization — energy and dead units compound cost there first.\n"
            "• **Network:** consolidate slow movers out of critical zones before approving capex for new space.\n"
            "• **Sustainability:** pair energy-heavy zones with dispatch smoothing to lower run-hours per unit shipped."
        )

    if key == "disp_delayed":
        dd = _safe_col(df, "Delay (days)", "delay_days")
        mx = 0
        if dd is not None:
            raw_mx = pd.to_numeric(dd, errors="coerce").max()
            mx = int(raw_mx) if pd.notna(raw_mx) else 0
        cust = _safe_col(df, "Customer", "customer_name")
        cust0 = str(cust.iloc[0]) if cust is not None and len(cust) else "top customers"
        return (
            f"{n} delayed orders; worst slip in view is about **{mx}** days — customer promise drift is visible.\n"
            "• **Control tower:** daily huddle on the top delay days until backlog clears.\n"
            f"• **CX:** proactive outreach for **{cust0}** where delays cluster."
        )

    if key == "disp_pending":
        return (
            f"{n} pending dispatches are cash in limbo — each day adds working-capital drag and SLA risk.\n"
            "• **Planning:** sequence by promised date and priority flags in the table.\n"
            "• **Yard:** align loading bays with pending clusters to avoid rehandles."
        )

    if key == "disp_picking":
        err = _safe_col(df, "Total Errors", "total_errors")
        pk = _safe_col(df, "Picker Name", "picker_name")
        if err is not None and pk is not None:
            i = err.astype(str).str.replace(",", "", regex=False)
            i = pd.to_numeric(i, errors="coerce").fillna(0).idxmax()
            return (
                f"Picking errors concentrate — **{pk.loc[i]}** shows the highest error load in this summary.\n"
                "• **Training:** short refresher plus zone audit for the worst two pickers by errors.\n"
                "• **Engineering:** validate barcode scans and pick-path signage before blaming speed."
            )

    if key == "disp_bay":
        bay = _safe_col(df, "Loading Bay", "loading_bay", "Loading bay")
        tm = _safe_col(df, "Avg Time", "avg_time")
        if bay is not None and tm is not None:
            i = pd.to_numeric(tm, errors="coerce").fillna(0).idxmax()
            return (
                f"**{bay.loc[i]}** shows the slowest average turnaround in this bay set — dock scheduling is the lever.\n"
                "• **Flow:** stagger vehicle arrivals to reduce queueing at that bay.\n"
                "• **Maintenance:** check equipment and pallet exchange cycles on the slowest bay first."
            )

    if key == "disp_delay_causes":
        return (
            "Delay reasons quantify where the network stutters — fix the top two causes before adding capacity.\n"
            "• **Ops design:** assign owners per root cause with weekly reduction targets.\n"
            "• **Supplier:** where inbound or vendor delay dominates, tighten lead-time buffers."
        )

    if key == "disp_error_types":
        return (
            "Error-type frequency shows whether training, master data, or layout drives defects.\n"
            "• **Quality:** Pareto the top two error types for immediate corrective action.\n"
            "• **Systems:** if mis-pick clusters on certain SKUs, validate dimensions and pick locations."
        )

    if key == "disp_bay_rank":
        return (
            "Efficiency score ranks bays for where dispatch is smooth vs friction — copy playbooks from the top bay.\n"
            "• **Benchmark:** compare labor mix and slot distance between best and worst bays.\n"
            "• **Investment:** target automation where low scores persist after staffing fixes."
        )

    if key == "disp_route":
        return (
            "Route economics tie distance, delay percent, and vehicle choice — optimize where delay percent and cost intersect.\n"
            "• **Transport:** redeploy vehicle types suggested for congested routes first.\n"
            "• **Customer:** communicate realistic cut-offs on routes with highest delay percentages."
        )

    if key == "disp_customer":
        cust = _safe_col(df, "Customer", "customer_name")
        c0 = str(cust.iloc[0]) if cust is not None and len(cust) else "Top account"
        return (
            f"**{c0}** leads delayed-order exposure in this ranking — relationship risk scales with repeated misses.\n"
            "• **Recovery:** offer expedited handling on the next order plus executive visibility.\n"
            "• **Root cause:** map this customer's SKUs to delay reasons to avoid generic apologies."
        )

    if key == "zone_transport":
        return (
            "Zone transport intelligence links vehicle policy, congestion, and revenue upside — use it to prioritize network bets.\n"
            "• **Revenue:** test throughput uplift scenarios on zones flagged as constrained but high revenue potential.\n"
            "• **Compliance:** align allowed vehicle types with local access rules before promising faster cycles."
        )

    if key == "zone_master":
        st_col = _safe_col(df, "Status", "status")
        crit = int((st_col == "Critical").sum()) if st_col is not None else 0
        return (
            f"{crit} zone(s) are in **Critical** utilization in master data — expansion vs productivity is the decision.\n"
            "• **Capacity:** validate used vs capacity weekly; defer inbound marketing bursts if critical persists.\n"
            "• **People:** align shift patterns in critical zones with pick waves to avoid overtime spirals."
        )

    return (
        f"{title} — {subtitle}\n"
        f"• **Snapshot:** {n} rows in view; scan extremes in highlighted columns for where to act first.\n"
        "• **Next step:** export this slice for a 15-minute stand-up with warehouse and transport leads."
    )


def _fetch_openai_table_insight(table_key: str, title: str, subtitle: str, csv_snippet: str) -> str:
    """Uncached OpenAI call (caller caches via session_state)."""
    import openai

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return ""
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    client = openai.OpenAI(api_key=api_key)
    system = (
        "You are QubiWare AI, a warehouse intelligence copilot. Given a small CSV table excerpt, "
        "write a compelling executive insight for a client demo.\n"
        "Rules: max 90 words. First line: one punchy sentence with a concrete hook using numbers from the data when possible. "
        "Then exactly two lines starting with the bullet character • (unicode bullet). "
        "Each bullet may start with **ShortLabel:** then advice. No markdown headings (#). "
        "Do not invent SKUs, customers, or numbers not present in the CSV. If data is thin, say so briefly."
    )
    user = (
        f"TABLE_ID: {table_key}\nTITLE: {title}\nSUBTITLE: {subtitle}\n"
        f"ROWS_CSV:\n{csv_snippet}\n"
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=260,
        temperature=0.35,
    )
    raw = resp.choices[0].message.content
    if raw is None:
        return ""
    if isinstance(raw, list):
        parts = []
        for block in raw:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text") or "")
            else:
                parts.append(getattr(block, "text", str(block)))
        return "".join(parts).strip()
    return str(raw).strip()


def get_table_wow_html(table_key: str, title: str, subtitle: str, df: pd.DataFrame) -> str:
    """Return HTML block to pass as wow_insight_html to df_to_styled_table."""
    try:
        return _get_table_wow_html_impl(table_key, title, subtitle, df)
    except Exception:
        return format_wow_html(
            "AI insight could not be generated for this table in this session.\n"
            "• **Action:** refresh the page or set TABLE_WOW_DISABLE_OPENAI=1 to use rule-only insights.\n"
            "• **Verify:** OPENAI_API_KEY in Secrets and that the latest app commit is deployed."
        )


def _get_table_wow_html_impl(table_key: str, title: str, subtitle: str, df: pd.DataFrame) -> str:
    if df is None:
        return format_wow_html(rule_based_wow(table_key, pd.DataFrame(), title, subtitle))

    if len(df) == 0:
        return format_wow_html(rule_based_wow(table_key, df, title, subtitle))

    snippet = df.head(22).to_csv(index=False)
    if len(snippet) > 12000:
        snippet = snippet[:12000]
    digest = hashlib.md5(f"{table_key}|{snippet}".encode()).hexdigest()

    if "_table_wow_cache_v1" not in st.session_state:
        st.session_state["_table_wow_cache_v1"] = {}
    bucket = st.session_state["_table_wow_cache_v1"]
    cache_key = f"{table_key}:{digest}"
    if cache_key in bucket:
        return bucket[cache_key]

    disable = os.environ.get("TABLE_WOW_DISABLE_OPENAI", "").lower() in ("1", "true", "yes")
    if os.environ.get("OPENAI_API_KEY", "").strip() and not disable:
        try:
            ai_text = _fetch_openai_table_insight(table_key, title, subtitle, snippet)
            if ai_text and len(ai_text) > 25:
                html = format_wow_html(ai_text)
                bucket[cache_key] = html
                return html
        except Exception:
            pass

    html = format_wow_html(rule_based_wow(table_key, df, title, subtitle))
    bucket[cache_key] = html
    return html
