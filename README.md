# QubiWare AI

**AI Control Tower for Warehouse, Inventory and Dispatch Operations**

Built by **Qubithm Corporation LLP** | AI Solutions for Logistics & Warehousing

---

## Overview

QubiWare AI is an AI intelligence layer that sits on top of existing warehouse data (WMS, ERP, Excel, barcode/RFID systems) and provides:

- Real-time inventory risk detection (low stock, overstock, dead stock)
- Order and dispatch delay tracking with root-cause analysis
- Warehouse zone utilization monitoring and congestion alerts
- AI-powered natural language queries on warehouse data
- Automated daily performance reports with action recommendations

**We do not replace your WMS, ERP, barcode/RFID system, or Excel. We add an AI layer that gives insights, alerts and reports from your existing data.**

---

## How to Run

### 1. Clone and Setup

```bash
cd QubiWare-AI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Generate Sample Data

```bash
python3 generate_data.py
```

### 3. (Optional) Configure AI API Key

```bash
cp .env.example .env
# Edit .env and add your Gemini or OpenAI API key
```

The app works without an API key using a built-in rule-based intelligence engine.

### 4. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Demo Flow

1. **Open Dashboard** - View warehouse KPIs and active alerts
2. **Inventory Intelligence** - Identify low-stock, overstock, and dead stock risks
3. **Dispatch Intelligence** - Track delayed orders and dispatch bottlenecks
4. **Zone Intelligence** - Monitor zone congestion and utilization
5. **AI Copilot** - Ask: "Which warehouse zone is most congested?"
6. **AI Copilot** - Ask: "Which SKUs should I reorder immediately?"
7. **Daily Report** - Generate and download a complete performance report

---

## Demo Questions for AI Copilot

- Which SKUs are at low-stock risk?
- Which warehouse zone is most congested?
- Which orders are delayed today?
- Which supplier has mismatch issues?
- Which products are overstocked?
- Which SKUs should I reorder immediately?
- Which loading bay is causing dispatch delay?
- Which picker has the highest error count?
- Generate a warehouse performance summary.
- What are the top 5 operational risks?

---

## Product Pitch

> QubiWare AI helps warehouse and logistics companies convert scattered warehouse data into AI-powered decisions, alerts and reports.

**Target customers:**
- Warehouse companies
- Logistics and 3PL companies
- WMS/ERP providers
- Barcode/RFID vendors
- Supply chain technology companies

**Value proposition:**
- No system replacement needed — works with existing data
- Instant visibility into inventory risks
- Automated alert generation
- Natural language querying of warehouse data
- Daily automated reports with recommendations

---

## Tech Stack

- **Python** + **Streamlit** — Web interface
- **Pandas** — Data processing
- **Plotly** — Interactive charts
- **Google Gemini / OpenAI** — AI responses (optional)
- **CSV files** — Sample data (replaceable with database/API)

---

## Future Scope

- ERP/WMS integration (SAP, Oracle, Manhattan Associates)
- Barcode/RFID real-time data integration
- Real-time IoT data integration (temperature, humidity sensors)
- WhatsApp alerts for warehouse supervisors
- Email automation for daily reports
- Predictive demand forecasting with ML models
- SLA monitoring for 3PL companies
- Vendor performance scoring and ranking
- Computer vision for warehouse safety compliance
- Mobile app for warehouse supervisors
- Multi-warehouse support and comparison
- Integration with transportation management systems (TMS)

---

## Folder Structure

```
QubiWare-AI/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── .env.example            # Environment variable template
├── generate_data.py        # Sample data generator
├── data/
│   ├── inventory.csv       # 300 inventory records
│   ├── orders.csv          # 500 order records
│   ├── warehouse_zones.csv # 8 warehouse zones
│   ├── inbound_shipments.csv  # 150 inbound records
│   └── picking_dispatch.csv   # 300 dispatch records
└── utils/
    ├── __init__.py
    ├── data_loader.py      # Data loading utilities
    ├── analytics.py        # Analytics computations
    ├── ai_helper.py        # AI Copilot logic
    └── report_generator.py # Report generation
```

---

## License

Proprietary - Qubithm Corporation LLP

---

*QubiWare AI v1.0 | Prototype*
