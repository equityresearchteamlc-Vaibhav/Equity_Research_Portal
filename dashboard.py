import streamlit as st
import pandas as pd
import datetime
import io
import backend_helper
import utils

if hasattr(st, "fragment"):
    fragment = st.fragment
elif hasattr(st, "experimental_fragment"):
    fragment = st.experimental_fragment
else:
    fragment = lambda func: func


# Initialize form_version and upload_dialog_open at page level to avoid AttributeError in callbacks
if "form_version" not in st.session_state:
    st.session_state.form_version = 0

if "upload_dialog_open" not in st.session_state:
    st.session_state.upload_dialog_open = False

# Inject premium CSS styling
utils.inject_custom_css(st.session_state.get("app_theme", "Dark"))

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
    st.session_state.pop("upload_success_message", None)


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
except Exception as e:
    st.error(f"⚠️ Angel One Connection Failed: {e}")
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

# Global fetch removed; will fetch inside fragment
# --- Total Companies Metric ---
try:
    drive_service = backend_helper.get_drive_service()
    folder_id = st.secrets["google_drive"]["folder_id"]
except Exception as e:
    drive_service = None
    folder_id = None
    if "drive_error" not in st.session_state:
        import traceback
        st.session_state["drive_error"] = f"{str(e)}\n{traceback.format_exc()}"

if not drive_service or not folder_id:
    details = st.session_state.get("drive_error", "Unknown initialization error.")
    st.error(f"Google Drive is not configured properly in st.secrets.\n\n**Error Details:**\n```\n{details}\n```")
    st.stop()

try:
    # Expire override if older than 15 seconds
    if 'override_reports_df' in st.session_state:
        import time
        if time.time() - st.session_state.get('override_reports_df_time', 0) > 15:
            st.session_state.pop('override_reports_df', None)
            st.session_state.pop('override_reports_df_time', None)
            
    if 'override_reports_df' in st.session_state:
        reports_df = st.session_state['override_reports_df']
    else:
        reports_df = backend_helper.load_csv_database(drive_service, folder_id, 'reports_db.csv')
        
    total_companies = len(reports_df) if not reports_df.empty else 0
except Exception as e:
    total_companies = 0
    reports_df = pd.DataFrame()

def reset_dialog_state():
    st.session_state.upload_dialog_open = False

