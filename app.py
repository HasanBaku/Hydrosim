import streamlit as st
import yaml
from core.mission_profile import simulate_mission
from core.hydrogen_system import evaluate_hydrogen_system
from core.energy_flow import calculate_energy_flow
from core.cost_model import estimate_costs
from core.emissions import calculate_emissions
import plotly.graph_objects as go
import pandas as pd
from math import radians, cos, sin, asin, sqrt
import geopandas as gpd
import json
from shapely.geometry import Point

st.set_page_config(page_title="HydroSim", layout="wide")
st.title("Hydrogen Marine Propulsion Simulator")

# Port data and coordinates (only routes available in the sea lane dataset)
ports = [
    "Singapore", "Port Klang", "Jakarta", "Rotterdam", "Hamburg", "Antwerp",
    "Los Angeles", "New York", "Houston", "Dubai", "Jeddah", "Doha"
]
port_coords = {
    'Singapore': (1.3521, 103.8198),
    'Port Klang': (3.0014, 101.4000),
    'Jakarta': (-6.2088, 106.8456),
    'Rotterdam': (51.9244, 4.4777),
    'Hamburg': (53.5511, 9.9937),
    'Antwerp': (51.2194, 4.4025),
    'Los Angeles': (33.7405, -118.2760),
    'New York': (40.7128, -74.0060),
    'Houston': (29.7604, -95.3698),
    'Dubai': (25.276987, 55.296249),
    'Jeddah': (21.4858, 39.1925),
    'Doha': (25.276987, 51.5200)
}

# Region mapping to assign fuel prices
region_mapping = {
    'Singapore': 'Southeast Asia', 'Port Klang': 'Southeast Asia', 'Jakarta': 'Southeast Asia',
    'Rotterdam': 'EU', 'Hamburg': 'EU', 'Antwerp': 'EU',
    'Los Angeles': 'USA', 'New York': 'USA', 'Houston': 'USA',
    'Dubai': 'Middle East', 'Jeddah': 'Middle East', 'Doha': 'Middle East'
}

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r

# Route selection
departure_port = st.selectbox("Select Departure Port", ports)
arrival_port = st.selectbox("Select Arrival Port", [p for p in ports if p != departure_port])

lat1, lon1 = port_coords[departure_port]
lat2, lon2 = port_coords[arrival_port]

st.markdown("## Route Overview", unsafe_allow_html=True)

# Plot with shipping lanes from GeoJSON
shipping_lanes = gpd.read_file("Shipping_Lanes_v1.geojson")
fig = go.Figure()

# Try to match route using port proximity
start_point = Point(lon1, lat1)
end_point = Point(lon2, lat2)
threshold_deg = 1.0  # ~50–100 km proximity threshold

filtered_lanes = []
for _, row in shipping_lanes.iterrows():
    geom = row.geometry
    if geom.type == 'LineString':
        if start_point.distance(geom) < threshold_deg and end_point.distance(geom) < threshold_deg:
            filtered_lanes.append(geom)
    elif geom.type == 'MultiLineString':
        for line in geom.geoms:
            if start_point.distance(line) < threshold_deg and end_point.distance(line) < threshold_deg:
                filtered_lanes.append(line)

for geom in filtered_lanes:
    lon, lat = list(geom.xy[0]), list(geom.xy[1])
    fig.add_trace(go.Scattergeo(
        lon=lon,
        lat=lat,
        mode='lines',
        line=dict(width=2, color='blue'),
        opacity=0.6,
        name="Matched Sea Lane"
    ))

if not filtered_lanes:
    fig.add_trace(go.Scattergeo(
        lon=[lon1, lon2],
        lat=[lat1, lat2],
        mode='lines+markers+text',
        line=dict(width=2, color='red'),
        marker=dict(size=6, color='red'),
        text=[departure_port, arrival_port],
        textposition="top center",
        name="Direct Route"
    ))

