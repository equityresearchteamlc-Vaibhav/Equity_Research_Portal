import streamlit as st
import pandas as pd
import datetime
import backend_helper
import utils
from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 5 minutes (300,000 ms)
st_autorefresh(interval=300_000, key="company_profile_autorefresh")

# Inject premium CSS styling
utils.inject_custom_css()

# Display Lingual logo in top right corner
utils.render_lingual_logo(position="top-right", show_tagline=False)

# Modern page header
utils.render_page_header(
    "Company Profile",
    "Detailed analysis and real-time data",
    "🔍"
)

# Market status + refresh bar
utils.render_status_bar(refresh_interval_secs=300)

# Load uploaded companies database
try:
    drive_service = backend_helper.get_drive_service()
    folder_id = st.secrets["google_drive"]["folder_id"]
    reports_df = backend_helper.load_csv_database(drive_service, folder_id, 'reports_db.csv')
except Exception as e:
    reports_df = pd.DataFrame()

if reports_df.empty:
    st.info("No companies have been uploaded yet. Go to the Dashboard to upload one!")
    st.stop()

# Create a list of options: "Company Name (Ticker)"
reports_df['Display_Name'] = reports_df['Company Name'] + " (" + reports_df['Ticker'] + ")"

# Determine index of currently selected ticker
current_ticker = st.session_state.get("selected_ticker")
default_index = 0
if current_ticker in reports_df['Ticker'].values:
    default_index = int(reports_df[reports_df['Ticker'] == current_ticker].index[0])

selected_display = st.selectbox(
    "Select a tracked company:",
    options=reports_df['Display_Name'].tolist(),
    index=default_index
)

# Extract row of chosen company
selected_row = reports_df[reports_df['Display_Name'] == selected_display].iloc[0]

ticker = selected_row['Ticker']
company_name = selected_row['Company Name']
exchange = selected_row.get('Exchange', 'NSE')
file_id = selected_row.get('File ID', '')
file_link = selected_row.get('File Link', '')
price_when_added = float(selected_row.get('Price When Added', 0))
mc_added = float(selected_row.get('Market Cap when added', 0))

# Save back to session state
st.session_state.selected_ticker = ticker
st.session_state.selected_company = company_name
st.session_state.selected_exchange = exchange
st.session_state.selected_file_id = file_id
st.session_state.selected_file_link = file_link
st.session_state.selected_price_added = price_when_added
st.session_state.selected_mc_added = mc_added

st.header(f"{company_name} ({ticker})")

# Fetch Real Data
cmp = 0.0
pct_change = 0.0
high_52 = 0.0
low_52 = 0.0

try:
    angel_secrets = st.secrets["angel_one"]
    client = backend_helper.get_angel_client(
        api_key=angel_secrets["api_key"],
        client_code=angel_secrets["client_code"],
        password=angel_secrets["password"],
        totp_secret=angel_secrets["totp_secret"]
    )
    
    if client:
        master_contract = backend_helper.fetch_master_contract()
        token = backend_helper.get_token_id(master_contract, ticker, exchange)
        if token:
            live_data = backend_helper.get_live_market_data(client, token, exchange)
            if live_data:
                cmp = live_data.get('cmp', 0.0)
                pct_change = live_data.get('pct_change', 0.0)
                high_52 = live_data.get('52w_high', 0.0)
                low_52 = live_data.get('52w_low', 0.0)
except Exception as e:
    st.error(f"Could not fetch live data: {e}")

# Calculate Changes
rs_change = cmp * (pct_change / 100) if cmp else 0
pct_change_since = ((cmp - price_when_added) / price_when_added) * 100 if price_when_added > 0 else 0
# Prefer live market cap from API; fall back to proportional estimate
market_cap = live_data.get('market_cap_cr', 0.0) if live_data and live_data.get('market_cap_cr', 0.0) > 0 \
             else (mc_added * (cmp / price_when_added) if price_when_added > 0 else mc_added)

# --- Deep-dive Stats ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="CMP (Real-time)", value=f"₹{cmp:,.2f}", delta=f"{pct_change:.2f}% / ₹{rs_change:.2f}")
with col2:
    st.metric(label="Real-time Market Cap", value=f"₹{market_cap:,.2f} Cr")
with col3:
    st.metric(label="Price When Added", value=f"₹{price_when_added:,.2f}", delta=f"{pct_change_since:.2f}% since added", delta_color="normal")
with col4:
    st.metric(label="52-Week Range", value=f"₹{low_52} - ₹{high_52}")

st.divider()

# --- About Company & File ---
st.subheader("ℹ️ About Company")
st.info(f"{company_name} is currently being tracked by the Equity Research Team.")

if file_link:
    st.markdown(f"📥 **[Click here to open the research file]({file_link})**")
