def evaluate_hydrogen_system(config, mission):
    engine_type = config["engine_type"]
    distance = mission["distance_km"]
    load_factor = mission["load_factor"]

    # Placeholder power requirement (kW)
    base_power_kw = 1500  # base for RoRo vessel
    adjusted_power_kw = base_power_kw * load_factor

    # Energy needed (kWh)
    energy_needed_kwh = adjusted_power_kw * mission["duration_hours"]

    # Efficiency based on engine type
    if engine_type == "PEMFC":
        efficiency = 0.50
    elif engine_type == "H2-ICE":
        efficiency = 0.38
    else:
        raise ValueError("Unsupported engine type")

    # Hydrogen consumption (kg)
    hydrogen_needed = energy_needed_kwh / (33.33 * efficiency)

    return {
        "engine_type": engine_type,
        "adjusted_power_kw": adjusted_power_kw,
        "energy_required_kwh": energy_needed_kwh,
        "efficiency": efficiency,
        "hydrogen_needed_kg": hydrogen_needed
    }
