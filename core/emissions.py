# core/emissions.py

def calculate_emissions(config, energy_data):
    emission_factor = config.get("emission_factor_kg_co2e_per_kg_h2", 10.0)
    hydrogen_used = energy_data["hydrogen_used_kg"]
    emissions_kg = hydrogen_used * emission_factor
    distance_km = config.get("route_km", 1)
    cargo_mass = config.get("cargo_mass_tons", 1)
    emissions_per_km = emissions_kg / distance_km
    emissions_per_ton_km = emissions_kg / (distance_km * cargo_mass)

    return {
        "emission_factor_kg_co2e_per_kg_h2": emission_factor,
        "total_emissions_kg_co2e": emissions_kg,
        "emissions_per_km_kg_co2e": emissions_per_km,
        "emissions_per_ton_km_kg_co2e": emissions_per_ton_km
    }

