# QubiWare AI — Implementation Summary

**Product:** QubiWare AI — AI Copilot for Warehouse, Inventory & Dispatch Intelligence
**Built by:** Qubithm Corporation LLP
**Date:** May 2026
**Status:** Working Prototype (Demo-Ready)

---

## What Is QubiWare AI?

QubiWare AI is an AI intelligence layer that sits on top of existing warehouse data (WMS, ERP, Excel, barcode/RFID exports) and converts scattered operational data into real-time insights, alerts, and actionable reports.

**Core Value Proposition:** "We don't replace your WMS, ERP, or barcode system. We add an AI layer that gives insights, alerts, and reports from your existing data."

**Target Audience:** Warehouse companies, logistics providers, WMS vendors, 3PL operators, barcode/RFID vendors, and supply-chain exhibitors.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit (Python) with custom CSS/HTML for premium UI |
| Data Processing | Pandas, NumPy |
| Visualizations | Plotly (interactive charts with modern styling) |
| AI Engine | Google Gemini API / OpenAI API (with rule-based fallback) |
| PDF Reports | fpdf2 |
| Data Source | CSV files (simulating WMS/ERP exports) |
| Config | python-dotenv for API keys |

---

## Modules Implemented

### 1. Executive Dashboard

Full-width KPI dashboard with 10 key metrics displayed as styled cards with icons:

- Total SKUs, Total Orders
- Low Stock Items, Overstock Items
- Delayed Orders, Pending Dispatches
- Average Delay Days
- Warehouse Utilization %
- Picking Accuracy %
- Inbound Mismatch Count

**Charts included:**
- Inventory Distribution by Category (bar chart)
- Orders by Status (donut chart)
- Warehouse Zone Utilization (horizontal bar)
- Top 10 Delayed SKUs (bar chart)
- Top 10 Fast-Moving SKUs (bar chart)
- Pending Dispatches by Zone (bar chart)

**AI Alert Engine:** Auto-generated alert cards across the dashboard for low stock, overstock, dispatch delays, zone congestion, picking errors, and inbound mismatches. Each alert shows count and recommended action.

---

### 2. Inventory Intelligence

Comprehensive inventory risk analysis with:

- **Low Stock Items** — SKUs where `current_stock <= reorder_level`
- **Overstock Items** — SKUs where `current_stock >= max_stock * 85%`
- **Dead Stock Items** — SKUs with no movement in 60+ days
- **Fast-Moving SKUs** — Top 20 by average daily sales
- **Reorder Recommendations** — Auto-calculated with `recommended_qty = max_stock - current_stock` and estimated cost

**Action Plan Generator:** One-click button generates a structured business summary listing which SKUs need immediate procurement, which are overstocked, which are dead stock, and recommended actions with estimated investment.

---

### 3. Order & Dispatch Intelligence

Dispatch risk monitoring with:

- Delayed orders table with zone, customer, priority, and delay days
- Pending orders tracking
- High-priority delayed orders highlighted
- Delay breakdown by warehouse zone
- Delay breakdown by customer
- Loading bay bottleneck analysis (avg dispatch time per bay)
- Picking error summary by picker

**Charts:**
- Delayed Orders by Zone
- Orders by Priority
- Dispatch Status Distribution
- Picking Errors by Picker
- Average Dispatch Time by Loading Bay

**Dispatch Risk Summary Generator:** One-click report with delayed count, worst zones, impacted customers, bay bottlenecks, and recommended actions.

---

### 4. Warehouse Zone Intelligence

Zone-level operational insights:

- **Zone Utilization %** = `used_units / capacity_units * 100`
- **Classification:** Normal (<75%), Warning (75-90%), Critical (>90%)
- Critical and warning zones flagged with styled alert cards
- Zone-wise stock count, delayed orders, and picking errors
- Available capacity tracking

**Zone Utilization Chart:** Color-coded horizontal bar chart showing all zones with threshold lines.

**Recommendations:** AI-generated suggestions for stock rebalancing, picking allocation, and dispatch prioritization from congested zones.

---

### 5. AI Copilot (Ask AI)

Interactive chat interface with:

- Styled chat UI with conversation history (persisted in session)
- Quick-action suggestion chips (clickable buttons):
  - "Which SKUs are at low-stock risk?"
  - "Which warehouse zone is most congested?"
  - "Which orders are delayed today?"
  - "Which supplier has mismatch issues?"
  - "Generate a warehouse performance summary"
  - "Which loading bay is causing delay?"
- Welcome screen with product intro and capability overview

**AI Backend (3-tier):**
1. **Google Gemini API** — If `GEMINI_API_KEY` is set in `.env`, queries Gemini 1.5 Flash with full warehouse data context
2. **OpenAI API** — If `OPENAI_API_KEY` is set, queries GPT-3.5-turbo as fallback
3. **Rule-Based Engine** — If no API key is available, a built-in Pandas-based engine handles 12+ query categories (low stock, overstock, dead stock, delays, zones, suppliers, picking, bays, performance summary, fast-moving SKUs, etc.) and returns formatted markdown responses

**Data Context Builder:** Automatically compiles KPIs, top risk items, zone utilization, picker performance, bay stats, supplier issues, and category breakdowns into a structured prompt context for the AI.

---

### 6. Daily Report Generator

On-screen report displayed using native Streamlit components with professional styling:

**Report Sections:**
1. Executive Summary — Natural language overview of today's operational state
2. Key Performance Indicators — 10 KPI cards matching the dashboard
3. Inventory Risks — Low stock, overstock, dead stock counts with data table
4. Dispatch Risks — Delayed, pending, high-priority counts with zone breakdown
5. Warehouse Zone Status — All zones with utilization %, capacity, and status
6. Supplier / Inbound Issues — Suppliers with mismatches and shortage counts
7. Picking Accuracy — Picker error rates
8. Recommended Actions — Categorized by urgency (Immediate / Short-Term / Medium-Term) with color-coded alerts
9. Email Draft — Ready-to-send email to operations manager with key highlights

**PDF Export:** Downloadable PDF report with:
- Dark branded header bar with QubiWare AI branding
- Styled KPI boxes in rows
- Modern tables with dark header rows and alternating row colors
- Color-coded action items (red/amber/blue by priority)
- Numbered sections with clean typography
- Professional footer on every page

---

## Data Architecture

### Datasets (5 CSVs, auto-generated with realistic anomalies)

| Dataset | Records | Key Columns |
|---|---|---|
| `inventory.csv` | 300 | sku_id, product_name, category, warehouse_zone, current_stock, reorder_level, max_stock, unit_price, last_movement_date, avg_daily_sales, supplier_name |
| `orders.csv` | 500 | order_id, customer_name, sku_id, order_quantity, order_date, promised_dispatch_date, actual_dispatch_date, status, warehouse_zone, delay_days, priority |
| `warehouse_zones.csv` | 8 | zone_id, zone_name, capacity_units, used_units, zone_type, manager_name |
| `inbound_shipments.csv` | 150 | shipment_id, supplier_name, sku_id, expected_date, received_date, quantity_expected, quantity_received, status |
| `picking_dispatch.csv` | 300 | dispatch_id, picker_name, order_id, warehouse_zone, items_picked, picking_errors, loading_bay, dispatch_time_minutes, status |

**Built-in Data Issues** (for realistic demo scenarios):
- Low stock SKUs, overstock SKUs, dead stock (no movement > 60 days)
- Delayed orders, pending dispatches, high-priority delays
- Zone over-utilization (>90% capacity)
- Picking errors across pickers
- Inbound shipment quantity mismatches
- Supplier delays and shortages

---

## Project Structure

```
QubiWare-AI/
├── app.py                      # Main Streamlit app (~1650 lines)
├── generate_data.py            # Sample data generator
├── requirements.txt            # Python dependencies
├── .env.example                # API key template
├── README.md                   # Setup & usage guide
├── IMPLEMENTATION_SUMMARY.md   # This document
├── data/
│   ├── inventory.csv
│   ├── orders.csv
│   ├── warehouse_zones.csv
│   ├── inbound_shipments.csv
│   └── picking_dispatch.csv
└── utils/
    ├── __init__.py
    ├── data_loader.py          # CSV loading with type parsing
    ├── analytics.py            # 20+ analytics functions (KPIs, filters, aggregations)
    ├── ai_helper.py            # AI engine (Gemini / OpenAI / rule-based fallback)
    └── report_generator.py     # PDF report generation
```

