import streamlit as st
import pandas as pd
import datetime
import io
from streamlit_autorefresh import st_autorefresh
import backend_helper
import utils

# Auto-refresh every 5 minutes (300,000 ms)
st_autorefresh(interval=300_000, key="dashboard_autorefresh")

# Inject premium CSS styling
utils.inject_custom_css()

# Display Lingual logo in top right corner
utils.render_lingual_logo(position="top-right", show_tagline=False)

# Modern page header
utils.render_page_header(
    "Equity Research Dashboard", 
    "Real-time market data and research management",
    "📊"
)

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

# --- Initialize Form Session States ---
# --- Initialize Form Version counter ---
if "form_version" not in st.session_state:
    st.session_state.form_version = 0

# --- Search Section ---
st.subheader("🔍 Search Tracked Companies")
search_query = st.text_input("Type company name or ticker to filter suggestions:", "", key="dashboard_company_search")

try:
    drive_service = backend_helper.get_drive_service()
    folder_id = st.secrets["google_drive"]["folder_id"]
    db_df = backend_helper.load_csv_database(drive_service, folder_id, 'reports_db.csv')
except Exception:
    db_df = pd.DataFrame()
    drive_service = None
    folder_id = None

if not db_df.empty:
    if search_query:
        filtered_df = db_df[
            db_df['Company Name'].str.contains(search_query, case=False, na=False) |
            db_df['Ticker'].str.contains(search_query, case=False, na=False)
        ]
    else:
        filtered_df = db_df

    if filtered_df.empty:
        st.info("No matching companies found.")
    else:
        # Create display list: "Company Name (Ticker)"
        display_options = (filtered_df['Company Name'] + " (" + filtered_df['Ticker'] + ")").tolist()
        
        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            selected_display = st.selectbox("Select a company from the list:", options=display_options, key="dashboard_search_select")
        with col_s2:
            st.write("")
            st.write("")
            if st.button("👁️ View Profile", key="dashboard_search_view_btn", use_container_width=True, type="primary"):
                # Extract ticker from within parentheses
                selected_ticker = selected_display.split("(")[-1].replace(")", "").strip()
                selected_row = db_df[db_df['Ticker'] == selected_ticker].iloc[0]
                st.session_state.selected_ticker = selected_row['Ticker']
                st.session_state.selected_company  = selected_row['Company Name']
                st.session_state.selected_exchange = selected_row.get('Exchange', 'NSE')
                st.session_state.selected_file_id  = selected_row.get('File ID', '')
                st.session_state.selected_file_link = selected_row.get('File Link', '')
                st.session_state.selected_price_added = selected_row.get('Price When Added', 0)
                st.session_state.selected_mc_added    = selected_row.get('Market Cap when added', 0)
                st.switch_page("pages/company_profile.py")
else:
    st.info("No tracked companies in the database.")

st.divider()

# --- Comprehensive Upload Form ---
st.subheader("📤 Upload New Research")

# Display persistent success message after rerun
if "upload_success_message" in st.session_state:
    st.success(st.session_state.upload_success_message)
    del st.session_state.upload_success_message

# We render the form elements with keys linked to st.session_state.form_version
with st.form("upload_research_form"):
    col_a, col_b = st.columns(2)

    with col_a:
        analyst_name = st.text_input(
            "Analyst Name",
            value=st.session_state.user_email.split('@')[0].capitalize()
                  if st.session_state.get('user_email') else 'Analyst'
        )
        company_name = st.text_input("Company Name", key=f"upload_company_name_{st.session_state.form_version}")
        ticker = st.text_input("Ticker Symbol (e.g., RELIANCE)", key=f"upload_ticker_{st.session_state.form_version}")
        exchange = st.selectbox("Exchange", ["NSE", "BSE"])
        price_during_research = st.number_input("Price during research (₹)", min_value=0.0, format="%.2f", key=f"upload_price_{st.session_state.form_version}")
        market_cap_research = st.number_input("Market Cap during research (₹ Cr)", min_value=0.0, format="%.2f", key=f"upload_market_cap_{st.session_state.form_version}")

    with col_b:
        industry = st.text_input("Industry / Sector", key=f"upload_industry_{st.session_state.form_version}")
        research_type = st.selectbox("Research Type", ["Fundamental only", "Technical only", "Both"])
        latest_qtr = st.text_input("Latest Qtr Result available (e.g., Q4 FY24)", key=f"upload_qtr_{st.session_state.form_version}")
        date_submission = st.date_input("Date of submission", datetime.date.today())
        rating = st.slider("Rating by Owner (1-10 Stars)", 1, 10, 5)
        comment_by_owner = st.text_area("Comment by Owner", key=f"upload_comment_{st.session_state.form_version}")

    uploaded_file = st.file_uploader(
        "📎 Upload Research File (PDF, PPTX, DOCX, XLSX...)",
        key=f"file_uploader_{st.session_state.form_version}"
    )

    submit_upload = st.form_submit_button("Submit Research & Sync to Drive", type="primary")

    if submit_upload:
        if company_name and ticker:
            if not drive_service or not folder_id:
                st.error("Google Drive is not configured properly in st.secrets.")
            else:
                status_placeholder = st.empty()
                with status_placeholder.container():
                    col_l, col_c, col_r = st.columns([2, 1, 2])
                    with col_c:
                        import os
                        gif_path = os.path.join(os.getcwd(), "loading.gif")
                        if not os.path.exists(gif_path):
                            gif_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "loading.gif")
                        
                        if os.path.exists(gif_path):
                            st.image(gif_path, use_container_width=True)
                        else:
                            st.info("🔄 Uploading...")
                    st.info("Uploading research file and syncing metadata...")
                try:
                    # --- Upload file to Google Drive ---
                    file_id = ""
                    file_link = ""
                    if uploaded_file:
                        file_bytes = uploaded_file.getvalue()
                        file_ext   = uploaded_file.name.rsplit('.', 1)[-1]
                        safe_name  = f"{ticker.upper().strip()}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
                        file_id    = backend_helper.upload_file_to_drive(drive_service, file_bytes, safe_name, folder_id)
                        if file_id:
                            file_link = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"

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
                        "File ID": file_id,
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
                    status_placeholder.empty()

                    if success:
                        st.session_state.upload_success_message = f"✅ Research for **{company_name}** saved successfully!"
                        
                        # Increment form version to clear all fields cleanly without session state errors
                        st.session_state.form_version += 1
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Metadata saved but failed to sync to Google Drive.")

                except Exception as e:
                    status_placeholder.empty()
                    st.error(f"❌ Error: {e}")
        else:
            st.error("Please fill in at least Company Name and Ticker.")


