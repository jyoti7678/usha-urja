import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# --- STEP 1: MOCK DATA GENERATOR ---
# This ensures the app works immediately even if CSVs are missing
def create_mock_data():
    if not os.path.exists("appliance_power.csv"):
        pd.DataFrame({
            "Appliance": ["Air Conditioner", "Refrigerator", "Washing Machine", "LED Lights", "Ceiling Fan", "Laptop", "Microwave"],
            "Wattage": [1500, 200, 500, 40, 75, 65, 1200]
        }).to_csv("appliance_power.csv", index=False)
        
    if not os.path.exists("household_load.csv"):
        pd.DataFrame({
            "Appliance": ["Air Conditioner", "Refrigerator", "Washing Machine", "LED Lights", "Ceiling Fan", "Laptop", "Microwave"],
            "Hours_per_day": [6, 24, 1, 8, 12, 10, 0.5]
        }).to_csv("household_load.csv", index=False)
        
    if not os.path.exists("tariff_delhi_domestic.csv"):
        pd.DataFrame({"Slab": ["Flat"], "Rate": [7.0]}).to_csv("tariff_delhi_domestic.csv", index=False)
        
    # Enhanced check: recreate if file missing OR if 'Average' is missing from the file
    recreate_neighborhood = False
    if not os.path.exists("neighborhood_usage.csv"):
        recreate_neighborhood = True
    else:
        try:
            temp_df = pd.read_csv("neighborhood_usage.csv")
            if 'Average' not in temp_df['Household'].values:
                recreate_neighborhood = True
        except:
            recreate_neighborhood = True

    if recreate_neighborhood:
        pd.DataFrame({
            "Household": ["You", "Neighbor A", "Neighbor B", "Neighbor C", "Average"],
            "Units": [320, 280, 450, 310, 340]
        }).to_csv("neighborhood_usage.csv", index=False)

create_mock_data()

# --- APP CONFIG ---
st.set_page_config(page_title="USHA URJA", page_icon="⚡", layout="wide")
st.title("⚡ USHA URJA – Smart Energy Platform")

# --- SIDEBAR NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["Home Dashboard", "Appliance Energy", "Bill Analysis", "Solar & P2P Sharing"])

# --- DATA LOADING ---
appliance = pd.read_csv("appliance_power.csv")
load = pd.read_csv("household_load.csv")
tariff = pd.read_csv("tariff_delhi_domestic.csv")
data = pd.merge(appliance, load, on="Appliance")

# Calculate Monthly Consumption
data["Monthly_kWh"] = (data["Wattage"] * data["Hours_per_day"] * 30) / 1000
rate = tariff["Rate"].iloc[0]

# --- 1. HOME DASHBOARD ---
if menu == "Home Dashboard":
    total_units = data["Monthly_kWh"].sum()
    bill = total_units * rate
    co2 = total_units * 0.82
    
    st.subheader("⚡ Energy Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Current Monthly Units", f"{total_units:.2f} kWh")
    c2.metric("Estimated Bill", f"₹ {bill:.2f}")
    c3.metric("CO₂ Emission", f"{co2:.2f} kg")

    st.divider()

    st.subheader("🏠 Efficiency Score & AI Insights")
    # Score logic: lower units = higher score
    score = max(0, min(100, 100 - (total_units / 10)))
    if score > 80: 
        st.success(f"Score: {score:.0f}/100 (Excellent) - Your consumption is highly optimized!")
    elif score > 50: 
        st.warning(f"Score: {score:.0f}/100 (Average) - Minor adjustments could save you ₹500/month.")
    else: 
        st.error(f"Score: {score:.0f}/100 (Poor) - High energy wastage detected!")

    # Dynamic AI Tips
    high_usage = data[data["Monthly_kWh"] > data["Monthly_kWh"].mean()]
    for _, row in high_usage.iterrows():
        st.info(f"🤖 **AI Tip:** Your **{row['Appliance']}** is a top consumer ({row['Monthly_kWh']:.1f} kWh). Reducing its use by just 1 hour daily saves **₹{row['Wattage']*1*30/1000*rate:.0f}** per month.")

