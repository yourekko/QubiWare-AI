"""Data loading and simulation utilities for QubiWare AI."""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_inventory():
    path = os.path.join(DATA_DIR, "inventory.csv")
    df = pd.read_csv(path)
    df["last_movement_date"] = pd.to_datetime(df["last_movement_date"])
    if "expiry_date" in df.columns:
        df["expiry_date"] = pd.to_datetime(df["expiry_date"], errors="coerce")
    return df


def load_orders():
    path = os.path.join(DATA_DIR, "orders.csv")
    df = pd.read_csv(path)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["promised_dispatch_date"] = pd.to_datetime(df["promised_dispatch_date"])
    df["actual_dispatch_date"] = pd.to_datetime(df["actual_dispatch_date"], errors="coerce")
    return df


def load_warehouse_zones():
    path = os.path.join(DATA_DIR, "warehouse_zones.csv")
    return pd.read_csv(path)


def load_inbound_shipments():
    path = os.path.join(DATA_DIR, "inbound_shipments.csv")
    df = pd.read_csv(path)
    df["expected_date"] = pd.to_datetime(df["expected_date"])
    df["received_date"] = pd.to_datetime(df["received_date"], errors="coerce")
    return df


def load_picking_dispatch():
    path = os.path.join(DATA_DIR, "picking_dispatch.csv")
    return pd.read_csv(path)


def load_routes():
    path = os.path.join(DATA_DIR, "routes.csv")
    return pd.read_csv(path)


def load_all_data():
    return {
        "inventory": load_inventory(),
        "orders": load_orders(),
        "zones": load_warehouse_zones(),
        "inbound": load_inbound_shipments(),
        "picking": load_picking_dispatch(),
        "routes": load_routes(),
    }


# ═══════════════════════════════════════════════════════════════════
# SIMULATION ENGINE
# ═══════════════════════════════════════════════════════════════════

def simulate_stock_drop(data):
    """Simulate a sudden stock drop across random SKUs."""
    inv = data["inventory"].copy()
    rng = np.random.default_rng()
    n_affected = rng.integers(15, 40)
    affected_idx = rng.choice(inv.index, size=min(n_affected, len(inv)), replace=False)
    drop_pct = rng.uniform(0.3, 0.8, size=len(affected_idx))
    inv.loc[affected_idx, "current_stock"] = (
        inv.loc[affected_idx, "current_stock"] * (1 - drop_pct)
    ).astype(int).clip(lower=0)
    for idx in affected_idx[:8]:
        inv.loc[idx, "last_movement_date"] = datetime.now() - timedelta(days=int(rng.integers(1, 5)))
    data["inventory"] = inv
    return data, n_affected


def simulate_new_delays(data):
    """Simulate new order delays hitting the system."""
    orders = data["orders"].copy()
    rng = np.random.default_rng()
    pending_mask = orders["status"].isin(["Pending", "Processing"])
    if pending_mask.sum() == 0:
        dispatched_mask = orders["status"] == "Dispatched"
        if dispatched_mask.sum() > 0:
            pending_mask = dispatched_mask
    pending_idx = orders[pending_mask].index
    n_delay = min(rng.integers(10, 30), len(pending_idx))
    delay_idx = rng.choice(pending_idx, size=n_delay, replace=False)
    orders.loc[delay_idx, "status"] = "Delayed"
    orders.loc[delay_idx, "delay_days"] = rng.integers(1, 12, size=n_delay)
    orders.loc[delay_idx, "actual_dispatch_date"] = pd.NaT
    high_prio_idx = rng.choice(delay_idx, size=min(5, len(delay_idx)), replace=False)
    orders.loc[high_prio_idx, "priority"] = "High"
    data["orders"] = orders
    return data, n_delay


def simulate_zone_surge(data):
    """Simulate a sudden surge in zone utilization."""
    zones = data["zones"].copy()
    rng = np.random.default_rng()
    n_surge = rng.integers(2, 5)
    surge_idx = rng.choice(zones.index, size=min(n_surge, len(zones)), replace=False)
    for idx in surge_idx:
        cap = zones.loc[idx, "capacity_units"]
        new_used = int(cap * rng.uniform(0.88, 0.98))
        zones.loc[idx, "used_units"] = min(new_used, cap)
    data["zones"] = zones
    return data, n_surge


def simulate_picking_errors(data):
    """Simulate a spike in picking errors."""
    picking = data["picking"].copy()
    rng = np.random.default_rng()
    n_affected = rng.integers(20, 50)
    affected_idx = rng.choice(picking.index, size=min(n_affected, len(picking)), replace=False)
    picking.loc[affected_idx, "picking_errors"] = picking.loc[affected_idx, "picking_errors"] + rng.integers(1, 5, size=len(affected_idx))
    data["picking"] = picking
    return data, n_affected


def simulate_inbound_mismatch(data):
    """Simulate new inbound shipment mismatches."""
    inbound = data["inbound"].copy()
    rng = np.random.default_rng()
    received_mask = inbound["status"] == "Received"
    if received_mask.sum() == 0:
        received_mask = pd.Series([True] * len(inbound))
    received_idx = inbound[received_mask].index
    n_mismatch = min(rng.integers(8, 20), len(received_idx))
    mismatch_idx = rng.choice(received_idx, size=n_mismatch, replace=False)
    shortage = rng.integers(5, 50, size=n_mismatch)
    inbound.loc[mismatch_idx, "quantity_received"] = (
        inbound.loc[mismatch_idx, "quantity_expected"] - shortage
    ).clip(lower=0)
    inbound.loc[mismatch_idx, "status"] = "Received"
    data["inbound"] = inbound
    return data, n_mismatch
