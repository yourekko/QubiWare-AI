"""Daily report generation for QubiWare AI."""

from datetime import datetime
from utils.analytics import (
    get_low_stock_items, get_overstock_items, get_dead_stock_items,
    get_delayed_orders, get_pending_orders, get_high_priority_delayed,
    get_zone_utilization, get_picking_errors_by_picker,
    get_inbound_mismatches, get_supplier_issues, get_dispatch_by_bay,
    compute_kpis
)


def _compute_report_data(data):
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
    high_priority = get_high_priority_delayed(orders)
    zone_util = get_zone_utilization(zones)
    picker_errors = get_picking_errors_by_picker(picking)
    mismatches = get_inbound_mismatches(inbound)
    supplier_issues = get_supplier_issues(inbound)
    bay_stats = get_dispatch_by_bay(picking)

    critical_zones = zone_util[zone_util["status"] == "Critical"]
    warning_zones = zone_util[zone_util["status"] == "Warning"]
    zone_delay = delayed.groupby("warehouse_zone")["delay_days"].count().sort_values(ascending=False)

    return dict(
        kpis=kpis, low_stock=low_stock, overstock=overstock, dead_stock=dead_stock,
        delayed=delayed, pending=pending, high_priority=high_priority,
        zone_util=zone_util, picker_errors=picker_errors, mismatches=mismatches,
        supplier_issues=supplier_issues, bay_stats=bay_stats,
        critical_zones=critical_zones, warning_zones=warning_zones,
        zone_delay=zone_delay,
        report_date=datetime.now().strftime("%d %B %Y"),
        report_time=datetime.now().strftime("%H:%M"),
    )


def _safe(text):
    """Clean text for FPDF."""
    if text is None:
        return ""
    return str(text)