# --- 2. APPLIANCE ENERGY ---
elif menu == "Appliance Energy":
    st.subheader("📊 Appliance Energy Breakdown")
    
    fig, ax = plt.subplots(figsize=(10, 4))
    colors = ["#FF6B6B","#4ECDC4","#FFD93D","#6A5ACD","#FF9F1C","#2EC4B6","#E71D36"]
    ax.bar(data["Appliance"], data["Monthly_kWh"], color=colors[:len(data)])
    ax.set_ylabel("Monthly kWh")
    plt.xticks(rotation=45)
    st.pyplot(fig)
    
    st.write("### 🔍 Live Calculator")
    app_choice = st.selectbox("Select an appliance to analyze:", data["Appliance"])
    hrs = st.slider("Adjust Daily Usage (Hours)", 0, 24, 5)
    selected_watt = data[data["Appliance"] == app_choice]["Wattage"].values[0]
    calc_cost = (selected_watt * hrs * 30 / 1000) * rate
    st.write(f"Estimated Monthly Cost for {app_choice}: **₹ {calc_cost:.2f}**")

# --- 3. BILL ANALYSIS ---
elif menu == "Bill Analysis":
    st.subheader("📂 Smart Bill Analysis")
    st.write("Upload your `sample_bill.csv` to unlock historical insights and neighborhood benchmarking.")
    
    uploaded_file = st.file_uploader("Upload Bill CSV", type=["csv"])
    
    if uploaded_file:
        bill_df = pd.read_csv(uploaded_file)
        
        # Summary Metrics
        colA, colB, colC = st.columns(3)
        avg_units = bill_df["Units"].mean()
        total_cost = bill_df["Cost"].sum()
        total_co2 = bill_df["Units"].sum() * 0.82
        
        colA.metric("Avg Monthly Units", f"{avg_units:.0f} kWh")
        colB.metric("Total Period Spend", f"₹ {total_cost:.0f}")
        colC.metric("Total CO₂ Impact", f"{total_co2:.1f} kg")
        
        st.write("### 📈 Consumption History")
        st.line_chart(bill_df.set_index("Month")["Units"])
        
        st.write("### 🏘 Neighborhood Benchmarking")
        neighbor = pd.read_csv("neighborhood_usage.csv")
        # Update 'You' with the average from uploaded bill data
        neighbor.loc[neighbor['Household'] == 'You', 'Units'] = avg_units
        st.bar_chart(neighbor.set_index("Household")["Units"])
        
        # Comparative Logic with safety check for IndexError
        avg_neighbor_data = neighbor[neighbor['Household'] == 'Average']['Units']
        if not avg_neighbor_data.empty:
            avg_neighbor = avg_neighbor_data.values[0]
            if avg_units > avg_neighbor:
                st.error(f"⚠️ Your usage is {(avg_units - avg_neighbor):.0f} units ABOVE the neighborhood average. Consider an energy audit.")
            else:
                st.success("✅ You are more energy-efficient than your average neighbor. Keep it up!")
        else:
            st.info("Neighborhood average data is currently unavailable for comparison.")
    else:
        st.info("Awaiting file upload... Please use the 'sample_bill.csv' provided in your project files.")

# --- 4. SOLAR & P2P SHARING ---
elif menu == "Solar & P2P Sharing":
    st.subheader("☀ Solar Forecast & P2P Marketplace")
    
    # Simulated Solar Forecast
    weather_df = pd.DataFrame({
        "Day": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], 
        "Solar": [4.5, 5.2, 5.5, 4.8, 4.0, 3.9, 4.6]
    })
    
    fig2, ax2 = plt.subplots(figsize=(10, 3))
    ax2.plot(weather_df["Day"], weather_df["Solar"], marker="o", color="#FFA500", lw=3)
    ax2.fill_between(weather_df["Day"], weather_df["Solar"], color="#FFF3E0", alpha=0.5)
    ax2.set_ylabel("Solar Potential (kWh)")
    st.pyplot(fig2)

    st.write("### 🤝 Peer-to-Peer Trading Simulator")
    gen = st.slider("Solar Generation (kWh)", 0, 50, 20)
    cons = st.slider("Home Consumption (kWh)", 0, 50, 12)
    surplus = gen - cons
    
    if surplus > 0:
        st.success(f"🌟 **Surplus Detected:** {surplus:.1f} kWh available for sharing.")
        st.write(f"💰 **Potential Earnings:** ₹{surplus * 5:.2f} (Calculated at ₹5/unit P2P rate)")
        if st.button("List Surplus on P2P Market"):
            st.toast("Listed! Your neighbors have been notified.", icon="✅")
    else:
        st.warning(f"No surplus available. You are consuming {abs(surplus):.1f} kWh from the grid.")