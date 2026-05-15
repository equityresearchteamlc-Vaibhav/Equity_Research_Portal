import streamlit as st
import pandas as pd
import random

st.title("🏢 Uploaded Companies")

# --- Mock Data Generation ---
# In reality, this would load data from Google Drive via backend_helper.load_csv_database
def generate_mock_companies_db():
    companies = [
        {"Company Name": "Reliance Industries", "Ticker": "RELIANCE", "Date Added": "2024-01-10", "Price When Added": 2500, "Market Cap when added": 1700000},
        {"Company Name": "Tata Consultancy Services", "Ticker": "TCS", "Date Added": "2024-02-15", "Price When Added": 3800, "Market Cap when added": 1400000},
        {"Company Name": "HDFC Bank", "Ticker": "HDFCBANK", "Date Added": "2024-03-20", "Price When Added": 1450, "Market Cap when added": 1100000},
        {"Company Name": "Infosys", "Ticker": "INFY", "Date Added": "2024-04-05", "Price When Added": 1400, "Market Cap when added": 580000},
    ]
    
    data = []
    for comp in companies:
        cmp = comp["Price When Added"] * (1 + random.uniform(-0.1, 0.15))
        pct_change_added = ((cmp - comp["Price When Added"]) / comp["Price When Added"]) * 100
        today_pct_change = random.uniform(-2.5, 2.5)
        rt_market_cap = comp["Market Cap when added"] * (cmp / comp["Price When Added"])
        mc_change = ((rt_market_cap - comp["Market Cap when added"]) / comp["Market Cap when added"]) * 100
        
        data.append({
            "Company Name": comp["Company Name"],
            "Ticker": comp["Ticker"],
            "Date Added": comp["Date Added"],
            "Price When Added": comp["Price When Added"],
            "CMP (Real-time)": round(cmp, 2),
            "% Change since added": round(pct_change_added, 2),
            "Today's % Change": round(today_pct_change, 2),
            "Market Cap when added (Cr)": round(comp["Market Cap when added"], 2),
            "Real-time Market Cap (Cr)": round(rt_market_cap, 2),
            "% Change of Market Cap": round(mc_change, 2)
        })
    return pd.DataFrame(data)

df = generate_mock_companies_db()

# --- Summary Data Table ---
st.dataframe(
    df,
    use_container_width=True,
    column_config={
        "Price When Added": st.column_config.NumberColumn(format="₹%.2f"),
        "CMP (Real-time)": st.column_config.NumberColumn(format="₹%.2f"),
        "% Change since added": st.column_config.NumberColumn(format="%.2f%%"),
        "Today's % Change": st.column_config.NumberColumn(format="%.2f%%"),
        "Market Cap when added (Cr)": st.column_config.NumberColumn(format="₹%.2f"),
        "Real-time Market Cap (Cr)": st.column_config.NumberColumn(format="₹%.2f"),
        "% Change of Market Cap": st.column_config.NumberColumn(format="%.2f%%"),
    },
    hide_index=True
)

st.divider()

# --- View Actions ---
st.subheader("Quick Actions")
col1, col2 = st.columns([3, 1])
with col1:
    selected_ticker = st.selectbox("Select a company to view in detail:", df['Ticker'].tolist())
with col2:
    st.write("") # spacing
    st.write("")
    if st.button("👁️ View Profile", use_container_width=True, type="primary"):
        st.session_state.selected_ticker = selected_ticker
        st.session_state.selected_company = df[df['Ticker'] == selected_ticker]['Company Name'].values[0]
        st.switch_page("pages/company_profile.py")
