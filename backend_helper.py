import os
import json
import urllib.request
import pyotp
import pandas as pd
import io
import time
from SmartApi import SmartConnect
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import streamlit as st

# --- Angel One Integration ---
@st.cache_resource(ttl=1800)
def get_angel_client(api_key, client_code, password, totp_secret):
    """
    Authenticates with Angel One SmartAPI using provided credentials.
    """
    try:
        obj = SmartConnect(api_key=api_key)
        totp = pyotp.TOTP(totp_secret).now()
        data = obj.generateSession(client_code, password, totp)
        if data['status']:
            return obj
        else:
            raise Exception(f"Angel One Login Failed: {data.get('message', 'Unknown error')}")
    except Exception as e:
        # Re-raise so Streamlit doesn't cache the failure
        raise e

@st.cache_data(ttl=3600, show_spinner="Loading your data...")
def fetch_master_contract():
    """
    Downloads Angel One's open-source master instrument JSON file.
    """
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    try:
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching master contract: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=86400, show_spinner=False)
def get_token_id(_df, ticker, exchange="NSE"):
    """
    Maps a stock ticker to its correct Token ID.
    Example ticker format: 'RELIANCE-EQ' or just 'RELIANCE'.
    """
    if exchange == "NSE":
        # Usually NSE equities end with '-EQ', '-BE', '-SM', '-ST', or '-BZ' in the symbol
        res = _df[(_df['name'] == ticker) & (_df['exch_seg'] == exchange) & (_df['symbol'].str.endswith(('-EQ', '-BE', '-SM', '-ST', '-BZ')))]
        if not res.empty:
             return res.iloc[0]['token']
    res = _df[(_df['name'] == ticker) & (_df['exch_seg'] == exchange)]
    if not res.empty:
        return res.iloc[0]['token']
    return None

@st.cache_data(ttl=15, show_spinner=False)
def get_live_market_data(_obj, token, exchange="NSE"):
    """
    Fetches real-time market data (CMP, 52W High/Low, Today's % Change).
    """
    try:
        data = {
            "mode": "FULL",
            "exchangeTokens": {
                exchange: [token]
            }
        }
        res = _obj.getMarketData(data['mode'], data['exchangeTokens'])
        if res and res.get('status') and res.get('data'):
            unpacked = res['data']['fetched'][0]
            cmp = unpacked.get('ltp', 0.0)
            high_52 = unpacked.get('52WeekHigh', unpacked.get('52weekhigh', unpacked.get('high52', 0.0)))
            low_52 = unpacked.get('52WeekLow', unpacked.get('52weeklow', unpacked.get('low52', 0.0)))
            close = unpacked.get('close', 0.0)
            # marketCap from Angel One API is in raw rupees; divide by 1 Cr (10,000,000)
            raw_mc = unpacked.get('marketCap', 0.0) or 0.0
            market_cap_cr = raw_mc / 10_000_000
            pct_change = ((cmp - close) / close * 100) if close != 0 else 0.0
            return {
                "cmp": cmp,
                "52w_high": high_52,
                "52w_low": low_52,
                "pct_change": pct_change,
                "close": close,
                "market_cap_cr": market_cap_cr
            }
        else:
            print("Failed to fetch live data")
            return None
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return None

@st.cache_data(ttl=15, show_spinner=False)
def get_live_market_data_batch(_obj, token_exchange_pairs):
    """
    Fetches real-time market data for multiple tokens in a single batch request.
    token_exchange_pairs is a list/set/tuple of (token, exchange) pairs.
    """
    if not _obj or not token_exchange_pairs:
        return {}
    
    # Group tokens by exchange
    exchange_tokens = {}
    for token, exchange in token_exchange_pairs:
        if token:
            exchange_tokens.setdefault(exchange, []).append(str(token))
            
    if not exchange_tokens:
        return {}
        
    try:
        res = _obj.getMarketData("FULL", exchange_tokens)
        result_map = {}
        if res and res.get('status') and res.get('data') and res['data'].get('fetched'):
            for item in res['data']['fetched']:
                token = item.get('symbolToken') or item.get('token')
                if not token:
                    continue
                cmp = item.get('ltp', 0.0)
                high_52 = item.get('52weekhigh', item.get('high52', 0.0))
                low_52 = item.get('52weeklow', item.get('low52', 0.0))
                close = item.get('close', 0.0)
                raw_mc = item.get('marketCap', 0.0) or 0.0
                market_cap_cr = raw_mc / 10_000_000
                pct_change = ((cmp - close) / close * 100) if close != 0 else 0.0
                
                result_map[str(token)] = {
                    "cmp": cmp,
                    "52w_high": high_52,
                    "52w_low": low_52,
                    "pct_change": pct_change,
                    "close": close,
                    "market_cap_cr": market_cap_cr
                }
            return result_map
        else:
            print("Failed to fetch live batch data")
            return {}
    except Exception as e:
        print(f"Error fetching batch market data: {e}")
        return {}

