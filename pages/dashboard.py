import streamlit as st
import pandas as pd
import datetime
import io
from streamlit_autorefresh import st_autorefresh
import backend_helper
import utils

# Auto-refresh every 5 minutes (300,000 ms)
st_autorefresh(interval=300_000, key="dashboard_autorefresh")

st.title("📊 Equity Research Dashboard")

# Market status + refresh bar
utils.render_status_bar(refresh_interval_secs=300)

# Initialize Angel One Client
try:
    angel_secrets = st.secrets["angel_one"]
    client = backend_helper.get_angel_client(
        api_key=angel_secrets["api_key"],
        client_code=angel_secrets["client_code"],
        password=angel_secrets["password"],
        totp_secret=angel_secrets["totp_secret"]
    )
except KeyError:
    st.error("⚠️ Angel One secrets not configured in .streamlit/secrets.toml!")
    client = None

# --- Real Angel One Data Fetcher ---
def get_real_index_data(obj):
    fallback = {"cmp": 0, "pct_change": 0}
    if not obj:
        return {"NIFTY 50": fallback, "SENSEX": fallback, "NIFTY SMALLCAP 100": fallback}

    nifty    = backend_helper.get_live_market_data(obj, "26000",    "NSE") or fallback
    sensex   = backend_helper.get_live_market_data(obj, "99919000", "BSE") or fallback
    smallcap = backend_helper.get_live_market_data(obj, "99926032", "NSE") or fallback

    return {
        "NIFTY 50": nifty,
        "SENSEX": sensex,
        "NIFTY SMALLCAP 100": smallcap
    }

indices_data = get_real_index_data(client)

# --- Total Companies Metric ---
try:
    drive_service = backend_helper.get_drive_service()
    folder_id = st.secrets["google_drive"]["folder_id"]
    reports_df = backend_helper.load_csv_database(drive_service, folder_id, 'reports_db.csv')
    total_companies = len(reports_df) if not reports_df.empty else 0
except Exception:
    total_companies = 0
    drive_service = None
    folder_id = None

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
    st.metric(label="Total Companies Uploaded", value=str(total_companies))
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
        analyst_name = st.text_input(
            "Analyst Name",
            value=st.session_state.user_email.split('@')[0].capitalize()
                  if st.session_state.get('user_email') else 'Analyst'
        )
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

    uploaded_file = st.file_uploader("📎 Upload Research File (PDF, PPTX, DOCX, XLSX...)")

    submit_upload = st.form_submit_button("Submit Research & Sync to Drive", type="primary")

    if submit_upload:
        if company_name and ticker:
            if not drive_service or not folder_id:
                st.error("Google Drive is not configured properly in st.secrets.")
            else:
                with st.spinner("Uploading and saving..."):
                    try:
                        # --- Upload file to Supabase Storage ---
                        file_link = ""
                        if uploaded_file:
                            file_bytes = uploaded_file.getvalue()
                            file_ext   = uploaded_file.name.rsplit('.', 1)[-1]
                            safe_name  = f"{ticker.upper().strip()}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
                            file_link  = backend_helper.upload_file_to_supabase(file_bytes, safe_name)

                        new_data = {
                            "Company Name": company_name,
                            "Ticker": ticker.upper().strip(),
                            "Exchange": exchange,
                            "Date Added": str(date_submission),
                            "Price When Added": price_during_research,
                            "Market Cap when added": market_cap_research,
                            "Industry": industry,
                            "Research Type": research_type,
                            "Latest Qtr": latest_qtr,
                            "Rating": rating,
                            "Analyst": analyst_name,
                            "Comment": comment_by_owner,
                            "File Link": file_link
                        }

                        # Load existing DB or create new
                        df = backend_helper.load_csv_database(drive_service, folder_id, 'reports_db.csv')
                        if df.empty:
                            df = pd.DataFrame([new_data])
                        else:
                            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)

                        # Save back to Drive
                        success = backend_helper.save_csv_database(drive_service, df, folder_id, 'reports_db.csv')

                        if success:
                            st.success(f"✅ Research for **{company_name}** saved successfully!")
                        else:
                            st.error("❌ Metadata saved but failed to sync to Google Drive.")

                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        else:
            st.error("Please fill in at least Company Name and Ticker.")