fig.update_layout(
    title='Shipping Route Visualization (With Real Sea Lanes)',
    height=550,
    margin=dict(l=0, r=0, t=40, b=0),  # 🔥 Remove all margins
    paper_bgcolor="#0e1117",         # 🔥 Dark background
    geo=dict(
        projection_type='orthographic',
        showland=True,
        showocean=True,
        showcountries=True,
        landcolor='rgb(0, 128, 0)',             # 🔥 Dark land
        oceancolor='rgb(20, 30, 60)',          # 🔥 Dark ocean
        bgcolor='rgba(0,0,0,0)',               # 🔥 Transparent globe bg
        countrycolor='rgb(90, 90, 90)',        # 🔥 Softer borders
    )
)

st.plotly_chart(fig, use_container_width=True)

# Get region automatically from departure port
region = region_mapping.get(departure_port, "Custom")

# [Simulation settings and remaining app logic continues unchanged below]


# [Simulation settings and remaining app logic continues unchanged below]
# Continue the rest in sidebar
with st.sidebar:
    st.header("Simulation Settings")

    engine_type = st.selectbox("Engine Type", ["PEMFC", "H2-ICE"])
    compare_to_diesel = st.checkbox("Compare with Diesel baseline")

    distance_km = haversine(lon1, lat1, lon2, lat2)
    use_port_distance = st.checkbox("Use Port-Based Distance")
    if use_port_distance:
        route_km = distance_km
        st.info(f"Auto-filled distance: {distance_km:.2f} km")
    else:
        route_km = st.slider("Route Distance (km)", 100, 3000, 400, 100)

    # ORC Module Toggle
    if engine_type == "H2-ICE":
        enable_orc = st.checkbox("Enable Organic Rankine Cycle (ORC) Module")
        if enable_orc:
            st.info("ORC module activated: Increases system efficiency by ~8–10% based on engine load.")
    else:
        enable_orc = False  # Force-disable for PEMFC

    if region == "Southeast Asia":
        hydrogen_cost_pemfc, hydrogen_cost_h2ice, diesel_price_per_liter = 6.0, 5.0, 0.85
    elif region == "EU":
        hydrogen_cost_pemfc, hydrogen_cost_h2ice, diesel_price_per_liter = 9.0, 7.5, 1.5
    elif region == "USA":
        hydrogen_cost_pemfc, hydrogen_cost_h2ice, diesel_price_per_liter = 7.0, 6.0, 1.0
    elif region == "Middle East":
        hydrogen_cost_pemfc, hydrogen_cost_h2ice, diesel_price_per_liter = 5.0, 4.0, 0.6
    else:
        hydrogen_cost_pemfc = st.number_input("Hydrogen Cost for PEMFC (USD/kg)", 1.0, 15.0, 6.0)
        hydrogen_cost_h2ice = st.number_input("Hydrogen Cost for H₂-ICE (USD/kg)", 1.0, 15.0, 5.0)
        diesel_price_per_liter = st.number_input("Diesel Price (USD/liter)", 0.0, 5.0, 0.8)

    # Manual Hydrogen Price Override
    manual_price_override = st.checkbox("Manually Enter Hydrogen Price")
    if manual_price_override:
        hydrogen_cost_pemfc = st.number_input("Hydrogen Cost for PEMFC (USD/kg)", 1.0, 15.0, hydrogen_cost_pemfc)
        hydrogen_cost_h2ice = st.number_input("Hydrogen Cost for H₂-ICE (USD/kg)", 1.0, 15.0, hydrogen_cost_h2ice)
    vessel_type = st.selectbox("Vessel Type", ["RoRo", "Tanker", "Ferry", "Bulk Carrier"])
    default_mass = {"RoRo": 3000, "Tanker": 7000, "Ferry": 1000, "Bulk Carrier": 10000}[vessel_type]
    default_load = {"RoRo": 0.8, "Tanker": 0.85, "Ferry": 0.6, "Bulk Carrier": 0.9}[vessel_type]

    cargo_mass = st.number_input("Cargo Mass (tons)", 100, 10000, default_mass, 100)
    load_factor = st.slider("Load Factor", 0.1, 1.0, default_load, 0.05)


    fuel_type = "Ultra-pure" if engine_type == "PEMFC" else "Standard"
    fuel_cost = hydrogen_cost_pemfc if engine_type == "PEMFC" else hydrogen_cost_h2ice

    emission_factor = st.number_input("Emission Factor (kg CO₂e/kg H₂)", 0.0, 12.0, 10.0)
    carbon_price = st.number_input("Carbon Price (USD/ton CO₂)", 0, 500, 100)
    compare_mode = st.checkbox("🔄 Compare PEMFC vs H2-ICE")
    baseline_emission_factor = st.number_input("Baseline Diesel Emission Factor (kg CO₂e/km)", 0.0, 100.0, 70.0, 1.0)

