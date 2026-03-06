
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# --- STEP 1: AUTO-GENERATE MOCK DATA (Hackathon Safety Net) ---
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
        
    if not os.path.exists("neighborhood_usage.csv"):
        pd.DataFrame({
            "Household": ["You", "Neighbor A", "Neighbor B", "Neighbor C", "Average"],
            "Units": [320, 280, 450, 310, 340]
        }).to_csv("neighborhood_usage.csv", index=False)

create_mock_data()

# --- STEP 2: APP CONFIGURATION ---
st.set_page_config(page_title="USHA URJA", page_icon="⚡", layout="wide")
st.title("⚡ USHA URJA – Smart Energy Platform")

# --- STEP 3: SIDEBAR NAVIGATION ---
menu = st.sidebar.radio(
    "Navigation",
    ["Home Dashboard", "Appliance Energy", "Bill Analysis", "Solar & P2P Sharing"]
)

# --- STEP 4: DATA PROCESSING ---
appliance = pd.read_csv("appliance_power.csv")
load = pd.read_csv("household_load.csv")
tariff = pd.read_csv("tariff_delhi_domestic.csv")
data = pd.merge(appliance, load, on="Appliance")

data["Energy_kWh_day"] = (data["Wattage"] * data["Hours_per_day"]) / 1000
data["Monthly_kWh"] = data["Energy_kWh_day"] * 30

rate = tariff["Rate"].iloc[0]
total_units = data["Monthly_kWh"].sum()
bill = total_units * rate
co2 = total_units * 0.82

# --- PAGE 1: HOME DASHBOARD ---
if menu == "Home Dashboard":
    st.subheader("⚡ Energy Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Monthly Units", f"{total_units:.2f} kWh")
    col2.metric("Estimated Bill", f"₹ {bill:.2f}")
    col3.metric("CO₂ Emission", f"{co2:.2f} kg")

    st.divider()
    
    # Energy Efficiency Score
    st.subheader("🏠 Energy Efficiency Score")
    score = max(0, min(100, 100 - (total_units / 10))) 
    if score > 80:
        st.success(f"Score: {score:.0f}/100 (Excellent) - Your consumption is optimized!")
    elif score > 60:
        st.warning(f"Score: {score:.0f}/100 (Average) - There's room for improvement.")
    else:
        st.error(f"Score: {score:.0f}/100 (Needs Improvement) - High energy wastage detected.")

    # AI Insights
    st.subheader("🤖 AI Energy Insights")
    high_usage = data[data["Monthly_kWh"] > data["Monthly_kWh"].mean()]
    for index, row in high_usage.iterrows():
        if row["Appliance"] == "Air Conditioner":
            st.warning(f"⚠️ **AC Alert:** High usage detected. Shift usage to 2 PM-4 PM to utilize 'Community Solar' and save ₹50.")
        else:
            st.info(f"ℹ️ **Optimization:** {row['Appliance']} is a top consumer. Check for standby power leakage.")

# --- PAGE 2: APPLIANCE ENERGY ---
elif menu == "Appliance Energy":
    st.subheader("📊 Appliance Energy Consumption")
    
    # Colored Chart
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#FF6B6B","#4ECDC4","#FFD93D","#6A5ACD","#FF9F1C","#2EC4B6","#E71D36"]
    ax.bar(data["Appliance"], data["Monthly_kWh"], color=colors[:len(data)])
    ax.set_ylabel("Monthly Energy (kWh)")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.subheader("🔢 Live Calculator")
    app_choice = st.selectbox("Select Appliance", appliance["Appliance"])
    hrs = st.slider("Daily Usage (Hours)", 0, 24, 4)
    w = appliance[appliance["Appliance"] == app_choice]["Wattage"].values[0]
    st.info(f"Monthly Cost for {app_choice}: ₹ {(w * hrs * 30 / 1000) * rate:.2f}")

# --- PAGE 3: BILL ANALYSIS ---
elif menu == "Bill Analysis":
    st.subheader("📂 Bill Insights")
    st.info("Upload your historical data to see trends.")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        bill_df = pd.read_csv(uploaded_file)
        st.line_chart(bill_df.set_index("Month")["Units"])
    
    st.subheader("🏘 Neighborhood Benchmark")
    try:
        neighbor = pd.read_csv("neighborhood_usage.csv")
        st.bar_chart(neighbor.set_index("Household"))
    except:
        st.warning("Comparison data missing.")

# --- PAGE 4: SOLAR & P2P SHARING ---
elif menu == "Solar & P2P Sharing":
    st.subheader("☀ Solar Energy Forecast")
    weather_df = pd.DataFrame({
        "Day": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
        "Solar_Potential_kWh": [4.5, 5.2, 5.5, 4.8, 4.0, 3.9, 4.6]
    })

    # Colored Solar Chart
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.plot(weather_df["Day"], weather_df["Solar_Potential_kWh"], marker="o", lw=3, color="#FFA500")
    ax2.fill_between(weather_df["Day"], weather_df["Solar_Potential_kWh"], color="#FFF3E0")
    ax2.set_ylabel("Solar Energy (kWh)")
    st.pyplot(fig2)

    st.subheader("⚡ P2P Energy Trading")
    gen = st.slider("Solar Generation (kWh)", 0, 50, 15)
    cons = st.slider("Home Consumption (kWh)", 0, 50, 10)
    surplus = gen - cons

    if surplus > 0:
        st.success(f"🌟 Surplus: {surplus:.2f} kWh. Potential Earnings: ₹ {surplus * 5:.2f}")
    else:
        st.warning("All solar energy consumed by household.")