elif file_id:
    # Backward compatibility for old records that used File ID
    old_drive_link = f"https://drive.google.com/uc?export=download&id={file_id}"
    st.markdown(f"📥 **[Click here to download the research file]({old_drive_link})**")
else:
    st.warning("No research file attached to this company.")

# --- Analyst Initial Research Notes ---
st.subheader("💡 Analyst Initial Research Notes")
analyst_name = selected_row.get("Analyst", "Unknown")
owner_rating = selected_row.get("Rating", "")
owner_comment = selected_row.get("Comment", "")

with st.container(border=True):
    st.write(f"🧑‍💻 **Research Submitted By:** {analyst_name}")
    if pd.notna(owner_rating) and str(owner_rating).strip() != "":
        st.write(f"⭐ **Analyst Rating:** **{int(float(owner_rating))}/10**")
    else:
        st.write("⭐ **Analyst Rating:** *Not rated*")
    
    if pd.notna(owner_comment) and str(owner_comment).strip() != "":
        st.write(f"📝 **Analyst Comment:** {owner_comment}")
    else:
        st.write("📝 **Analyst Comment:** *No comment provided*")

st.divider()

# --- Team Discussion (Drive Backed) ---
st.subheader("💬 Team Discussion")

try:
    drive_service = backend_helper.get_drive_service()
    folder_id = st.secrets["google_drive"]["folder_id"]
    comments_df = backend_helper.load_comments_database(drive_service, folder_id)
except Exception as e:
    comments_df = pd.DataFrame()

# Filter comments for this ticker
if not comments_df.empty and 'Ticker' in comments_df.columns:
    ticker_comments = comments_df[comments_df['Ticker'] == ticker]
else:
    ticker_comments = pd.DataFrame()

# Render Comments using HTML/CSS
dark_mode_compatible_css = """
<style>
.comment-box {
    display: flex; 
    margin-bottom: 15px; 
    background-color: var(--secondary-background-color); 
    padding: 15px; 
    border-radius: 10px; 
    border: 1px solid var(--faded-text-40);
}
.comment-avatar {
    width: 40px; 
    height: 40px; 
    border-radius: 50%; 
    margin-right: 15px;
}
.comment-header {
    display: flex; 
    justify-content: space-between; 
    align-items: baseline;
}
.comment-user {
    font-weight: bold; 
    color: var(--text-color);
}
.comment-time {
    font-size: 0.8em; 
    color: var(--faded-text-60);
}
.comment-stars {
    color: #FFD700; 
    font-size: 1.1em; 
    margin-bottom: 5px;
}
.comment-text {
    color: var(--text-color); 
    font-family: sans-serif;
}
</style>
"""

st.markdown(dark_mode_compatible_css, unsafe_allow_html=True)

if ticker_comments.empty:
    st.write("No comments yet. Be the first to share your thoughts!")
else:
    for _, comment in ticker_comments.iterrows():
        rating = int(comment.get('Rating', 5))
        stars_str = "★" * rating + "☆" * (5 - rating)
        html = f"""
        <div class="comment-box">
            <img src="{comment.get('Avatar', 'https://api.dicebear.com/7.x/adventurer/svg?seed=user')}" class="comment-avatar">
            <div style="flex-grow: 1;">
                <div class="comment-header">
                    <span class="comment-user">@{comment.get('User', 'analyst')}</span>
                    <span class="comment-time">{comment.get('Timestamp', '')}</span>
                </div>
                <div class="comment-stars">{stars_str}</div>
                <div class="comment-text">{comment.get('Text', '')}</div>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

# --- Add New Comment ---
st.write("---")
with st.form("new_comment_form", clear_on_submit=True):
    st.markdown("**Add your insight**")
    new_rating = st.slider("Rating", 1, 5, 5)
    new_comment = st.text_input("Write a comment...", placeholder="What are your thoughts on this company?")
    submit_comment = st.form_submit_button("Post Comment")
    
    if submit_comment and new_comment:
        if drive_service and folder_id:
            username = st.session_state.get("user_email", "user@firm.com").split('@')[0]
            new_row = {
                "Ticker": ticker,
                "User": username,
                "Avatar": f"https://api.dicebear.com/7.x/adventurer/svg?seed={username}",
                "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Rating": new_rating,
                "Text": new_comment
            }
            
            import pandas as pd
            if comments_df.empty:
                comments_df = pd.DataFrame([new_row])
            else:
                comments_df = pd.concat([comments_df, pd.DataFrame([new_row])], ignore_index=True)
                
            backend_helper.save_comments_database(drive_service, comments_df, folder_id)
            st.success("Comment posted!")
            st.rerun()
        else:
            st.error("Google Drive not configured.")