config = {
    "engine_type": engine_type,
    "route_km": route_km,
    "enable_orc": enable_orc,
    "load_factor": load_factor,
    "fuel_cost_usd_per_kg": fuel_cost,
    "emission_factor_kg_co2e_per_kg_h2": emission_factor,
    "carbon_price_usd_per_ton": carbon_price,
    "cargo_mass_tons": cargo_mass,
    "vessel_type": vessel_type
}



def simulate(config):
    mission = simulate_mission(config)
    hydro = evaluate_hydrogen_system(config, mission)
    energy = calculate_energy_flow(config, hydro)
    cost = estimate_costs(config, energy)
    emissions = calculate_emissions(config, energy)
    distance = config["route_km"]
    baseline_emissions_total = baseline_emission_factor * distance
    carbon_savings = baseline_emissions_total - emissions["total_emissions_kg_co2e"]
    return {
        "mission": mission,
        "hydrogen": hydro,
        "energy": energy,
        "cost": cost,
        "emissions": emissions,
        "baseline_emissions_total": baseline_emissions_total,
        "carbon_savings": carbon_savings
    }

if compare_mode:
    results = {}
    for etype in ["PEMFC", "H2-ICE"]:
        cfg = config.copy()
        cfg["engine_type"] = etype
        cfg["fuel_cost_usd_per_kg"] = hydrogen_cost_pemfc if etype == "PEMFC" else hydrogen_cost_h2ice
        results[etype] = simulate(cfg)

    st.subheader("PEMFC vs H2-ICE Comparison")
    col1, col2 = st.columns(2)
    for i, etype in enumerate(["PEMFC", "H2-ICE"]):
        r = results[etype]
        with (col1 if i == 0 else col2):
            st.markdown(f"### {etype}")
            st.metric("Total Cost", f"${r['cost']['total_cost_usd']:,.0f}")
            st.metric("Cost per ton-km", f"${r['cost']['cost_per_ton_km_usd']:.4f}")
            st.metric("CO₂ Emissions", f"{r['emissions']['total_emissions_kg_co2e']:,.0f} kg")
            st.metric("Emissions per ton-km", f"{r['emissions']['emissions_per_ton_km_kg_co2e']:.4f} kg")
            st.metric("Baseline Emissions", f"{r['baseline_emissions_total']:,.0f} kg CO₂e")
            st.metric("Carbon Savings", f"{r['carbon_savings']:,.0f} kg CO₂e avoided")

    comp_fig = go.Figure([
        go.Bar(name='PEMFC', x=["Total Cost", "Emissions"], y=[
            results["PEMFC"]["cost"]["total_cost_usd"],
            results["PEMFC"]["emissions"]["total_emissions_kg_co2e"]
        ]),
        go.Bar(name='H2-ICE', x=["Total Cost", "Emissions"], y=[
            results["H2-ICE"]["cost"]["total_cost_usd"],
            results["H2-ICE"]["emissions"]["total_emissions_kg_co2e"]
        ])
    ])
    comp_fig.update_layout(barmode="group", title="Total Cost & Emissions Comparison")
    st.plotly_chart(comp_fig, use_container_width=True)

    if config["route_km"] <= 0:
        st.error("❗Route distance must be greater than zero. Please select different ports or manually enter a valid distance.")
        st.stop()



