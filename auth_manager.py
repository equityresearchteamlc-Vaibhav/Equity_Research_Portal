import pandas as pd
import os
import bcrypt
import streamlit as st
import backend_helper

DB_FILE = 'users_db.csv'

def get_drive_details():
    try:
        if "google_drive" in st.secrets and "gcp_service_account" in st.secrets:
            service = backend_helper.get_drive_service()
            folder_id = st.secrets["google_drive"]["folder_id"]
            return service, folder_id
    except Exception:
        pass
    return None, None

def load_db():
    service, folder_id = get_drive_details()
    if service and folder_id:
        try:
            df = backend_helper.load_csv_database(service, folder_id, DB_FILE)
            if not df.empty:
                return df
        except Exception as e:
            print(f"Error loading {DB_FILE} from Google Drive: {e}")
            
    # Fallback to local copy
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE)
        except Exception:
            pass
    return pd.DataFrame()

def save_db(df):
    # Save local copy as backup
    try:
        df.to_csv(DB_FILE, index=False)
    except Exception as e:
        print(f"Error saving {DB_FILE} locally: {e}")
        
    service, folder_id = get_drive_details()
    if service and folder_id:
        try:
            backend_helper.save_csv_database(service, df, folder_id, DB_FILE)
        except Exception as e:
            print(f"Error saving {DB_FILE} to Google Drive: {e}")

def init_db():
    df = load_db()
    
    # If the file is completely empty or doesn't exist, create it with initial users
    if df.empty:
        default_pwd = bcrypt.hashpw("123456".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        initial_users = [
            {"Name": "Vaibhav Gupta", "Email": "vaibhavgupta@lingualconsultancy.in", "Password": default_pwd, "Is_First_Login": True, "Is_Approved": True, "Last_Seen": "", "Is_Admin": True},
            {"Name": "Ashutosh Singh", "Email": "ashutosh.singh@seminalresearch.com", "Password": default_pwd, "Is_First_Login": True, "Is_Approved": True, "Last_Seen": "", "Is_Admin": False},
            {"Name": "Ajay Yadav", "Email": "ajay.yadav@lingualconsultancy.com", "Password": default_pwd, "Is_First_Login": True, "Is_Approved": True, "Last_Seen": "", "Is_Admin": False},
            {"Name": "Vaibhav Srivastava", "Email": "vaibhav.srivastava@lingualconsultancy.in", "Password": default_pwd, "Is_First_Login": True, "Is_Approved": True, "Last_Seen": "", "Is_Admin": False},
            {"Name": "Mahesssss", "Email": "maheshyaduvanshi20@gmail.com", "Password": default_pwd, "Is_First_Login": True, "Is_Approved": True, "Last_Seen": "", "Is_Admin": False}
        ]
        df = pd.DataFrame(initial_users)
        save_db(df)
        return

    # Migration: Ensure all required columns exist without wiping the DB
    updated = False
    required_defaults = {
        "Name": "",
        "Email": "",
        "Password": "",
        "Is_First_Login": True,
        "Is_Approved": False,
        "Last_Seen": "",
        "Is_Admin": False
    }
    
    for col, default in required_defaults.items():
        if col not in df.columns:
            df[col] = default
            updated = True
            
    # Explicitly make sure vaibhavgupta@lingualconsultancy.in is admin and named Vaibhav Gupta
    idx = df[df['Email'] == "vaibhavgupta@lingualconsultancy.in"].index
    if not idx.empty:
        if not df.loc[idx[0], 'Is_Admin']:
            df.loc[idx, 'Is_Admin'] = True
            updated = True
        if df.loc[idx[0], 'Name'] != "Vaibhav Gupta":
            df.loc[idx, 'Name'] = "Vaibhav Gupta"
            updated = True

    if updated:
        save_db(df)

def get_users_df():
    init_db()
    return load_db()

def verify_login(email, password):
    df = get_users_df()
    user_row = df[df['Email'] == email]
    if user_row.empty:
        return False, "User not found. Have you registered?"
    
    user = user_row.iloc[0]
    
    if not user['Is_Approved']:
        return False, "Account pending approval from Admin."
    
    hashed_pwd = user['Password'].encode('utf-8')
    if bcrypt.checkpw(password.encode('utf-8'), hashed_pwd):
        return True, user.to_dict()
    else:
        return False, "Incorrect password."

def change_password(email, new_password):
    df = get_users_df()
    idx = df[df['Email'] == email].index
    if not idx.empty:
        new_hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        df.loc[idx, 'Password'] = new_hashed
        df.loc[idx, 'Is_First_Login'] = False
        save_db(df)
        return True
    return False

def register_user(name, email, password):
    df = get_users_df()
    if not df[df['Email'] == email].empty:
        return False, "Email already exists."
    
    new_hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    new_user = {
        "Name": name, 
        "Email": email, 
        "Password": new_hashed, 
        "Is_First_Login": False, 
        "Is_Approved": False,
        "Last_Seen": "",
        "Is_Admin": False
    }
    df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
    save_db(df)
    return True, "Registration successful! Pending Admin approval."

def get_pending_approvals():
    df = get_users_df()
    return df[df['Is_Approved'] == False]

def approve_user(email):
    df = get_users_df()
    idx = df[df['Email'] == email].index
    if not idx.empty:
        df.loc[idx, 'Is_Approved'] = True
        save_db(df)
        return True
    return False

def reject_user(email):
    df = get_users_df()
    idx = df[df['Email'] == email].index
    if not idx.empty:
        df = df.drop(idx)
        save_db(df)
        return True
    return False

def get_user_by_email(email):
    df = get_users_df()
    user_row = df[df['Email'] == email]
    if user_row.empty:
        return None
    return user_row.iloc[0].to_dict()

def update_user_activity(email):
    import datetime
    import pytz
    df = get_users_df()
    idx = df[df['Email'] == email].index
    if not idx.empty:
        # Cast Last_Seen to object type to support string assignment on empty/float columns
        df['Last_Seen'] = df['Last_Seen'].astype(object)
        df.loc[idx, 'Last_Seen'] = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")
        save_db(df)
        return True
    return False

def reset_user_password(email):
    df = get_users_df()
    idx = df[df['Email'] == email].index
    if not idx.empty:
        default_pwd = bcrypt.hashpw("123456".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        df.loc[idx, 'Password'] = default_pwd
        df.loc[idx, 'Is_First_Login'] = True
        save_db(df)
        return True
    return False

def toggle_admin_status(email):
    df = get_users_df()
    idx = df[df['Email'] == email].index
    if not idx.empty:
        new_val = not bool(df.loc[idx[0], 'Is_Admin'])
        df.loc[idx, 'Is_Admin'] = new_val
        save_db(df)
        return True, new_val
    return False, None

def remove_user(email):
    df = get_users_df()
    idx = df[df['Email'] == email].index
    if not idx.empty:
        df = df.drop(idx)
        save_db(df)
        return True
    return False

def verify_mfa(code):
    try:
        import pyotp
        totp_secret = st.secrets["angel_one"]["totp_secret"]
        totp = pyotp.TOTP(totp_secret)
        # Verify allowing adjacent time steps for user latency
        return totp.verify(str(code).strip(), valid_window=1)
    except Exception:
        return False

# Ensure DB is initialized on import
init_db()
