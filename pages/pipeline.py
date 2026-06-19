import streamlit as st
import pandas as pd
import datetime
import pytz
import backend_helper
import utils
from streamlit_autorefresh import st_autorefresh
import threading
import time

# Inject premium CSS styling
utils.inject_custom_css(st.session_state.get("app_theme", "Game of Thrones"))

# Display Lingual logo in top right corner
utils.render_lingual_logo(position="top-right", show_tagline=False)

# Modern page header
utils.render_page_header(
    "Pipeline & Shortlist", 
    "Manage prospective companies and nominations",
    "🚀"
)

# Market status + refresh bar
utils.render_status_bar(refresh_interval_secs=300)

# Always clear stale error before attempting reconnection
st.session_state.pop("drive_error", None)
try:
    drive_service = backend_helper.get_drive_service()
    folder_id = st.secrets["google_drive"]["folder_id"]
except Exception as e:
    drive_service = None
    folder_id = None
    import traceback
    st.session_state["drive_error"] = f"{str(e)}\n{traceback.format_exc()}"

if not drive_service or not folder_id:
    details = st.session_state.get("drive_error", "Unknown initialization error.")
    st.error(f"Google Drive is not configured properly in st.secrets.\n\n**Error Details:**\n```\n{details}\n```")
    st.stop()

# Helper for instant background saving
def save_async(df, db_name, override_key):
    # Set the session state override immediately so the UI is instant
    st.session_state[override_key] = df
    st.session_state[f"{override_key}_time"] = time.time()
    
    # Run the Google Drive save in a background thread
    def run_save():
        backend_helper.save_csv_database(drive_service, df, folder_id, db_name=db_name)
    threading.Thread(target=run_save).start()

# Expire old overrides (older than 15 seconds)
current_time = time.time()
for key in ['override_pipeline_df', 'override_shortlisted_df', 'override_comments_df']:
    if key in st.session_state:
        if current_time - st.session_state.get(f"{key}_time", 0) > 15:
            st.session_state.pop(key, None)
            st.session_state.pop(f"{key}_time", None)

# Load pipeline and shortlisted
pipeline_df = backend_helper.load_pipeline_database(drive_service, folder_id)
if 'override_pipeline_df' in st.session_state:
    pipeline_df = st.session_state['override_pipeline_df']

shortlisted_df = backend_helper.load_shortlisted_database(drive_service, folder_id)
if 'override_shortlisted_df' in st.session_state:
    shortlisted_df = st.session_state['override_shortlisted_df']

try:
    angel_secrets = st.secrets["angel_one"]
    client = backend_helper.get_angel_client(
        api_key=angel_secrets["api_key"],
        client_code=angel_secrets["client_code"],
        password=angel_secrets["password"],
        totp_secret=angel_secrets["totp_secret"]
    )
except Exception as e:
    client = None

