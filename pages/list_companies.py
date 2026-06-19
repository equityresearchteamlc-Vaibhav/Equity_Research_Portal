import streamlit as st
import pandas as pd
import backend_helper
import utils
from streamlit_autorefresh import st_autorefresh

# Inject premium CSS styling
utils.inject_custom_css(st.session_state.get("app_theme", "Dark"))

# Display Lingual logo in top right corner
utils.render_lingual_logo(position="top-right", show_tagline=False)

# Modern page header
utils.render_page_header(
    "Uploaded Companies",
    "Track and analyze your research portfolio",
    "🏢"
)

# Market status + refresh bar
utils.render_status_bar(refresh_interval_secs=300)

# Expire override if older than 15 seconds
if 'override_reports_df' in st.session_state:
    import time
    if time.time() - st.session_state.get('override_reports_df_time', 0) > 15:
        st.session_state.pop('override_reports_df', None)
        st.session_state.pop('override_reports_df_time', None)

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

# Load and optimize dataframe
if 'override_reports_df' in st.session_state:
    df = backend_helper.load_real_companies_db_raw(st.session_state['override_reports_df'])
else:
    df = backend_helper.load_real_companies_db()

if not df.empty:
    df = utils.optimize_dataframe(df)

if df.empty:
    st.info("No companies have been uploaded yet. Go to the Dashboard to upload one!")
