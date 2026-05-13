"""Generate realistic sample data for QubiWare AI prototype."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# --- Constants ---
CATEGORIES = [
    "Electronics", "Apparel", "FMCG", "Pharmaceuticals",
    "Auto Parts", "Industrial Tools", "Packaging Materials", "Chemicals"
]

PERISHABLE_CATEGORIES = {"FMCG", "Pharmaceuticals", "Chemicals"}

SUPPLIERS = [
    "Reliance Logistics", "Tata Supply Co.", "Mahindra Parts Ltd.",
    "Infosys Materials", "Bharti Supply Chain", "Godrej Warehouse Supplies",
    "Adani Industrial", "Wipro Components", "HCL Packaging", "L&T Raw Materials",
    "Bajaj Distributors", "Hero Supply Corp."
]

ZONES = [
    ("Z-A", "Zone A - Fast Moving", 5000, "Fast Moving", "Rajesh Kumar"),
    ("Z-B", "Zone B - General Storage", 8000, "General", "Priya Sharma"),
    ("Z-C", "Zone C - Cold Storage", 3000, "Cold Storage", "Amit Patel"),
    ("Z-D", "Zone D - Bulk Storage", 10000, "Bulk", "Sanjay Gupta"),
    ("Z-E", "Zone E - Hazardous", 2000, "Hazardous", "Deepa Nair"),
    ("Z-F", "Zone F - Returns", 4000, "Returns", "Vikram Singh"),
    ("Z-G", "Zone G - High Value", 2500, "High Value", "Meera Joshi"),
    ("Z-H", "Zone H - Overflow", 6000, "Overflow", "Arjun Reddy"),
]

ZONE_TYPE_MAP = {z[0]: z[3] for z in ZONES}

CUSTOMERS = [
    "Amazon India", "Flipkart", "Reliance Retail", "BigBasket",
    "DMart", "Snapdeal", "Myntra", "Nykaa", "Pharmeasy",
    "Urban Company", "Swiggy Instamart", "Blinkit", "JioMart",
    "Tata Cliq", "Ajio", "Meesho", "FirstCry", "Lenskart",
    "Boat Lifestyle", "Mamaearth"
]

PICKERS = [
    "Rahul Verma", "Suresh Yadav", "Manoj Kumar", "Vijay Prasad",
    "Anil Sharma", "Ramesh Patil", "Kiran Desai", "Saurabh Jain",
    "Naveen Gupta", "Deepak Tiwari", "Pradeep Singh", "Ravi Shankar"
]

LOADING_BAYS = ["Bay-1", "Bay-2", "Bay-3", "Bay-4", "Bay-5", "Bay-6"]

PRODUCT_PREFIXES = [
    "Widget", "Connector", "Module", "Sensor", "Panel", "Board",
    "Valve", "Cable", "Bracket", "Filter", "Gasket", "Bearing",
    "Motor", "Pump", "Switch", "Relay", "Capacitor", "Transformer",
    "Adapter", "Coupler", "Seal", "Hose", "Clamp", "Fitting"
]

ROUTE_IDS = [f"RT-{str(i).zfill(2)}" for i in range(1, 13)]

DELAY_REASONS = [
    "Stock Unavailable", "Zone Congestion", "Picker Shortage",
    "Vehicle Breakdown", "Weather Disruption", "Loading Bay Bottleneck",
    "Documentation Error", "Route Blocked"
]

DEAD_STOCK_REASONS = [
    "High Price", "Low Reliability", "Bulk Only", "Seasonal Product",
    "Obsolete Model", "Poor Quality Feedback", "No Marketing Push",
    "Better Competitor Product"
]

CONGESTION_REASONS = [
    "Seasonal Demand Surge", "Inbound Backlog", "Slow Dispatch Cycle",
    "Understaffed", "Equipment Maintenance", "Layout Inefficiency"
]

ERROR_TYPES = [
    "Wrong Item Picked", "Wrong Quantity", "Damaged During Pick",
    "Mislabeled Package", "Incorrect Barcode Scan", "Wrong Zone Pick"
]

VEHICLE_TYPES = ["Mini Truck", "LCV", "HCV", "Two Wheeler", "Three Wheeler"]

RETURN_POLICIES = ["Returnable", "Non-Returnable", "Partial Return"]

STORAGE_COST_RANGES = {
    "Cold Storage": (8.0, 15.0),
    "Hazardous": (5.0, 10.0),
    "High Value": (4.0, 8.0),
    "Fast Moving": (2.0, 5.0),
    "General": (0.5, 2.0),
    "Bulk": (0.5, 3.0),
    "Returns": (1.0, 4.0),
    "Overflow": (0.5, 2.5),
}

ENERGY_COST_RANGES = {
    "Cold Storage": (3500, 5000),
    "Hazardous": (2000, 3500),
    "High Value": (1500, 2500),
    "Fast Moving": (1000, 2000),
    "General": (500, 1000),
    "Bulk": (800, 1500),
    "Returns": (600, 1200),
    "Overflow": (500, 1000),
}

ALLOWED_VEHICLES = {
    "Cold Storage": "Mini Truck,LCV",
    "Hazardous": "Mini Truck,LCV",
    "Fast Moving": "Mini Truck,LCV,HCV",
    "General": "Mini Truck,LCV,HCV",
    "Bulk": "LCV,HCV",
    "Returns": "Mini Truck,LCV,Three Wheeler",
    "High Value": "Mini Truck,LCV",
    "Overflow": "Mini Truck,LCV,HCV",
}

MAX_VEHICLE_CAPACITY = {
    "Cold Storage": (2.0, 8.0),
    "Hazardous": (2.0, 6.0),
    "Fast Moving": (5.0, 15.0),
    "General": (5.0, 20.0),
    "Bulk": (10.0, 20.0),
    "Returns": (2.0, 10.0),
    "High Value": (2.0, 8.0),
    "Overflow": (5.0, 15.0),
}


def generate_routes():
    """Generate the routes master data."""
    routes = [
        ("RT-01", "Mumbai Port Road", 45, 60, 800, "Urban", "High", "LCV", True),
        ("RT-02", "Pune Expressway", 165, 180, 3200, "Highway", "Medium", "HCV", True),
        ("RT-03", "Delhi NCR Circuit", 85, 120, 1500, "Urban", "High", "LCV", True),
        ("RT-04", "Bangalore Tech Corridor", 55, 75, 950, "Suburban", "Medium", "Mini Truck", True),
        ("RT-05", "Chennai Industrial Route", 120, 150, 2400, "Industrial", "Low", "HCV", True),
        ("RT-06", "Hyderabad Ring Road", 70, 90, 1200, "Suburban", "Medium", "LCV", True),
        ("RT-07", "Kolkata Dock Link", 30, 45, 600, "Industrial", "High", "HCV", True),
        ("RT-08", "Ahmedabad Highway", 190, 240, 4200, "Highway", "Low", "HCV", True),
        ("RT-09", "Jaipur Suburban", 95, 130, 1800, "Suburban", "Low", "LCV", True),
        ("RT-10", "Lucknow Urban", 25, 40, 450, "Urban", "Medium", "Mini Truck", True),
        ("RT-11", "Nagpur Bypass", 140, 170, 2800, "Highway", "Low", "HCV", False),
        ("RT-12", "Kochi Coastal", 60, 80, 1100, "Suburban", "Medium", "LCV", True),
    ]

    records = []
    for rt in routes:
        records.append({
            "route_id": rt[0],
            "route_name": rt[1],
            "distance_km": rt[2],
            "estimated_time_min": rt[3],
            "route_cost": rt[4],
            "route_type": rt[5],
            "congestion_level": rt[6],
            "best_vehicle": rt[7],
            "active": rt[8],
        })

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(DATA_DIR, "routes.csv"), index=False)
    print(f"Generated {len(df)} route records")
    return df


def generate_inventory(n=300):
    records = []
    today = datetime.now()

    for i in range(n):
        sku_id = f"SKU-{1000 + i}"
        product_name = f"{random.choice(PRODUCT_PREFIXES)}-{random.choice(['Pro', 'Max', 'Lite', 'Plus', 'Standard', 'Ultra'])}-{random.randint(100, 999)}"
        category = random.choice(CATEGORIES)
        zone = random.choice(ZONES)
        warehouse_zone = zone[0]
        zone_type = zone[3]
        max_stock = random.randint(100, 2000)
        reorder_level = int(max_stock * random.uniform(0.15, 0.30))

        # Create realistic stock situations
        r = random.random()
        is_low_stock = r < 0.12
        is_overstock = 0.12 <= r < 0.20
        is_dead_stock = 0.20 <= r < 0.28

        if is_low_stock:
            current_stock = random.randint(0, reorder_level)
        elif is_overstock:
            current_stock = random.randint(int(max_stock * 0.85), int(max_stock * 1.1))
        elif is_dead_stock:
            current_stock = random.randint(reorder_level + 1, int(max_stock * 0.5))
        else:
            current_stock = random.randint(reorder_level + 1, int(max_stock * 0.8))

        unit_price = round(random.uniform(50, 5000), 2)
        purchase_price = round(unit_price * random.uniform(0.40, 0.80), 2)

        # Last movement date - dead stock items haven't moved in >60 days
        if is_dead_stock:
            days_ago = random.randint(61, 180)
        else:
            days_ago = random.randint(0, 45)
        last_movement_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        avg_daily_sales = round(random.uniform(0.5, 50), 1)
        if is_dead_stock:
            avg_daily_sales = round(random.uniform(0, 2), 1)

        supplier_name = random.choice(SUPPLIERS)

        # Perishable logic
        is_perishable = category in PERISHABLE_CATEGORIES
        if is_perishable:
            shelf_life_days = random.randint(30, 365)
            if is_dead_stock:
                # Dead stock perishables: already expired (causing losses)
                expired_days_ago = random.randint(1, 60)
                expiry_date = (today - timedelta(days=expired_days_ago)).strftime("%Y-%m-%d")
            elif random.random() < 0.15:
                # Some items about to expire within 7 days
                expiry_date = (today + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")
            else:
                manufacture_date = today - timedelta(days=random.randint(0, shelf_life_days - 30))
                expiry_date = (manufacture_date + timedelta(days=shelf_life_days)).strftime("%Y-%m-%d")
        else:
            shelf_life_days = None
            expiry_date = None

        # Storage cost based on zone type
        cost_range = STORAGE_COST_RANGES.get(zone_type, (0.5, 3.0))
        storage_cost = round(random.uniform(*cost_range), 2)
        if is_perishable and zone_type == "Cold Storage":
            storage_cost = round(storage_cost * 1.3, 2)

        # Dead stock reason
        dead_stock_reason = None
        if is_dead_stock:
            if is_perishable and expiry_date and datetime.strptime(expiry_date, "%Y-%m-%d") < today:
                dead_stock_reason = random.choice(["Seasonal Product", "Poor Quality Feedback", "Obsolete Model"])
            elif unit_price > 2000:
                dead_stock_reason = random.choice(["High Price", "Better Competitor Product", "No Marketing Push"])
            else:
                dead_stock_reason = random.choice(DEAD_STOCK_REASONS)

        # Competitor price for overstock and dead stock
        competitor_price = None
        if is_overstock or is_dead_stock:
            if is_overstock and random.random() < 0.5:
                competitor_price = round(unit_price * random.uniform(0.75, 0.95), 2)
            else:
                competitor_price = round(unit_price * random.uniform(0.80, 1.10), 2)

        return_policy = random.choice(RETURN_POLICIES)
        handling_cost_per_unit = round(random.uniform(0.2, 5.0), 2)

        records.append({
            "sku_id": sku_id,
            "product_name": product_name,
            "category": category,
            "warehouse_zone": warehouse_zone,
            "current_stock": current_stock,
            "reorder_level": reorder_level,
            "max_stock": max_stock,
            "unit_price": unit_price,
            "purchase_price": purchase_price,
            "last_movement_date": last_movement_date,
            "avg_daily_sales": avg_daily_sales,
            "supplier_name": supplier_name,
            "is_perishable": is_perishable,
            "shelf_life_days": shelf_life_days,
            "expiry_date": expiry_date,
            "storage_cost_per_day": storage_cost,
            "dead_stock_reason": dead_stock_reason,
            "competitor_price": competitor_price,
            "return_policy": return_policy,
            "handling_cost_per_unit": handling_cost_per_unit,
        })

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(DATA_DIR, "inventory.csv"), index=False)
    print(f"Generated {len(df)} inventory records")
    return df


def generate_orders(n=500, inventory_df=None):
    records = []
    today = datetime.now()
    statuses = ["Delivered", "Dispatched", "Pending", "Delayed", "Cancelled"]

    for i in range(n):
        order_id = f"ORD-{10000 + i}"
        customer_name = random.choice(CUSTOMERS)
        sku_id = random.choice(inventory_df["sku_id"].tolist()) if inventory_df is not None else f"SKU-{random.randint(1000, 1299)}"

        order_quantity = random.randint(5, 200)
        order_date = (today - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
        promised_days = random.randint(1, 5)
        order_dt = datetime.strptime(order_date, "%Y-%m-%d")
        promised_dispatch_date = (order_dt + timedelta(days=promised_days)).strftime("%Y-%m-%d")

        r = random.random()
        if r < 0.30:
            status = "Delivered"
            actual_dispatch = (order_dt + timedelta(days=random.randint(1, promised_days))).strftime("%Y-%m-%d")
            delay_days = 0
        elif r < 0.45:
            status = "Dispatched"
            actual_dispatch = (order_dt + timedelta(days=random.randint(1, promised_days + 2))).strftime("%Y-%m-%d")
            delay_days = max(0, (datetime.strptime(actual_dispatch, "%Y-%m-%d") - datetime.strptime(promised_dispatch_date, "%Y-%m-%d")).days)
        elif r < 0.65:
            status = "Pending"
            actual_dispatch = ""
            delay_days = max(0, (today - datetime.strptime(promised_dispatch_date, "%Y-%m-%d")).days)
        elif r < 0.85:
            status = "Delayed"
            delay_extra = random.randint(1, 7)
            actual_dispatch = (datetime.strptime(promised_dispatch_date, "%Y-%m-%d") + timedelta(days=delay_extra)).strftime("%Y-%m-%d")
            delay_days = delay_extra
        else:
            status = "Cancelled"
            actual_dispatch = ""
            delay_days = 0

        zone = random.choice(ZONES)
        priority = random.choice(["High", "Medium", "Low"])
        if r >= 0.65 and r < 0.85:
            priority = random.choice(["High", "High", "Medium"])

        delay_reason = None
        if status in ("Delayed", "Pending"):
            delay_reason = random.choice(DELAY_REASONS)

        estimated_delivery_km = random.randint(5, 500)
        delivery_cost = round(estimated_delivery_km * 2.5 + random.uniform(50, 300), 2)
        route_id = random.choice(ROUTE_IDS)

        if order_quantity <= 20:
            vehicle_type = random.choice(["Two Wheeler", "Three Wheeler"])
        elif order_quantity <= 50:
            vehicle_type = random.choice(["Mini Truck", "Three Wheeler"])
        elif order_quantity <= 100:
            vehicle_type = "LCV"
        else:
            vehicle_type = "HCV"

        records.append({
            "order_id": order_id,
            "customer_name": customer_name,
            "sku_id": sku_id,
            "order_quantity": order_quantity,
            "order_date": order_date,
            "promised_dispatch_date": promised_dispatch_date,
            "actual_dispatch_date": actual_dispatch,
            "status": status,
            "warehouse_zone": zone[0],
            "delay_days": delay_days,
            "priority": priority,
            "delay_reason": delay_reason,
            "estimated_delivery_km": estimated_delivery_km,
            "delivery_cost": delivery_cost,
            "route_id": route_id,
            "vehicle_type": vehicle_type,
        })

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(DATA_DIR, "orders.csv"), index=False)
    print(f"Generated {len(df)} order records")
    return df


def generate_warehouse_zones():
    records = []
    today = datetime.now()

    for zone in ZONES:
        zone_id, zone_name, capacity, zone_type, manager = zone
        # Create varying utilization levels
        if zone_id in ["Z-B", "Z-D"]:
            used = int(capacity * random.uniform(0.90, 0.97))
        elif zone_id in ["Z-A", "Z-G"]:
            used = int(capacity * random.uniform(0.78, 0.89))
        elif zone_id == "Z-H":
            used = int(capacity * random.uniform(0.60, 0.74))
        else:
            used = int(capacity * random.uniform(0.45, 0.75))

        utilization_pct = used / capacity
        if utilization_pct >= 0.90:
            zone_status = "Critical"
        elif utilization_pct >= 0.78:
            zone_status = "Warning"
        else:
            zone_status = "Normal"

        allowed_vehicles = ALLOWED_VEHICLES.get(zone_type, "Mini Truck,LCV,HCV")
        cap_range = MAX_VEHICLE_CAPACITY.get(zone_type, (5.0, 15.0))
        max_vehicle_cap = round(random.uniform(*cap_range), 1)

        expected_critical_until = None
        congestion_reason = None
        if zone_status in ("Critical", "Warning"):
            expected_critical_until = (today + timedelta(days=random.randint(7, 30))).strftime("%Y-%m-%d")
            congestion_reason = random.choice(CONGESTION_REASONS)

        energy_range = ENERGY_COST_RANGES.get(zone_type, (500, 1500))
        energy_cost = round(random.uniform(*energy_range), 2)

        zone_throughput_rate = random.randint(50, 500)
        revenue_potential = round(random.uniform(5000, 100000), 2)

        utilization_trend = random.choices(
            ["Increasing", "Decreasing", "Stable"],
            weights=[0.35, 0.25, 0.40],
        )[0]

        records.append({
            "zone_id": zone_id,
            "zone_name": zone_name,
            "capacity_units": capacity,
            "used_units": used,
            "zone_type": zone_type,
            "manager_name": manager,
            "zone_status": zone_status,
            "allowed_vehicle_types": allowed_vehicles,
            "max_vehicle_capacity_tons": max_vehicle_cap,
            "expected_critical_until": expected_critical_until,
            "congestion_reason": congestion_reason,
            "energy_cost_per_day": energy_cost,
            "zone_throughput_rate": zone_throughput_rate,
            "revenue_potential_per_day": revenue_potential,
            "utilization_trend": utilization_trend,
        })

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(DATA_DIR, "warehouse_zones.csv"), index=False)
    print(f"Generated {len(df)} warehouse zone records")
    return df


def generate_inbound_shipments(n=150, inventory_df=None):
    records = []
    today = datetime.now()

    for i in range(n):
        shipment_id = f"SHP-{5000 + i}"
        supplier_name = random.choice(SUPPLIERS)
        sku_id = random.choice(inventory_df["sku_id"].tolist()) if inventory_df is not None else f"SKU-{random.randint(1000, 1299)}"

        expected_date = (today - timedelta(days=random.randint(0, 20))).strftime("%Y-%m-%d")
        quantity_expected = random.randint(50, 500)

        r = random.random()
        if r < 0.50:
            status = "Received"
            received_date = (datetime.strptime(expected_date, "%Y-%m-%d") + timedelta(days=random.randint(0, 3))).strftime("%Y-%m-%d")
            quantity_received = quantity_expected
        elif r < 0.70:
            status = "Received"
            received_date = (datetime.strptime(expected_date, "%Y-%m-%d") + timedelta(days=random.randint(0, 2))).strftime("%Y-%m-%d")
            # Mismatch
            quantity_received = quantity_expected - random.randint(5, int(quantity_expected * 0.2))
        elif r < 0.85:
            status = "In Transit"
            received_date = ""
            quantity_received = 0
        else:
            status = "Delayed"
            received_date = ""
            quantity_received = 0

        records.append({
            "shipment_id": shipment_id,
            "supplier_name": supplier_name,
            "sku_id": sku_id,
            "expected_date": expected_date,
            "received_date": received_date,
            "quantity_expected": quantity_expected,
            "quantity_received": quantity_received,
            "status": status
        })

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(DATA_DIR, "inbound_shipments.csv"), index=False)
    print(f"Generated {len(df)} inbound shipment records")
    return df


def generate_picking_dispatch(n=300, orders_df=None):
    records = []

    order_route_map = {}
    if orders_df is not None:
        order_route_map = dict(zip(orders_df["order_id"], orders_df["route_id"]))

    for i in range(n):
        dispatch_id = f"DSP-{2000 + i}"
        picker_name = random.choice(PICKERS)
        order_id = random.choice(orders_df["order_id"].tolist()) if orders_df is not None else f"ORD-{random.randint(10000, 10499)}"
        zone = random.choice(ZONES)
        warehouse_zone = zone[0]

        items_picked = random.randint(1, 30)

        # Some pickers have higher error rates
        if picker_name in ["Rahul Verma", "Manoj Kumar"]:
            picking_errors = random.choices([0, 1, 2, 3], weights=[0.4, 0.3, 0.2, 0.1])[0]
        else:
            picking_errors = random.choices([0, 1, 2], weights=[0.8, 0.15, 0.05])[0]

        loading_bay = random.choice(LOADING_BAYS)

        # Some bays are slower
        if loading_bay in ["Bay-3", "Bay-5"]:
            dispatch_time_minutes = random.randint(25, 60)
        else:
            dispatch_time_minutes = random.randint(8, 30)

        r = random.random()
        if r < 0.60:
            status = "Completed"
        elif r < 0.80:
            status = "In Progress"
        else:
            status = "Pending"

        error_type = None
        if picking_errors > 0:
            error_type = random.choice(ERROR_TYPES)

        bay_cost_per_hour = round(random.uniform(100, 500), 2)
        route_id = order_route_map.get(order_id, random.choice(ROUTE_IDS))

        records.append({
            "dispatch_id": dispatch_id,
            "picker_name": picker_name,
            "order_id": order_id,
            "warehouse_zone": warehouse_zone,
            "items_picked": items_picked,
            "picking_errors": picking_errors,
            "loading_bay": loading_bay,
            "dispatch_time_minutes": dispatch_time_minutes,
            "status": status,
            "error_type": error_type,
            "bay_cost_per_hour": bay_cost_per_hour,
            "route_id": route_id,
        })

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(DATA_DIR, "picking_dispatch.csv"), index=False)
    print(f"Generated {len(df)} picking/dispatch records")
    return df


if __name__ == "__main__":
    print("Generating QubiWare AI sample data...")
    print("=" * 50)
    generate_routes()
    inv_df = generate_inventory(300)
    orders_df = generate_orders(500, inv_df)
    generate_warehouse_zones()
    generate_inbound_shipments(150, inv_df)
    generate_picking_dispatch(300, orders_df)
    print("=" * 50)
    print("Data generation complete!")
