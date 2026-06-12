import streamlit as st
import pandas as pd
import datetime
import io
from streamlit_autorefresh import st_autorefresh
import importlib
import backend_helper
importlib.reload(backend_helper)
import utils


# Inject premium CSS styling
utils.inject_custom_css(st.session_state.get("app_theme", "Dark"))

# Auto-refresh every 5 minutes (300,000 ms)
st_autorefresh(interval=300_000, key="dashboard_autorefresh")

# Display Lingual logo in top right corner
utils.render_lingual_logo(position="top-right", show_tagline=False)

# Modern page header
utils.render_page_header(
    "Equity Research Dashboard", 
    "Real-time market data and research management",
    "📊"
)

# Display Game of Thrones banner if theme is selected
if st.session_state.get("app_theme", "Dark") == "Game of Thrones":
    import os
    if os.path.exists("got_banner.png"):
        st.image("got_banner.png", use_container_width=True)

# Market status + refresh bar
utils.render_status_bar(refresh_interval_secs=300)

# Display persistent success message after rerun
if "upload_success_message" in st.session_state:
    st.success(st.session_state.upload_success_message)
    del st.session_state.upload_success_message

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

# --- Real Angel One Data Fetcher (Batch & Cached) ---
@st.cache_data(ttl=30, show_spinner=False)
def get_cached_index_data(_obj):
    fallback = {"cmp": 0, "pct_change": 0}
    result = {
        "NIFTY 50": fallback,
        "SENSEX": fallback,
        "NIFTY SMALLCAP 100": fallback
    }
    if not _obj:
        return result

    try:
        # Batch request for Nifty 50, Sensex, and Smallcap 100 in a single network call
        exchange_tokens = {
            "NSE": ["26000", "99926032"],
            "BSE": ["99919000"]
        }
        res = _obj.getMarketData("FULL", exchange_tokens)
        if res and res.get('status') and res.get('data') and res['data'].get('fetched'):
            for item in res['data']['fetched']:
                token = item.get('symbolToken') or item.get('token')
                cmp = item.get('ltp', 0.0)
                close = item.get('close', 0.0)
                pct_change = ((cmp - close) / close * 100) if close != 0 else 0.0
                
                parsed_data = {"cmp": cmp, "pct_change": pct_change}
                
                if token == "26000":
                    result["NIFTY 50"] = parsed_data
                elif token == "99919000":
                    result["SENSEX"] = parsed_data
                elif token == "99926032":
                    result["NIFTY SMALLCAP 100"] = parsed_data
    except Exception as e:
        print(f"Error fetching batch index data: {e}")
        
    return result

indices_data = get_cached_index_data(client)

# --- Total Companies Metric ---
try:
    drive_service = backend_helper.get_drive_service()
    folder_id = st.secrets["google_drive"]["folder_id"]
    reports_df = backend_helper.load_csv_database(drive_service, folder_id, 'reports_db.csv')
    total_companies = len(reports_df) if not reports_df.empty else 0
except Exception:
    total_companies = 0
    reports_df = pd.DataFrame()
    drive_service = None
    folder_id = None

