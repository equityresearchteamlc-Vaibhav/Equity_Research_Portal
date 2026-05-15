import streamlit as st
import pandas as pd
import backend_helper

st.title("🏢 Uploaded Companies")

@st.cache_data(ttl=60)
def load_real_companies_db():
    try:
        drive_service = backend_helper.get_drive_service()
        folder_id = st.secrets["google_drive"]["folder_id"]
        
        # Load the DB
        df = backend_helper.load_csv_database(drive_service, folder_id, 'reports_db.csv')
        
        if df.empty:
            return pd.DataFrame()
        
        # We need to fetch live prices for each row
        angel_secrets = st.secrets["angel_one"]
        client = backend_helper.get_angel_client(
            api_key=angel_secrets["api_key"],
            client_code=angel_secrets["client_code"],
            password=angel_secrets["password"],
            totp_secret=angel_secrets["totp_secret"]
        )
        
        master_contract = backend_helper.fetch_master_contract()
        
        enhanced_data = []
        for index, row in df.iterrows():
            ticker = row.get("Ticker", "")
            exchange = row.get("Exchange", "NSE")
            price_added = float(row.get("Price When Added", 0))
            mc_added = float(row.get("Market Cap when added", 0))
            
            # Fetch Live Data
            token = backend_helper.get_token_id(master_contract, ticker, exchange)
            if client and token:
                live_data = backend_helper.get_live_market_data(client, token, exchange)
            else:
                live_data = None
                
            if live_data:
                cmp = live_data['cmp']
                today_pct = live_data['pct_change']
            else:
                cmp = price_added
                today_pct = 0.0
                
            # Calculate changes
            pct_change_added = ((cmp - price_added) / price_added * 100) if price_added > 0 else 0
            rt_market_cap = mc_added * (cmp / price_added) if price_added > 0 else mc_added
            mc_change = ((rt_market_cap - mc_added) / mc_added * 100) if mc_added > 0 else 0
            
            enhanced_data.append({
                "Company Name": row.get("Company Name", ticker),
                "Ticker": ticker,
                "Exchange": exchange,
                "Date Added": row.get("Date Added", ""),
                "Price When Added": price_added,
                "CMP (Real-time)": round(cmp, 2),
                "% Change since added": round(pct_change_added, 2),
                "Today's % Change": round(today_pct, 2),
                "Market Cap when added (Cr)": round(mc_added, 2),
                "Real-time Market Cap (Cr)": round(rt_market_cap, 2),
                "% Change of Market Cap": round(mc_change, 2),
                "File ID": row.get("File ID", "")
            })
            
        return pd.DataFrame(enhanced_data)

    except KeyError:
        st.error("Secrets not configured correctly in .streamlit/secrets.toml!")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_real_companies_db()

if df.empty:
    st.info("No companies have been uploaded to the database yet. Go to the Dashboard to upload one!")
else:
    # --- Summary Data Table ---
    display_df = df.drop(columns=["File ID", "Exchange"], errors='ignore')
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "Price When Added": st.column_config.NumberColumn(format="₹%.2f"),
            "CMP (Real-time)": st.column_config.NumberColumn(format="₹%.2f"),
            "% Change since added": st.column_config.NumberColumn(format="%.2f%%"),
            "Today's % Change": st.column_config.NumberColumn(format="%.2f%%"),
            "Market Cap when added (Cr)": st.column_config.NumberColumn(format="₹%.2f"),
            "Real-time Market Cap (Cr)": st.column_config.NumberColumn(format="₹%.2f"),
            "% Change of Market Cap": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True
    )
    
    st.divider()
    
    # --- View Actions ---
    st.subheader("Quick Actions")
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_ticker = st.selectbox("Select a company to view in detail:", df['Ticker'].tolist())
    with col2:
        st.write("") # spacing
        st.write("")
        if st.button("👁️ View Profile", use_container_width=True, type="primary"):
            st.session_state.selected_ticker = selected_ticker
            selected_row = df[df['Ticker'] == selected_ticker].iloc[0]
            st.session_state.selected_company = selected_row['Company Name']
            st.session_state.selected_exchange = selected_row.get('Exchange', 'NSE')
            st.session_state.selected_file_id = selected_row.get('File ID', '')
            st.session_state.selected_price_added = selected_row.get('Price When Added', 0)
            st.session_state.selected_mc_added = selected_row.get('Market Cap when added', 0)
            st.switch_page("pages/company_profile.py")
