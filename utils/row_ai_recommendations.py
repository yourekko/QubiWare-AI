"""Per-row AI-style recommendations for intelligence tables (rules + optional OpenAI batch)."""

from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Optional

import pandas as pd
import streamlit as st

COL = "AI Recommendation"


def _clip(s: str, max_len: int = 118) -> str:
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def _num(x: Any) -> float:
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return float("nan")
        return float(str(x).replace(",", "").replace("INR", "").strip())
    except (TypeError, ValueError):
        return float("nan")


def _fmt_int(x: float) -> str:
    try:
        return f"{int(abs(x)):,}"
    except (TypeError, ValueError):
        return "0"


def _rule_fast_moving(r: pd.Series) -> str:
    s = _num(r.get("Stock"))
    o = _num(r.get("Reorder Lvl"))
    ads = _num(r.get("Avg Daily Sales"))
    if pd.isna(s) or pd.isna(o):
        return _clip("Validate stock and reorder master data for this SKU.")
    if pd.isna(ads) or ads <= 0:
        return _clip("High listing velocity but missing demand signal — confirm sales feed.")
    cover = s / ads
    if s <= o:
        return _clip("At or below reorder — raise PO or inbound transfer before stockout risk hits OTIF.")
    if s <= o * 1.12:
        return _clip("Within ~12% of reorder — align supplier dates; this mover can drain fast.")
    if cover < 5:
        return _clip(f"~{cover:.0f}d cover at current pace — treat as sprint SKU for inbound and pick-face.")
    if cover < 14:
        return _clip(f"~{cover:.0f}d cover — weekly demand check; keep buffer for promo spikes.")
    return _clip(f"~{cover:.0f}d cover — buffer is healthy; optimize slotting toward dispatch if travel is high.")


def _rule_low_stock(r: pd.Series) -> str:
    s = _num(r.get("Stock"))
    o = _num(r.get("Reorder Lvl"))
    mx = _num(r.get("Max Stock"))
    if pd.isna(s) or pd.isna(o):
        return _clip("Confirm on-hand and reorder parameters in WMS for this line.")
    gap = s - o
    if s <= 0:
        return _clip("Zero or negative on-hand in view — immediate backorder / substitution review.")
    if gap <= 0:
        short = o - s
        return _clip(f"Below/equal reorder by ~{_fmt_int(short)} units — expedite PO and protect pick wave.")
    if mx and not pd.isna(mx) and s < mx * 0.25:
        return _clip("Low vs max target — once replenished, rebuild safety stock toward max policy.")
    return _clip("Slightly above reorder but still in risk band — do not cancel inbound yet.")


def _rule_overstock(r: pd.Series) -> str:
    s = _num(r.get("Stock"))
    mx = _num(r.get("Max Stock"))
    if pd.isna(s) or pd.isna(mx) or mx <= 0:
        return _clip("Compare stock vs max policy to decide transfer vs promotion.")
    pct = s / mx
    if pct >= 0.98:
        return _clip("At/near max — freeze new buys; prioritize promo, bundle, or network transfer.")
    if pct >= 0.9:
        return _clip("Deep in upper band — rebalance to lighter zones before next inbound wave.")
    return _clip("Above policy threshold — review forecast bias and supplier MOQs.")


def _rule_dead_row(r: pd.Series) -> str:
    d = _num(r.get("Days Inactive"))
    s = _num(r.get("Stock"))
    if pd.isna(d):
        return _clip("Stale movement signal — validate last scan / movement timestamps.")
    if d > 120:
        return _clip(f"{int(d)}d idle — strong liquidation or donation candidate after margin review.")
    if d > 90:
        return _clip(f"{int(d)}d idle — run targeted promo before slot becomes long-term dead.")
    return _clip(f"{int(d)}d idle — pair with sales push or kitting before write-down.")


