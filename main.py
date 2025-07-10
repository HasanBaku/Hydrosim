import yaml
import json
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

from core.mission_profile import simulate_mission
from core.hydrogen_system import evaluate_hydrogen_system
from core.energy_flow import calculate_energy_flow
from core.cost_model import estimate_costs
from core.emissions import calculate_emissions
from utils.logger import log

def load_config(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def run_simulation(config):
    log(f"Simulating for engine type: {config['engine_type']}")
    mission = simulate_mission(config)
    hydro = evaluate_hydrogen_system(config, mission)
    energy = calculate_energy_flow(config, hydro)
    cost = estimate_costs(config, energy)
    emissions = calculate_emissions(config, energy)

    return {
        "engine": config["engine_type"],
        "mission": mission,
        "hydrogen": hydro,
        "energy": energy,
        "cost": cost,
        "emissions": emissions
    }

# Create output dir
output_dir = "outputs/results"
os.makedirs(output_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Load base config and run both engine types
base_config = load_config("config/sample_scenarios/high_carbon_price.yaml")
results_all = []

for engine_type in ["PEMFC", "H2-ICE"]:
    config = base_config.copy()
    config["engine_type"] = engine_type
    sim_result = run_simulation(config)
    results_all.append(sim_result)

# Convert to DataFrame and save CSV
rows = []
for res in results_all:
    flat = {"engine": res["engine"]}
    for section in ["mission", "hydrogen", "energy", "cost", "emissions"]:
        for k, v in res[section].items():
            flat[f"{section}_{k}"] = v
    rows.append(flat)

df = pd.DataFrame(rows)
csv_file = f"{output_dir}/comparison_{timestamp}.csv"
df.to_csv(csv_file, index=False)
print(f"📄 Comparison CSV saved: {csv_file}")

# Plot comparison chart
labels = ["PEMFC", "H2-ICE"]
costs = df["cost_total_cost_usd"].tolist()
emissions = df["emissions_total_emissions_kg_co2e"].tolist()
costs_per_ton_km = df["cost_cost_per_ton_km_usd"].tolist()
emissions_per_ton_km = df["emissions_emissions_per_ton_km_kg_co2e"].tolist()


x = range(len(labels))
width = 0.35

fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.bar([i - width/2 for i in x], costs, width, label="Fuel Cost (USD)", color="green")
ax1.bar([i + width/2 for i in x], emissions, width, label="CO₂ Emissions (kg)", color="red")
ax1.set_xticks(x)
ax1.set_xticklabels(labels)
ax1.set_ylabel("Amount")
ax1.set_title(f"Engine Comparison – {base_config['route_km']} km Route")
ax1.legend()
ax1.grid(axis="y", linestyle="--", alpha=0.6)

# Annotate values
for i in x:
    ax1.text(i - width/2, costs[i] + 200, f"${costs[i]:,.0f}", ha='center', fontsize=10, fontweight='bold')
    ax1.text(i + width/2, emissions[i] + 200, f"{emissions[i]:,.0f} kg", ha='center', fontsize=10, fontweight='bold')

plot_file = f"{output_dir}/comparison_plot_{timestamp}.png"
plt.tight_layout()
plt.savefig(plot_file)
plt.close()

print(f"📊 Comparison plot saved: {plot_file}")



distances = list(range(200, 2200, 200))
results_distance_scaled = {"PEMFC": [], "H2-ICE": []}

for engine in ["PEMFC", "H2-ICE"]:
    for dist in distances:
        config = base_config.copy()
        config["engine_type"] = engine
        config["route_km"] = dist
        sim_result = run_simulation(config)

        cost_per_km = sim_result["cost"]["cost_per_km_usd"]
        emissions_per_km = sim_result["emissions"]["emissions_per_km_kg_co2e"]

        results_distance_scaled[engine].append({
            "distance": dist,
            "cost_per_km": cost_per_km,
            "emissions_per_km": emissions_per_km
        })

# Plot Line Graph
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)

# Cost per km
ax1.plot(
    distances,
    [x["cost_per_km"] for x in results_distance_scaled["PEMFC"]],
    label="PEMFC", color="green", marker="o"
)
ax1.plot(
    distances,
    [x["cost_per_km"] for x in results_distance_scaled["H2-ICE"]],
    label="H2-ICE", color="blue", marker="s"
)
ax1.set_ylabel("Cost per km (USD)")
ax1.set_title("Cost Comparison vs Distance")
ax1.legend()
ax1.grid(True)

# Emissions per km
ax2.plot(
    distances,
    [x["emissions_per_km"] for x in results_distance_scaled["PEMFC"]],
    label="PEMFC", color="green", marker="o"
)
ax2.plot(
    distances,
    [x["emissions_per_km"] for x in results_distance_scaled["H2-ICE"]],
    label="H2-ICE", color="blue", marker="s"
)
ax2.set_ylabel("Emissions per km (kg CO₂e)")
ax2.set_xlabel("Route Distance (km)")
ax2.set_title("Emissions Comparison vs Distance")
ax2.legend()
ax2.grid(True)

# Save
plot_path = f"{output_dir}/scaling_plot_{timestamp}.png"
plt.tight_layout()
plt.savefig(plot_path)
plt.close()

print(f"📈 Distance scaling plot saved: {plot_path}")