def generate_pdf_report(data):
    """Generate a professionally formatted PDF report."""
    from fpdf import FPDF

    d = _compute_report_data(data)
    kpis = d["kpis"]

    class QubiPDF(FPDF):
        def _draw_header_bar(self):
            self.set_fill_color(15, 23, 42)
            self.rect(0, 0, 210, 48, "F")

            self.set_fill_color(30, 41, 59)
            self.rect(0, 48, 210, 4, "F")

            self.set_text_color(56, 189, 248)
            self.set_font("Helvetica", "B", 8)
            self.set_xy(16, 10)
            self.cell(0, 4, "DAILY WAREHOUSE PERFORMANCE REPORT")

            self.set_text_color(255, 255, 255)
            self.set_font("Helvetica", "B", 18)
            self.set_xy(16, 17)
            self.cell(0, 9, "QubiWare AI")

            self.set_text_color(148, 163, 184)
            self.set_font("Helvetica", "", 8.5)
            self.set_xy(16, 28)
            self.cell(0, 5, _safe(f"{d['report_date']}  |  {d['report_time']}  |  Qubithm Corporation LLP"))

            self.set_xy(16, 35)
            self.set_text_color(100, 116, 139)
            self.set_font("Helvetica", "", 7.5)
            self.cell(0, 4, "AI Control Tower for Warehouse, Inventory and Dispatch Operations")

        def footer(self):
            self.set_y(-15)
            self.set_draw_color(226, 232, 240)
            self.line(15, self.get_y(), 195, self.get_y())
            self.ln(2)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(148, 163, 184)
            self.cell(0, 4, _safe(f"QubiWare AI  |  Qubithm Corporation LLP  |  Page {self.page_no()}"), align="C")

    pdf = QubiPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf._draw_header_bar()
    pdf.set_y(58)

    def section_title(num, title):
        pdf.ln(3)
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(226, 232, 240)
        y = pdf.get_y()
        pdf.rect(15, y, 180, 8, "F")
        pdf.line(15, y + 8, 195, y + 8)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(15, 23, 42)
        pdf.set_xy(17, y)
        pdf.cell(0, 8, _safe(f"{num}.  {title}"))
        pdf.ln(10)

    def body_text(text):
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(51, 65, 85)
        pdf.set_x(16)
        pdf.multi_cell(178, 4.5, _safe(text))
        pdf.ln(2)

    def kpi_box(items):
        start_x = 16
        box_w = 34.5
        gap = 1
        y = pdf.get_y()
        for i, (label, value) in enumerate(items):
            x = start_x + i * (box_w + gap)
            pdf.set_fill_color(248, 250, 252)
            pdf.set_draw_color(226, 232, 240)
            pdf.rect(x, y, box_w, 16, "DF")
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(15, 23, 42)
            pdf.set_xy(x, y + 1)
            pdf.cell(box_w, 7, _safe(str(value)), align="C")
            pdf.set_font("Helvetica", "", 6)
            pdf.set_text_color(100, 116, 139)
            pdf.set_xy(x, y + 8)
            pdf.cell(box_w, 5, _safe(label), align="C")
        pdf.set_y(y + 19)

    def table(headers, rows, widths):
        pdf.set_fill_color(15, 23, 42)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_x(16)
        for i, h in enumerate(headers):
            pdf.cell(widths[i], 7, _safe(f" {h}"), border=0, fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 7.5)
        fill = False
        for row in rows:
            if fill:
                pdf.set_fill_color(248, 250, 252)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(51, 65, 85)
            pdf.set_x(16)
            for i, val in enumerate(row):
                pdf.cell(widths[i], 6, _safe(f" {str(val)[:32]}"), border=0, fill=True)
            pdf.ln()
            fill = not fill

        pdf.set_draw_color(226, 232, 240)
        pdf.line(16, pdf.get_y(), 16 + sum(widths), pdf.get_y())
        pdf.ln(3)

    def action_item(text, color_rgb):
        r, g, b = color_rgb
        pdf.set_fill_color(r, g, b)
        y = pdf.get_y()
        pdf.rect(16, y, 2, 5, "F")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(51, 65, 85)
        pdf.set_xy(20, y)
        pdf.cell(0, 5, _safe(text))
        pdf.ln(6)

    # --- 1. Executive Summary ---
    section_title("1", "EXECUTIVE SUMMARY")
    body_text(
        f"Today's operations show {len(d['low_stock'])} SKUs at critical low stock, "
        f"{len(d['delayed'])} delayed orders ({len(d['high_priority'])} high-priority), "
        f"and warehouse utilization averaging {kpis['Warehouse Utilization %']}%. "
        f"There are {len(d['critical_zones'])} zone(s) in critical state requiring immediate attention. "
        f"Picking accuracy stands at {kpis['Picking Accuracy %']}% with "
        f"{len(d['mismatches'])} inbound shipment mismatches."
    )

    # --- 2. KPIs ---
    section_title("2", "KEY PERFORMANCE INDICATORS")
    kpi_box([
        ("TOTAL SKUs", f"{kpis['Total SKUs']:,}"),
        ("TOTAL ORDERS", f"{kpis['Total Orders']:,}"),
        ("LOW STOCK", kpis["Low Stock Items"]),
        ("OVERSTOCK", kpis["Overstock Items"]),
        ("DELAYED ORDERS", kpis["Delayed Orders"]),
    ])
    kpi_box([
        ("PENDING", kpis["Pending Dispatches"]),
        ("AVG DELAY", f"{kpis['Avg Delay Days']} days"),
        ("UTILIZATION", f"{kpis['Warehouse Utilization %']}%"),
        ("PICK ACCURACY", f"{kpis['Picking Accuracy %']}%"),
        ("MISMATCHES", kpis["Inbound Mismatch Count"]),
    ])

    # --- 3. Inventory Risks ---
    section_title("3", "INVENTORY RISKS")
    body_text(f"Low Stock: {len(d['low_stock'])}   |   Overstock: {len(d['overstock'])}   |   Dead Stock: {len(d['dead_stock'])}")
    w = [24, 52, 20, 22, 42]
    table(
        ["SKU", "Product", "Stock", "Reorder", "Supplier"],
        [[r["sku_id"], r["product_name"][:28], r["current_stock"], r["reorder_level"], r["supplier_name"][:22]]
         for _, r in d["low_stock"].head(8).iterrows()],
        w
    )

    # --- 4. Dispatch Risks ---
    section_title("4", "DISPATCH RISKS")
    body_text(
        f"Delayed: {len(d['delayed'])}   |   Pending: {len(d['pending'])}   |   "
        f"High-Priority: {len(d['high_priority'])}   |   Avg Delay: {kpis['Avg Delay Days']} days"
    )
    w = [50, 40]
    table(
        ["Zone", "Delayed Orders"],
        [[zone, int(count)] for zone, count in d["zone_delay"].head(5).items()],
        w
    )

    # --- 5. Zone Status ---
    section_title("5", "WAREHOUSE ZONE STATUS")
    w = [52, 24, 46, 24]
    table(
        ["Zone", "Utilization", "Used / Capacity", "Status"],
        [[r["zone_name"], f"{r['utilization_pct']}%",
          f"{r['used_units']:,} / {r['capacity_units']:,}", r["status"]]
         for _, r in d["zone_util"].sort_values("utilization_pct", ascending=False).iterrows()],
        w
    )

    # --- 6. Supplier Issues ---
    section_title("6", "SUPPLIER / INBOUND ISSUES")
    body_text(f"Total shipments with quantity mismatch: {len(d['mismatches'])}")
    if len(d["supplier_issues"]) > 0:
        w = [60, 35, 40]
        table(
            ["Supplier", "Mismatches", "Shortage (units)"],
            [[r["supplier_name"], int(r["mismatch_count"]), int(r["total_shortage"])]
             for _, r in d["supplier_issues"].head(5).iterrows()],
            w
        )

    # --- 7. Picking Accuracy ---
    section_title("7", "PICKING ACCURACY")
    body_text(f"Overall Picking Accuracy: {kpis['Picking Accuracy %']}%")
    w = [45, 28, 28, 28]
    table(
        ["Picker", "Errors", "Picks", "Error Rate"],
        [[r["picker_name"], int(r["total_errors"]), int(r["total_picks"]),
          f"{r['avg_errors_per_pick']:.2f}"]
         for _, r in d["picker_errors"].head(6).iterrows()],
        w
    )

    # --- 8. Recommended Actions ---
    section_title("8", "RECOMMENDED ACTIONS")

    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(220, 38, 38)
    pdf.set_x(16)
    pdf.cell(0, 5, "IMMEDIATE (Today)")
    pdf.ln(6)
    action_item(f"Initiate procurement for {len(d['low_stock'])} critical low-stock SKUs", (239, 68, 68))
    action_item(f"Dispatch {len(d['high_priority'])} high-priority delayed orders", (239, 68, 68))
    action_item("Reassign resources to decongest critical warehouse zones", (239, 68, 68))
    action_item("Address loading bay bottlenecks at slow bays", (239, 68, 68))

    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(217, 119, 6)
    pdf.set_x(16)
    pdf.cell(0, 5, "SHORT-TERM (This Week)")
    pdf.ln(6)
    action_item("Review overstock items for redistribution or clearance", (245, 158, 11))
    action_item(f"Conduct dead stock audit ({len(d['dead_stock'])} items, no movement > 60 days)", (245, 158, 11))
    action_item("Retrain pickers with high error rates", (245, 158, 11))
    action_item("Escalate supplier mismatch issues to procurement", (245, 158, 11))

    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(37, 99, 235)
    pdf.set_x(16)
    pdf.cell(0, 5, "MEDIUM-TERM (This Month)")
    pdf.ln(6)
    action_item("Rebalance warehouse zone allocation", (59, 130, 246))
    action_item("Review and update reorder levels based on demand", (59, 130, 246))
    action_item("Implement quality checks for inbound shipments", (59, 130, 246))
    action_item("Optimize picking routes for high-traffic zones", (59, 130, 246))

    # --- 9. Email Draft ---
    section_title("9", "EMAIL DRAFT TO OPERATIONS MANAGER")
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.set_x(16)
    pdf.cell(0, 5, _safe(f"Subject: Daily Warehouse Report - {d['report_date']}"))
    pdf.ln(7)

    email_lines = [
        "Dear Operations Manager,",
        "",
        "Please find below the key highlights from today's warehouse performance:",
        "",
        f"  {len(d['low_stock'])} SKUs below reorder level (stockout risk)",
        f"  {len(d['delayed'])} orders delayed ({len(d['high_priority'])} high-priority)",
        f"  {len(d['critical_zones'])} zone(s) at critical capacity (>90%)",
        f"  {len(d['mismatches'])} inbound shipments with mismatch",
        "",
        f"  Warehouse Utilization: {kpis['Warehouse Utilization %']}%",
        f"  Picking Accuracy: {kpis['Picking Accuracy %']}%",
        f"  Average Delay: {kpis['Avg Delay Days']} days",
        "",
        "Please review the full report for detailed recommendations.",
        "",
        "Best regards,",
        "QubiWare AI Intelligence Engine",
        "Qubithm Corporation LLP",
    ]
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(51, 65, 85)
    for line in email_lines:
        pdf.set_x(16)
        pdf.cell(0, 4.5, _safe(line))
        pdf.ln()

    return bytes(pdf.output())