def _rule_reorder(r: pd.Series) -> str:
    q = _num(r.get("Reorder Qty"))
    s = _num(r.get("Stock"))
    mx = _num(r.get("Max"))
    if not pd.isna(q) and q >= 500:
        return _clip("Large recommended buy — coordinate dock labor, pallets, and supplier lead time.")
    if not pd.isna(q) and q > 0 and not pd.isna(mx) and not pd.isna(s):
        headroom = mx - s
        if headroom > 0 and q / headroom > 0.85:
            return _clip("Buy pushes toward max — confirm financing and slow-mover risk before approving.")
    if not pd.isna(q) and q > 0:
        return _clip("Execute PO in line with criticality; stagger receipts if cash is tight this week.")
    return _clip("Validate reorder math against lead time and demand before releasing to procurement.")


def _rule_liquidation_row(r: pd.Series) -> str:
    strat = str(r.get("Strategy", "") or "")
    if "Discount" in strat or "discount" in strat:
        return _clip("Price-led exit — guard margin floor and channel conflict with retail partners.")
    if "Bundle" in strat or "bundle" in strat:
        return _clip("Bundle-led recovery — pair with hero SKU to lift attach rate in outbound.")
    if "Return" in strat or "return" in strat:
        return _clip("Supplier return path — document QC evidence to shorten dispute cycles.")
    return _clip("Track execution weekly until line clears or strategy is revised.")


def _rule_resource_zone(r: pd.Series) -> str:
    stt = str(r.get("Status", "") or "")
    dead = _num(r.get("Dead stock units"))
    if "Critical" in stt:
        return _clip("Critical utilization — dead units here burn the most expensive space; clear first.")
    if not pd.isna(dead) and dead > 20:
        return _clip("Meaningful dead stock in zone — slotting review plus outbound push for these SKUs.")
    return _clip("Watch energy and labor per unit — keep throughput aligned with cost curve.")


def _rule_delayed_order(r: pd.Series) -> str:
    dd = _num(r.get("Delay (days)"))
    pr = str(r.get("Priority", "") or "")
    if not pd.isna(dd) and dd >= 7:
        return _clip(f"{int(dd)}d late — executive recovery path; protect customer promise on next wave.")
    if pr == "High":
        return _clip("High priority delay — assign expeditor and dock window within 24h.")
    return _clip("Re-sequence pick and pack with carrier cut-offs; communicate revised ETA early.")


def _rule_pending_order(r: pd.Series) -> str:
    return _clip("Pending dispatch — confirm inventory allocation and bay slot before carrier booking.")


def _rule_picker_row(r: pd.Series) -> str:
    err = _num(r.get("Total Errors"))
    picks = _num(r.get("Total Picks")) if "Total Picks" in r.index else _num(r.get("Total picks"))
    if not pd.isna(err) and err >= 8:
        return _clip("Elevated errors — shadow pick + barcode audit before adding volume.")
    if not pd.isna(err) and not pd.isna(picks) and picks > 0 and err / picks > 0.02:
        return _clip("Error rate above ~2% — review pick path and SKU master dimensions.")
    return _clip("Within tolerance — keep coaching cadence and rotate fatigue-prone zones.")


def _rule_bay_row(r: pd.Series) -> str:
    t = _num(r.get("Avg Time")) if "Avg Time" in r.index else _num(r.get("Avg Time (min)"))
    e = _num(r.get("Total Errors"))
    if not pd.isna(t) and t >= 45:
        return _clip("High average dwell — stagger vehicle arrivals and pre-stage pallets.")
    if not pd.isna(e) and e >= 5:
        return _clip("Error cluster at bay — check equipment calibration and yard signage.")
    return _clip("Stable bay — copy staffing template to slower peers.")


def _rule_dead_detail_row(r: pd.Series) -> str:
    cost = _num(r.get("Total Storage Cost"))
    days = _num(r.get("Days Inactive")) if "Days Inactive" in r.index else _num(r.get("Days inactive"))
    if not pd.isna(cost) and cost > 5000:
        return _clip("High storage burn — prioritize clearance or slot relocation to cut daily carry.")
    if not pd.isna(days) and days > 90:
        return _clip("Long idle plus cost exposure — pair finance sign-off with exit strategy.")
    return _clip("Quantify carrying cost weekly until line is dispositioned.")


