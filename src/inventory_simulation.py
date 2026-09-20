import numpy as np


def simulate_bar_inventory(
    actual_demand,
    par_level,
    lead_time=2,
    initial_stock=None,
):
    actual_demand = np.maximum(np.asarray(actual_demand, dtype=float), 0.0)
    par_level = max(0.0, float(par_level))
    lead_time = max(1, int(lead_time))

    if initial_stock is None:
        initial_stock = par_level

    stock = float(initial_stock)
    stockouts = 0
    lost_demand_volume = 0.0
    pending_orders = []
    history = []

    for demand in actual_demand:
        arrivals = []
        remaining_orders = []

        for days_until_arrival, qty in pending_orders:
            days_until_arrival -= 1
            if days_until_arrival <= 0:
                arrivals.append(qty)
            else:
                remaining_orders.append([days_until_arrival, qty])

        stock += sum(arrivals)
        pending_orders = remaining_orders

        fulfilled = min(stock, demand)
        if fulfilled < demand:
            stockouts += 1
            lost_demand_volume += demand - fulfilled

        stock -= fulfilled

        on_order = sum(order[1] for order in pending_orders)
        effective_inventory = stock + on_order

        if effective_inventory < par_level:
            order_qty = par_level - effective_inventory
            pending_orders.append([lead_time, order_qty])

        history.append(stock)

    average_inventory = float(np.mean(history)) if history else 0.0
    total_demand = float(np.sum(actual_demand))
    turnover = total_demand / average_inventory if average_inventory > 0 else np.nan

    return {
        "stockout_days": int(stockouts),
        "lost_volume_ml": float(lost_demand_volume),
        "average_inventory_ml": average_inventory,
        "turnover_ratio": float(turnover) if np.isfinite(turnover) else np.nan,
        "history": history,
    }
