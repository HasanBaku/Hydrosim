# core/energy_flow.py

def calculate_energy_flow(config, hydrogen_data):
    # Just return hydrogen energy data for now (acts as pass-through)
    return {
        "energy_delivered_kwh": hydrogen_data["energy_required_kwh"],
        "hydrogen_used_kg": hydrogen_data["hydrogen_needed_kg"]
    }
