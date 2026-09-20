import numpy as np


def compute_par_level(
    predicted_daily_demand,
    std_daily_demand,
    lead_time_days=2,
    service_level_z=1.645,
):
    predicted_daily_demand = max(0.0, float(predicted_daily_demand))
    std_daily_demand = max(0.0, float(std_daily_demand))
    lead_time_days = max(1, int(lead_time_days))

    lead_time_demand = predicted_daily_demand * lead_time_days
    safety_stock = service_level_z * std_daily_demand * np.sqrt(lead_time_days)
    par_level = lead_time_demand + safety_stock

    return {
        "lead_time_demand": float(lead_time_demand),
        "safety_stock": float(safety_stock),
        "par_level": float(par_level),
    }


def dynamic_par_levels(forecast, historical_std, lead_time_days=2, service_level_z=1.645):
    forecast = np.asarray(forecast, dtype=float)
    return np.array([
        compute_par_level(
            predicted_daily_demand=value,
            std_daily_demand=historical_std,
            lead_time_days=lead_time_days,
            service_level_z=service_level_z,
        )["par_level"]
        for value in forecast
    ])
