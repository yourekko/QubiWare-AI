"""Analytics and intelligence computations for QubiWare AI."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def df_to_styled_table(df, title="", subtitle="", max_rows=15, highlight_cols=None, status_col=None, **kwargs):
    """Convert a DataFrame to a premium styled HTML table with optional title, status badges, and AI insight strip."""
    wow_insight_html = kwargs.pop("wow_insight_html", None)
    # Tolerate stray kwargs from older call sites / partial deploys without breaking the table.
    highlight_cols = highlight_cols or {}
    df_display = df.head(max_rows)

    h = ''
    if title:
        h += '<div style="background:white;border:1px solid #E5E7EB;border-radius:14px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06);margin-bottom:16px;">'
        h += f'<div style="padding:16px 20px 12px 20px;border-bottom:1px solid #F3F4F6;display:flex;align-items:center;gap:10px;">'
        h += f'<div style="width:6px;height:6px;border-radius:50%;background:linear-gradient(135deg,#2563EB,#06B6D4);flex-shrink:0;"></div>'
        h += f'<div><div style="font-size:0.85rem;font-weight:700;color:#111827;">{title}</div>'
        if subtitle:
            h += f'<div style="font-size:0.68rem;color:#9CA3AF;margin-top:1px;">{subtitle}</div>'
        h += '</div></div>'
    else:
        h += '<div style="background:white;border:1px solid #E5E7EB;border-radius:14px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06);margin-bottom:16px;">'

    if wow_insight_html:
        try:
            h += str(wow_insight_html)
        except Exception:
            pass

    h += '<div style="overflow-x:auto;">'
    h += '<table style="width:100%;border-collapse:collapse;font-size:0.78rem;">'
    h += '<thead><tr style="background:#F8FAFC;">'
    for col in df_display.columns:
        h += f'<th style="padding:10px 14px;text-align:left;font-weight:700;color:#64748B;font-size:0.66rem;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #E5E7EB;white-space:nowrap;">{col}</th>'
    h += '</tr></thead><tbody>'

    status_colors = {"Critical": "#EF4444", "Warning": "#F59E0B", "Normal": "#10B981",
                     "Delayed": "#EF4444", "Pending": "#F59E0B", "Delivered": "#10B981", "Dispatched": "#2563EB",
                     "Completed": "#10B981", "In Progress": "#2563EB",
                     "High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"}

    for idx, (_, row) in enumerate(df_display.iterrows()):
        bg = '#FFFFFF' if idx % 2 == 0 else '#F8FAFC'
        h += f'<tr style="background:{bg};transition:background 0.15s;">'
        for j, col in enumerate(df_display.columns):
            val = row[col]
            color = highlight_cols.get(col, '#374151')
            fw = '600' if j == 0 else '400'

            if status_col and col == status_col and str(val) in status_colors:
                sc = status_colors[str(val)]
                cell = f'<span style="background:{sc}12;color:{sc};font-size:0.68rem;font-weight:700;padding:3px 10px;border-radius:6px;white-space:nowrap;">{val}</span>'
                h += f'<td style="padding:8px 14px;border-bottom:1px solid #F3F4F6;">{cell}</td>'
            elif col in highlight_cols:
                h += f'<td style="padding:8px 14px;color:{color};font-weight:700;border-bottom:1px solid #F3F4F6;white-space:nowrap;">{val}</td>'
            else:
                h += f'<td style="padding:8px 14px;color:{color};font-weight:{fw};border-bottom:1px solid #F3F4F6;">{val}</td>'
        h += '</tr>'

    h += '</tbody></table></div>'
    row_note = f'<div style="padding:8px 20px 10px 20px;font-size:0.68rem;color:#9CA3AF;border-top:1px solid #F3F4F6;">Showing {len(df_display)} of {len(df)} records</div>' if len(df) > max_rows else ''
    h += row_note
    h += '</div>'
    return h


def get_low_stock_items(inventory_df):
    return inventory_df[inventory_df["current_stock"] <= inventory_df["reorder_level"]].copy()


def get_overstock_items(inventory_df):
    return inventory_df[inventory_df["current_stock"] >= inventory_df["max_stock"] * 0.85].copy()


def get_dead_stock_items(inventory_df):
    cutoff = datetime.now() - timedelta(days=60)
    return inventory_df[inventory_df["last_movement_date"] < cutoff].copy()


def get_fast_moving_skus(inventory_df, top_n=20):
    return inventory_df.nlargest(top_n, "avg_daily_sales").copy()


def get_reorder_recommendations(inventory_df):
    low = get_low_stock_items(inventory_df).copy()
    low["recommended_reorder_qty"] = low["max_stock"] - low["current_stock"]
    low["estimated_cost"] = low["recommended_reorder_qty"] * low["unit_price"]
    return low.sort_values("recommended_reorder_qty", ascending=False)


def get_delayed_orders(orders_df):
    return orders_df[orders_df["status"] == "Delayed"].copy()


def get_pending_orders(orders_df):
    return orders_df[orders_df["status"] == "Pending"].copy()


def get_high_priority_delayed(orders_df):
    delayed = get_delayed_orders(orders_df)
    return delayed[delayed["priority"] == "High"].copy()


def get_delay_by_zone(orders_df):
    delayed = orders_df[orders_df["status"].isin(["Delayed", "Pending"])]
    return delayed.groupby("warehouse_zone")["delay_days"].agg(["count", "mean"]).reset_index()


def get_delay_by_customer(orders_df):
    delayed = orders_df[orders_df["status"].isin(["Delayed", "Pending"])]
    return delayed.groupby("customer_name")["delay_days"].agg(["count", "sum", "mean"]).reset_index().sort_values("count", ascending=False)


def get_zone_utilization(zones_df):
    df = zones_df.copy()
    df["utilization_pct"] = (df["used_units"] / df["capacity_units"] * 100).round(1)
    df["status"] = df["utilization_pct"].apply(
        lambda x: "Critical" if x > 90 else ("Warning" if x > 75 else "Normal")
    )
    return df


def get_picking_errors_by_picker(picking_df):
    return picking_df.groupby("picker_name")["picking_errors"].agg(["sum", "count", "mean"]).reset_index().rename(
        columns={"sum": "total_errors", "count": "total_picks", "mean": "avg_errors_per_pick"}
    ).sort_values("total_errors", ascending=False)


def get_dispatch_by_bay(picking_df):
    return picking_df.groupby("loading_bay").agg(
        avg_time=("dispatch_time_minutes", "mean"),
        total_dispatches=("dispatch_id", "count"),
        total_errors=("picking_errors", "sum")
    ).reset_index().sort_values("avg_time", ascending=False)


def get_inbound_mismatches(inbound_df):
    received = inbound_df[inbound_df["status"] == "Received"].copy()
    mismatched = received[received["quantity_received"] < received["quantity_expected"]].copy()
    mismatched["shortage"] = mismatched["quantity_expected"] - mismatched["quantity_received"]
    return mismatched


def get_supplier_issues(inbound_df):
    mismatched = get_inbound_mismatches(inbound_df)
    return mismatched.groupby("supplier_name").agg(
        mismatch_count=("shipment_id", "count"),
        total_shortage=("shortage", "sum")
    ).reset_index().sort_values("mismatch_count", ascending=False)


def compute_kpis(data):
    inv = data["inventory"]
    orders = data["orders"]
    zones = data["zones"]
    picking = data["picking"]
    inbound = data["inbound"]

    total_skus = len(inv)
    total_orders = len(orders)
    low_stock = len(get_low_stock_items(inv))
    overstock = len(get_overstock_items(inv))
    delayed_orders = len(get_delayed_orders(orders))
    pending_dispatches = len(orders[orders["status"] == "Pending"])

    delayed_with_days = orders[orders["delay_days"] > 0]
    avg_delay = round(delayed_with_days["delay_days"].mean(), 1) if len(delayed_with_days) > 0 else 0

    zone_util = get_zone_utilization(zones)
    avg_utilization = round(zone_util["utilization_pct"].mean(), 1)

    total_picks = picking["items_picked"].sum()
    total_errors = picking["picking_errors"].sum()
    picking_accuracy = round((1 - total_errors / total_picks) * 100, 1) if total_picks > 0 else 100.0

    inbound_mismatch = len(get_inbound_mismatches(inbound))

    return {
        "Total SKUs": total_skus,
        "Total Orders": total_orders,
        "Low Stock Items": low_stock,
        "Overstock Items": overstock,
        "Delayed Orders": delayed_orders,
        "Pending Dispatches": pending_dispatches,
        "Avg Delay Days": avg_delay,
        "Warehouse Utilization %": avg_utilization,
        "Picking Accuracy %": picking_accuracy,
        "Inbound Mismatch Count": inbound_mismatch,
    }




def _html_report_header(title, subtitle, timestamp):
    return (
        f'<div style="background:linear-gradient(135deg,#0F172A 0%,#1E293B 50%,#334155 100%);padding:28px 32px;border-radius:14px 14px 0 0;position:relative;overflow:hidden;">'
        f'<div style="position:absolute;top:-40px;right:-20px;width:180px;height:180px;background:radial-gradient(circle,rgba(37,99,235,0.12) 0%,transparent 70%);border-radius:50%;"></div>'
        f'<div style="font-size:0.62rem;font-weight:700;color:#2563EB;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;position:relative;z-index:1;">AI-Generated Report</div>'
        f'<div style="font-size:1.3rem;font-weight:800;color:white;letter-spacing:-0.3px;position:relative;z-index:1;">{title}</div>'
        f'<div style="font-size:0.8rem;color:#94A3B8;margin-top:4px;position:relative;z-index:1;">{subtitle} &middot; {timestamp}</div>'
        f'</div>'
    )


def _html_kpi_strip(items):
    html = '<div style="display:flex;gap:0;border-bottom:1px solid #E5E7EB;">'
    for i, (value, label, color) in enumerate(items):
        border_right = 'border-right:1px solid #E5E7EB;' if i < len(items) - 1 else ''
        html += (
            f'<div style="flex:1;padding:16px 20px;{border_right}text-align:center;">'
            f'<div style="font-size:1.4rem;font-weight:800;color:{color};">{value}</div>'
            f'<div style="font-size:0.65rem;font-weight:600;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.5px;margin-top:2px;">{label}</div>'
            f'</div>'
        )
    html += '</div>'
    return html


def _html_section(title, badge="", badge_color="#EF4444"):
    badge_html = f'<span style="background:{badge_color}15;color:{badge_color};font-size:0.6rem;font-weight:700;padding:2px 8px;border-radius:4px;text-transform:uppercase;letter-spacing:0.5px;margin-left:10px;">{badge}</span>' if badge else ""
    return (
        f'<div style="padding:6px 32px 6px 32px;margin-top:4px;">'
        f'<div style="font-size:0.88rem;font-weight:700;color:#111827;display:flex;align-items:center;">'
        f'<div style="width:6px;height:6px;border-radius:50%;background:linear-gradient(135deg,#2563EB,#06B6D4);margin-right:10px;flex-shrink:0;"></div>'
        f'{title}{badge_html}</div></div>'
    )


def _html_table(headers, rows, colors=None):
    html = '<div style="padding:0 32px 8px 32px;"><table style="width:100%;border-collapse:collapse;font-size:0.78rem;">'
    html += '<thead><tr style="background:#F8FAFC;">'
    for h in headers:
        html += f'<th style="padding:8px 12px;text-align:left;font-weight:700;color:#64748B;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #E5E7EB;">{h}</th>'
    html += '</tr></thead><tbody>'
    for i, row in enumerate(rows):
        bg = '#FFFFFF' if i % 2 == 0 else '#F8FAFC'
        html += f'<tr style="background:{bg};">'
        for j, val in enumerate(row):
            color = colors[j] if colors and j < len(colors) else '#374151'
            fw = '700' if j == 0 else '400'
            html += f'<td style="padding:8px 12px;color:{color};font-weight:{fw};border-bottom:1px solid #F3F4F6;">{val}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    return html


def _html_action_item(num, text, urgency_color):
    return (
        f'<div style="display:flex;align-items:flex-start;gap:12px;padding:8px 32px;">'
        f'<div style="width:24px;height:24px;background:{urgency_color};color:white;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:0.68rem;font-weight:700;flex-shrink:0;">{num}</div>'
        f'<div style="font-size:0.82rem;color:#374151;line-height:1.5;padding-top:2px;">{text}</div>'
        f'</div>'
    )


def get_dead_stock_analysis(inventory_df):
    """Analyze dead stock by reason, perishability, storage cost impact, and liquidation options."""
    dead = get_dead_stock_items(inventory_df)
    if len(dead) == 0:
        return dead
    dead = dead.copy()
    dead["days_inactive"] = (datetime.now() - dead["last_movement_date"]).dt.days
    dead["total_storage_cost"] = dead["storage_cost_per_day"] * dead["current_stock"] * dead["days_inactive"]
    dead["inventory_value"] = dead["current_stock"] * dead["unit_price"]
    dead["purchase_value"] = dead["current_stock"] * dead["purchase_price"]
    if "expiry_date" in dead.columns:
        dead["is_expired"] = dead["expiry_date"].notna() & (dead["expiry_date"] < datetime.now())
        dead["perishable_loss"] = dead.apply(
            lambda r: r["purchase_value"] + r["total_storage_cost"] if r.get("is_expired") else 0, axis=1
        )
    return dead


def get_liquidation_strategies(inventory_df):
    """Generate liquidation strategies: return to supplier, sell at discount, competitor pricing."""
    dead = get_dead_stock_analysis(inventory_df)
    if len(dead) == 0:
        return []
    strategies = []
    for _, row in dead.iterrows():
        s = {"sku_id": row["sku_id"], "product_name": row["product_name"], "stock": int(row["current_stock"]),
             "reason": row.get("dead_stock_reason", "Unknown"), "inventory_value": row["inventory_value"],
             "storage_cost": row["total_storage_cost"]}
        if row.get("return_policy") == "Returnable":
            s["strategy"] = "Return to Supplier"
            s["recovery"] = row["purchase_value"] * 0.9
        elif row.get("competitor_price") and row["competitor_price"] < row["unit_price"]:
            s["strategy"] = "Discount Sale (match competitor)"
            s["recovery"] = row["current_stock"] * row["competitor_price"] * 0.85
        elif row.get("is_perishable") and row.get("is_expired", False):
            s["strategy"] = "Write-off (expired)"
            s["recovery"] = 0
        else:
            s["strategy"] = "Bulk Clearance Sale"
            s["recovery"] = row["inventory_value"] * 0.5
        strategies.append(s)
    return strategies


def get_resource_optimization(data):
    """Analyze how to reduce warehouse resource costs (storage, energy, dead stock units by zone)."""
    inv = data["inventory"]
    zones = data["zones"]
    zone_util = get_zone_utilization(zones)
    dead = get_dead_stock_analysis(inv)

    total_storage_cost = 0
    if len(dead) > 0 and "total_storage_cost" in dead.columns:
        total_storage_cost = float(dead["total_storage_cost"].sum())

    total_energy_daily = float(zones["energy_cost_per_day"].sum()) if "energy_cost_per_day" in zones.columns else 0.0
    total_energy_monthly = total_energy_daily * 30

    dead_units_total = int(dead["current_stock"].sum()) if len(dead) > 0 else 0

    zb = zone_util[["zone_id", "zone_name", "used_units", "capacity_units", "utilization_pct", "status"]].copy()
    if "energy_cost_per_day" in zones.columns:
        ec = zones.set_index("zone_id")["energy_cost_per_day"]
        zb["energy_cost_monthly"] = zb["zone_id"].map(ec).fillna(0) * 30
    else:
        zb["energy_cost_monthly"] = 0.0

    if len(dead) > 0 and "warehouse_zone" in dead.columns:
        du = dead.groupby("warehouse_zone", as_index=False)["current_stock"].sum()
        du.columns = ["zone_id", "dead_stock_units"]
        zb = zb.merge(du, on="zone_id", how="left")
    else:
        zb["dead_stock_units"] = 0
    zb["dead_stock_units"] = zb["dead_stock_units"].fillna(0).astype(int)
    zb["potential_space_freed_pct"] = (
        (zb["dead_stock_units"] / zb["used_units"].clip(lower=1)) * 100
    ).round(1)

    return {
        "total_storage_cost_dead": total_storage_cost,
        "dead_storage_cost": total_storage_cost,
        "total_energy_cost": total_energy_monthly,
        "total_energy_daily": total_energy_daily,
        "dead_stock_sku_count": len(dead),
        "potential_space_freed": dead_units_total,
        "critical_zones": int((zone_util["status"] == "Critical").sum()),
        "zone_breakdown": zb,
    }


def get_delay_root_causes(orders_df):
    """Analyze delay reasons across orders."""
    delayed = orders_df[orders_df["status"].isin(["Delayed", "Pending"])].copy()
    if "delay_reason" not in delayed.columns or len(delayed) == 0:
        return pd.DataFrame()
    return delayed.groupby("delay_reason").agg(
        count=("order_id", "count"),
        avg_delay=("delay_days", "mean"),
        max_delay=("delay_days", "max"),
        total_cost=("delivery_cost", "sum") if "delivery_cost" in delayed.columns else ("delay_days", "count"),
    ).reset_index().sort_values("count", ascending=False)


def get_route_efficiency(data):
    """Analyze route performance for cost and speed optimization."""
    orders = data["orders"]
    routes = data.get("routes", pd.DataFrame())
    if "route_id" not in orders.columns or len(routes) == 0:
        return pd.DataFrame()
    order_routes = orders.groupby("route_id").agg(
        orders=("order_id", "count"),
        avg_distance=("estimated_delivery_km", "mean"),
        avg_cost=("delivery_cost", "mean"),
        delayed=("status", lambda x: (x == "Delayed").sum()),
    ).reset_index()
    merged = order_routes.merge(routes[["route_id", "route_name", "route_type", "congestion_level", "best_vehicle"]], on="route_id", how="left")
    merged["delay_pct"] = (merged["delayed"] / merged["orders"] * 100).round(1)
    return merged.sort_values("avg_cost", ascending=False)


def get_zone_transport_analysis(data):
    """Analyze zones with transport capabilities and predictions."""
    zones = data["zones"]
    zone_util = get_zone_utilization(zones)
    result = zone_util.copy()
    if "allowed_vehicle_types" in zones.columns:
        result["allowed_vehicle_types"] = zones["allowed_vehicle_types"]
    if "max_vehicle_capacity_tons" in zones.columns:
        result["max_vehicle_capacity_tons"] = zones["max_vehicle_capacity_tons"]
    if "expected_critical_until" in zones.columns:
        result["expected_critical_until"] = zones["expected_critical_until"]
    if "congestion_reason" in zones.columns:
        result["congestion_reason"] = zones["congestion_reason"]
    if "energy_cost_per_day" in zones.columns:
        result["energy_cost_per_day"] = zones["energy_cost_per_day"]
    if "zone_throughput_rate" in zones.columns:
        result["zone_throughput_rate"] = zones["zone_throughput_rate"]
    if "revenue_potential_per_day" in zones.columns:
        result["revenue_potential_per_day"] = zones["revenue_potential_per_day"]
    if "utilization_trend" in zones.columns:
        result["utilization_trend"] = zones["utilization_trend"]
    return result


def get_customer_impact(orders_df):
    """Analyze customer impact from delays with improvement recommendations."""
    delayed = orders_df[orders_df["status"] == "Delayed"].copy()
    if len(delayed) == 0:
        return pd.DataFrame()
    impact = delayed.groupby("customer_name").agg(
        delayed_orders=("order_id", "count"),
        total_delay_days=("delay_days", "sum"),
        avg_delay=("delay_days", "mean"),
        total_value=("order_quantity", "sum"),
    ).reset_index().sort_values("delayed_orders", ascending=False)
    return impact


def get_picking_error_analysis(picking_df):
    """Analyze picking errors by type and picker."""
    errors_only = picking_df[picking_df["picking_errors"] > 0].copy()
    if "error_type" not in errors_only.columns or len(errors_only) == 0:
        return pd.DataFrame()
    return errors_only.groupby("error_type").agg(
        occurrences=("dispatch_id", "count"),
        total_errors=("picking_errors", "sum"),
        affected_pickers=("picker_name", "nunique"),
    ).reset_index().sort_values("total_errors", ascending=False)


def get_bay_optimization(picking_df):
    """Identify best and worst bays with cost analysis."""
    bays = get_dispatch_by_bay(picking_df)
    if "bay_cost_per_hour" not in picking_df.columns:
        return bays
    bay_cost = picking_df.groupby("loading_bay")["bay_cost_per_hour"].mean().reset_index()
    merged = bays.merge(bay_cost, on="loading_bay", how="left")
    merged["cost_per_dispatch"] = (merged["bay_cost_per_hour"] * merged["avg_time"] / 60).round(2)
    merged["efficiency_score"] = ((merged["total_dispatches"] / merged["avg_time"]) * (1 - merged["total_errors"] / merged["total_dispatches"].clip(lower=1)) * 100).round(1)
    return merged.sort_values("efficiency_score", ascending=False)


def generate_inventory_action_plan(inventory_df):
    """Full consolidated plan. Deterministic: same data produces the same report order and sections."""
    low = get_low_stock_items(inventory_df)
    overstock = get_overstock_items(inventory_df)
    dead = get_dead_stock_items(inventory_df)
    reorder = get_reorder_recommendations(inventory_df)
    ts = datetime.now().strftime('%d %b %Y, %H:%M:%S')
    est_cost = f"INR {reorder['estimated_cost'].sum():,.0f}" if len(reorder) > 0 else "N/A"
    rid = abs(hash((len(low), len(overstock), len(dead), len(reorder)))) % 90000 + 10000

    focus_title = "Full inventory action plan"
    focus_sub = "Consolidated low stock, reorder, overstock, and dead stock (deterministic from current data)"
    focus_color = "#2563EB"

    h = '<div style="background:white;border:1px solid #E5E7EB;border-radius:14px;overflow:hidden;box-shadow:0 4px 6px -1px rgba(0,0,0,0.07);">'
    h += _html_report_header(f"Inventory Action Plan &mdash; {focus_title}", focus_sub, ts)
    h += _html_kpi_strip([
        (len(low), "Critical Low Stock", "#EF4444"),
        (len(overstock), "Overstock SKUs", "#F59E0B"),
        (len(dead), "Dead Stock SKUs", "#8B5CF6"),
        (est_cost, "Est. Reorder Cost", "#2563EB"),
    ])

    reorder_sorted = reorder.sort_values(["estimated_cost", "sku_id"], ascending=[False, True]).head(10) if len(reorder) > 0 else reorder
    h += _html_section("Immediate Reorder Required", f"{len(low)} SKUs", "#EF4444")
    if len(reorder_sorted) > 0:
        rows = []
        for _, r in reorder_sorted.iterrows():
            rows.append([r['sku_id'], r['product_name'][:28], int(r['current_stock']), int(r['reorder_level']), int(r['recommended_reorder_qty']), r['supplier_name'][:20]])
        h += _html_table(["SKU", "Product", "Stock", "Reorder Lvl", "Order Qty", "Supplier"], rows, ['#111827', '#4B5563', '#EF4444', '#64748B', '#2563EB', '#64748B'])

    h += _html_section("Highest Investment Reorders", "Top by estimated cost", "#2563EB")
    if len(reorder) > 0:
        top_cost = reorder.nlargest(8, "estimated_cost").sort_values("sku_id")
        rows = [[r['sku_id'], str(r['product_name'])[:25], int(r['recommended_reorder_qty']), f"INR {r['estimated_cost']:,.0f}"] for _, r in top_cost.iterrows()]
        h += _html_table(["SKU", "Product", "Qty Needed", "Est. Cost"], rows, ['#111827', '#4B5563', '#2563EB', '#8B5CF6'])

    h += _html_section("Supplier dependency (low-stock SKUs)", "At-risk count by supplier", "#F59E0B")
    if len(low) > 0:
        supplier_risk = low.groupby("supplier_name").agg(
            at_risk=("sku_id", "count"),
            avg_stock=("current_stock", "mean"),
        ).reset_index().sort_values(["at_risk", "supplier_name"], ascending=[False, True]).head(8)
        rows = [[str(r['supplier_name'])[:22], int(r['at_risk']), f"{r['avg_stock']:.0f}"] for _, r in supplier_risk.iterrows()]
        h += _html_table(["Supplier", "At-Risk SKUs", "Avg Stock"], rows, ['#111827', '#EF4444', '#64748B'])

    over_sample = overstock.sort_values(["current_stock", "sku_id"], ascending=[False, True]).head(8) if len(overstock) > 0 else overstock
    h += _html_section("Overstock Alert", f"{len(overstock)} SKUs", "#F59E0B")
    if len(over_sample) > 0:
        rows = []
        for _, r in over_sample.iterrows():
            excess = r["current_stock"] - int(r["max_stock"] * 0.7)
            rows.append([r['sku_id'], r['product_name'][:28], int(r['current_stock']), int(r['max_stock']), f"~{excess}", r['warehouse_zone']])
        h += _html_table(["SKU", "Product", "Stock", "Max", "Excess", "Zone"], rows, ['#111827', '#4B5563', '#F59E0B', '#64748B', '#D97706', '#64748B'])

    dead_sample = dead.sort_values(["last_movement_date", "sku_id"]).head(8) if len(dead) > 0 else dead
    h += _html_section("Dead Stock Warning", f"{len(dead)} SKUs", "#8B5CF6")
    if len(dead_sample) > 0:
        rows = []
        for _, r in dead_sample.iterrows():
            days = (datetime.now() - r["last_movement_date"]).days
            rows.append([r['sku_id'], r['product_name'][:28], int(r['current_stock']), f"{days} days", r['warehouse_zone']])
        h += _html_table(["SKU", "Product", "Stock", "Inactive", "Zone"], rows, ['#111827', '#4B5563', '#64748B', '#8B5CF6', '#64748B'])

    selected_actions = [
        (f"<strong>Initiate procurement</strong> for {len(low)} critical low-stock SKUs immediately to prevent stockouts", "#EF4444"),
        (f"<strong>Review {len(overstock)} overstock items</strong> for promotional clearance, redistribution, or supplier return", "#F59E0B"),
        (f"<strong>Conduct dead stock audit</strong> on {len(dead)} items with no movement &gt; 60 days; consider liquidation or write-off", "#8B5CF6"),
        ("<strong>Rebalance inventory</strong> across warehouse zones to optimize space utilization and picking efficiency", "#2563EB"),
        ("<strong>Set up automated reorder alerts</strong> for SKUs approaching reorder level to prevent future stockouts", "#10B981"),
        ("<strong>Schedule weekly inventory audit</strong> with zone managers to track movement trends and catch risks early", "#8B5CF6"),
    ]
    if len(reorder) > 0:
        selected_actions.append((f"<strong>Estimated reorder investment:</strong> {est_cost} across {len(reorder)} SKUs", "#10B981"))

    h += _html_section("Recommended Actions")
    h += '<div style="padding:4px 0 16px 0;">'
    for i, (text, color) in enumerate(selected_actions):
        h += _html_action_item(i + 1, text, color)
    h += '</div>'

    h += f'<div style="background:#F8FAFC;padding:12px 32px;border-top:1px solid #E5E7EB;font-size:0.7rem;color:#9CA3AF;display:flex;justify-content:space-between;"><span>Generated by QubiWare AI &middot; Qubithm Corporation LLP</span><span>Report ID: RPT-{rid}</span></div>'
    h += '</div>'
    return h


def _report_wrap():
    return '<div style="background:white;border:1px solid #E5E7EB;border-radius:14px;overflow:hidden;box-shadow:0 4px 6px -1px rgba(0,0,0,0.07);margin-top:12px;">'


def generate_inventory_tab_report(inventory_df, data, tab_key: str):
    """
    HTML report scoped to the Inventory Intelligence tab the user is on.
    tab_key: low_stock | overstock | dead_stock | fast_moving | reorder | dead_stock_analysis | liquidation | resource
    """
    ts = datetime.now().strftime('%d %b %Y, %H:%M:%S')
    rid = abs(hash((tab_key, len(inventory_df)))) % 90000 + 10000
    h = _report_wrap()

    if tab_key == "low_stock":
        low = get_low_stock_items(inventory_df)
        h += _html_report_header("Low stock report", "SKUs at or below reorder level", ts)
        h += _html_kpi_strip([(len(low), "Low-stock SKUs", "#EF4444")])
        h += _html_section("Action list", f"{len(low)} SKUs need reorder or transfer", "#EF4444")
        if len(low) > 0:
            df = low.sort_values(["current_stock", "sku_id"]).head(15)
            rows = [[r['sku_id'], str(r['product_name'])[:26], int(r['current_stock']), int(r['reorder_level']), str(r['warehouse_zone']), str(r['supplier_name'])[:18]] for _, r in df.iterrows()]
            h += _html_table(["SKU", "Product", "Stock", "Reorder", "Zone", "Supplier"], rows, ['#111827', '#4B5563', '#EF4444', '#64748B', '#64748B', '#64748B'])
        else:
            h += '<div style="padding:16px 24px;color:#64748B;">No low-stock SKUs.</div>'
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Confirm lead times</strong> with suppliers for the SKUs above and raise purchase orders by priority (lowest stock first).", "#EF4444")
        h += _html_action_item(2, "<strong>Reserve inbound capacity</strong> for the highest-impact lines to avoid floor stockouts.", "#2563EB")
        h += '</div>'

    elif tab_key == "overstock":
        over = get_overstock_items(inventory_df)
        h += _html_report_header("Overstock report", "SKUs at or above 85% of max stock", ts)
        h += _html_kpi_strip([(len(over), "Overstock SKUs", "#F59E0B")])
        h += _html_section("Candidates for clearance or rebalance", f"{len(over)} SKUs", "#F59E0B")
        if len(over) > 0:
            df = over.sort_values(["current_stock", "sku_id"], ascending=[False, True]).head(15)
            rows = [[r['sku_id'], str(r['product_name'])[:26], int(r['current_stock']), int(r['max_stock']), str(r['warehouse_zone'])] for _, r in df.iterrows()]
            h += _html_table(["SKU", "Product", "Stock", "Max", "Zone"], rows, ['#111827', '#4B5563', '#F59E0B', '#64748B', '#64748B'])
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Run promotion or bundle</strong> for slow-turn overstock lines; transfer excess to regional hubs if applicable.", "#F59E0B")
        h += _html_action_item(2, "<strong>Freeze reorders</strong> on overstock SKUs until a target cover week is reached.", "#2563EB")
        h += '</div>'

    elif tab_key == "dead_stock":
        dead = get_dead_stock_items(inventory_df)
        h += _html_report_header("Dead stock listing report", "No movement in 60+ days", ts)
        h += _html_kpi_strip([(len(dead), "Dead SKUs", "#8B5CF6")])
        h += _html_section("SKU list", f"{len(dead)} items", "#8B5CF6")
        if len(dead) > 0:
            d2 = dead.copy()
            d2["days_inactive"] = (datetime.now() - d2["last_movement_date"]).dt.days
            df = d2.sort_values(["days_inactive", "sku_id"], ascending=[False, True]).head(15)
            rows = [[r['sku_id'], str(r['product_name'])[:26], int(r['current_stock']), int(r['days_inactive']), str(r['warehouse_zone'])] for _, r in df.iterrows()]
            h += _html_table(["SKU", "Product", "Stock", "Days inactive", "Zone"], rows, ['#111827', '#4B5563', '#64748B', '#8B5CF6', '#64748B'])
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Segregate dead stock</strong> physically and tag for liquidation, return, or write-off workflow.", "#8B5CF6")
        h += '</div>'

    elif tab_key == "fast_moving":
        fast = get_fast_moving_skus(inventory_df, 20)
        h += _html_report_header("Fast-moving SKU report", "Top SKUs by average daily sales", ts)
        h += _html_kpi_strip([(len(fast), "Top movers (view)", "#10B981")])
        h += _html_section("Protect availability on high velocity", "Top 15 by sales", "#10B981")
        df = fast.sort_values(["avg_daily_sales", "sku_id"], ascending=[False, True]).head(15)
        rows = [[r['sku_id'], str(r['product_name'])[:26], f"{r['avg_daily_sales']:.1f}", int(r['current_stock']), int(r['reorder_level']), str(r['warehouse_zone'])] for _, r in df.iterrows()]
        h += _html_table(["SKU", "Product", "Daily sales", "Stock", "Reorder", "Zone"], rows, ['#111827', '#4B5563', '#10B981', '#64748B', '#64748B', '#64748B'])
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Prioritize slotting</strong> in fast-pick zones and maintain safety stock above reorder for these SKUs.", "#10B981")
        h += '</div>'

    elif tab_key == "reorder":
        reorder = get_reorder_recommendations(inventory_df)
        tot = reorder['estimated_cost'].sum() if len(reorder) > 0 else 0
        h += _html_report_header("Reorder recommendations report", "Quantities and estimated investment", ts)
        h += _html_kpi_strip([
            (len(reorder), "SKUs to reorder", "#2563EB"),
            (f"INR {tot:,.0f}" if tot else "INR 0", "Est. investment", "#8B5CF6"),
        ])
        h += _html_section("Recommended purchase lines", "Sorted by estimated cost", "#2563EB")
        if len(reorder) > 0:
            df = reorder.sort_values(["estimated_cost", "sku_id"], ascending=[False, True]).head(15)
            rows = [[r['sku_id'], str(r['product_name'])[:24], int(r['recommended_reorder_qty']), f"INR {r['estimated_cost']:,.0f}", str(r['supplier_name'])[:16]] for _, r in df.iterrows()]
            h += _html_table(["SKU", "Product", "Qty", "Est. cost", "Supplier"], rows, ['#111827', '#4B5563', '#2563EB', '#8B5CF6', '#64748B'])
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Issue POs</strong> in descending cost impact; align delivery windows with inbound dock capacity.", "#2563EB")
        h += '</div>'

    elif tab_key == "dead_stock_analysis":
        da = get_dead_stock_analysis(inventory_df)
        h += _html_report_header("Dead stock root-cause report", "Reasons, holding cost, and perishable exposure", ts)
        if len(da) == 0:
            h += '<div style="padding:20px 24px;color:#64748B;">No dead stock SKUs in the current dataset.</div>'
        else:
            tstor = float(da["total_storage_cost"].sum()) if "total_storage_cost" in da.columns else 0
            tval = float(da["inventory_value"].sum()) if "inventory_value" in da.columns else 0
            exp = int(da["is_expired"].sum()) if "is_expired" in da.columns else 0
            h += _html_kpi_strip([(len(da), "Dead SKUs", "#8B5CF6"), (f"INR {tstor:,.0f}", "Storage cost", "#EF4444"), (f"INR {tval:,.0f}", "Tied-up value", "#F59E0B"), (exp, "Expired", "#DC2626")])
            if "dead_stock_reason" in da.columns:
                h += _html_section("Root causes (counts)", "Why stock is not moving", "#8B5CF6")
                rc = da["dead_stock_reason"].value_counts().reset_index()
                rc.columns = ["reason", "cnt"]
                rows = [[str(r['reason'])[:40], int(r['cnt'])] for _, r in rc.iterrows()]
                h += _html_table(["Reason", "SKUs"], rows, ['#111827', '#8B5CF6'])
            h += _html_section("Highest holding-cost lines", "Top 10 by total storage cost", "#EF4444")
            if "total_storage_cost" in da.columns:
                top = da.sort_values(["total_storage_cost", "sku_id"], ascending=[False, True]).head(10)
                rows = [[r['sku_id'], str(r['product_name'])[:24], f"INR {float(r['total_storage_cost']):,.0f}", str(r.get('dead_stock_reason', ''))[:28]] for _, r in top.iterrows()]
                h += _html_table(["SKU", "Product", "Storage cost", "Reason"], rows, ['#111827', '#4B5563', '#EF4444', '#64748B'])
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Address top reasons</strong> (price, reliability, bulk-only) with commercial and merchandising actions per bucket.", "#8B5CF6")
        h += '</div>'

    elif tab_key == "liquidation":
        strat = get_liquidation_strategies(inventory_df)
        h += _html_report_header("Liquidation & recovery report", "Per-SKU strategy and estimated recovery", ts)
        if not strat:
            h += '<div style="padding:20px 24px;color:#64748B;">No dead stock items to liquidate.</div>'
        else:
            df = pd.DataFrame(strat)
            tot_v = float(df["inventory_value"].sum())
            tot_r = float(df["recovery"].sum())
            h += _html_kpi_strip([
                (len(df), "SKUs in plan", "#8B5CF6"),
                (f"INR {tot_v:,.0f}", "Tied-up value", "#EF4444"),
                (f"INR {tot_r:,.0f}", "Est. recovery", "#10B981"),
                (f"{(100*tot_r/max(tot_v,1)):.0f}%", "Recovery %", "#2563EB"),
            ])
            h += _html_section("Line-level liquidation plan", "Return / discount / bulk / write-off", "#8B5CF6")
            df2 = df.sort_values(["recovery", "sku_id"], ascending=[False, True]).head(15)
            rows = [[r['sku_id'], str(r['product_name'])[:22], str(r['strategy'])[:22], f"INR {float(r['recovery']):,.0f}", str(r.get('reason', ''))[:20]] for _, r in df2.iterrows()]
            h += _html_table(["SKU", "Product", "Strategy", "Est. recovery", "Dead reason"], rows, ['#111827', '#4B5563', '#2563EB', '#10B981', '#64748B'])
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Execute by strategy bucket</strong>: supplier returns first, then competitive match pricing, then bulk clearance; write off expired per policy.", "#10B981")
        h += '</div>'

    elif tab_key == "resource":
        opt = get_resource_optimization(data)
        h += _html_report_header("Resource & warehouse charge report", "Dead-stock holding cost and zone energy footprint", ts)
        h += _html_kpi_strip([
            (f"INR {opt['dead_storage_cost']:,.0f}", "Dead storage est.", "#EF4444"),
            (f"INR {opt['total_energy_cost']:,.0f}", "Energy /mo (est.)", "#F59E0B"),
            (opt["critical_zones"], "Critical zones", "#DC2626"),
            (f"{opt['potential_space_freed']:,}", "Dead units", "#8B5CF6"),
        ])
        h += _html_section("Zone footprint", "Sorted by dead stock units", "#2563EB")
        zb = opt["zone_breakdown"].sort_values(["dead_stock_units", "zone_id"], ascending=[False, True])
        rows = [[r['zone_name'], f"{r['utilization_pct']}%", f"INR {float(r['energy_cost_monthly']):,.0f}", int(r['dead_stock_units'])] for _, r in zb.iterrows()]
        h += _html_table(["Zone", "Utilization", "Energy/mo", "Dead units"], rows, ['#111827', '#64748B', '#F59E0B', '#8B5CF6'])
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Clear dead units</strong> in high-energy zones first to maximize cost avoidance per square foot.", "#EF4444")
        h += _html_action_item(2, "<strong>Consolidate</strong> slow movers out of critical zones to reduce congestion overtime.", "#2563EB")
        h += '</div>'

    else:
        h += _html_report_header("Inventory report", tab_key, ts)
        h += '<div style="padding:16px 24px;color:#64748B;">Unknown report type.</div>'

    h += f'<div style="background:#F8FAFC;padding:12px 32px;border-top:1px solid #E5E7EB;font-size:0.7rem;color:#9CA3AF;">Generated by QubiWare AI &middot; Report ID RPT-{rid} &middot; {ts}</div></div>'
    return h


def generate_dispatch_risk_summary(orders_df, picking_df):
    delayed = get_delayed_orders(orders_df)
    pending = get_pending_orders(orders_df)
    high_priority = get_high_priority_delayed(orders_df)
    zone_delay = get_delay_by_zone(orders_df)
    customer_delay = get_delay_by_customer(orders_df)
    bay_stats = get_dispatch_by_bay(picking_df)
    ts = datetime.now().strftime('%d %b %Y, %H:%M:%S')
    avg_delay = f"{delayed['delay_days'].mean():.1f}" if len(delayed) > 0 else "0"
    rid = abs(hash((len(delayed), len(pending), len(zone_delay)))) % 90000 + 10000

    focus_sub = "All zones, customers, bays, and priorities in one view (deterministic from current data)"

    h = '<div style="background:white;border:1px solid #E5E7EB;border-radius:14px;overflow:hidden;box-shadow:0 4px 6px -1px rgba(0,0,0,0.07);">'
    h += _html_report_header("Consolidated dispatch risk summary", focus_sub, ts)
    h += _html_kpi_strip([
        (len(delayed), "Delayed Orders", "#EF4444"),
        (len(pending), "Pending Orders", "#F59E0B"),
        (len(high_priority), "High Priority", "#DC2626"),
        (f"{avg_delay} days", "Avg Delay", "#8B5CF6"),
    ])

    h += _html_section("Zones causing maximum delay", "Top 5 by count", "#EF4444")
    if len(zone_delay) > 0:
        top_zones = zone_delay.nlargest(5, "count").sort_values("warehouse_zone")
        rows = [[r['warehouse_zone'], int(r['count']), f"{r['mean']:.1f} days"] for _, r in top_zones.iterrows()]
        h += _html_table(["Zone", "Delayed Orders", "Avg Delay"], rows, ['#111827', '#EF4444', '#64748B'])

    h += _html_section("Customer delay exposure", "Top 6 by delayed order count", "#F59E0B")
    if len(customer_delay) > 0:
        cust_top = customer_delay.sort_values(["count", "customer_name"], ascending=[False, True]).head(6)
        rows = [[r['customer_name'], int(r['count']), f"{r['sum']:.0f} days", f"{r['mean']:.1f} days"] for _, r in cust_top.iterrows()]
        h += _html_table(["Customer", "Delayed Orders", "Total Delay", "Avg Delay"], rows, ['#111827', '#F59E0B', '#64748B', '#8B5CF6'])

    h += _html_section("Loading bay performance", "Sorted by avg dispatch time (slowest first)", "#2563EB")
    if len(bay_stats) > 0:
        bay_sorted = bay_stats.sort_values(["avg_time", "loading_bay"], ascending=[False, True]).head(6)
        rows = [[r['loading_bay'], f"{r['avg_time']:.0f} min", int(r['total_dispatches']), int(r['total_errors'])] for _, r in bay_sorted.iterrows()]
        h += _html_table(["Bay", "Avg Time", "Dispatches", "Errors"], rows, ['#111827', '#8B5CF6', '#64748B', '#EF4444'])

    h += _html_section("Delay severity by priority", "Delayed orders only", "#DC2626")
    if len(delayed) > 0:
        prio_breakdown = delayed.groupby("priority").agg(count=("order_id", "count"), avg_delay=("delay_days", "mean"), max_delay=("delay_days", "max")).reset_index().sort_values("priority")
        rows = [[r['priority'], int(r['count']), f"{r['avg_delay']:.1f} days", f"{int(r['max_delay'])} days"] for _, r in prio_breakdown.iterrows()]
        h += _html_table(["Priority", "Count", "Avg Delay", "Max Delay"], rows, ['#111827', '#EF4444', '#64748B', '#DC2626'])

    selected_actions = [
        (f"<strong>Prioritize {len(high_priority)} high-priority delayed orders</strong> for immediate dispatch to prevent SLA breaches", "#EF4444"),
        ("<strong>Investigate congested zones</strong> and reassign picking resources to reduce zone-level delays", "#F59E0B"),
        ("<strong>Address loading bay bottlenecks</strong> with staffing, equipment, or load redistribution", "#8B5CF6"),
        ("<strong>Communicate revised timelines</strong> to impacted customers proactively", "#2563EB"),
        ("<strong>Review picker allocation</strong> for highest-delay zones and introduce batch picking where applicable", "#10B981"),
        ("<strong>Implement real-time dispatch tracking</strong> to catch delays before they breach SLA", "#06B6D4"),
    ]

    h += _html_section("Recommended Actions")
    h += '<div style="padding:4px 0 16px 0;">'
    for i, (text, color) in enumerate(selected_actions):
        h += _html_action_item(i + 1, text, color)
    h += '</div>'

    h += f'<div style="background:#F8FAFC;padding:12px 32px;border-top:1px solid #E5E7EB;font-size:0.7rem;color:#9CA3AF;display:flex;justify-content:space-between;"><span>Generated by QubiWare AI &middot; Qubithm Corporation LLP</span><span>Report ID: RPT-{rid}</span></div>'
    h += '</div>'
    return h


def generate_dispatch_tab_report(data, tab_key: str):
    """
    HTML report scoped to one Dispatch Intelligence tab only.
    tab_key: delayed | pending | picking_errors | loading_bay | delay_root_causes | route_bay | customer_impact
    """
    orders = data["orders"]
    picking = data["picking"]
    ts = datetime.now().strftime('%d %b %Y, %H:%M:%S')
    rid = abs(hash((tab_key, len(orders), len(picking)))) % 90000 + 10000
    h = _report_wrap()

    delayed = get_delayed_orders(orders)
    pending = get_pending_orders(orders)
    high_priority = get_high_priority_delayed(orders)
    avg_delay = f"{delayed['delay_days'].mean():.1f}" if len(delayed) > 0 else "0"

    if tab_key == "delayed":
        h += _html_report_header("Delayed orders report", "Orders beyond promised dispatch", ts)
        h += _html_kpi_strip([
            (len(delayed), "Delayed", "#EF4444"),
            (len(high_priority), "High priority", "#DC2626"),
            (f"{avg_delay}d", "Avg delay", "#8B5CF6"),
        ])
        h += _html_section("Worst delayed lines", "Top 12 by delay days", "#EF4444")
        if len(delayed) > 0:
            d2 = delayed.sort_values(["delay_days", "order_id"], ascending=[False, True]).head(12)
            rows = [[r["order_id"], str(r["customer_name"])[:18], str(r["warehouse_zone"]), int(r["delay_days"]), str(r["priority"])] for _, r in d2.iterrows()]
            h += _html_table(["Order", "Customer", "Zone", "Delay days", "Priority"], rows, ["#111827", "#4B5563", "#64748B", "#EF4444", "#64748B"])
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Triage by priority</strong> and promised date; clear the longest delays first.", "#EF4444")
        h += "</div>"

    elif tab_key == "pending":
        h += _html_report_header("Pending orders report", "Awaiting dispatch", ts)
        h += _html_kpi_strip([(len(pending), "Pending orders", "#F59E0B")])
        h += _html_section("Pending queue", "Soonest promised dispatch first", "#F59E0B")
        if len(pending) > 0:
            p2 = pending.sort_values(["promised_dispatch_date", "order_id"]).head(15)
            rows = []
            for _, r in p2.iterrows():
                pd_str = r["promised_dispatch_date"].strftime("%Y-%m-%d") if hasattr(r["promised_dispatch_date"], "strftime") else str(r["promised_dispatch_date"])[:10]
                rows.append([r["order_id"], str(r["customer_name"])[:18], str(r["warehouse_zone"]), pd_str, str(r["priority"])])
            h += _html_table(["Order", "Customer", "Zone", "Promised", "Priority"], rows, ["#111827", "#4B5563", "#64748B", "#F59E0B", "#64748B"])
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Slot picks and bays</strong> to drain pending before promised dates slip to delayed.", "#F59E0B")
        h += "</div>"

    elif tab_key == "picking_errors":
        pe = get_picking_errors_by_picker(picking)
        h += _html_report_header("Picking errors report", "Errors by picker and by type", ts)
        tot_err = int(pe["total_errors"].sum()) if len(pe) > 0 else 0
        h += _html_kpi_strip([(tot_err, "Total errors", "#EF4444"), (len(pe), "Pickers", "#64748B")])
        h += _html_section("Picker leaderboard", "Highest errors first", "#EF4444")
        if len(pe) > 0:
            top = pe.sort_values(["total_errors", "picker_name"], ascending=[False, True]).head(12)
            rows = [[str(r["picker_name"])[:22], int(r["total_errors"]), int(r["total_picks"]), f"{r['avg_errors_per_pick']:.2f}"] for _, r in top.iterrows()]
            h += _html_table(["Picker", "Errors", "Picks", "Avg/pick"], rows, ["#111827", "#EF4444", "#64748B", "#64748B"])
        err_analysis = get_picking_error_analysis(picking)
        if len(err_analysis) > 0:
            h += _html_section("Error types", "Frequency", "#F59E0B")
            ea = err_analysis.sort_values(["total_errors", "error_type"], ascending=[False, True])
            rows = [[str(r["error_type"])[:28], int(r["occurrences"]), int(r["total_errors"])] for _, r in ea.iterrows()]
            h += _html_table(["Error type", "Occurrences", "Total errors"], rows, ["#111827", "#EF4444", "#DC2626"])
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Coach</strong> high-error pickers; add verification for the dominant error types.", "#EF4444")
        h += "</div>"

    elif tab_key == "loading_bay":
        bay_stats = get_dispatch_by_bay(picking)
        h += _html_report_header("Loading bay report", "Throughput and time by bay", ts)
        h += _html_kpi_strip([(len(bay_stats), "Bays", "#2563EB")])
        h += _html_section("Bay performance", "Slowest average time first", "#8B5CF6")
        if len(bay_stats) > 0:
            bs = bay_stats.sort_values(["avg_time", "loading_bay"], ascending=[False, True])
            rows = [[r["loading_bay"], f"{r['avg_time']:.0f} min", int(r["total_dispatches"]), int(r["total_errors"])] for _, r in bs.iterrows()]
            h += _html_table(["Bay", "Avg time", "Dispatches", "Errors"], rows, ["#111827", "#8B5CF6", "#64748B", "#EF4444"])
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Balance load</strong> across bays; inspect equipment and staging on slowest bays.", "#8B5CF6")
        h += "</div>"

    elif tab_key == "delay_root_causes":
        delay_causes = get_delay_root_causes(orders)
        h += _html_report_header("Delay root causes report", "Reasons for delayed and pending orders", ts)
        h += _html_kpi_strip([
            (len(delay_causes), "Reason buckets", "#EF4444"),
            (len(delayed) + len(pending), "Affected orders", "#F59E0B"),
        ])
        h += _html_section("Reason breakdown", "By order count", "#EF4444")
        if len(delay_causes) > 0:
            dc = delay_causes.sort_values(["count", "delay_reason"], ascending=[False, True])
            rows = [[str(r["delay_reason"])[:32], int(r["count"]), f"{float(r['avg_delay']):.1f}d", int(r["max_delay"])] for _, r in dc.iterrows()]
            h += _html_table(["Reason", "Orders", "Avg delay", "Max delay"], rows, ["#111827", "#EF4444", "#64748B", "#DC2626"])
        err_analysis = get_picking_error_analysis(picking)
        if len(err_analysis) > 0:
            h += _html_section("Picking error types", "Cross-check with fulfillment quality", "#F59E0B")
            rows = [[str(r["error_type"])[:26], int(r["total_errors"])] for _, r in err_analysis.head(8).iterrows()]
            h += _html_table(["Error type", "Total errors"], rows, ["#111827", "#EF4444"])
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Assign owners</strong> per top delay reason (congestion, bay, picker shortage, route).", "#EF4444")
        h += "</div>"

    elif tab_key == "route_bay":
        bay_opt = get_bay_optimization(picking)
        route_eff = get_route_efficiency(data)
        h += _html_report_header("Route & bay optimization report", "Efficiency and route economics", ts)
        h += _html_kpi_strip([(len(bay_opt), "Bays ranked", "#10B981"), (len(route_eff), "Routes", "#2563EB")])
        h += _html_section("Bay efficiency", "Higher score is better", "#10B981")
        if len(bay_opt) > 0 and "efficiency_score" in bay_opt.columns:
            bo = bay_opt.sort_values(["efficiency_score", "loading_bay"], ascending=[False, True]).head(8)
            rows = []
            for _, r in bo.iterrows():
                cpd = float(r["cost_per_dispatch"]) if pd.notna(r.get("cost_per_dispatch")) else 0.0
                rows.append([r["loading_bay"], f"{r['efficiency_score']:.1f}", f"{r['avg_time']:.0f}m", int(r["total_dispatches"]), f"INR {cpd:,.0f}"])
            h += _html_table(["Bay", "Score", "Avg time", "Dispatches", "Cost/dispatch"], rows, ["#111827", "#10B981", "#64748B", "#64748B", "#8B5CF6"])
        h += _html_section("Route performance", "Higher cost and delay % need attention", "#2563EB")
        if len(route_eff) > 0:
            re = route_eff.sort_values(["avg_cost", "route_id"], ascending=[False, True]).head(10)
            rows = []
            for _, r in re.iterrows():
                dp = f"{float(r['delay_pct']):.1f}%" if "delay_pct" in re.columns and pd.notna(r.get("delay_pct")) else ""
                ac = f"INR {float(r['avg_cost']):,.0f}" if "avg_cost" in re.columns and pd.notna(r.get("avg_cost")) else ""
                rows.append([str(r.get("route_id", "")), str(r.get("route_name", ""))[:20], ac, dp, str(r.get("best_vehicle", ""))[:14]])
            h += _html_table(["Route", "Name", "Avg cost", "Delay %", "Vehicle"], rows, ["#111827", "#4B5563", "#8B5CF6", "#EF4444", "#64748B"])
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Favor best bays</strong> and right-sized vehicles on high-delay, high-cost routes.", "#2563EB")
        h += "</div>"

    elif tab_key == "customer_impact":
        cust = get_customer_impact(orders)
        h += _html_report_header("Customer impact report", "Customers by delayed-order exposure", ts)
        h += _html_kpi_strip([(len(cust), "Customers affected", "#EF4444")])
        h += _html_section("Severity ranking", "By delayed order count", "#EF4444")
        if len(cust) > 0:
            c2 = cust.sort_values(["delayed_orders", "customer_name"], ascending=[False, True]).head(12)
            rows = [[str(r["customer_name"])[:22], int(r["delayed_orders"]), f"{float(r['total_delay_days']):.0f}", f"{float(r['avg_delay']):.1f}d"] for _, r in c2.iterrows()]
            h += _html_table(["Customer", "Delayed", "Total delay days", "Avg delay"], rows, ["#111827", "#EF4444", "#8B5CF6", "#64748B"])
        h += _html_section("Recommended actions")
        h += '<div style="padding:4px 0 16px 0;">'
        h += _html_action_item(1, "<strong>Proactive comms</strong> and recovery for customers with the most delayed orders.", "#EF4444")
        h += "</div>"

    else:
        h += _html_report_header("Dispatch report", str(tab_key), ts)
        h += '<div style="padding:16px 24px;color:#64748B;">Unknown report type.</div>'

    h += f'<div style="background:#F8FAFC;padding:12px 32px;border-top:1px solid #E5E7EB;font-size:0.7rem;color:#9CA3AF;">QubiWare AI &middot; RPT-{rid} &middot; {ts}</div></div>'
    return h