@st.cache_data(ttl=86400, show_spinner=False)
def get_historical_price(ticker, exchange, date_obj):
    import yfinance as yf
    import datetime
    import pandas as pd
    try:
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.datetime.strptime(date_obj, "%Y-%m-%d").date()
            except ValueError:
                pass
        
        yf_ticker = f"{ticker}.NS" if exchange == "NSE" else f"{ticker}.BO"
        start_date = date_obj.strftime('%Y-%m-%d')
        end_date = (date_obj + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        
        data = yf.download(yf_ticker, start=start_date, end=end_date, progress=False)
        if not data.empty:
            return float(data['Close'].iloc[0].item()) if hasattr(data['Close'].iloc[0], 'item') else float(data['Close'].iloc[0])
    except Exception as e:
        print(f"Error fetching historical price for {ticker}: {e}")
    return 0.0

# --- Google Drive Integration ---

@st.cache_resource
def get_drive_service():
    """
    Builds the Google Drive service client from st.secrets.
    """
    SCOPES = ['https://www.googleapis.com/auth/drive']
    try:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building Drive service: {e}")
        return None

def find_file_in_folder(service, folder_id, file_name):
    """
    Helper to find a file by name within a specific folder.
    Supports both My Drive and Shared Drives.
    """
    query = f"'{folder_id}' in parents and name = '{file_name}' and trashed = false"
    try:
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        files = results.get('files', [])
        if files:
            return files[0]['id']
        return None
    except Exception as e:
        print(f"Error finding file {file_name}: {e}")
        return None

# --- Google Drive File Upload ---

def upload_file_to_drive(service, file_bytes, file_name, folder_id, mime_type='application/octet-stream'):
    """
    Uploads any research file type to Google Drive using Google Apps Script Web App.
    """
    import base64
    try:
        url = st.secrets["google_drive"]["apps_script_url"]
        token = st.secrets["google_drive"]["apps_script_token"]
        
        encoded_bytes = base64.b64encode(file_bytes).decode('utf-8')
        
        payload = {
            "action": "upload",
            "token": token,
            "folderId": folder_id,
            "fileName": file_name,
            "fileBytes": encoded_bytes,
            "mimeType": mime_type
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if res_data.get('success'):
                return res_data.get('fileId')
            else:
                raise Exception(res_data.get('error', 'Unknown Apps Script error'))
    except Exception as e:
        print(f"Error uploading via Apps Script: {e}")
        raise e

@st.cache_data(ttl=300, show_spinner=False)
def load_csv_database(_service, folder_id, db_name='reports_db.csv'):
    """
    Reads a CSV file directly into a Pandas DataFrame from Drive.
    Uses MediaIoBaseDownload for reliable streaming of file content.
    """
    file_id = find_file_in_folder(_service, folder_id, db_name)
    if not file_id:
        return pd.DataFrame()
    try:
        request = _service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return pd.read_csv(fh)
    except Exception as e:
        print(f"Error reading CSV {db_name}: {e}")
        return pd.DataFrame()

def save_csv_database(service, dataframe, folder_id, db_name='reports_db.csv'):
    """
    Overwrites/updates the CSV on Drive using Google Apps Script Web App.
    """
    try:
        url = st.secrets["google_drive"]["apps_script_url"]
        token = st.secrets["google_drive"]["apps_script_token"]
        
        csv_content = dataframe.to_csv(index=False)
        
        payload = {
            "action": "save_csv",
            "token": token,
            "folderId": folder_id,
            "fileName": db_name,
            "csvContent": csv_content
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if res_data.get('success'):
                load_csv_database.clear()
                return True
            else:
                raise Exception(res_data.get('error', 'Unknown Apps Script error'))
    except Exception as e:
        print(f"Error saving CSV via Apps Script: {e}")
        return False

def load_comments_database(service, folder_id):
    """
    Manage an Instagram-style comment ledger named 'comments_db.csv'.
    """
    return load_csv_database(service, folder_id, db_name='comments_db.csv')

def save_comments_database(service, dataframe, folder_id):
    """
    Save the comments database back to Drive.
    """
    return save_csv_database(service, dataframe, folder_id, db_name='comments_db.csv')

def load_pipeline_database(service, folder_id):
    return load_csv_database(service, folder_id, db_name='pipeline_db.csv')

def save_pipeline_database(service, dataframe, folder_id):
    return save_csv_database(service, dataframe, folder_id, db_name='pipeline_db.csv')

def load_shortlisted_database(service, folder_id):
    return load_csv_database(service, folder_id, db_name='shortlisted_db.csv')

def save_shortlisted_database(service, dataframe, folder_id):
    return save_csv_database(service, dataframe, folder_id, db_name='shortlisted_db.csv')

@st.cache_data(ttl=86400, show_spinner=False)
def get_unified_company_list(cache_path="listed_companies_cache_v2.csv"):
    """
    Returns a DataFrame of all active companies listed on NSE and BSE, merged with names from NSE.
    Caches the processed list locally to speed up subsequent loads.
    """
    import os
    import time
    
    # Check if local cache is fresh (less than 24 hours old)
    if os.path.exists(cache_path):
        mtime = os.path.getmtime(cache_path)
        if (time.time() - mtime) < 86400: # 24 hours
            try:
                df = pd.read_csv(cache_path)
                if not df.empty:
                    return df
            except Exception as e:
                print(f"Error reading local company cache: {e}")
                
    # Cache is either missing, empty, or stale. Let's rebuild it.
    import urllib.request
    import io
    import json
    
    # 1. Download NSE EQUITY_L.csv and SME_EQUITY_L.csv
    try:
        req_nse = urllib.request.Request(
            "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv",
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req_nse) as response:
            nse_df = pd.read_csv(io.BytesIO(response.read()))
        # Clean columns: strip whitespace
        nse_df.columns = nse_df.columns.str.strip()
        nse_df = nse_df[['SYMBOL', 'NAME OF COMPANY']].rename(columns={
            'SYMBOL': 'symbol_nse',
            'NAME OF COMPANY': 'company_name'
        })
    except Exception as e:
        print(f"Error fetching NSE list: {e}")
        nse_df = pd.DataFrame(columns=['symbol_nse', 'company_name'])
        
    try:
        req_sme = urllib.request.Request(
            "https://nsearchives.nseindia.com/content/equities/SME_EQUITY_L.csv",
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req_sme) as response:
            sme_df = pd.read_csv(io.BytesIO(response.read()))
        sme_df.columns = sme_df.columns.str.strip()
        sme_df = sme_df[['SYMBOL', 'NAME OF COMPANY']].rename(columns={
            'SYMBOL': 'symbol_nse',
            'NAME OF COMPANY': 'company_name'
        })
        nse_df = pd.concat([nse_df, sme_df], ignore_index=True)
    except Exception as e:
        print(f"Error fetching NSE SME list: {e}")

    nse_df = nse_df.drop_duplicates(subset=['symbol_nse'])
        
    # 2. Download Angel One master JSON
    try:
        url_angel = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        response = urllib.request.urlopen(url_angel)
        angel_data = json.loads(response.read())
        angel_df = pd.DataFrame(angel_data)
    except Exception as e:
        print(f"Error fetching Angel One master list: {e}")
        # If we failed to get Angel One list, return whatever we have from local cache or empty
        if os.path.exists(cache_path):
            try:
                return pd.read_csv(cache_path)
            except Exception:
                pass
        return pd.DataFrame()

    try:
        # Filter Angel One for NSE equities (symbol ends with -EQ, -BE, -SM, -ST, or -BZ and exch_seg is NSE)
        nse_equities = angel_df[(angel_df['exch_seg'] == 'NSE') & (angel_df['symbol'].str.endswith(('-EQ', '-BE', '-SM', '-ST', '-BZ')))].copy()
        
        # Filter Angel One for BSE equities (token matches 6-digit starting with 5, exch_seg is BSE, expiry is empty)
        bse_equities = angel_df[(angel_df['exch_seg'] == 'BSE') & (angel_df['expiry'] == '') & (angel_df['token'].str.match(r'^5\d{5}$'))].copy()

        # Map company name from nse_df to nse_equities
        nse_merged = pd.merge(
            nse_equities,
            nse_df,
            left_on='name',
            right_on='symbol_nse',
            how='left'
        )
        
        # Manual fallback mapping for new or unlisted symbols
        fallback_names = {
            "C2C": "C2C Advanced Systems Limited"
        }
        for ticker, full_name in fallback_names.items():
            nse_merged.loc[nse_merged['name'] == ticker, 'company_name'] = full_name
            
        nse_merged['company_name'] = nse_merged['company_name'].fillna(nse_merged['name'])
        
        # Map BSE equities to nse_df
        bse_merged = pd.merge(
            bse_equities,
            nse_df,
            left_on='name',
            right_on='symbol_nse',
            how='left'
        )
        for ticker, full_name in fallback_names.items():
            bse_merged.loc[bse_merged['name'] == ticker, 'company_name'] = full_name
            
        bse_merged['company_name'] = bse_merged['company_name'].fillna(bse_merged['name'])

        # Create combined candidates list
        nse_candidates = nse_merged[['company_name', 'name', 'exch_seg', 'symbol', 'token']].rename(columns={
            'name': 'ticker',
            'exch_seg': 'exchange',
            'symbol': 'exchange_symbol'
        })
        
        bse_candidates = bse_merged[['company_name', 'name', 'exch_seg', 'symbol', 'token']].rename(columns={
            'name': 'ticker',
            'exch_seg': 'exchange',
            'symbol': 'exchange_symbol'
        })
        
        combined = pd.concat([nse_candidates, bse_candidates], ignore_index=True)
        
        # Sort so that NSE comes first (primary)
        combined['exchange_priority'] = combined['exchange'].apply(lambda x: 0 if x == 'NSE' else 1)
        combined = combined.sort_values(by=['ticker', 'exchange_priority'])
        
        # Drop duplicates by ticker, keeping the first (which will be NSE if available, else BSE)
        final_df = combined.drop_duplicates(subset=['ticker'], keep='first')
        
        # Sort alphabetically by company_name for dropdown
        final_df = final_df.sort_values(by='company_name')
        
        # Save to local cache
        final_df.to_csv(cache_path, index=False)
        return final_df
    except Exception as e:
        print(f"Error building unified company list: {e}")
        if os.path.exists(cache_path):
            try:
                return pd.read_csv(cache_path)
            except Exception:
                pass
        return pd.DataFrame()


@st.cache_data(ttl=604800, show_spinner=False)
def fetch_industry_metadata(ticker):
    """
    Scrapes the industry and sector for a given ticker from Screener.in.
    Returns (sector, industry).
    """
    import urllib.request
    import re
    import html
    
    url = f"https://www.screener.in/company/{ticker}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            html_content = response.read().decode('utf-8')
        
        sector_match = re.search(r'title="Sector"\s*>\s*([^<]+)\s*</a>', html_content, re.IGNORECASE)
        industry_match = re.search(r'title="Industry"\s*>\s*([^<]+)\s*</a>', html_content, re.IGNORECASE)
        
        sector = html.unescape(sector_match.group(1).strip()) if sector_match else ""
        industry = html.unescape(industry_match.group(1).strip()) if industry_match else ""
        
        return sector, industry
    except Exception as e:
        print(f"Error fetching industry metadata for {ticker}: {e}")
        return "", ""


def get_cached_token_id(ticker, exchange="NSE"):
    """
    Looks up the Token ID of a ticker locally from the cached unified company list.
    Saves loading the massive 25MB Angel One scrip master contract.
    """
    try:
        unified = get_unified_company_list()
        if unified.empty:
            return None
        # Clean ticker and exchange values
        t_clean = str(ticker).strip().upper()
        e_clean = str(exchange).strip().upper()
        
        res = unified[(unified['ticker'] == t_clean) & (unified['exchange'] == e_clean)]
        if not res.empty:
            return str(res.iloc[0]['token'])
    except Exception as e:
        print(f"Error looking up cached token for {ticker}: {e}")
    return None


@st.cache_data(ttl=300, show_spinner="Loading your data...")
def load_real_companies_db():
    """
    Loads company metadata from Google Drive and merges it with real-time Angel One market data.
    Caches the results for 5 minutes (300 seconds).
    """
    try:
        drive_service = get_drive_service()
        folder_id = st.secrets["google_drive"]["folder_id"]

        df = load_csv_database(drive_service, folder_id, 'reports_db.csv')

        if df.empty:
            return pd.DataFrame()

        try:
            angel_secrets = st.secrets["angel_one"]
            client = get_angel_client(
                api_key=angel_secrets["api_key"],
                client_code=angel_secrets["client_code"],
                password=angel_secrets["password"],
                totp_secret=angel_secrets["totp_secret"]
            )
        except Exception as e:
            print(f"Warning: Angel One login failed in load_real_companies_db: {e}")
            client = None

        # Load unified list once and build a fast hash map lookup in memory
        unified = get_unified_company_list()
        token_map = {}
        if not unified.empty:
            for _, u_row in unified.iterrows():
                t = str(u_row.get('ticker', '')).strip().upper()
                e = str(u_row.get('exchange', '')).strip().upper()
                token_map[(t, e)] = str(u_row.get('token', ''))

        # Gather tokens to fetch in batch using local memory lookup
        token_exchange_pairs = []
        row_tokens = []
        for _, row in df.iterrows():
            ticker   = str(row.get("Ticker", "")).strip().upper()
            exchange = str(row.get("Exchange", "NSE")).strip().upper()
            token    = token_map.get((ticker, exchange))
            token_exchange_pairs.append((token, exchange))
            row_tokens.append((row, token))

        # Batch request market data
        batch_data = {}
        if client and token_exchange_pairs:
            batch_data = get_live_market_data_batch(client, token_exchange_pairs)

        enhanced_data = []
        for row, token in row_tokens:
            ticker     = row.get("Ticker", "")
            exchange   = row.get("Exchange", "NSE")
            price_added = float(row.get("Price When Added", 0) or 0)
            mc_added    = float(row.get("Market Cap when added", 0) or 0)

            # Look up live data using token string
            live_data = batch_data.get(str(token)) if token else None

            if live_data:
                cmp       = live_data['cmp']
                today_pct = live_data['pct_change']
                rt_market_cap = live_data.get('market_cap_cr', 0.0)
                if rt_market_cap == 0.0 and price_added > 0:
                    rt_market_cap = mc_added * (cmp / price_added)
            else:
                cmp           = price_added
                today_pct     = 0.0
                rt_market_cap = mc_added

            pct_change_added = ((cmp - price_added) / price_added * 100) if price_added > 0 else 0
            mc_change        = ((rt_market_cap - mc_added) / mc_added * 100) if mc_added > 0 else 0

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
                "Rating": f"{int(float(row.get('Rating', 5)))}/10" if pd.notna(row.get('Rating')) and str(row.get('Rating')).strip() != "" else "",
                "Rating_Num": float(row.get('Rating', 5)) if pd.notna(row.get('Rating')) and str(row.get('Rating')).strip() != "" else 5.0,
                "Target Price": float(row.get("Target Price", 0) or 0),
                "Expected Return": round(((float(row.get("Target Price", 0) or 0) - cmp) / cmp * 100), 2) if cmp > 0 and float(row.get("Target Price", 0) or 0) > 0 else 0.0,
                "Industry": row.get("Industry", "Unknown"),
                "Uploaded By": row.get("Analyst", "Unknown"),
                "Owner Comment": row.get("Comment", ""),
                "File ID": row.get("File ID", ""),
                "File Link": row.get("File Link", "")
            })

        return pd.DataFrame(enhanced_data)
    except Exception as e:
        print(f"Error loading enhanced company list: {e}")
        return pd.DataFrame()