with st.expander("➕ Add Company to Pipeline", expanded=False):
    # We can use the same company search mechanism using AngelOne / local unified list
    companies_df = backend_helper.get_unified_company_list()
    company_display_list = []
    if not companies_df.empty:
        companies_df['display_name'] = (
            companies_df['company_name'] + " (Ticker: " + companies_df['ticker'] + " | " + companies_df['exchange'] + ")"
        )
        company_display_list = companies_df['display_name'].tolist()

    def handle_pipeline_selection():
        selected = st.session_state.pipeline_search_selector
        if selected and selected != "-- Select a Company --":
            row = companies_df[companies_df['display_name'] == selected]
            if not row.empty:
                item = row.iloc[0]
                st.session_state.pipe_company_name = item['company_name']
                st.session_state.pipe_ticker = item['ticker']
                st.session_state.pipe_exchange = item['exchange']
                
    st.selectbox(
        "🔍 Search Company (AngelOne DB):",
        options=["-- Select a Company --"] + company_display_list,
        key="pipeline_search_selector",
        on_change=handle_pipeline_selection
    )
    
    with st.form("pipeline_add_form"):
        p_comp = st.text_input("Company Name", key="pipe_company_name")
        p_tick = st.text_input("Ticker", key="pipe_ticker")
        p_exch = st.text_input("Exchange (NSE/BSE)", value=st.session_state.get("pipe_exchange", "NSE"))
        p_sugg = st.text_input("Suggested By (Person Name)", value=st.session_state.get("user_name", "Unknown"))
        
        p_submit = st.form_submit_button("Add to Pipeline")
        if p_submit and p_comp and p_tick:
            today_date = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).date()
            
            # Fetch current live data for the token
            p_cmp = 0.0
            p_mc = 0.0
            if client:
                tk = backend_helper.get_cached_token_id(p_tick, p_exch)
                if tk:
                    ld = backend_helper.get_live_market_data(client, tk, p_exch)
                    if ld:
                        p_cmp = ld.get('cmp', 0.0)
                        p_mc = ld.get('market_cap_cr', 0.0)
            
            new_pipe = {
                "Company Name": p_comp,
                "Ticker": p_tick.upper().strip(),
                "Exchange": p_exch.upper().strip(),
                "Suggested By": p_sugg,
                "Date Added": str(today_date),
                "Price When Added": p_cmp,
                "Market Cap when added": p_mc
            }
            
            if pipeline_df.empty:
                pipeline_df = pd.DataFrame([new_pipe])
            else:
                pipeline_df = pd.concat([pipeline_df, pd.DataFrame([new_pipe])], ignore_index=True)
            
            save_async(pipeline_df, 'pipeline_db.csv', 'override_pipeline_df')
            st.success(f"Added {p_comp} to Pipeline!")
            st.rerun()

st.markdown("### 📋 Current Pipeline")
if pipeline_df.empty:
    st.info("No companies in pipeline.")
