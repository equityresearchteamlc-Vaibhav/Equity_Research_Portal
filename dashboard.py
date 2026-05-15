import streamlit as st
import pandas as pd
import datetime
from streamlit_autorefresh import st_autorefresh

# Use autorefresh to update the page every 10 seconds (10000 milliseconds)
st_autorefresh(interval=10000, key="dashboard_autorefresh")

st.title("📊 Equity Research Dashboard")

# --- Mock Angel One Data Fetcher ---
# In a real scenario, this would use backend_helper.py to fetch actual data.
def get_mock_index_data():
    # Returns dummy data for demonstration
    import random
    return {
        "NIFTY 50": {"cmp": 22500 + random.randint(-50, 50), "pct_change": random.uniform(-1, 1)},
        "SENSEX": {"cmp": 74000 + random.randint(-150, 150), "pct_change": random.uniform(-1, 1)},
        "NIFTY SMALLCAP 100": {"cmp": 16500 + random.randint(-40, 40), "pct_change": random.uniform(-1.5, 1.5)}
    }

indices_data = get_mock_index_data()

# --- Real-Time Metric Cards ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="NIFTY 50", 
        value=f"₹{indices_data['NIFTY 50']['cmp']:,.2f}", 
        delta=f"{indices_data['NIFTY 50']['pct_change']:.2f}%"
    )
with col2:
    st.metric(
        label="SENSEX", 
        value=f"₹{indices_data['SENSEX']['cmp']:,.2f}", 
        delta=f"{indices_data['SENSEX']['pct_change']:.2f}%"
    )
with col3:
    st.metric(
        label="NIFTY SMALLCAP 100", 
        value=f"₹{indices_data['NIFTY SMALLCAP 100']['cmp']:,.2f}", 
        delta=f"{indices_data['NIFTY SMALLCAP 100']['pct_change']:.2f}%"
    )
with col4:
    # "Total Companies Uploaded" metric box redirecting to the list page
    st.metric(label="Total Companies Uploaded", value="24")
    if st.button("View All Companies ➡️", use_container_width=True):
        st.switch_page("pages/list_companies.py")

st.divider()

# --- Search Bar ---
search_query = st.text_input("🔍 Search Companies by Keyword (e.g. 'Tata', 'Tech')", "")

# --- Comprehensive Upload Form ---
st.subheader("📤 Upload New Research")
with st.form("upload_research_form"):
    col_a, col_b = st.columns(2)
    
    with col_a:
        analyst_name = st.text_input("Analyst Name", value=st.session_state.user_email.split('@')[0].capitalize() if st.session_state.get('user_email') else 'Analyst')
        company_name = st.text_input("Company Name")
        ticker = st.text_input("Ticker Symbol (e.g., RELIANCE)")
        exchange = st.selectbox("Exchange", ["NSE", "BSE"])
        price_during_research = st.number_input("Price during research (₹)", min_value=0.0, format="%.2f")
        market_cap_research = st.number_input("Market Cap during research (₹ Cr)", min_value=0.0, format="%.2f")
    
    with col_b:
        industry = st.text_input("Industry / Sector")
        research_type = st.selectbox("Research Type", ["Fundamental only", "Technical only", "Both"])
        latest_qtr = st.text_input("Latest Qtr Result available (e.g., Q4 FY24)")
        date_submission = st.date_input("Date of submission", datetime.date.today())
        rating = st.slider("Rating by Owner (1-5 Stars)", 1, 5, 3)
        comment_by_owner = st.text_area("Comment by Owner")
        
    uploaded_file = st.file_uploader("Upload Research File (PDF, PPTX, DOCX, etc.)")
    
    submit_upload = st.form_submit_button("Submit Research & Sync to Drive", type="primary")
    
    if submit_upload:
        if company_name and ticker and uploaded_file:
            st.success(f"Successfully uploaded research for {company_name}! (Mock Sync)")
            # Here, you would call backend_helper.upload_file_to_drive 
            # and then update the 'reports_db.csv' database.
        else:
            st.error("Please fill in the Company Name, Ticker, and attach a file.")
