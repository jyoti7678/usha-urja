
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# --- STEP 1: MOCK DATA GENERATOR ---
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
        
    # Check/Create neighborhood data
    recreate_neighborhood = False
    if not os.path.exists("neighborhood_usage.csv"):
        recreate_neighborhood = True
    else:
        try:
            temp_df = pd.read_csv("neighborhood_usage.csv")
            if 'Average' not in temp_df['Household'].values: recreate_neighborhood = True
        except: recreate_neighborhood = True

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
    score = max(0, min(100, 100 - (total_units / 10)))
    if score > 80: st.success(f"Score: {score:.0f}/100 (Excellent)")
    elif score > 50: st.warning(f"Score: {score:.0f}/100 (Average)")
    else: st.error(f"Score: {score:.0f}/100 (Poor)")

    high_usage = data[data["Monthly_kWh"] > data["Monthly_kWh"].mean()]
    for _, row in high_usage.iterrows():
        st.info(f"🤖 **AI Tip:** {row['Appliance']} consumes {row['Monthly_kWh']:.1f} kWh. Shaving 1 hour off saves ₹{row['Wattage']*1*30/1000*rate:.0f}.")

# --- 2. APPLIANCE ENERGY ---
elif menu == "Appliance Energy":
    st.subheader("📊 Appliance Energy Breakdown")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(data["Appliance"], data["Monthly_kWh"], color=["#FF6B6B","#4ECDC4","#FFD93D","#6A5ACD","#FF9F1C","#2EC4B6","#E71D36"])
    plt.xticks(rotation=45)
    st.pyplot(fig)

# --- 3. BILL ANALYSIS (FIXED FOR electricity_usage.csv) ---
elif menu == "Bill Analysis":
    st.subheader("📂 Smart Bill Analysis")
    uploaded_file = st.file_uploader("Upload your bill CSV (electricity_usage.csv)", type=["csv"])
    
    if uploaded_file:
        bill_df = pd.read_csv(uploaded_file)
        
        # Look for columns in your specific file
        col_units = next((c for c in bill_df.columns if c.lower() in ["units_consumed", "units", "consumption"]), None)
        col_cost = next((c for c in bill_df.columns if c.lower() in ["bill_amount", "cost", "amount"]), None)
        col_month = next((c for c in bill_df.columns if c.lower() in ["month", "billing_period"]), None)

        if col_units and col_cost:
            # Stats based on ALL data in the CSV
            avg_u = bill_df[col_units].mean()
            tot_c = bill_df[col_cost].sum()
            tot_co2 = bill_df[col_units].sum() * 0.82
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Avg Monthly Units", f"{avg_u:.1f} kWh")
            c2.metric("Total Period Spend", f"₹ {tot_c:.0f}")
            c3.metric("Total CO₂ Impact", f"{tot_co2:.1f} kg")
            
            # Historical Trend Chart
            st.write("### 📈 Consumption History")
            if col_month:
                # Groups by month and averages the consumption (useful if CSV has multiple users)
                monthly_trend = bill_df.groupby(col_month)[col_units].mean()
                st.line_chart(monthly_trend)
            else:
                st.line_chart(bill_df[col_units])
            
            # Neighborhood Benchmark
            st.write("### 🏘 Neighborhood Benchmarking")
            neighbor = pd.read_csv("neighborhood_usage.csv")
            neighbor.loc[neighbor['Household'] == 'You', 'Units'] = avg_u
            st.bar_chart(neighbor.set_index("Household")["Units"])
            
            avg_n = neighbor[neighbor['Household'] == 'Average']['Units'].values[0]
            if avg_u > avg_n:
                st.error(f"⚠️ You are {avg_u - avg_n:.0f} units ABOVE average.")
            else:
                st.success("✅ You are more energy-efficient than your neighbors!")
        else:
            st.error("Error: Could not find 'units_consumed' or 'bill_amount' in your CSV.")
    else:
        st.info("Awaiting file upload... Try uploading your 'electricity_usage.csv'.")

# --- 4. SOLAR & P2P SHARING ---
elif menu == "Solar & P2P Sharing":
    st.subheader("☀ Solar Forecast & P2P Marketplace")
    weather_df = pd.DataFrame({"Day": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], "Solar": [4.5, 5.2, 5.5, 4.8, 4.0, 3.9, 4.6]})
    st.line_chart(weather_df.set_index("Day")["Solar"])
    
    gen = st.slider("Solar Generation (kWh)", 0, 50, 20)
    cons = st.slider("Home Consumption (kWh)", 0, 50, 12)
    surplus = gen - cons
    if surplus > 0:
        st.success(f"🌟 Surplus: {surplus:.1f} kWh. Earn ₹{surplus*5:.0f} today.")
        if st.button("List on P2P Market"): st.toast("Listed!", icon="✅")
    else:
        st.warning(f"No surplus. Consuming {abs(surplus):.1f} kWh from grid.")