---

## UI/UX Design

- **Layout:** Wide-mode Streamlit with custom CSS overriding default components
- **Navigation:** Sidebar with icon-based nav items (SVG icons), Qubithm branding, powered-by footer
- **KPI Cards:** Custom HTML cards with color-coded icons (blue, red, amber, green, purple)
- **Charts:** Plotly charts with transparent backgrounds, rounded corners, gradient colors, consistent color palette
- **Alert System:** Color-coded alert cards (critical=red, warning=amber, info=blue) throughout all pages
- **Tables:** Streamlit dataframes with full-width stretch
- **Theme:** Light/clean professional theme — white sidebar, light backgrounds, dark text for readability
- **Branding:** "QubiWare AI by Qubithm Corporation LLP" with consistent footer across all pages

---

## Analytics Engine (20+ Functions)

| Function | Purpose |
|---|---|
| `get_low_stock_items()` | SKUs below reorder level |
| `get_overstock_items()` | SKUs at 85%+ of max capacity |
| `get_dead_stock_items()` | No movement in 60+ days |
| `get_fast_moving_skus()` | Top N by avg daily sales |
| `get_reorder_recommendations()` | Auto-calc reorder qty and cost |
| `get_delayed_orders()` | Orders with "Delayed" status |
| `get_pending_orders()` | Orders with "Pending" status |
| `get_high_priority_delayed()` | High-priority + delayed |
| `get_delay_by_zone()` | Delay count/avg grouped by zone |
| `get_delay_by_customer()` | Delay count/avg grouped by customer |
| `get_zone_utilization()` | Utilization % with Normal/Warning/Critical |
| `get_picking_errors_by_picker()` | Error rates per picker |
| `get_dispatch_by_bay()` | Avg time, dispatches, errors per bay |
| `get_inbound_mismatches()` | Shipments with quantity shortages |
| `get_supplier_issues()` | Suppliers ranked by mismatch count |
| `compute_kpis()` | All 10 KPIs in one call |
| `generate_inventory_action_plan()` | Full markdown action plan |
| `generate_dispatch_risk_summary()` | Full markdown risk report |

---

## Demo Flow (Recommended)

1. **Open Dashboard** — Show 10 KPIs and 6 interactive charts at a glance
2. **Review AI Alerts** — Point out auto-generated low stock, delay, and zone alerts
3. **Inventory Intelligence** — Show low stock table, click "Generate Action Plan"
4. **Dispatch Intelligence** — Show delayed orders, zone bottlenecks, click "Generate Risk Summary"
5. **Zone Intelligence** — Show critical zones, utilization chart, recommendations
6. **AI Copilot** — Ask: "Which warehouse zone is most congested?" then "Which SKUs should I reorder immediately?"
7. **Daily Report** — Click "Generate Report", walk through all 9 sections, download PDF
8. **Closing Pitch** — "This connects with any existing WMS, ERP, Excel, barcode, or RFID system"

---

## How to Run

```bash
cd QubiWare-AI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 generate_data.py       # Generate sample datasets
streamlit run app.py           # Launch at http://localhost:8501
```

**Optional:** Add API keys in `.env` for AI-powered copilot responses:
```
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```
Without API keys, the AI Copilot uses a built-in rule-based engine that covers all major query categories.

---

## Future Scope (Not Yet Implemented)

- ERP/WMS live integration (SAP, Oracle, etc.)
- Barcode/RFID real-time data integration
- IoT sensor data for warehouse monitoring
- WhatsApp/SMS alert automation
- Email automation for daily reports
- Predictive demand forecasting (ML models)
- SLA monitoring for 3PL companies
- Vendor performance scoring
- Computer vision for warehouse safety
- Mobile app for warehouse supervisors
- Multi-warehouse support
- Role-based access control

---

*QubiWare AI — AI Control Tower for Warehouse, Inventory and Dispatch Operations*
*Built by Qubithm Corporation LLP | AI Solutions for Logistics & Warehousing*
