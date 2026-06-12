import streamlit as st
import pandas as pd
import datetime
import backend_helper
import utils
from streamlit_autorefresh import st_autorefresh
import pytz

# Inject premium CSS styling
utils.inject_custom_css(st.session_state.get("app_theme", "Dark"))

# Initialize local comments list in session state
if "local_comments" not in st.session_state:
    st.session_state.local_comments = []
if "deleted_comments" not in st.session_state:
    st.session_state.deleted_comments = []

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
        token = backend_helper.get_cached_token_id(ticker, exchange)
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

# --- Deep-dive Stats (Custom Premium Cards with Perfect Alignment) ---
st.markdown(
    """
    <style>
    .metric-card {
        background: rgba(17, 24, 39, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 130px;
        box-sizing: border-box;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: rgba(139, 92, 246, 0.4);
        box-shadow: 0 4px 20px rgba(139, 92, 246, 0.15);
        background: rgba(17, 24, 39, 0.6);
        transform: translateY(-2px);
    }
    .metric-title {
        font-size: 0.75rem;
        color: rgba(249, 250, 251, 0.6);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin: 0;
    }
    .metric-value {
        font-size: 1.25rem;
        font-weight: 700;
        color: #ffffff;
        margin: 8px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.2;
    }
    .metric-delta {
        font-size: 0.72rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 8px;
        border-radius: 6px;
        width: fit-content;
        margin-top: auto;
    }
    .delta-positive {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
    }
    .delta-negative {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
    }
    .delta-neutral {
        background: rgba(255, 255, 255, 0.06);
        color: rgba(249, 250, 251, 0.7);
    }
    </style>
    """,
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

# Card 1: CMP (Real-time)
cmp_delta_class = "delta-positive" if pct_change >= 0 else "delta-negative"
cmp_arrow = "▲" if pct_change >= 0 else "▼"
cmp_delta_text = f"{cmp_arrow} {abs(pct_change):.2f}% / ₹{abs(rs_change):,.2f}"

card_cmp_html = f"""
<div class="metric-card">
    <div class="metric-title">CMP (Real-time)</div>
    <div class="metric-value">₹{cmp:,.2f}</div>
    <div class="metric-delta {cmp_delta_class}">{cmp_delta_text}</div>
</div>
"""

# Card 2: Real-time Market Cap
card_mcap_html = f"""
<div class="metric-card">
    <div class="metric-title">Real-time Market Cap</div>
    <div class="metric-value">₹{market_cap:,.2f} Cr</div>
    <div class="metric-delta delta-neutral">📊 Live Cap</div>
</div>
"""

# Card 3: Price When Added
added_delta_class = "delta-positive" if pct_change_since >= 0 else "delta-negative"
added_arrow = "▲" if pct_change_since >= 0 else "▼"
added_delta_text = f"{added_arrow} {abs(pct_change_since):.2f}% since added"

card_added_html = f"""
<div class="metric-card">
    <div class="metric-title">Price When Added</div>
    <div class="metric-value">₹{price_when_added:,.2f}</div>
    <div class="metric-delta {added_delta_class}">{added_delta_text}</div>
</div>
"""

# Card 4: 52-Week Range
try:
    range_val = f"₹{float(low_52):,.2f} - ₹{float(high_52):,.2f}"
except Exception:
    range_val = f"₹{low_52} - ₹{high_52}"

card_range_html = f"""
<div class="metric-card">
    <div class="metric-title">52-Week Range</div>
    <div class="metric-value" style="font-size: 1.12rem; white-space: normal;">{range_val}</div>
    <div class="metric-delta delta-neutral">📅 52-W Range</div>
</div>
"""

with col1:
    st.markdown(card_cmp_html, unsafe_allow_html=True)
with col2:
    st.markdown(card_mcap_html, unsafe_allow_html=True)
with col3:
    st.markdown(card_added_html, unsafe_allow_html=True)
with col4:
    st.markdown(card_range_html, unsafe_allow_html=True)

st.divider()

# --- About Company & File ---
st.subheader("ℹ️ About Company")

analyst_name = selected_row.get("Analyst", "Unknown")

col_a1, col_a2 = st.columns(2)
with col_a1:
    st.info(f"{company_name} is currently being tracked by the Equity Research Team.")
with col_a2:
    with st.container(border=True):
        st.markdown(f"🧑‍💻 **Research Uploaded By:** **{analyst_name}**")
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

def handle_post_comment(service, fid):
    new_comment = st.session_state.get("new_comment_text", "").strip()
    new_rating = st.session_state.get("new_comment_rating", 10)
    
    if not new_comment:
        return
        
    if service and fid:
        username = st.session_state.get("user_email", "user@firm.com").split('@')[0]
        new_row = {
            "Ticker": ticker,
            "User": username,
            "Avatar": "",
            "Timestamp": datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S"),
            "Rating": new_rating,
            "Text": new_comment
        }
        
        st.session_state.local_comments.append(new_row)
        
        df = backend_helper.load_comments_database(service, fid)
        import pandas as pd
        if df.empty:
            full_comments_df = pd.DataFrame([new_row])
        else:
            full_comments_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
        import threading
        
        def save_comments_async(s, d, f):
            backend_helper.save_comments_database(s, d, f)
            backend_helper.load_csv_database.clear()
            
        upload_thread = threading.Thread(
            target=save_comments_async,
            args=(service, full_comments_df, fid)
        )
        upload_thread.daemon = True
        upload_thread.start()
        
        # Clear inputs in session state before widget rendering to avoid StreamlitAPIException
        st.session_state.new_comment_text = ""
        st.session_state.new_comment_rating = 10
        st.session_state.comment_success_message = "Comment posted!"

try:
    drive_service = backend_helper.get_drive_service()
    folder_id = st.secrets["google_drive"]["folder_id"]
    comments_df = backend_helper.load_comments_database(drive_service, folder_id)
except Exception as e:
    comments_df = pd.DataFrame()

# Filter out deleted comments in session state from comments_df
if "deleted_comments" in st.session_state and not comments_df.empty:
    for dc in st.session_state.deleted_comments:
        comments_df = comments_df[~(
            (comments_df['Ticker'] == dc.get('Ticker')) &
            (comments_df['User'] == dc.get('User')) &
            (comments_df['Timestamp'] == dc.get('Timestamp')) &
            (comments_df['Text'] == dc.get('Text'))
        )]

# Filter comments for this ticker
if not comments_df.empty and 'Ticker' in comments_df.columns:
    ticker_comments = comments_df[comments_df['Ticker'] == ticker]
else:
    ticker_comments = pd.DataFrame()

# Append temporary local comments for this ticker and remove duplicates
if st.session_state.local_comments:
    local_ticker = [c for c in st.session_state.local_comments if c.get('Ticker') == ticker]
    if local_ticker:
        local_df = pd.DataFrame(local_ticker)
        if ticker_comments.empty:
            ticker_comments = local_df
        else:
            ticker_comments = pd.concat([ticker_comments, local_df], ignore_index=True)
            ticker_comments = ticker_comments.drop_duplicates(subset=['Ticker', 'User', 'Timestamp', 'Text'])

def get_initials(name_or_username):
    name_str = str(name_or_username).replace('.', ' ').replace('_', ' ').replace('-', ' ').strip()
    parts = name_str.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    elif len(parts) == 1 and len(parts[0]) > 0:
        import re
        camel_parts = re.findall('[A-Z][^A-Z]*', parts[0])
        if len(camel_parts) >= 2:
            return (camel_parts[0][0] + camel_parts[-1][0]).upper()
        return parts[0][:2].upper()
    return "U"

def get_avatar_color(name):
    colors = [
        "#3b82f6", # Blue
        "#8b5cf6", # Purple
        "#ec4899", # Pink
        "#10b981", # Emerald
        "#f59e0b", # Amber
        "#ef4444", # Red
        "#14b8a6", # Teal
        "#6366f1"  # Indigo
    ]
    hash_val = sum(ord(c) for c in str(name))
    return colors[hash_val % len(colors)]

def get_user_display_info(username, users_df=None):
    if users_df is not None and not users_df.empty:
        try:
            matching_user = users_df[users_df['Email'].str.startswith(username + '@', na=False)]
            if not matching_user.empty:
                full_name = matching_user.iloc[0]['Name']
                clean_name = full_name.replace(" (Admin)", "")
                return clean_name, get_initials(clean_name), get_avatar_color(clean_name)
        except Exception:
            pass
    else:
        try:
            import auth_manager
            df = auth_manager.get_users_df()
            matching_user = df[df['Email'].str.startswith(username + '@', na=False)]
            if not matching_user.empty:
                full_name = matching_user.iloc[0]['Name']
                clean_name = full_name.replace(" (Admin)", "")
                return clean_name, get_initials(clean_name), get_avatar_color(clean_name)
        except Exception:
            pass
    
    clean_username = username.replace('.', ' ').title()
    return clean_username, get_initials(clean_username), get_avatar_color(clean_username)

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
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    color: white;
    font-size: 0.95rem;
    font-family: 'Calibri', 'Calibri', sans-serif;
    flex-shrink: 0;
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
    font-family: 'Calibri', sans-serif;
}
</style>
"""

st.markdown(dark_mode_compatible_css, unsafe_allow_html=True)

if ticker_comments.empty:
    st.write("No comments yet. Be the first to share your thoughts!")
else:
    # Load users database once to avoid reloading it inside the comments loop
    try:
        import auth_manager
        users_df = auth_manager.get_users_df()
    except Exception:
        users_df = None

    for idx_row, comment in ticker_comments.iterrows():
        user_name, initials, avatar_color = get_user_display_info(comment.get('User', 'analyst'), users_df)
        rating = int(comment.get('Rating', 10))
        stars_str = "★" * rating + "☆" * (10 - rating)
        html = f"""
        <div class="comment-box" style="margin-bottom: 0px;">
            <div class="comment-avatar" style="background-color: {avatar_color};">{initials}</div>
            <div style="flex-grow: 1;">
                <div class="comment-header">
                    <span class="comment-user">{user_name} (@{comment.get('User', 'analyst')})</span>
                    <span class="comment-time">{comment.get('Timestamp', '')}</span>
                </div>
                <div class="comment-stars">{stars_str}</div>
                <div class="comment-text">{comment.get('Text', '')}</div>
            </div>
        </div>
        """
        
        # Check if current user is an admin to display the delete button
        is_user_admin = st.session_state.get("is_admin", False)
        
        if is_user_admin:
            col_c1, col_c2 = st.columns([12, 1])
            with col_c1:
                st.markdown(html, unsafe_allow_html=True)
            with col_c2:
                st.write("")
                st.write("")
                if st.button("🗑️", key=f"del_comment_{idx_row}", help=f"Delete comment by {user_name}"):
                    # Filter out this comment from local session state comments if present
                    if "local_comments" in st.session_state:
                        st.session_state.local_comments = [
                            c for c in st.session_state.local_comments
                            if not (c['Ticker'] == ticker and c['User'] == comment.get('User') and c['Timestamp'] == comment.get('Timestamp') and c['Text'] == comment.get('Text'))
                        ]

                    # Add to session state deleted_comments to filter out instantly on rerun
                    st.session_state.deleted_comments.append({
                        "Ticker": ticker,
                        "User": comment.get('User'),
                        "Timestamp": comment.get('Timestamp'),
                        "Text": comment.get('Text')
                    })

                    # Filter out this comment from comments database
                    comments_df = comments_df[~(
                        (comments_df['Ticker'] == ticker) &
                        (comments_df['User'] == comment.get('User')) &
                        (comments_df['Timestamp'] == comment.get('Timestamp')) &
                        (comments_df['Text'] == comment.get('Text'))
                    )]
                    
                    if drive_service and folder_id:
                        import threading
                        
                        def delete_comments_async(service, df, fid):
                            backend_helper.save_comments_database(service, df, fid)
                            backend_helper.load_csv_database.clear()
                            
                        upload_thread = threading.Thread(
                            target=delete_comments_async,
                            args=(drive_service, comments_df, folder_id)
                        )
                        upload_thread.daemon = True
                        upload_thread.start()
                        
                        st.success("Comment deleted!")
                        st.rerun()
                    else:
                        st.error("Google Drive not configured.")
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        else:
            st.markdown(html, unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# --- Add New Comment ---
st.write("---")
st.markdown("**Add your insight**")
new_rating = st.slider("Rating (1-10 Stars)", 1, 10, 10, key="new_comment_rating")
new_comment = st.text_input("Write a comment...", placeholder="What are your thoughts on this company?", key="new_comment_text")
st.button("Post Comment", type="primary", on_click=handle_post_comment, args=(drive_service, folder_id))

if st.session_state.get("comment_success_message"):
    st.success(st.session_state.comment_success_message)
    st.session_state.comment_success_message = ""

# Auto-refresh every 5 minutes (300,000 ms) in the background
st_autorefresh(interval=300_000, key="company_profile_autorefresh")