else:
    # --- Filter Section ---
    st.markdown("### 🏆 Filter & Rank Portfolio")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        sort_option = st.selectbox(
            "Sort Portfolio By:",
            options=[
                "Highest Return Since Added",
                "Lowest Return Since Added",
                "Highest Rating",
                "Most Recent Submissions",
                "Highest Real-time Market Cap"
            ]
        )
        
    with col_f2:
        min_rating = st.slider("Min Rating (Stars)", 1, 10, 1)
        
    with col_f3:
        analyst_options = ["All Analysts"] + sorted(df["Uploaded By"].unique().tolist())
        selected_analyst = st.selectbox("Filter by Analyst:", analyst_options)

    # Apply filters
    filtered_df = df.copy()
    
    # 1. Filter by Analyst
    if selected_analyst != "All Analysts":
        filtered_df = filtered_df[filtered_df["Uploaded By"] == selected_analyst]
        
    # 2. Filter by Rating
    filtered_df = filtered_df[filtered_df["Rating_Num"] >= min_rating]
    
    # 3. Apply Sorting
    if sort_option == "Highest Return Since Added":
        filtered_df = filtered_df.sort_values(by="% Change since added", ascending=False)
    elif sort_option == "Lowest Return Since Added":
        filtered_df = filtered_df.sort_values(by="% Change since added", ascending=True)
    elif sort_option == "Highest Rating":
        filtered_df = filtered_df.sort_values(by="Rating_Num", ascending=False)
    elif sort_option == "Most Recent Submissions":
        filtered_df = filtered_df.sort_values(by="Date Added", ascending=False)
    elif sort_option == "Highest Real-time Market Cap":
        filtered_df = filtered_df.sort_values(by="Real-time Market Cap (Cr)", ascending=False)

    # 4. Target Achieved Indicator
    if 'Target Status' in filtered_df.columns:
        filtered_df['Target Achieved'] = filtered_df['Target Status']
    else:
        filtered_df['Target Achieved'] = "⏳ Pending"

    # Calculate how many times target achieved
    target_achieved_count = len(filtered_df[filtered_df['Target Achieved'] == "✅ Achieved"])
    st.markdown(f"**🎯 Total Targets Achieved:** {target_achieved_count}")

    # Select and order columns
    cols_to_keep = [
        "Company Name", "Rating", "Industry", "Date Added", 
        "Price When Added", "CMP (Real-time)", "% Change since added", 
        "Today's % Change", "Market Cap when added (Cr)", "Real-time Market Cap (Cr)",
        "Target Price", "Target Achieved %", "Target End Date", "Target Achieved", "Uploaded By"
    ]
    # Ensure columns exist before filtering
    available_cols = [c for c in cols_to_keep if c in filtered_df.columns]
    
    # Add Ticker to available_cols so we can identify the clicked row
    if "Ticker" not in available_cols and "Ticker" in filtered_df.columns:
        available_cols.append("Ticker")
        
    display_df = filtered_df[available_cols].copy()

    try:
        event = st.dataframe(
            display_df,
            use_container_width=True,
            selection_mode="single-row",
            on_select="rerun",
            column_config={
                "Ticker": None, # Hide Ticker column from view
                "Price When Added":            st.column_config.NumberColumn(format="₹%.2f"),
                "CMP (Real-time)":             st.column_config.NumberColumn(format="₹%.2f"),
                "% Change since added":        st.column_config.NumberColumn(format="%.2f%%"),
                "Today's % Change":            st.column_config.NumberColumn(format="%.2f%%"),
                "Market Cap when added (Cr)":  st.column_config.NumberColumn(format="₹%.2f Cr"),
                "Real-time Market Cap (Cr)":   st.column_config.NumberColumn(format="₹%.2f Cr"),
                "Target Price":                st.column_config.NumberColumn(format="₹%.2f"),
                "Target Achieved %":            st.column_config.NumberColumn(format="%.2f%%"),
            },
            hide_index=True
        )
        
        if event and hasattr(event, 'selection') and event.selection.rows:
            row_idx = event.selection.rows[0]
            selected_ticker = display_df.iloc[row_idx]['Ticker']
            st.session_state.selected_ticker = selected_ticker
            selected_row = df[df['Ticker'] == selected_ticker].iloc[0]
            st.session_state.selected_company  = selected_row['Company Name']
            st.session_state.selected_exchange = selected_row.get('Exchange', 'NSE')
            st.session_state.selected_file_id  = selected_row.get('File ID', '')
            st.session_state.selected_file_link = selected_row.get('File Link', '')
            st.session_state.selected_price_added = selected_row.get('Price When Added', 0)
            st.session_state.selected_mc_added    = selected_row.get('Market Cap when added (Cr)', 0)
            st.switch_page("pages/company_profile.py")
            
    except Exception:
        # Fallback for older Streamlit versions that don't support on_select
        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "Ticker": None,
                "Price When Added":            st.column_config.NumberColumn(format="₹%.2f"),
                "CMP (Real-time)":             st.column_config.NumberColumn(format="₹%.2f"),
                "% Change since added":        st.column_config.NumberColumn(format="%.2f%%"),
                "Today's % Change":            st.column_config.NumberColumn(format="%.2f%%"),
                "Market Cap when added (Cr)":  st.column_config.NumberColumn(format="₹%.2f Cr"),
                "Real-time Market Cap (Cr)":   st.column_config.NumberColumn(format="₹%.2f Cr"),
                "Target Price":                st.column_config.NumberColumn(format="₹%.2f"),
                "Target Achieved %":            st.column_config.NumberColumn(format="%.2f%%"),
            },
            hide_index=True
        )

    st.divider()

    st.subheader("Quick Actions")
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_ticker = st.selectbox("Select a company to view in detail:", df['Ticker'].tolist())
    with col2:
        st.write("")
        st.write("")
        if st.button("👁️ View Profile", use_container_width=True, type="primary"):
            st.session_state.selected_ticker = selected_ticker
            selected_row = df[df['Ticker'] == selected_ticker].iloc[0]
            st.session_state.selected_company  = selected_row['Company Name']
            st.session_state.selected_exchange = selected_row.get('Exchange', 'NSE')
            st.session_state.selected_file_id  = selected_row.get('File ID', '')
            st.session_state.selected_file_link = selected_row.get('File Link', '')
            st.session_state.selected_price_added = selected_row.get('Price When Added', 0)
            st.session_state.selected_mc_added    = selected_row.get('Market Cap when added (Cr)', 0)
            st.switch_page("pages/company_profile.py")

# Auto-refresh every 5 minutes (300,000 ms) in the background
st_autorefresh(interval=300_000, key="list_companies_autorefresh")