@st.dialog("📤 Upload New Research", width="large")
def show_upload_dialog(client, drive_service, folder_id):
    # We render the form elements with keys linked to st.session_state.form_version
    companies_df = backend_helper.get_unified_company_list()
    company_display_list = []
    if not companies_df.empty:
        companies_df['display_name'] = (
            companies_df['company_name'] + " (Ticker: " + companies_df['ticker'] + " | " + companies_df['exchange'] + ")"
        )
        company_display_list = companies_df['display_name'].tolist()

    # Handle form version changes to reset searchable selector
    if "last_form_version" not in st.session_state:
        st.session_state.last_form_version = st.session_state.form_version

    if st.session_state.last_form_version != st.session_state.form_version:
        st.session_state.last_form_version = st.session_state.form_version
        st.session_state.company_search_selector = "-- Select a Company --"

    def handle_company_selection():
        selected = st.session_state.company_search_selector
        fv = st.session_state.form_version
        if selected and selected != "-- Select a Company --":
            row = companies_df[companies_df['display_name'] == selected]
            if not row.empty:
                item = row.iloc[0]
                st.session_state[f"upload_company_name_{fv}"] = item['company_name']
                st.session_state[f"upload_ticker_{fv}"] = item['ticker']
                st.session_state[f"upload_exchange_{fv}"] = item['exchange']
                
                # Fetch real-time price, market cap, and industry metadata
                with st.spinner("Fetching live market and industry data..."):
                    if client:
                        token = item['token']
                        exch = item['exchange']
                        live_data = backend_helper.get_live_market_data(client, token, exch)
                        if live_data:
                            st.session_state[f"upload_price_{fv}"] = float(live_data['cmp'])
                            st.session_state[f"upload_market_cap_{fv}"] = float(live_data['market_cap_cr'])
                        else:
                            st.session_state[f"upload_price_{fv}"] = 0.0
                            st.session_state[f"upload_market_cap_{fv}"] = 0.0
                    
                    # Fetch industry from Screener
                    try:
                        _, industry_val = backend_helper.fetch_industry_metadata(item['ticker'])
                        st.session_state[f"upload_industry_{fv}"] = industry_val if industry_val else ""
                    except Exception:
                        st.session_state[f"upload_industry_{fv}"] = ""
        else:
            st.session_state[f"upload_company_name_{fv}"] = ""
            st.session_state[f"upload_ticker_{fv}"] = ""
            st.session_state[f"upload_exchange_{fv}"] = "NSE"
            st.session_state[f"upload_price_{fv}"] = 0.0
            st.session_state[f"upload_market_cap_{fv}"] = 0.0
            st.session_state[f"upload_industry_{fv}"] = ""

    st.selectbox(
        "🔍 Search and Select Company to Auto-Fill Form (Optional):",
        options=["-- Select a Company --"] + company_display_list,
        key="company_search_selector",
        on_change=handle_company_selection
    )

    with st.form("upload_research_form"):
        col_a, col_b = st.columns(2)

        with col_a:
            analyst_name = st.text_input(
                "Analyst Name",
                value=st.session_state.get('user_name', 'Analyst')
            )
            company_name = st.text_input("Company Name", key=f"upload_company_name_{st.session_state.form_version}")
            ticker = st.text_input("Ticker Symbol (e.g., RELIANCE)", key=f"upload_ticker_{st.session_state.form_version}")
            exchange = st.selectbox("Exchange", ["NSE", "BSE"], key=f"upload_exchange_{st.session_state.form_version}")
            price_during_research = st.number_input("Price during research (₹)", min_value=0.0, format="%.2f", key=f"upload_price_{st.session_state.form_version}")
            market_cap_research = st.number_input("Market Cap during research (₹ Cr)", min_value=0.0, format="%.2f", key=f"upload_market_cap_{st.session_state.form_version}")

        with col_b:
            industry = st.text_input("Industry / Sector", key=f"upload_industry_{st.session_state.form_version}")
            research_type = st.selectbox("Research Type", ["Fundamental only", "Technical only", "Both"])
            latest_qtr = st.text_input("Latest Qtr Result available (e.g., Q4 FY24)", key=f"upload_qtr_{st.session_state.form_version}")
            import pytz
            ist_today = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).date()
            date_submission = st.date_input("Date of submission", ist_today)
            rating = st.slider("Rating by Owner (1-10 Stars)", 1, 10, 5)
            comment_by_owner = st.text_area("Comment by Owner", key=f"upload_comment_{st.session_state.form_version}")

        uploaded_file = st.file_uploader(
            "📎 Upload Research File (PDF, PPTX, DOCX, XLSX...)",
            key=f"file_uploader_{st.session_state.form_version}"
        )

        submit_upload = st.form_submit_button("Submit Research & Sync to Drive", type="primary")

        if submit_upload:
            if company_name and ticker and uploaded_file:
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
                            
                            # Increment form version to clear all fields cleanly
                            st.session_state.form_version += 1
                            backend_helper.load_csv_database.clear()
                            backend_helper.load_real_companies_db.clear()
                            st.rerun()
                        else:
                            st.error("❌ Metadata saved but failed to sync to Google Drive.")

                    except Exception as e:
                        status_placeholder.empty()
                        st.error(f"❌ Error: {e}")
            else:
                st.error("Please fill in all fields (Company Name, Ticker) and upload a research file.")


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
    with st.container(border=True):
        st.markdown(
            "<p style='font-size: 0.8rem; text-transform: uppercase; color: var(--text-secondary); font-weight: 600; margin: 0 0 10px 0; text-align: center;'>Quick Actions</p>", 
            unsafe_allow_html=True
        )
        if st.button(f"📁 Total Companies Uploaded - ({total_companies})", use_container_width=True, type="primary", key="btn_total_cos_list"):
            st.switch_page("pages/list_companies.py")
        if st.button("📤 Submit Research Form", use_container_width=True, key="btn_open_upload_dialog"):
            show_upload_dialog(client, drive_service, folder_id)

st.divider()

# --- Initialize Form Session States ---
if "expand_upload_form" not in st.session_state:
    st.session_state.expand_upload_form = False

# --- Initialize Form Version counter ---
if "form_version" not in st.session_state:
    st.session_state.form_version = 0

# --- Search Section ---
st.subheader("🔍 Search Tracked Companies")

db_df = reports_df

if not db_df.empty:
    # Create display list: "Company Name (Ticker)"
    display_options = (db_df['Company Name'] + " (" + db_df['Ticker'] + ")").tolist()
    
    # Callback for selection change to instantly view profile
    def redirect_to_profile():
        selected = st.session_state.get("dashboard_search_select")
        if selected and selected != "-- Select a Company --":
            selected_ticker = selected.split("(")[-1].replace(")", "").strip()
            matching_rows = db_df[db_df['Ticker'] == selected_ticker]
            if not matching_rows.empty:
                selected_row = matching_rows.iloc[0]
                st.session_state.selected_ticker = selected_row['Ticker']
                st.session_state.selected_company  = selected_row['Company Name']
                st.session_state.selected_exchange = selected_row.get('Exchange', 'NSE')
                st.session_state.selected_file_id  = selected_row.get('File ID', '')
                st.session_state.selected_file_link = selected_row.get('File Link', '')
                st.session_state.selected_price_added = selected_row.get('Price When Added', 0)
                st.session_state.selected_mc_added    = selected_row.get('Market Cap when added', 0)
                # Reset the dropdown value for the next time dashboard is loaded
                st.session_state.dashboard_search_select = "-- Select a Company --"
                st.switch_page("pages/company_profile.py")

    st.selectbox(
        "Select a company from the list:",
        options=["-- Select a Company --"] + display_options,
        key="dashboard_search_select",
        on_change=redirect_to_profile
    )
else:
    st.info("No tracked companies in the database.")

# End of Dashboard file
