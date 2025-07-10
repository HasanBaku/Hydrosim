def simulate_mission(config):
    # For now just return dummy mission data
    return {
        "distance_km": config["route_km"],
        "load_factor": config["load_factor"],
        "duration_hours": config["route_km"] / 30  # Assume avg 30 km/h
    }
