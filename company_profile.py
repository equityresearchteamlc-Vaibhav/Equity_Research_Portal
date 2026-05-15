import streamlit as st
import datetime

st.title("🔍 Company Profile")

# Determine which company is selected
ticker = st.session_state.get("selected_ticker", "RELIANCE")
company_name = st.session_state.get("selected_company", "Reliance Industries")

st.header(f"{company_name} ({ticker})")

# --- Deep-dive Stats ---
col1, col2, col3, col4 = st.columns(4)
# Dummy data for demonstration
cmp = 2850.50
pct_change = 1.2
rs_change = cmp * (pct_change / 100)
market_cap = 1900000
price_when_added = 2500
pct_change_since = ((cmp - price_when_added) / price_when_added) * 100
high_52 = 3000
low_52 = 2200

with col1:
    st.metric(label="CMP (Real-time)", value=f"₹{cmp:,.2f}", delta=f"{pct_change}% / ₹{rs_change:.2f}")
with col2:
    st.metric(label="Market Cap", value=f"₹{market_cap:,.2f} Cr")
with col3:
    st.metric(label="Price When Added", value=f"₹{price_when_added:,.2f}", delta=f"{pct_change_since:.2f}% since added", delta_color="normal")
with col4:
    st.metric(label="52-Week Range", value=f"₹{low_52} - ₹{high_52}")

st.divider()

# --- About Company & File ---
st.subheader("ℹ️ About Company")
st.info(f"{company_name} is a leading player in its sector. This section is populated via an external API to provide a brief overview of the company's core business, history, and key operational metrics.")

if st.button("📥 Click here to view uploaded research file", type="primary"):
    st.success("Downloading file from Google Drive... (Mock action)")

st.divider()

# --- Instagram-style Comments Feed ---
st.subheader("💬 Team Discussion")

# Initialize mock comments if not exist
if f"comments_{ticker}" not in st.session_state:
    st.session_state[f"comments_{ticker}"] = [
        {"user": "alex_analyst", "avatar": "https://api.dicebear.com/7.x/adventurer/svg?seed=alex", "timestamp": "2 hours ago", "rating": 4, "text": "Solid fundamentals, but the latest quarter margins were a bit squeezed. Watching closely."},
        {"user": "sam_research", "avatar": "https://api.dicebear.com/7.x/adventurer/svg?seed=sam", "timestamp": "1 day ago", "rating": 5, "text": "Great management commentary. The new capex cycle will definitely drive growth over the next 2-3 years."}
    ]

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

for comment in st.session_state[f"comments_{ticker}"]:
    stars_str = "★" * comment["rating"] + "☆" * (5 - comment["rating"])
    html = f"""
    <div class="comment-box">
        <img src="{comment['avatar']}" class="comment-avatar">
        <div style="flex-grow: 1;">
            <div class="comment-header">
                <span class="comment-user">@{comment['user']}</span>
                <span class="comment-time">{comment['timestamp']}</span>
            </div>
            <div class="comment-stars">{stars_str}</div>
            <div class="comment-text">{comment['text']}</div>
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
        username = st.session_state.get("user_email", "user@firm.com").split('@')[0]
        st.session_state[f"comments_{ticker}"].insert(0, {
            "user": username,
            "avatar": f"https://api.dicebear.com/7.x/adventurer/svg?seed={username}",
            "timestamp": "Just now",
            "rating": new_rating,
            "text": new_comment
        })
        st.rerun()
