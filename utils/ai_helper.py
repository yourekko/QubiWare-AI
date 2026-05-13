"""AI CoPilot helper for QubiWare AI."""

import os
from datetime import datetime

import pandas as pd

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


SYSTEM_PROMPT = """You are QubiWare AI CoPilot, an intelligent warehouse operations assistant.
You help warehouse managers, logistics teams, and operations heads make data-driven decisions.

You have access to warehouse data including inventory, orders, dispatch, zone utilization,
and inbound shipment information.

RESPONSE FORMAT INSTRUCTIONS:
- Always structure responses with clear sections using markdown headers (##, ###)
- Use markdown tables (| col1 | col2 |) for any data that has multiple attributes
- Use **bold** for key metrics and numbers
- Use bullet points for lists of items
- Start with a brief executive summary
- Include a "Recommended Actions" section at the end with numbered steps
- Keep responses professional and concise
- Format numbers with commas for readability"""


def build_data_context(data):
    """Build a context string from dataframes for AI consumption."""
    from utils.analytics import (
        get_low_stock_items, get_overstock_items, get_dead_stock_items,
        get_delayed_orders, get_pending_orders, get_zone_utilization,
        get_picking_errors_by_picker, get_dispatch_by_bay,
        get_inbound_mismatches, get_supplier_issues, compute_kpis,
        get_dead_stock_analysis, get_delay_root_causes,
        get_route_efficiency, get_zone_transport_analysis, get_customer_impact
    )

    inv = data["inventory"]
    orders = data["orders"]
    zones = data["zones"]
    picking = data["picking"]
    inbound = data["inbound"]

    kpis = compute_kpis(data)
    low_stock = get_low_stock_items(inv)
    overstock = get_overstock_items(inv)
    dead_stock = get_dead_stock_items(inv)
    delayed = get_delayed_orders(orders)
    pending = get_pending_orders(orders)
    zone_util = get_zone_utilization(zones)
    picker_errors = get_picking_errors_by_picker(picking)
    bay_stats = get_dispatch_by_bay(picking)
    mismatches = get_inbound_mismatches(inbound)
    supplier_issues = get_supplier_issues(inbound)

    context = f"""
WAREHOUSE DATA SUMMARY (as of {datetime.now().strftime('%Y-%m-%d')}):

KPIs:
- Total SKUs: {kpis['Total SKUs']}
- Total Orders: {kpis['Total Orders']}
- Low Stock Items: {kpis['Low Stock Items']}
- Overstock Items: {kpis['Overstock Items']}
- Delayed Orders: {kpis['Delayed Orders']}
- Pending Dispatches: {kpis['Pending Dispatches']}
- Avg Delay Days: {kpis['Avg Delay Days']}
- Warehouse Utilization: {kpis['Warehouse Utilization %']}%
- Picking Accuracy: {kpis['Picking Accuracy %']}%
- Inbound Mismatches: {kpis['Inbound Mismatch Count']}

LOW STOCK ITEMS (top 10):
{low_stock[['sku_id', 'product_name', 'current_stock', 'reorder_level', 'supplier_name']].head(10).to_string(index=False)}

OVERSTOCK ITEMS (top 10):
{overstock[['sku_id', 'product_name', 'current_stock', 'max_stock', 'warehouse_zone']].head(10).to_string(index=False)}

DEAD STOCK (top 10):
{dead_stock[['sku_id', 'product_name', 'last_movement_date', 'current_stock']].head(10).to_string(index=False)}

DELAYED ORDERS (top 10):
{delayed[['order_id', 'customer_name', 'sku_id', 'delay_days', 'warehouse_zone', 'priority']].head(10).to_string(index=False)}

ZONE UTILIZATION:
{zone_util[['zone_id', 'zone_name', 'utilization_pct', 'status']].to_string(index=False)}

PICKER PERFORMANCE:
{picker_errors[['picker_name', 'total_errors', 'total_picks']].head(10).to_string(index=False)}

LOADING BAY STATS:
{bay_stats[['loading_bay', 'avg_time', 'total_dispatches', 'total_errors']].to_string(index=False)}

SUPPLIER ISSUES:
{supplier_issues[['supplier_name', 'mismatch_count', 'total_shortage']].head(10).to_string(index=False)}

INVENTORY BY CATEGORY:
{inv.groupby('category')['current_stock'].agg(['count', 'sum']).reset_index().to_string(index=False)}

ORDERS BY STATUS:
{orders['status'].value_counts().to_string()}
"""

    try:
        dead_analysis = get_dead_stock_analysis(inv)
        if len(dead_analysis) > 0:
            reason_summary = dead_analysis.groupby("dead_stock_reason").size().reset_index(name="count").sort_values("count", ascending=False)
            context += f"\nDEAD STOCK ROOT CAUSES:\n{reason_summary.to_string(index=False)}\n"
            if "total_storage_cost" in dead_analysis.columns:
                context += f"- Total dead stock storage cost (estimated): {dead_analysis['total_storage_cost'].sum():,.0f}\n"
            if "is_expired" in dead_analysis.columns:
                context += f"- Expired SKUs (expiry-based): {int(dead_analysis['is_expired'].sum())}\n"
    except Exception:
        pass

    try:
        delay_rc = get_delay_root_causes(orders)
        if len(delay_rc) > 0:
            context += f"\nDELAY ROOT CAUSES (aggregated):\n{delay_rc.to_string(index=False)}\n"
    except Exception:
        pass

    try:
        routes = get_route_efficiency(data)
        if len(routes) > 0:
            rcols = [c for c in ["route_id", "route_name", "avg_cost", "delay_pct", "delayed", "orders", "best_vehicle", "congestion_level"] if c in routes.columns]
            context += f"\nROUTE EFFICIENCY:\n{routes[rcols].head(12).to_string(index=False)}\n"
    except Exception:
        pass

    try:
        zt = get_zone_transport_analysis(data)
        if len(zt) > 0:
            zt_cols = ["zone_name", "status", "utilization_pct", "allowed_vehicle_types", "revenue_potential_per_day", "expected_critical_until"]
            avail_cols = [c for c in zt_cols if c in zt.columns]
            context += f"\nZONE TRANSPORT & PREDICTIONS:\n{zt[avail_cols].to_string(index=False)}\n"
    except Exception:
        pass

    try:
        cust = get_customer_impact(orders)
        if len(cust) > 0:
            context += f"\nTOP IMPACTED CUSTOMERS:\n{cust[['customer_name', 'delayed_orders', 'total_delay_days']].head(5).to_string(index=False)}\n"
    except Exception:
        pass

    return context


def ask_ai_gemini(question, context, api_key):
    """Query Gemini API using the new google.genai SDK."""
    client = genai.Client(api_key=api_key)
    prompt = f"{SYSTEM_PROMPT}\n\nDATA CONTEXT:\n{context}\n\nUSER QUESTION: {question}"
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text