def _rule_dead_reason_agg(r: pd.Series) -> str:
    reason = str(r.get("Reason", r.get("reason", "")) or "this driver")
    c = int(_num(r.get("Count"))) if not pd.isna(_num(r.get("Count"))) else 0
    return _clip(f"Pareto focus on {reason} ({c} SKUs) — assign owner and 30-day reduction target.")


def _rule_strat_dist_row(r: pd.Series) -> str:
    strat = str(r.get("Strategy", "") or "")
    n = int(_num(r.get("Items"))) if not pd.isna(_num(r.get("Items"))) else 0
    return _clip(f"Execute {strat} playbook across {n} SKUs — track sell-through vs plan weekly.")


def _rule_delay_cause_row(r: pd.Series) -> str:
    reason = str(r.get("Delay Reason", r.get("Delay reason", "")) or "this cause")
    c = int(_num(r.get("Count"))) if not pd.isna(_num(r.get("Count"))) else 0
    if c >= 15:
        return _clip(f"{reason} is systemic ({c}) — war-room with carrier + inbound leads.")
    return _clip(f"{reason} ({c}) — document fixes in SOP and measure next week's delta.")


def _rule_error_type_row(r: pd.Series) -> str:
    et = str(r.get("Error Type", r.get("Error type", "")) or "this defect")
    return _clip(f"Tighten controls for {et} — root-cause five whys then pilot countermeasure on one zone.")


def _rule_bay_rank_row(r: pd.Series) -> str:
    sc = _num(r.get("Efficiency Score"))
    if not pd.isna(sc) and sc >= 85:
        return _clip("Top-quartile bay — export playbook (labor mix, staging) to laggards.")
    if not pd.isna(sc) and sc < 60:
        return _clip("Low score — time-motion study plus equipment check before adding headcount.")
    return _clip("Middle of fleet — benchmark against best bay on cost per dispatch.")


def _rule_route_row(r: pd.Series) -> str:
    dp = _num(r.get("Delay Pct")) if "Delay Pct" in r.index else _num(r.get("Delay pct"))
    if not pd.isna(dp) and dp >= 25:
        return _clip("High delay % on route — revisit vehicle type and cut-off promises with transport.")
    return _clip("Stabilize route plan with dynamic buffers where congestion is seasonal.")


def _rule_customer_row(r: pd.Series) -> str:
    d = _num(r.get("Delayed Orders"))
    if not pd.isna(d) and d >= 5:
        return _clip("Heavy delay load — assign named recovery owner and weekly exec readout.")
    return _clip("Protect relationship with proactive ETAs and service credit policy clarity.")


def _rule_zone_transport_row(r: pd.Series) -> str:
    st = str(r.get("Status", "") or "")
    if "Critical" in st:
        return _clip("Critical zone — align vehicle policy with throughput before promising faster cycles.")
    return _clip("Tune revenue levers only after congestion and vehicle fit are validated.")


def _rule_zone_master_row(r: pd.Series) -> str:
    st = str(r.get("Status", "") or "")
    if "Critical" in st:
        return _clip("Critical utilization — defer discretionary inbound and rebalance before capex.")
    return _clip("Monitor weekly; keep pick waves matched to staffing to avoid overtime drift.")


def _rule_generic_inventory(r: pd.Series) -> str:
    return _clip("Use highlighted metrics to prioritize stand-up actions for this line.")


_RULE_DISPATCH = {
    "disp_delayed": _rule_delayed_order,
    "disp_pending": _rule_pending_order,
    "disp_picking": _rule_picker_row,
    "disp_bay": _rule_bay_row,
}


