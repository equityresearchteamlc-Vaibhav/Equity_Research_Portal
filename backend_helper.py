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
            print(f"Login Failed: {data['message']}")
            return None
    except Exception as e:
        print(f"Error during Angel One authentication: {e}")
        return None

@st.cache_data(ttl=3600)
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

def get_token_id(df, ticker, exchange="NSE"):
    """
    Maps a stock ticker to its correct Token ID.
    Example ticker format: 'RELIANCE-EQ' or just 'RELIANCE'.
    """
    if exchange == "NSE":
        # Usually NSE equities end with '-EQ' in the symbol
        res = df[(df['name'] == ticker) & (df['exch_seg'] == exchange) & (df['symbol'].str.endswith('-EQ'))]
        if not res.empty:
             return res.iloc[0]['token']
    res = df[(df['name'] == ticker) & (df['exch_seg'] == exchange)]
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
            high_52 = unpacked.get('52weekhigh', unpacked.get('high52', 0.0))
            low_52 = unpacked.get('52weeklow', unpacked.get('low52', 0.0))
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

@st.cache_data(ttl=60, show_spinner=False)
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