else:
    results = simulate(config)
    cost = results["cost"]
    emissions = results["emissions"]
    hydro = results["hydrogen"]
    baseline_emissions_total = results["baseline_emissions_total"]
    carbon_savings = results["carbon_savings"]

    hydrogen_kwh = hydro["hydrogen_needed_kg"] * 33.3
    diesel_liters_needed = hydrogen_kwh / 10.7
    diesel_cost = diesel_liters_needed * diesel_price_per_liter
    fuel_savings = diesel_cost - cost["fuel_cost_usd"]

    st.subheader("Simulation Results")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Hydrogen Fuel Cost", f"${cost['fuel_cost_usd']:,.0f}")
        st.metric("Diesel Equivalent Cost", f"${diesel_cost:,.0f}")
        st.metric("Fuel Cost Savings", f"${fuel_savings:,.0f}")
        st.metric("Total Cost", f"${cost['total_cost_usd']:,.0f}")
    with col2:
        st.metric("Hydrogen Used", f"{hydro['hydrogen_needed_kg']:,.0f} kg")
        st.metric("CO₂ Emissions", f"{emissions['total_emissions_kg_co2e']:,.0f} kg")
        st.metric("Baseline Emissions", f"{baseline_emissions_total:,.0f} kg")
        st.metric("Carbon Savings", f"{carbon_savings:,.0f} kg")

    cost_fig = go.Figure()
    cost_fig.add_trace(go.Bar(
        x=["Fuel Cost", "Carbon Cost"],
        y=[cost["fuel_cost_usd"], cost["carbon_cost_usd"]],
        marker_color=["green", "red"],
        text=[f"${cost['fuel_cost_usd']:,.0f}", f"${cost['carbon_cost_usd']:,.0f}"],
        textposition="auto"
    ))
    cost_fig.update_layout(title=f"{engine_type} – Cost Breakdown", yaxis_title="USD")
    st.plotly_chart(cost_fig, use_container_width=True)

    em_fig = go.Figure()
    em_fig.add_trace(go.Bar(
        x=["Hydrogen Emissions", "Diesel Baseline"],
        y=[emissions["total_emissions_kg_co2e"], baseline_emissions_total],
        marker_color=["green", "orange"],
        text=[f"{emissions['total_emissions_kg_co2e']:,.0f} kg", f"{baseline_emissions_total:,.0f} kg"],
        textposition="auto"
    ))
    em_fig.update_layout(title="Emissions Comparison", yaxis_title="kg CO₂e", barmode="group")
    st.plotly_chart(em_fig, use_container_width=True)

    flat_result = {
        "engine_type": engine_type,
        "fuel_type": fuel_type,
        "region": region,
        "route_km": route_km,
        "cargo_mass_tons": cargo_mass,
        "load_factor": load_factor,
        "fuel_cost_usd_per_kg": fuel_cost,
        "diesel_price_per_liter": diesel_price_per_liter,
        "diesel_equivalent_cost_usd": diesel_cost,
        "fuel_cost_savings_usd": fuel_savings,
        "emission_factor_kg_co2e_per_kg_h2": emission_factor,
        "carbon_price_usd_per_ton": carbon_price,
        "baseline_emissions_kg": baseline_emissions_total,
        "carbon_savings_kg": carbon_savings,
        **cost,
        **emissions,
        **hydro
    }

    df = pd.DataFrame([flat_result])
    st.download_button(
        label="⬇️ Download Results as CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="hydrosim_results.csv",
        mime="text/csv"
    )