def ask_ai_openai(question, context, api_key):
    """Query OpenAI API."""
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"DATA CONTEXT:\n{context}\n\nQUESTION: {question}"}
        ],
        max_tokens=1000,
        temperature=0.3
    )
    return response.choices[0].message.content


def _ai_html_panel(title, icon_color, body_html):
    """Wrap AI response in a premium styled panel."""
    return (
        f'<div style="background:white;border:1px solid #E5E7EB;border-radius:14px;overflow:hidden;box-shadow:0 4px 6px -1px rgba(0,0,0,0.07);margin:8px 0;">'
        f'<div style="background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);padding:14px 20px;display:flex;align-items:center;gap:10px;">'
        f'<div style="width:28px;height:28px;background:{icon_color};border-radius:8px;display:flex;align-items:center;justify-content:center;">'
        f'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg></div>'
        f'<div style="font-size:0.85rem;font-weight:700;color:white;">{title}</div></div>'
        f'<div style="padding:16px 20px;">{body_html}</div>'
        f'<div style="background:#F8FAFC;padding:8px 20px;border-top:1px solid #E5E7EB;font-size:0.65rem;color:#9CA3AF;">QubiWare AI CoPilot &middot; Qubithm Corporation LLP</div>'
        f'</div>'
    )


def _ai_kpi_row(items):
    """Small KPI strip inside AI response."""
    h = '<div style="display:flex;gap:0;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden;margin-bottom:14px;">'
    for i, (val, lab, col) in enumerate(items):
        border = 'border-right:1px solid #E5E7EB;' if i < len(items) - 1 else ''
        h += f'<div style="flex:1;padding:10px 14px;text-align:center;{border}"><div style="font-size:1.1rem;font-weight:800;color:{col};">{val}</div><div style="font-size:0.6rem;color:#9CA3AF;font-weight:600;text-transform:uppercase;letter-spacing:0.3px;margin-top:1px;">{lab}</div></div>'
    h += '</div>'
    return h


def _ai_mini_table(headers, rows, colors=None):
    """Compact styled table for AI responses."""
    h = '<table style="width:100%;border-collapse:collapse;font-size:0.78rem;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden;margin-bottom:12px;">'
    h += '<thead><tr style="background:#F8FAFC;">'
    for hdr in headers:
        h += f'<th style="padding:8px 12px;text-align:left;font-weight:700;color:#64748B;font-size:0.66rem;text-transform:uppercase;letter-spacing:0.4px;border-bottom:2px solid #E5E7EB;">{hdr}</th>'
    h += '</tr></thead><tbody>'
    for i, row in enumerate(rows):
        bg = '#FFFFFF' if i % 2 == 0 else '#F8FAFC'
        h += f'<tr style="background:{bg};">'
        for j, val in enumerate(row):
            color = colors[j] if colors and j < len(colors) else '#374151'
            fw = '600' if j == 0 else '400'
            h += f'<td style="padding:7px 12px;color:{color};font-weight:{fw};border-bottom:1px solid #F3F4F6;">{val}</td>'
        h += '</tr>'
    h += '</tbody></table>'
    return h


def _ai_action_list(actions):
    """Numbered action items for AI responses."""
    h = '<div style="margin-top:6px;">'
    urgency_colors = ["#EF4444", "#F59E0B", "#2563EB", "#8B5CF6", "#10B981", "#06B6D4"]
    for i, action in enumerate(actions):
        c = urgency_colors[i % len(urgency_colors)]
        h += (
            f'<div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:6px;">'
            f'<div style="width:22px;height:22px;background:{c};color:white;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:0.65rem;font-weight:700;flex-shrink:0;">{i+1}</div>'
            f'<div style="font-size:0.8rem;color:#374151;line-height:1.5;padding-top:1px;">{action}</div></div>'
        )
    h += '</div>'
    return h


def _ai_section_label(text, color="#111827"):
    return f'<div style="font-size:0.68rem;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:0.8px;margin:14px 0 8px 0;display:flex;align-items:center;gap:6px;"><div style="width:5px;height:5px;border-radius:50%;background:{color};"></div>{text}</div>'