else:
    # Fetch live data for pipeline companies to compare
    token_exchange_pairs = []
    token_map = {}
    for _, row in pipeline_df.iterrows():
        t = str(row['Ticker']).upper()
        e = str(row.get('Exchange', 'NSE')).upper()
        tk = backend_helper.get_cached_token_id(t, e)
        if tk:
            token_exchange_pairs.append((tk, e))
            token_map[t] = tk
            
    batch_data = {}
    if client and token_exchange_pairs:
        batch_data = backend_helper.get_live_market_data_batch(client, token_exchange_pairs)
        
    pipe_display = []
    for _, row in pipeline_df.iterrows():
        t = str(row['Ticker']).upper()
        tk = token_map.get(t)
        ld = batch_data.get(tk) if tk else None
        
        p_added = float(row.get("Price When Added", 0))
        if ld:
            live_cmp = ld.get('cmp', 0.0)
            live_mc = ld.get('market_cap_cr', 0.0)
        else:
            live_cmp = p_added
            live_mc = float(row.get("Market Cap when added", 0))
            
        pct_change = ((live_cmp - p_added) / p_added * 100) if p_added > 0 else 0
        
        pipe_display.append({
            "Company": row["Company Name"],
            "Ticker": t,
            "Suggested By": row.get("Suggested By", ""),
            "Date Added": row.get("Date Added", ""),
            "Price When Added": p_added,
            "Live CMP": live_cmp,
            "% Change": pct_change,
            "Live Market Cap (Cr)": live_mc
        })
        
    pipe_df_display = pd.DataFrame(pipe_display)
    
    # Display as table
    st.dataframe(
        pipe_df_display,
        use_container_width=True,
        column_config={
            "Price When Added": st.column_config.NumberColumn(format="₹%.2f"),
            "Live CMP": st.column_config.NumberColumn(format="₹%.2f"),
            "% Change": st.column_config.NumberColumn(format="%.2f%%"),
            "Live Market Cap (Cr)": st.column_config.NumberColumn(format="₹%.2f Cr"),
        },
        hide_index=True
    )
    
    # Actions for pipeline: Nominate or Comment
    st.markdown("#### Actions")
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        sel_pipe_tick = st.selectbox("Select Pipeline Company:", options=pipe_df_display['Ticker'].tolist())
    with action_col2:
        st.write("")
        st.write("")
        if st.button("⭐ Nominate to Shortlisted", type="primary", use_container_width=True):
            # Move to shortlisted
            row_to_move = pipeline_df[pipeline_df['Ticker'] == sel_pipe_tick].iloc[0]
            
            if shortlisted_df.empty:
                shortlisted_df = pd.DataFrame([row_to_move])
            else:
                shortlisted_df = pd.concat([shortlisted_df, pd.DataFrame([row_to_move])], ignore_index=True)
                
            pipeline_df = pipeline_df[pipeline_df['Ticker'] != sel_pipe_tick]
            
            save_async(shortlisted_df, 'shortlisted_db.csv', 'override_shortlisted_df')
            save_async(pipeline_df, 'pipeline_db.csv', 'override_pipeline_df')
            
            st.success(f"{sel_pipe_tick} Nominated and moved to Shortlisted!")
            st.rerun()
            
        if st.session_state.get("is_admin"):
            if st.button("❌ Remove from Pipeline", use_container_width=True):
                pipeline_df = pipeline_df[pipeline_df['Ticker'] != sel_pipe_tick]
                save_async(pipeline_df, 'pipeline_db.csv', 'override_pipeline_df')
                st.success(f"Removed {sel_pipe_tick} from Pipeline!")
                st.rerun()

    with st.expander(f"💬 Comments for {sel_pipe_tick}"):
        if 'override_comments_df' in st.session_state:
            comments_df = st.session_state['override_comments_df']
        elif 'last_comments_df' in st.session_state:
            comments_df = st.session_state['last_comments_df']
        else:
            comments_df = backend_helper.load_comments_database(drive_service, folder_id)
            st.session_state['last_comments_df'] = comments_df
            
        if not comments_df.empty and 'Ticker' in comments_df.columns:
            tick_comments = comments_df[(comments_df['Ticker'] == f"PIPE_{sel_pipe_tick}")]
            for _, c in tick_comments.iterrows():
                st.markdown(f"**{c.get('User', 'Unknown')}** ({c.get('Timestamp', '')}): {c.get('Text', '')}")
        
        with st.form(f"pipe_comment_{sel_pipe_tick}"):
            new_c = st.text_input("Add a comment:")
            if st.form_submit_button("Post Comment") and new_c:
                n_row = {
                    "Ticker": f"PIPE_{sel_pipe_tick}",
                    "User": st.session_state.get("user_email", "user").split('@')[0],
                    "Timestamp": datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S"),
                    "Text": new_c,
                    "Rating": 0, "Avatar": ""
                }
                if comments_df.empty:
                    comments_df = pd.DataFrame([n_row])
                else:
                    comments_df = pd.concat([comments_df, pd.DataFrame([n_row])], ignore_index=True)
                
                st.session_state['last_comments_df'] = comments_df
                save_async(comments_df, 'comments_db.csv', 'override_comments_df')
                st.success("Comment added!")
                st.rerun()

st.markdown("### ⭐ Shortlisted Companies")
if shortlisted_df.empty:
    st.info("No shortlisted companies yet.")
else:
    st.dataframe(shortlisted_df, use_container_width=True, hide_index=True)
    
    if st.session_state.get("is_admin"):
        st.markdown("#### Admin Actions")
        short_col1, short_col2 = st.columns(2)
        with short_col1:
            sel_short_tick = st.selectbox("Select Shortlisted Company:", options=shortlisted_df['Ticker'].tolist())
        with short_col2:
            st.write("")
            st.write("")
            if st.button("❌ Remove from Shortlisted", use_container_width=True):
                shortlisted_df = shortlisted_df[shortlisted_df['Ticker'] != sel_short_tick]
                save_async(shortlisted_df, 'shortlisted_db.csv', 'override_shortlisted_df')
                st.success(f"Removed {sel_short_tick} from Shortlisted!")
                st.rerun()

# Auto-refresh every 5 minutes (300,000 ms) in the background
st_autorefresh(interval=300_000, key="pipeline_autorefresh")