@st.dialog("📤 Upload New Research", width="large", on_dismiss=reset_dialog_state)
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
    if "form_version" not in st.session_state:
        st.session_state.form_version = 0

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
                        _, industry_val, screener_mc = backend_helper.fetch_industry_metadata(item['ticker'])
                        st.session_state[f"upload_industry_{fv}"] = industry_val if industry_val else ""
                        if st.session_state[f"upload_market_cap_{fv}"] == 0.0 and screener_mc > 0:
                            st.session_state[f"upload_market_cap_{fv}"] = screener_mc
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
            target_price = st.number_input("Target Price (₹)", min_value=0.0, format="%.2f")
            target_timeframe = st.selectbox("Target Timeframe (Months)", options=[3, 6, 12, 18, 24, 36], index=2)

        with col_b:
            latest_qtr = st.text_input("Latest Qtr Result available (e.g., Q4 FY24)", key=f"upload_qtr_{st.session_state.form_version}")
            import pytz
            ist_today = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).date()
            date_research = st.date_input("Date of research", ist_today)
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
                    details = st.session_state.get("drive_error", "Unknown initialization error.")
                    st.error(f"Google Drive is not configured properly in st.secrets.\n\n**Error Details:**\n```\n{details}\n```")
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

                        # --- Logic for fetching missing data ---
                        final_exchange = st.session_state.get(f"upload_exchange_{st.session_state.form_version}", "NSE")
                        final_industry = st.session_state.get(f"upload_industry_{st.session_state.form_version}", "")
                        pre_filled_mc = st.session_state.get(f"upload_market_cap_{st.session_state.form_version}", 0.0)
                        
                        _, screener_ind, screener_mc = backend_helper.fetch_industry_metadata(ticker)
                        if not final_industry:
                            final_industry = screener_ind
                            
                        # Fetch historical price based on date_research
                        hist_price = backend_helper.get_historical_price(ticker, final_exchange, date_research)
                        
                        live_cmp = 0.0
                        live_mc = 0.0
                        
                        if client:
                            tk = backend_helper.get_cached_token_id(ticker, final_exchange)
                            if tk:
                                ld = backend_helper.get_live_market_data(client, tk, final_exchange)
                                if ld:
                                    live_cmp = ld.get('cmp', 0.0)
                                    live_mc = ld.get('market_cap_cr', 0.0)
                        
                        # Determine actual market cap to save
                        if live_mc == 0.0:
                            if pre_filled_mc > 0:
                                live_mc = pre_filled_mc
                            elif screener_mc > 0:
                                live_mc = screener_mc
                        
                        if hist_price == 0.0:
                            hist_price = live_cmp
                            
                        # Estimate historical market cap
                        if live_mc > 0 and live_cmp > 0:
                            hist_mc = live_mc * (hist_price / live_cmp)
                        else:
                            hist_mc = live_mc

                        new_data = {
                            "Company Name": company_name,
                            "Ticker": ticker.upper().strip(),
                            "Exchange": final_exchange,
                            "Date Added": str(date_research),
                            "Price When Added": hist_price,
                            "Market Cap when added": hist_mc,
                            "Industry": final_industry,
                            "Target Price": target_price,
                            "Target Timeframe (Months)": target_timeframe,
                            "Latest Qtr": latest_qtr,
                            "Rating": rating,
                            "Analyst": analyst_name,
                            "Comment": comment_by_owner,
                            "File ID": file_id,
                            "File Link": file_link
                        }

                        import threading
                        import time

                        # Threads to clean up pipeline and shortlist in parallel with adding to reports database
                        def clean_pipeline():
                            try:
                                pipe_df = backend_helper.load_pipeline_database(drive_service, folder_id)
                                if not pipe_df.empty and 'Ticker' in pipe_df.columns:
                                    before_len = len(pipe_df)
                                    pipe_df = pipe_df[pipe_df['Ticker'] != ticker.upper().strip()]
                                    if len(pipe_df) < before_len:
                                        backend_helper.save_pipeline_database(drive_service, pipe_df, folder_id)
                            except Exception as e:
                                print(f"Error updating pipeline in background: {e}")

                        def clean_shortlist():
                            try:
                                short_df = backend_helper.load_shortlisted_database(drive_service, folder_id)
                                if not short_df.empty and 'Ticker' in short_df.columns:
                                    before_len = len(short_df)
                                    short_df = short_df[short_df['Ticker'] != ticker.upper().strip()]
                                    if len(short_df) < before_len:
                                        backend_helper.save_shortlisted_database(drive_service, short_df, folder_id)
                            except Exception as e:
                                print(f"Error updating shortlist in background: {e}")

                        reports_status = {"success": False, "df": None}
                        def save_reports():
                            try:
                                df = backend_helper.load_csv_database(drive_service, folder_id, 'reports_db.csv')
                                if df.empty:
                                    updated_df = pd.DataFrame([new_data])
                                else:
                                    updated_df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                                
                                success = backend_helper.save_csv_database(drive_service, updated_df, folder_id, 'reports_db.csv')
                                reports_status["success"] = success
                                reports_status["df"] = updated_df
                            except Exception as e:
                                print(f"Error updating reports in background: {e}")

                        t_pipe = threading.Thread(target=clean_pipeline)
                        t_short = threading.Thread(target=clean_shortlist)
                        t_reports = threading.Thread(target=save_reports)

                        t_pipe.start()
                        t_short.start()
                        t_reports.start()

                        t_pipe.join()
                        t_short.join()
                        t_reports.join()

                        status_placeholder.empty()

                        if reports_status["success"]:
                            st.session_state['override_reports_df'] = reports_status["df"]
                            st.session_state['override_reports_df_time'] = time.time()

                            st.session_state.upload_success_message = f"✅ Research for **{company_name}** saved successfully!"
                            st.session_state.upload_dialog_open = False
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


# --- Real-Time Metric Cards (Indices Only) ---
def render_indices_content():
    indices_data = get_cached_index_data(client)
    col1, col2, col3 = st.columns(3)
    
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

@fragment(run_every=300)
def render_indices_auto():
    render_indices_content()

@fragment
def render_indices_static():
    render_indices_content()

if st.session_state.get("upload_dialog_open", False):
    render_indices_static()
else:
    render_indices_auto()

st.divider()

# --- Search & Quick Actions Section ---
col_search, col_actions = st.columns([2, 1])

with col_search:
    @fragment
    def render_company_search(db_df):
        st.subheader("🔍 Search Tracked Companies")
        db_df = reports_df
        if not db_df.empty:
            # Create display list: "Company Name (Ticker)"
            display_options = (db_df['Company Name'] + " (" + db_df['Ticker'] + ")").tolist()

            # Check selection state and redirect BEFORE rendering the selectbox to avoid StreamlitAPIException
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
                key="dashboard_search_select"
            )
        else:
            st.info("No tracked companies in the database.")


    render_company_search(reports_df)

with col_actions:
    with st.container(border=True):
        st.markdown(
            "<p style='font-size: 0.8rem; text-transform: uppercase; color: var(--text-secondary); font-weight: 600; margin: 0 0 10px 0; text-align: center;'>Quick Actions</p>", 
            unsafe_allow_html=True
        )
        if st.button(f"📁 Total Companies Uploaded - ({total_companies})", use_container_width=True, type="primary", key="btn_total_cos_list"):
            st.switch_page("pages/list_companies.py")
        if st.button("📤 Submit Research Form", use_container_width=True, key="btn_open_upload_dialog"):
            st.session_state.upload_dialog_open = True
            st.rerun()

# If the dialog open flag is True, render the dialog
if st.session_state.get("upload_dialog_open", False):
    show_upload_dialog(client, drive_service, folder_id)

# Auto-refresh removed from global scope to prevent dialog closing
# End of Dashboard file