def ask_ai_fallback(question, data):
    """Rule-based fallback with rich HTML formatting."""
    from utils.analytics import (
        get_low_stock_items, get_overstock_items, get_dead_stock_items,
        get_delayed_orders, get_zone_utilization, get_picking_errors_by_picker,
        get_dispatch_by_bay, get_inbound_mismatches, get_supplier_issues,
        compute_kpis
    )

    inv = data["inventory"]
    orders = data["orders"]
    zones = data["zones"]
    picking = data["picking"]
    inbound = data["inbound"]

    q = question.lower().strip()

    # ─── Greeting handling ───
    greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "howdy", "what's up", "sup", "yo"]
    if any(g == q.rstrip("!.?") for g in greetings):
        kpis = compute_kpis(data)
        body = f'<div style="font-size:0.88rem;color:#374151;line-height:1.6;margin-bottom:14px;">Hello! I\'m your warehouse intelligence assistant. Here\'s a quick snapshot of today\'s operations:</div>'
        body += _ai_kpi_row([
            (kpis['Low Stock Items'], "Low Stock", "#EF4444"),
            (kpis['Delayed Orders'], "Delayed", "#F59E0B"),
            (f"{kpis['Warehouse Utilization %']}%", "Utilization", "#8B5CF6"),
            (f"{kpis['Picking Accuracy %']}%", "Accuracy", "#10B981"),
        ])
        body += _ai_section_label("What would you like to know?", "#2563EB")
        body += '<div style="font-size:0.82rem;color:#4B5563;line-height:1.7;">Try asking me:<ul style="margin:6px 0;padding-left:18px;">'
        body += '<li>Which SKUs are at low-stock risk?</li>'
        body += '<li>Which warehouse zone is most congested?</li>'
        body += '<li>Which orders are delayed today?</li>'
        body += '<li>Generate a warehouse performance summary</li>'
        body += '</ul></div>'
        return _ai_html_panel("Welcome to QubiWare AI CoPilot", "linear-gradient(135deg,#2563EB,#06B6D4)", body)

    # ─── Off-topic / non-warehouse guardrail ───
    off_topic_signals = ["weather", "recipe", "movie", "song", "joke", "poem", "story",
                         "who are you", "what are you", "your name", "politics", "sports",
                         "cricket", "football", "game", "news", "how old"]
    if any(sig in q for sig in off_topic_signals):
        kpis = compute_kpis(data)
        body = '<div style="font-size:0.85rem;color:#374151;line-height:1.6;margin-bottom:12px;">I\'m QubiWare AI CoPilot, specialized in <strong>warehouse, inventory, and dispatch intelligence</strong>. I can only answer questions related to your warehouse operations data.</div>'
        body += _ai_section_label("Here's what I can help with:", "#2563EB")
        body += '<div style="font-size:0.82rem;color:#4B5563;line-height:1.8;"><ul style="margin:6px 0;padding-left:18px;">'
        body += '<li>Inventory health &mdash; low stock, overstock, dead stock, reorder</li>'
        body += '<li>Dispatch &mdash; delayed orders, pending shipments, bottlenecks</li>'
        body += '<li>Warehouse zones &mdash; utilization, congestion, capacity</li>'
        body += '<li>Operations &mdash; picking errors, loading bay performance</li>'
        body += '<li>Suppliers &mdash; inbound mismatches, shortage tracking</li>'
        body += '</ul></div>'
        body += _ai_kpi_row([
            (kpis['Low Stock Items'], "Low Stock", "#EF4444"),
            (kpis['Delayed Orders'], "Delayed", "#F59E0B"),
            (f"{kpis['Warehouse Utilization %']}%", "Utilization", "#8B5CF6"),
        ])
        return _ai_html_panel("QubiWare AI CoPilot &mdash; Warehouse Intelligence Only", "linear-gradient(135deg,#2563EB,#06B6D4)", body)

    # ─── Broad keyword matching for warehouse queries ───
    if "low stock" in q or "low-stock" in q or "reorder" in q or "stock risk" in q or "stockout" in q or "out of stock" in q or "running low" in q or "need to order" in q or "procurement" in q:
        low = get_low_stock_items(inv)
        body = _ai_kpi_row([(len(low), "Low Stock SKUs", "#EF4444"), (f"{len(inv)}", "Total SKUs", "#2563EB"), (f"{len(low)/len(inv)*100:.1f}%", "At Risk", "#8B5CF6")])
        body += _ai_section_label("Top Items Requiring Immediate Reorder", "#EF4444")
        rows = [[r['sku_id'], str(r['product_name'])[:25], int(r['current_stock']), int(r['reorder_level']), str(r['supplier_name'])[:18]] for _, r in low.head(10).iterrows()]
        body += _ai_mini_table(["SKU", "Product", "Stock", "Reorder Lvl", "Supplier"], rows, ['#111827', '#4B5563', '#EF4444', '#64748B', '#64748B'])
        body += _ai_section_label("Recommended Actions", "#2563EB")
        body += _ai_action_list([
            f"<strong>Initiate procurement</strong> for {len(low)} critical low-stock SKUs immediately to prevent stockouts",
            "<strong>Set up automated alerts</strong> for items approaching reorder level",
            "<strong>Review supplier lead times</strong> and adjust reorder levels for frequently low items"
        ])
        return _ai_html_panel("Low Stock Risk Analysis", "#EF4444", body)

    elif "overstock" in q or "over stock" in q or "excess stock" in q or "too much stock" in q or "surplus" in q or "overstocked" in q:
        over = get_overstock_items(inv)
        body = _ai_kpi_row([(len(over), "Overstocked", "#F59E0B"), (f"{len(inv)}", "Total SKUs", "#2563EB")])
        body += _ai_section_label("Top Overstocked Items", "#F59E0B")
        rows = [[r['sku_id'], str(r['product_name'])[:25], int(r['current_stock']), int(r['max_stock']), r['warehouse_zone']] for _, r in over.head(10).iterrows()]
        body += _ai_mini_table(["SKU", "Product", "Stock", "Max", "Zone"], rows, ['#111827', '#4B5563', '#F59E0B', '#64748B', '#64748B'])
        body += _ai_section_label("Recommended Actions", "#2563EB")
        body += _ai_action_list([
            f"<strong>Review {len(over)} overstock items</strong> for promotional clearance or redistribution",
            "<strong>Negotiate supplier returns</strong> for items with excessive surplus",
            "<strong>Adjust demand forecasting</strong> to prevent future overstock situations"
        ])
        return _ai_html_panel("Overstock Analysis", "#F59E0B", body)

    elif "congested" in q or "utilization" in q or "zone" in q or "capacity" in q or "space" in q or "full" in q or "warehouse space" in q or "congestion" in q:
        zone_util = get_zone_utilization(zones)
        critical = zone_util[zone_util["status"] == "Critical"]
        warning = zone_util[zone_util["status"] == "Warning"]
        body = _ai_kpi_row([
            (len(critical), "Critical", "#EF4444"),
            (len(warning), "Warning", "#F59E0B"),
            (f"{zone_util['utilization_pct'].mean():.1f}%", "Avg Util", "#8B5CF6"),
        ])
        body += _ai_section_label("Zone Status Overview", "#111827")
        rows = [[r['zone_name'], f"{r['utilization_pct']}%", f"{int(r['used_units']):,}", f"{int(r['capacity_units']):,}", r['status']] for _, r in zone_util.sort_values("utilization_pct", ascending=False).iterrows()]
        status_colors = {"Critical": "#EF4444", "Warning": "#F59E0B", "Normal": "#10B981"}
        h_t = '<table style="width:100%;border-collapse:collapse;font-size:0.78rem;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden;margin-bottom:12px;">'
        h_t += '<thead><tr style="background:#F8FAFC;"><th style="padding:8px 12px;text-align:left;font-weight:700;color:#64748B;font-size:0.66rem;text-transform:uppercase;letter-spacing:0.4px;border-bottom:2px solid #E5E7EB;">Zone</th><th style="padding:8px 12px;text-align:left;font-weight:700;color:#64748B;font-size:0.66rem;text-transform:uppercase;letter-spacing:0.4px;border-bottom:2px solid #E5E7EB;">Utilization</th><th style="padding:8px 12px;text-align:left;font-weight:700;color:#64748B;font-size:0.66rem;text-transform:uppercase;letter-spacing:0.4px;border-bottom:2px solid #E5E7EB;">Used</th><th style="padding:8px 12px;text-align:left;font-weight:700;color:#64748B;font-size:0.66rem;text-transform:uppercase;letter-spacing:0.4px;border-bottom:2px solid #E5E7EB;">Capacity</th><th style="padding:8px 12px;text-align:left;font-weight:700;color:#64748B;font-size:0.66rem;text-transform:uppercase;letter-spacing:0.4px;border-bottom:2px solid #E5E7EB;">Status</th></tr></thead><tbody>'
        for i, row in enumerate(rows):
            bg = '#FFFFFF' if i % 2 == 0 else '#F8FAFC'
            sc = status_colors.get(row[4], '#64748B')
            badge = f'<span style="background:{sc}12;color:{sc};font-size:0.68rem;font-weight:700;padding:2px 8px;border-radius:5px;">{row[4]}</span>'
            h_t += f'<tr style="background:{bg};"><td style="padding:7px 12px;font-weight:600;color:#111827;border-bottom:1px solid #F3F4F6;">{row[0]}</td><td style="padding:7px 12px;color:#8B5CF6;font-weight:700;border-bottom:1px solid #F3F4F6;">{row[1]}</td><td style="padding:7px 12px;color:#374151;border-bottom:1px solid #F3F4F6;">{row[2]}</td><td style="padding:7px 12px;color:#374151;border-bottom:1px solid #F3F4F6;">{row[3]}</td><td style="padding:7px 12px;border-bottom:1px solid #F3F4F6;">{badge}</td></tr>'
        h_t += '</tbody></table>'
        body += h_t
        body += _ai_section_label("Recommended Actions", "#2563EB")
        body += _ai_action_list([
            "<strong>Move slow-moving inventory</strong> out of critical zones to free up capacity",
            "<strong>Consider overflow redistribution</strong> for zones approaching critical threshold",
            "<strong>Review zone allocation policy</strong> and rebalance based on demand patterns"
        ])
        return _ai_html_panel("Zone Congestion Analysis", "#8B5CF6", body)

    elif "delayed" in q or "delay" in q or "late" in q or "overdue" in q or "behind schedule" in q or "sla" in q or "not delivered" in q or "pending order" in q or "order status" in q:
        delayed = get_delayed_orders(orders)
        avg_d = f"{delayed['delay_days'].mean():.1f}" if len(delayed) > 0 else "0"
        body = _ai_kpi_row([(len(delayed), "Delayed Orders", "#EF4444"), (avg_d, "Avg Delay (days)", "#8B5CF6")])
        body += _ai_section_label("Delays by Zone", "#EF4444")
        zone_delay = delayed.groupby("warehouse_zone")["delay_days"].agg(["count", "mean"]).reset_index().sort_values("count", ascending=False)
        rows = [[r['warehouse_zone'], int(r['count']), f"{r['mean']:.1f} days"] for _, r in zone_delay.head(5).iterrows()]
        body += _ai_mini_table(["Zone", "Delayed Orders", "Avg Delay"], rows, ['#111827', '#EF4444', '#64748B'])
        body += _ai_section_label("Recommended Actions", "#2563EB")
        body += _ai_action_list([
            "<strong>Prioritize high-priority delayed orders</strong> for immediate dispatch",
            "<strong>Investigate congested zones</strong> and reassign picking resources",
            "<strong>Communicate revised timelines</strong> to impacted customers proactively"
        ])
        return _ai_html_panel("Delayed Orders Analysis", "#EF4444", body)

    elif "supplier" in q or "mismatch" in q or "inbound" in q or "shipment" in q or "vendor" in q or "received" in q or "shortage" in q or "delivery" in q:
        issues = get_supplier_issues(inbound)
        mismatches = get_inbound_mismatches(inbound)
        body = _ai_kpi_row([(len(mismatches), "Mismatched Shipments", "#EF4444"), (f"{len(issues)}", "Suppliers with Issues", "#F59E0B")])
        body += _ai_section_label("Suppliers with Most Issues", "#EF4444")
        rows = [[str(r['supplier_name'])[:22], int(r['mismatch_count']), int(r['total_shortage'])] for _, r in issues.head(5).iterrows()]
        body += _ai_mini_table(["Supplier", "Mismatches", "Shortage (units)"], rows, ['#111827', '#F59E0B', '#EF4444'])
        body += _ai_section_label("Recommended Actions", "#2563EB")
        body += _ai_action_list([
            "<strong>Escalate to procurement team</strong> for suppliers with repeated mismatches",
            "<strong>Review supplier SLAs</strong> and enforce penalty clauses",
            "<strong>Identify backup suppliers</strong> for critical SKU categories"
        ])
        return _ai_html_panel("Supplier & Inbound Analysis", "#F59E0B", body)

    elif "picker" in q or "picking" in q or "error" in q or "accuracy" in q or "mistakes" in q or "wrong pick" in q or "fulfillment" in q:
        errors = get_picking_errors_by_picker(picking)
        total_err = int(errors["total_errors"].sum())
        body = _ai_kpi_row([(total_err, "Total Errors", "#EF4444"), (f"{len(errors)}", "Active Pickers", "#2563EB")])
        body += _ai_section_label("Pickers with Highest Error Count", "#EF4444")
        rows = []
        for _, r in errors.head(6).iterrows():
            err_rate = round(r['avg_errors_per_pick'], 2)
            rows.append([r['picker_name'], int(r['total_errors']), int(r['total_picks']), f"{err_rate:.2f}"])
        body += _ai_mini_table(["Picker", "Errors", "Total Picks", "Error Rate"], rows, ['#111827', '#EF4444', '#64748B', '#8B5CF6'])
        body += _ai_section_label("Recommended Actions", "#2563EB")
        body += _ai_action_list([
            "<strong>Provide additional training</strong> to pickers with high error rates",
            "<strong>Review picking processes</strong> in zones with most errors",
            "<strong>Consider implementing barcode verification</strong> at pick points"
        ])
        return _ai_html_panel("Picking Accuracy Analysis", "#EF4444", body)

    elif "loading bay" in q or "bay" in q or "dispatch" in q or "bottleneck" in q or "shipping" in q or "loading" in q or "dock" in q or "throughput" in q:
        bays = get_dispatch_by_bay(picking)
        slowest = bays.iloc[0] if len(bays) > 0 else None
        body = ''
        if slowest is not None:
            body = _ai_kpi_row([(f"{slowest['avg_time']:.0f} min", "Slowest Bay", "#EF4444"), (f"{int(bays['total_dispatches'].sum())}", "Total Dispatches", "#2563EB")])
        body += _ai_section_label("Bay Performance Overview", "#111827")
        rows = [[r['loading_bay'], f"{r['avg_time']:.0f} min", int(r['total_dispatches']), int(r['total_errors'])] for _, r in bays.iterrows()]
        body += _ai_mini_table(["Bay", "Avg Time", "Dispatches", "Errors"], rows, ['#111827', '#8B5CF6', '#64748B', '#EF4444'])
        body += _ai_section_label("Recommended Actions", "#2563EB")
        body += _ai_action_list([
            f"<strong>Investigate bottleneck</strong> at {slowest['loading_bay'] if slowest is not None else 'slowest bay'} with highest avg dispatch time",
            "<strong>Consider load redistribution</strong> across bays to balance dispatch workload",
            "<strong>Review staffing and equipment</strong> at underperforming bays"
        ])
        return _ai_html_panel("Loading Bay Analysis", "#8B5CF6", body)

    elif "risk" in q or "summary" in q or "performance" in q or "overview" in q or "dashboard" in q or "kpi" in q or "health" in q or "report" in q or "status" in q or "how are we doing" in q or "today" in q or "operations" in q or "metrics" in q or "generate" in q:
        kpis = compute_kpis(data)
        body = _ai_kpi_row([
            (kpis['Total SKUs'], "SKUs", "#2563EB"),
            (kpis['Low Stock Items'], "Low Stock", "#EF4444"),
            (kpis['Delayed Orders'], "Delayed", "#F59E0B"),
            (f"{kpis['Warehouse Utilization %']}%", "Utilization", "#8B5CF6"),
        ])
        body += _ai_section_label("Key Performance Metrics", "#111827")
        rows = [[k, str(v)] for k, v in kpis.items()]
        body += _ai_mini_table(["Metric", "Value"], rows, ['#111827', '#2563EB'])
        body += _ai_section_label("Top 5 Operational Risks", "#EF4444")
        body += _ai_action_list([
            f"<strong>{kpis['Low Stock Items']} SKUs below reorder level</strong> &mdash; stockout risk across warehouse",
            f"<strong>{kpis['Delayed Orders']} orders delayed</strong> &mdash; customer SLA breach potential",
            f"<strong>Warehouse at {kpis['Warehouse Utilization %']}% utilization</strong> &mdash; zone congestion risk",
            f"<strong>Picking accuracy at {kpis['Picking Accuracy %']}%</strong> &mdash; fulfillment error risk",
            f"<strong>{kpis['Inbound Mismatch Count']} inbound mismatches</strong> &mdash; supply chain reliability risk",
        ])
        return _ai_html_panel("Warehouse Performance Summary", "linear-gradient(135deg,#2563EB,#06B6D4)", body)

    # ─── Dead Stock Root Cause (before generic "dead stock" list) ───
    elif "why dead stock" in q or "why is dead" in q or "why not selling" in q or "why not buying" in q or "people not buying" in q or "not selling why" in q or "dead stock reason" in q or "dead stock cause" in q or "perishable loss" in q:
        from utils.analytics import get_dead_stock_analysis
        try:
            dead = get_dead_stock_analysis(inv)
            total_dead = len(dead)
            total_cost = float(dead["total_storage_cost"].sum()) if len(dead) > 0 and "total_storage_cost" in dead.columns else 0
            perishable_expired = int(dead["is_expired"].sum()) if len(dead) > 0 and "is_expired" in dead.columns else 0
            body = _ai_kpi_row([
                (total_dead, "Dead Stock SKUs", "#8B5CF6"),
                (f"₹{total_cost:,.0f}", "Storage Cost (dead SKUs)", "#EF4444"),
                (perishable_expired, "Expired (date)", "#F59E0B"),
            ])
            body += _ai_section_label("Dead Stock by Root Cause", "#8B5CF6")
            if len(dead) > 0:
                reason_counts = dead.groupby("dead_stock_reason").size().reset_index(name="count").sort_values("count", ascending=False)
                rows = [[r["dead_stock_reason"], int(r["count"])] for _, r in reason_counts.iterrows()]
                body += _ai_mini_table(["Root Cause", "SKU Count"], rows, ["#111827", "#8B5CF6"])
            if perishable_expired > 0 and "is_expired" in dead.columns:
                body += _ai_section_label("Perishable Loss Analysis", "#EF4444")
                expired = dead[dead["is_expired"] == True]
                cost_col = "perishable_loss" if "perishable_loss" in expired.columns else "total_storage_cost"
                rows = [[r["sku_id"], str(r["product_name"])[:25], int(r["current_stock"]), f"₹{float(r[cost_col]):,.0f}"] for _, r in expired.head(8).iterrows()]
                body += _ai_mini_table(["SKU", "Product", "Stock", "Est. Loss"], rows, ["#111827", "#4B5563", "#EF4444", "#DC2626"])
            body += _ai_section_label("Recommended Actions", "#2563EB")
            body += _ai_action_list([
                "<strong>Investigate pricing strategy</strong> for items marked as 'Price Too High' — align with market rates",
                "<strong>Negotiate returns to suppliers</strong> for overstock / bulk-buy errors to recover capital",
                "<strong>Launch targeted marketing push</strong> for low-demand items with discount or bundle offers",
                "<strong>Conduct quality audit</strong> on obsolete items and initiate write-off for unsalvageable stock",
            ])
        except Exception:
            body = '<div style="font-size:0.85rem;color:#374151;">Dead stock root cause analysis is being set up. Please try again shortly.</div>'
        return _ai_html_panel("Dead Stock Root Cause Analysis", "#8B5CF6", body)

    elif "dead stock" in q or "no movement" in q or "stagnant" in q or "obsolete" in q or "inactive" in q or "not moving" in q or "slow moving" in q:
        dead = get_dead_stock_items(inv)
        body = _ai_kpi_row([(len(dead), "Dead Stock SKUs", "#8B5CF6"), (f"{len(inv)}", "Total SKUs", "#2563EB")])
        body += _ai_section_label("Top Dead Stock Items", "#8B5CF6")
        rows = []
        for _, r in dead.head(10).iterrows():
            days = (datetime.now() - r["last_movement_date"]).days
            rows.append([r['sku_id'], str(r['product_name'])[:25], int(r['current_stock']), f"{days} days", r['warehouse_zone']])
        body += _ai_mini_table(["SKU", "Product", "Stock", "Inactive", "Zone"], rows, ['#111827', '#4B5563', '#64748B', '#8B5CF6', '#64748B'])
        body += _ai_section_label("Recommended Actions", "#2563EB")
        body += _ai_action_list([
            f"<strong>Review {len(dead)} items</strong> for liquidation, write-off, or promotional clearance",
            "<strong>Free up warehouse space</strong> by relocating dead stock to lower-cost zones",
            "<strong>Investigate root causes</strong> of dead stock accumulation for future prevention"
        ])
        return _ai_html_panel("Dead Stock Analysis", "#8B5CF6", body)

    elif "fast moving" in q or "fast-moving" in q or "top selling" in q or "best seller" in q or "highest sales" in q or "popular" in q or "most sold" in q or "top sku" in q or "top product" in q:
        fast = inv.nlargest(10, "avg_daily_sales")
        body = _ai_section_label("Top 10 by Daily Sales Velocity", "#10B981")
        rows = [[r['sku_id'], str(r['product_name'])[:25], f"{r['avg_daily_sales']:.1f}", int(r['current_stock']), r['warehouse_zone']] for _, r in fast.iterrows()]
        body += _ai_mini_table(["SKU", "Product", "Daily Sales", "Stock", "Zone"], rows, ['#111827', '#4B5563', '#10B981', '#64748B', '#64748B'])
        body += _ai_section_label("Recommended Actions", "#2563EB")
        body += _ai_action_list([
            "<strong>Ensure fast-moving SKUs</strong> are placed in fast-access picking zones",
            "<strong>Maintain adequate stock levels</strong> with safety stock buffers",
            "<strong>Monitor demand trends</strong> and adjust reorder levels accordingly"
        ])
        return _ai_html_panel("Fast-Moving SKU Analysis", "#10B981", body)

    # ─── Dead Stock Liquidation ───
    elif "liquidate" in q or "get rid of dead stock" in q or "sell dead stock" in q or "clear dead stock" in q or "dead stock solution" in q or "what to do with dead stock" in q or "reduce dead stock" in q or "no loss" in q or "no profit no loss" in q or "sell at low price" in q or "return to distributor" in q or "sell to competitor" in q:
        from utils.analytics import get_liquidation_strategies
        try:
            liq_raw = get_liquidation_strategies(inv)
            liq = pd.DataFrame(liq_raw) if liq_raw else pd.DataFrame()
            total_recovery = float(liq["recovery"].sum()) if len(liq) > 0 and "recovery" in liq.columns else 0
            total_value = float(liq["inventory_value"].sum()) if len(liq) > 0 and "inventory_value" in liq.columns else 0
            body = _ai_kpi_row([
                (len(liq), "Items to Liquidate", "#8B5CF6"),
                (f"₹{total_recovery:,.0f}", "Potential Recovery", "#10B981"),
                (f"₹{total_value:,.0f}", "Total Inventory Value", "#2563EB"),
            ])
            body += _ai_section_label("Liquidation Strategies by SKU", "#8B5CF6")
            if len(liq) > 0:
                rows = [[r["sku_id"], str(r.get("reason", "N/A"))[:28], r["strategy"], f"₹{float(r['recovery']):,.0f}"] for _, r in liq.head(12).iterrows()]
                body += _ai_mini_table(["SKU", "Reason", "Strategy", "Recovery"], rows, ["#111827", "#64748B", "#2563EB", "#10B981"])
            body += _ai_section_label("Recovery Summary", "#10B981")
            recovery_pct = (total_recovery / total_value * 100) if total_value > 0 else 0
            body += f'<div style="font-size:0.82rem;color:#374151;margin-bottom:10px;">Estimated recovery: <strong style="color:#10B981;">₹{total_recovery:,.0f}</strong> out of <strong>₹{total_value:,.0f}</strong> total dead stock value (<strong>{recovery_pct:.1f}%</strong> recovery rate)</div>'
            body += _ai_section_label("Recommended Actions", "#2563EB")
            body += _ai_action_list([
                "<strong>Negotiate supplier returns</strong> for items with return-eligible terms to maximize recovery",
                "<strong>Match competitor pricing</strong> for slow-demand items and list on discount marketplaces",
                "<strong>Organize bulk clearance sales</strong> for items beyond 90-day inactivity threshold",
                "<strong>Write off unsalvageable items</strong> and free up premium warehouse space immediately",
            ])
        except Exception:
            body = '<div style="font-size:0.85rem;color:#374151;">Liquidation strategy analysis is being set up. Please try again shortly.</div>'
        return _ai_html_panel("Dead Stock Liquidation Strategies", "linear-gradient(135deg,#8B5CF6,#06B6D4)", body)

    # ─── Warehouse Resource Optimization ───
    elif "reduce resources" in q or "reduce cost" in q or "reduce warehouse cost" in q or "warehouse charges" in q or "storage charges" in q or "energy cost" in q or "energy lose" in q or "save cost" in q or "reduce resource" in q or "faster sales" in q or "faster operation" in q or "operational cost" in q:
        from utils.analytics import get_resource_optimization
        try:
            opt = get_resource_optimization(data)
            body = _ai_kpi_row([
                (f"₹{opt['dead_storage_cost']:,.0f}", "Dead Stock Storage Cost", "#EF4444"),
                (f"₹{opt['total_energy_cost']:,.0f}", "Monthly Energy (est.)", "#F59E0B"),
                (f"{opt['potential_space_freed']:,}", "Dead Stock Units", "#10B981"),
            ])
            body += _ai_section_label("Zone-wise Energy & Dead Stock Footprint", "#F59E0B")
            zb = opt["zone_breakdown"]
            rows = [[r["zone_name"], f"{r['utilization_pct']}%", f"₹{float(r['energy_cost_monthly']):,.0f}", int(r["dead_stock_units"]), f"{r['potential_space_freed_pct']}%"] for _, r in zb.iterrows()]
            body += _ai_mini_table(["Zone", "Utilization", "Energy /mo", "Dead Units", "Dead % of Used"], rows, ["#111827", "#8B5CF6", "#F59E0B", "#EF4444", "#10B981"])
            body += _ai_section_label("Recommended Actions", "#2563EB")
            body += _ai_action_list([
                "<strong>Remove dead stock immediately</strong> to free up warehouse space and reduce storage overhead",
                "<strong>Implement faster dispatch cycles</strong> to reduce inventory holding time and energy usage",
                "<strong>Close or consolidate underutilized zones</strong> to cut fixed operational costs",
                "<strong>Reduce energy consumption</strong> in low-utilization zones by adjusting climate control schedules",
            ])
        except Exception:
            body = '<div style="font-size:0.85rem;color:#374151;">Resource optimization analysis is being set up. Please try again shortly.</div>'
        return _ai_html_panel("Warehouse Resource Optimization", "#F59E0B", body)

    # ─── Delay Root Cause ───
    elif "why delay" in q or "why delayed" in q or "delay reason" in q or "cause of delay" in q or "reason for delay" in q or "why pending" in q or "pending reason" in q or "how to speed" in q or "faster delivery" in q or "speed up" in q or "make them fast" in q:
        from utils.analytics import get_delay_root_causes
        try:
            delayed_pending = orders[orders["status"].isin(["Delayed", "Pending"])].copy()
            delayed_rc = get_delay_root_causes(orders)
            n_affected = len(delayed_pending)
            avg_d = float(delayed_pending["delay_days"].mean()) if n_affected > 0 else 0
            max_d = float(delayed_pending["delay_days"].max()) if n_affected > 0 else 0
            body = _ai_kpi_row([
                (n_affected, "Delayed / Pending", "#EF4444"),
                (f"{avg_d:.1f}", "Avg Delay (days)", "#8B5CF6"),
                (f"{int(max_d)}", "Max Delay (days)", "#DC2626"),
            ])
            body += _ai_section_label("Delay Reasons Breakdown", "#EF4444")
            if len(delayed_rc) > 0:
                rows = [[r["delay_reason"], int(r["count"]), f"{float(r['avg_delay']):.1f}", int(r["max_delay"])] for _, r in delayed_rc.iterrows()]
                body += _ai_mini_table(["Delay Reason", "Orders", "Avg Delay", "Max Delay"], rows, ["#111827", "#EF4444", "#64748B", "#DC2626"])
            body += _ai_section_label("Zones Causing Maximum Delay", "#8B5CF6")
            if n_affected > 0:
                zone_agg = delayed_pending.groupby("warehouse_zone")["delay_days"].agg(["count", "mean"]).reset_index().sort_values("count", ascending=False).head(5)
                rows = [[r["warehouse_zone"], int(r["count"]), f"{float(r['mean']):.1f} days"] for _, r in zone_agg.iterrows()]
                body += _ai_mini_table(["Zone", "Affected Orders", "Avg Delay"], rows, ["#111827", "#EF4444", "#64748B"])
            body += _ai_section_label("Recommended Actions", "#2563EB")
            body += _ai_action_list([
                "<strong>Address top delay reasons</strong> — prioritize capacity overflow and SLA-miss orders for immediate resolution",
                "<strong>Add resources to congested zones</strong> — deploy additional pickers and dispatch staff",
                "<strong>Fix scheduling bottlenecks</strong> — optimize dispatch slot allocation and reduce idle time",
                "<strong>Set up real-time delay alerts</strong> to catch delays before they escalate past SLA thresholds",
            ])
        except Exception:
            body = '<div style="font-size:0.85rem;color:#374151;">Delay root cause analysis is being set up. Please try again shortly.</div>'
        return _ai_html_panel("Delay Root Cause Analysis", "#EF4444", body)

    # ─── Picking Error Root Cause ───
    elif "why error" in q or "picking error reason" in q or "error type" in q or "why picking error" in q or "eliminate error" in q or "reduce error" in q or "wrong pick" in q or "how to eliminate" in q:
        from utils.analytics import get_picking_error_analysis
        try:
            err_analysis = get_picking_error_analysis(picking)
            total_occ = int(err_analysis["occurrences"].sum()) if len(err_analysis) > 0 else 0
            total_pickers = int(err_analysis["affected_pickers"].sum()) if len(err_analysis) > 0 else 0
            body = _ai_kpi_row([
                (total_occ, "Error Occurrences", "#EF4444"),
                (total_pickers, "Pickers Affected", "#F59E0B"),
                (len(err_analysis), "Error Types Found", "#8B5CF6"),
            ])
            body += _ai_section_label("Error Type Breakdown", "#EF4444")
            if len(err_analysis) > 0:
                rows = [[r["error_type"], int(r["occurrences"]), int(r["affected_pickers"]), int(r["total_errors"])] for _, r in err_analysis.iterrows()]
                body += _ai_mini_table(["Error Type", "Occurrences", "Pickers Affected", "Total Errors"], rows, ["#111827", "#EF4444", "#F59E0B", "#DC2626"])
            body += _ai_section_label("Recommended Actions", "#2563EB")
            body += _ai_action_list([
                "<strong>Implement barcode verification</strong> at every pick point to eliminate wrong-SKU errors",
                "<strong>Conduct targeted training</strong> for pickers involved in quantity-mismatch errors",
                "<strong>Reorganize zone bin layouts</strong> to reduce wrong-location picks and improve navigation",
                "<strong>Introduce pick-to-light systems</strong> in high-error zones for guided picking accuracy",
            ])
        except Exception:
            body = '<div style="font-size:0.85rem;color:#374151;">Picking error analysis is being set up. Please try again shortly.</div>'
        return _ai_html_panel("Picking Error Root Cause Analysis", "#EF4444", body)

    # ─── Best Bay / Route Optimization ───
    elif "best bay" in q or "fastest bay" in q or "bay efficiency" in q or "best route" in q or "fastest route" in q or "low cost route" in q or "efficient route" in q or "route optimization" in q or "reduce delivery cost" in q or "delivery cost" in q:
        from utils.analytics import get_bay_optimization, get_route_efficiency
        try:
            bays = get_bay_optimization(picking)
            routes = get_route_efficiency(data)
            body = ''
            body += _ai_section_label("Bay Efficiency Ranking", "#2563EB")
            if len(bays) > 0:
                rows = [[f"#{int(r['rank'])}", r["loading_bay"], f"{r['efficiency_score']:.1f}", f"{r['avg_time']:.0f} min", int(r["total_dispatches"]), int(r["total_errors"])] for _, r in bays.iterrows()]
                body += _ai_mini_table(["Rank", "Bay", "Score", "Avg Time", "Dispatches", "Errors"], rows, ["#8B5CF6", "#111827", "#10B981", "#64748B", "#64748B", "#EF4444"])
            body += _ai_section_label("Route Analysis by Zone", "#8B5CF6")
            if len(routes) > 0:
                rows = [[r["warehouse_zone"], f"₹{r['est_cost_per_dispatch']:,.0f}", int(r["total_dispatches"]), f"{r['delay_pct']:.1f}%", f"{r['avg_dispatch_time']:.0f} min"] for _, r in routes.head(8).iterrows()]
                body += _ai_mini_table(["Zone Route", "Est. Cost/Dispatch", "Dispatches", "Delay %", "Avg Time"], rows, ["#111827", "#F59E0B", "#64748B", "#EF4444", "#8B5CF6"])
            body += _ai_section_label("Recommended Actions", "#2563EB")
            best_bay = bays.iloc[0]["loading_bay"] if len(bays) > 0 else "best-performing bay"
            body += _ai_action_list([
                f"<strong>Prioritize {best_bay}</strong> for high-priority dispatches — highest efficiency score",
                "<strong>Use lowest-cost routes</strong> for bulk / non-urgent shipments to reduce delivery spend",
                "<strong>Right-size vehicles</strong> per route — avoid underloaded trucks on short routes",
                "<strong>Rebalance bay assignments</strong> to distribute load away from bottleneck bays",
            ])
        except Exception:
            body = '<div style="font-size:0.85rem;color:#374151;">Bay and route optimization analysis is being set up. Please try again shortly.</div>'
        return _ai_html_panel("Bay & Route Optimization", "linear-gradient(135deg,#2563EB,#10B981)", body)

    # ─── Zone Transport & Prediction ───
    elif "zone transport" in q or "vehicle zone" in q or "what vehicle" in q or "allowed vehicle" in q or "zone prediction" in q or "until when critical" in q or "when will zone" in q or "zone forecast" in q or "maximum profit zone" in q or "profit zone" in q or "revenue zone" in q or "redirect route" in q:
        from utils.analytics import get_zone_transport_analysis
        try:
            zt = get_zone_transport_analysis(zones, inv)
            body = _ai_kpi_row([
                (len(zt), "Active Zones", "#2563EB"),
                (f"{zt['utilization_pct'].mean():.1f}%", "Avg Utilization", "#8B5CF6"),
                (f"₹{zt['revenue_potential'].sum():,.0f}", "Total Revenue Potential", "#10B981"),
            ])
            body += _ai_section_label("Zone Transport & Prediction Overview", "#2563EB")
            if len(zt) > 0:
                rows = []
                for _, r in zt.iterrows():
                    rows.append([
                        r["zone_name"], r["status"], f"{r['utilization_pct']}%",
                        str(r.get("allowed_vehicles", "N/A"))[:22],
                        f"{int(r['max_capacity']):,}", r["trend"],
                        str(r.get("expected_critical_until", "N/A")),
                        f"₹{r['revenue_potential']:,.0f}",
                    ])
                body += _ai_mini_table(
                    ["Zone", "Status", "Util%", "Vehicles", "Capacity", "Trend", "Critical ETA", "Revenue"],
                    rows, ["#111827", "#64748B", "#8B5CF6", "#2563EB", "#64748B", "#F59E0B", "#EF4444", "#10B981"]
                )
            body += _ai_section_label("Recommended Actions", "#2563EB")
            top_revenue = zt.nlargest(1, "revenue_potential").iloc[0]["zone_name"] if len(zt) > 0 else "top zone"
            body += _ai_action_list([
                "<strong>Plan vehicle assignments</strong> based on zone type — match vehicle size to zone throughput needs",
                "<strong>Monitor rising-trend zones</strong> and pre-allocate capacity before they hit critical levels",
                f"<strong>Redirect high-value routes to {top_revenue}</strong> — highest revenue potential zone",
                "<strong>Forecast capacity needs</strong> using trend data and schedule preventive rebalancing",
            ])
        except Exception:
            body = '<div style="font-size:0.85rem;color:#374151;">Zone transport analysis is being set up. Please try again shortly.</div>'
        return _ai_html_panel("Zone Transport & Prediction Intelligence", "linear-gradient(135deg,#2563EB,#8B5CF6)", body)

    # ─── Customer Impact ───
    elif "customer impact" in q or "customer affected" in q or "customer delay" in q or "impacted customer" in q or "how to improve customer" in q or "customer satisfaction" in q:
        from utils.analytics import get_customer_impact
        try:
            impact = get_customer_impact(orders)
            total_affected = len(impact)
            total_delay_days = int(impact["total_delay_days"].sum()) if len(impact) > 0 else 0
            body = _ai_kpi_row([
                (total_affected, "Customers Affected", "#EF4444"),
                (total_delay_days, "Total Delay Days", "#F59E0B"),
                (f"{impact['avg_delay'].mean():.1f}" if len(impact) > 0 else "0", "Avg Delay (days)", "#8B5CF6"),
            ])
            body += _ai_section_label("Top 10 Most Affected Customers", "#EF4444")
            if len(impact) > 0:
                rows = [[r["customer_name"], int(r["delayed_orders"]), int(r["total_delay_days"]), f"{r['avg_delay']:.1f}", int(r["max_delay"])] for _, r in impact.head(10).iterrows()]
                body += _ai_mini_table(["Customer", "Delayed Orders", "Total Delay Days", "Avg Delay", "Max Delay"], rows, ["#111827", "#EF4444", "#F59E0B", "#64748B", "#DC2626"])
            body += _ai_section_label("Recommended Actions", "#2563EB")
            body += _ai_action_list([
                "<strong>Proactive communication</strong> — notify top-affected customers with revised delivery timelines",
                "<strong>Expedite pending orders</strong> for customers with highest total delay exposure",
                "<strong>Offer compensation or discounts</strong> to retain customers impacted by repeated delays",
                "<strong>Assign dedicated dispatch priority</strong> for high-value customer accounts",
            ])
        except Exception:
            body = '<div style="font-size:0.85rem;color:#374151;">Customer impact analysis is being set up. Please try again shortly.</div>'
        return _ai_html_panel("Customer Impact Analysis", "linear-gradient(135deg,#EF4444,#F59E0B)", body)

    else:
        # Catch-all: provide a full warehouse summary for any unrecognized query
        kpis = compute_kpis(data)
        low = get_low_stock_items(inv)
        delayed_o = get_delayed_orders(orders)
        zone_util = get_zone_utilization(zones)
        critical = zone_util[zone_util["status"] == "Critical"]

        body = f'<div style="font-size:0.85rem;color:#374151;line-height:1.6;margin-bottom:12px;">Based on your query, here\'s a comprehensive warehouse intelligence snapshot:</div>'
        body += _ai_kpi_row([
            (kpis['Total SKUs'], "Total SKUs", "#2563EB"),
            (kpis['Low Stock Items'], "Low Stock", "#EF4444"),
            (kpis['Delayed Orders'], "Delayed", "#F59E0B"),
            (f"{kpis['Warehouse Utilization %']}%", "Utilization", "#8B5CF6"),
            (f"{kpis['Picking Accuracy %']}%", "Pick Accuracy", "#10B981"),
        ])

        body += _ai_section_label("Top Operational Risks", "#EF4444")
        body += _ai_action_list([
            f"<strong>{kpis['Low Stock Items']} SKUs below reorder level</strong> &mdash; stockout risk",
            f"<strong>{kpis['Delayed Orders']} orders delayed</strong> &mdash; avg {kpis['Avg Delay Days']} days behind schedule",
            f"<strong>{len(critical)} zones at critical capacity</strong> &mdash; congestion and picking delays",
            f"<strong>{kpis['Inbound Mismatch Count']} inbound mismatches</strong> &mdash; supplier reliability concerns",
        ])

        body += _ai_section_label("Quick Insights", "#2563EB")
        body += '<div style="font-size:0.82rem;color:#4B5563;line-height:1.7;"><ul style="margin:4px 0;padding-left:18px;">'
        if len(low) > 0:
            body += f'<li>Most critical SKU: <strong>{low.iloc[0]["sku_id"]}</strong> ({low.iloc[0]["product_name"]}) &mdash; only {int(low.iloc[0]["current_stock"])} units left</li>'
        if len(delayed_o) > 0:
            worst_zone = delayed_o.groupby("warehouse_zone").size().idxmax()
            body += f'<li>Zone with most delays: <strong>{worst_zone}</strong></li>'
        if len(critical) > 0:
            body += f'<li>Most congested: <strong>{critical.iloc[0]["zone_name"]}</strong> at {critical.iloc[0]["utilization_pct"]}%</li>'
        body += '</ul></div>'

        body += _ai_section_label("Try asking more specific questions:", "#64748B")
        body += '<div style="font-size:0.78rem;color:#64748B;line-height:1.6;">Which SKUs need reorder? &middot; Which zone is congested? &middot; Show delayed orders &middot; Supplier issues &middot; Picking errors &middot; Loading bay performance</div>'
        return _ai_html_panel("Warehouse Intelligence Summary", "linear-gradient(135deg,#2563EB,#06B6D4)", body)


def get_ai_response(question, data):
    """Main function to get AI response - tries API first, falls back to rules."""
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    context = build_data_context(data)

    if gemini_key and GEMINI_AVAILABLE:
        try:
            return ask_ai_gemini(question, context, gemini_key)
        except Exception as e:
            return f"Gemini API error: {str(e)}\n\nFalling back to rule-based analysis...\n\n" + ask_ai_fallback(question, data)

    elif openai_key and OPENAI_AVAILABLE:
        try:
            return ask_ai_openai(question, context, openai_key)
        except Exception as e:
            return f"OpenAI API error: {str(e)}\n\nFalling back to rule-based analysis...\n\n" + ask_ai_fallback(question, data)

    else:
        return ask_ai_fallback(question, data)