def _apply_rules(df: pd.DataFrame, table_key: str) -> pd.Series:
    if table_key == "inv_fast_moving":
        return df.apply(_rule_fast_moving, axis=1)
    if table_key == "inv_low_stock":
        return df.apply(_rule_low_stock, axis=1)
    if table_key == "inv_overstock":
        return df.apply(_rule_overstock, axis=1)
    if table_key == "inv_dead_stock":
        return df.apply(_rule_dead_row, axis=1)
    if table_key == "inv_reorder":
        return df.apply(_rule_reorder, axis=1)
    if table_key == "inv_liquidation":
        return df.apply(_rule_liquidation_row, axis=1)
    if table_key == "inv_resource_zones":
        return df.apply(_rule_resource_zone, axis=1)
    if table_key == "inv_dead_detail":
        return df.apply(_rule_dead_detail_row, axis=1)
    if table_key == "inv_dead_reason":
        return df.apply(_rule_dead_reason_agg, axis=1)
    if table_key == "inv_strat_dist":
        return df.apply(_rule_strat_dist_row, axis=1)
    if table_key == "disp_delay_causes":
        return df.apply(_rule_delay_cause_row, axis=1)
    if table_key == "disp_error_types":
        return df.apply(_rule_error_type_row, axis=1)
    if table_key == "disp_bay_rank":
        return df.apply(_rule_bay_rank_row, axis=1)
    if table_key == "disp_route":
        return df.apply(_rule_route_row, axis=1)
    if table_key == "disp_customer":
        return df.apply(_rule_customer_row, axis=1)
    if table_key == "zone_transport":
        return df.apply(_rule_zone_transport_row, axis=1)
    if table_key == "zone_master":
        return df.apply(_rule_zone_master_row, axis=1)
    fn = _RULE_DISPATCH.get(table_key)
    if fn:
        return df.apply(fn, axis=1)
    return df.apply(_rule_generic_inventory, axis=1)


def _batch_openai_row_texts(table_key: str, df: pd.DataFrame, sku_col: str = "SKU") -> Optional[dict[str, str]]:
    if os.environ.get("ROW_AI_OPENAI_BATCH", "").lower() not in ("1", "true", "yes"):
        return None
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    if sku_col not in df.columns or len(df) == 0:
        return None
    import openai

    take = df.head(25).copy()
    csv_blob = take.to_csv(index=False)
    digest = hashlib.md5(f"{table_key}|rowbatch|{csv_blob}".encode()).hexdigest()
    if "_row_ai_batch_cache_v1" not in st.session_state:
        st.session_state["_row_ai_batch_cache_v1"] = {}
    cache = st.session_state["_row_ai_batch_cache_v1"]
    ck = f"{table_key}:{digest}"
    if ck in cache:
        return cache[ck]

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    client = openai.OpenAI(api_key=key)
    sys = (
        "You are QubiWare warehouse AI. Given CSV rows, output a single JSON object whose keys are "
        f"exact values from the {sku_col!r} column and values are one short recommendation (max 130 chars), "
        "operations tone, no markdown, use only facts from that row. Cover every row in the CSV."
    )
    user = f"TABLE_ID: {table_key}\nCSV:\n{csv_blob[:11000]}\n"
    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        max_tokens=1200,
        temperature=0.25,
    )
    raw = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            return None
        data = json.loads(m.group(0))
    if not isinstance(data, dict):
        return None
    out = {str(k): _clip(str(v)) for k, v in data.items()}
    cache[ck] = out
    return out


def add_per_row_ai_recommendation(df: pd.DataFrame, table_key: str, sku_col: str = "SKU") -> pd.DataFrame:
    """Append COL with rule-based text; optionally overwrite from OpenAI JSON batch (ROW_AI_OPENAI_BATCH=1)."""
    if df is None or len(df) == 0:
        return df
    out = df.copy()
    if COL in out.columns:
        out = out.drop(columns=[COL])
    try:
        series = _apply_rules(out, table_key)
        out[COL] = series.map(_clip)
    except Exception:
        out[COL] = _clip("Recommendation unavailable for this row shape.")
    try:
        oai = _batch_openai_row_texts(table_key, out, sku_col=sku_col)
        if oai and sku_col in out.columns:
            mapped = out[sku_col].astype(str).map(oai)
            out[COL] = mapped.where(mapped.notna(), out[COL])
    except Exception:
        pass
    return out
