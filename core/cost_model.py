def estimate_costs(config, energy_data):
    fuel_cost = config.get("fuel_cost_usd_per_kg", 5.0)
    hydrogen_used = energy_data["hydrogen_used_kg"]
    
    # Fuel cost
    total_fuel_cost = fuel_cost * hydrogen_used

    # Carbon pricing
    carbon_price = config.get("carbon_price_usd_per_ton", 0)
    emission_factor = config.get("emission_factor_kg_co2e_per_kg_h2", 0)
    emissions_kg = hydrogen_used * emission_factor
    emissions_ton = emissions_kg / 1000
    carbon_cost = emissions_ton * carbon_price

    # Total cost (including carbon tax)
    total_cost = total_fuel_cost + carbon_cost

    distance_km = config.get("route_km", 1)  # avoid divide by zero
    cost_per_km = total_cost / distance_km
    cargo_mass = config.get("cargo_mass_tons", 1)
    cost_per_km = total_cost / distance_km
    cost_per_ton_km = total_cost / (distance_km * cargo_mass)

    return {
        "fuel_cost_usd": total_fuel_cost,
        "carbon_price_usd_per_ton": carbon_price,
        "carbon_cost_usd": carbon_cost,
        "total_cost_usd": total_cost,
        "hydrogen_price_usd_per_kg": fuel_cost,
        "total_hydrogen_used_kg": hydrogen_used,
        "cost_per_km_usd": cost_per_km,
        "cost_per_ton_km_usd": cost_per_ton_km
    }

