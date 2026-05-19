import pandas as pd
import os
import bcrypt

DB_FILE = 'users_db.csv'

def init_db():
    if not os.path.exists(DB_FILE):
        # Create initial DataFrame
        default_pwd = bcrypt.hashpw("123456".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        initial_users = [
            {"Name": "Vaibhav Gupta", "Email": "vaibhavgupta@lingualconsultancy.in", "Password": default_pwd, "Is_First_Login": True, "Is_Approved": True, "Last_Seen": ""},
            {"Name": "Ashutosh Singh", "Email": "ashutosh.singh@seminalresearch.com", "Password": default_pwd, "Is_First_Login": True, "Is_Approved": True, "Last_Seen": ""},
            {"Name": "Ajay Yadav", "Email": "ajay.yadav@lingualconsultancy.com", "Password": default_pwd, "Is_First_Login": True, "Is_Approved": True, "Last_Seen": ""},
            {"Name": "Vaibhav Srivastava", "Email": "vaibhav.srivastava@lingualconsultancy.in", "Password": default_pwd, "Is_First_Login": True, "Is_Approved": True, "Last_Seen": ""},
            {"Name": "Mahesssss", "Email": "maheshyaduvanshi20@gmail.com", "Password": default_pwd, "Is_First_Login": True, "Is_Approved": True, "Last_Seen": ""}
        ]
        df = pd.DataFrame(initial_users)
        df.to_csv(DB_FILE, index=False)
    else:
        df = pd.read_csv(DB_FILE)
        if "Last_Seen" not in df.columns:
            df["Last_Seen"] = ""
            df.to_csv(DB_FILE, index=False)

def get_users_df():
    init_db()
    return pd.read_csv(DB_FILE)

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
        df.to_csv(DB_FILE, index=False)
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
        "Is_Approved": False
    }
    df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)
    return True, "Registration successful! Pending Admin approval."

def get_pending_approvals():
    df = get_users_df()
    return df[df['Is_Approved'] == False]

def approve_user(email):
    df = get_users_df()
    idx = df[df['Email'] == email].index
    if not idx.empty:
        df.loc[idx, 'Is_Approved'] = True
        df.to_csv(DB_FILE, index=False)
        return True
    return False

def reject_user(email):
    df = get_users_df()
    idx = df[df['Email'] == email].index
    if not idx.empty:
        df = df.drop(idx)
        df.to_csv(DB_FILE, index=False)
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
    df = get_users_df()
    idx = df[df['Email'] == email].index
    if not idx.empty:
        # Cast Last_Seen to object type to support string assignment on empty/float columns
        df['Last_Seen'] = df['Last_Seen'].astype(object)
        df.loc[idx, 'Last_Seen'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.to_csv(DB_FILE, index=False)
        return True
    return False

def reset_user_password(email):
    df = get_users_df()
    idx = df[df['Email'] == email].index
    if not idx.empty:
        default_pwd = bcrypt.hashpw("123456".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        df.loc[idx, 'Password'] = default_pwd
        df.loc[idx, 'Is_First_Login'] = True
        df.to_csv(DB_FILE, index=False)
        return True
    return False

# Ensure DB is initialized on import
init_db()
