import streamlit as st
import auth_manager

st.title("⚙️ Admin Panel")
st.markdown("Manage user approvals and platform settings.")

st.divider()

st.subheader("Pending User Approvals")

pending_users = auth_manager.get_pending_approvals()

if pending_users.empty:
    st.info("No pending user registrations at the moment.")
else:
    for index, row in pending_users.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**Name:** {row['Name']}")
                st.write(f"**Email:** {row['Email']}")
            
            with col2:
                if st.button("✅ Approve", key=f"approve_{row['Email']}", type="primary"):
                    if auth_manager.approve_user(row['Email']):
                        st.success(f"Approved {row['Email']}!")
                        st.rerun()
            
            with col3:
                if st.button("❌ Reject", key=f"reject_{row['Email']}"):
                    if auth_manager.reject_user(row['Email']):
                        st.warning(f"Rejected {row['Email']}.")
                        st.rerun()
            st.divider()

# --- Active Users Panel ---
st.subheader("👥 Active Users Manager")

import datetime
import pandas as pd

users_df = auth_manager.get_users_df()
active_users = users_df[users_df['Is_Approved'] == True]

st.write(f"Total Active Users: **{len(active_users)}**")

for index, row in active_users.iterrows():
    # Calculate status
    status = "🔴 Offline"
    if pd.notna(row.get('Last_Seen')) and str(row.get('Last_Seen')).strip() != "":
        try:
            last_seen_time = datetime.datetime.strptime(str(row['Last_Seen']), "%Y-%m-%d %H:%M:%S")
            time_diff = (datetime.datetime.now() - last_seen_time).total_seconds()
            if abs(time_diff) < 300:
                status = "🟢 Online"
            else:
                # Show neat formatted last active string
                status = f"🔴 Offline (Last active: {row['Last_Seen']})"
        except Exception:
            status = "🔴 Offline"
            
    with st.container():
        col_u1, col_u2 = st.columns([3, 1])
        with col_u1:
            st.write(f"👤 **Name:** {row['Name']}")
            st.write(f"📧 **Email:** `{row['Email']}`")
            st.write(f"📶 **Status:** {status}")
            st.write(f"🔑 **Hashed Password:** `{row['Password'][:30]}...` (Encrypted with bcrypt)")
            
        with col_u2:
            # Add password reset button
            if st.button("🔄 Reset Password", key=f"reset_pwd_{row['Email']}", help="Reset password to default '123456'"):
                if auth_manager.reset_user_password(row['Email']):
                    st.success(f"Reset password to '123456'!")
                    st.rerun()
                else:
                    st.error("Failed to reset password.")
        st.divider()

# --- Manage Tracked Companies Section ---
st.subheader("🗑️ Manage Tracked Companies")

import backend_helper
import pandas as pd

try:
    drive_service = backend_helper.get_drive_service()
    folder_id = st.secrets["google_drive"]["folder_id"]
    reports_df = backend_helper.load_csv_database(drive_service, folder_id, 'reports_db.csv')
except Exception as e:
    reports_df = pd.DataFrame()

if reports_df.empty:
    st.info("No companies are currently tracked.")
else:
    st.markdown("Select an uploaded company to permanently delete from the platform database:")
    
    # Create Display Name column
    reports_df['Display_Name'] = reports_df['Company Name'] + " (" + reports_df['Ticker'] + ")"
    company_to_delete = st.selectbox(
        "Select company to delete:",
        options=reports_df['Display_Name'].tolist(),
        key="company_delete_select"
    )
    
    selected_row = reports_df[reports_df['Display_Name'] == company_to_delete].iloc[0]
    selected_ticker = selected_row['Ticker']
    
    with st.expander(f"⚠️ Confirm Deletion of {company_to_delete}"):
        st.warning(f"Are you sure you want to permanently delete **{selected_row['Company Name']}** ({selected_ticker})? This action cannot be undone.")
        confirm_btn = st.button("🔥 Permanently Delete Company", type="primary", use_container_width=True)
        
        if confirm_btn:
            with st.spinner("Deleting company from Drive..."):
                # Filter out company
                updated_df = reports_df[reports_df['Ticker'] != selected_ticker]
                updated_df = updated_df.drop(columns=['Display_Name'], errors='ignore')
                
                # Save updated companies list
                success = backend_helper.save_csv_database(drive_service, updated_df, folder_id, 'reports_db.csv')
                
                if success:
                    # Clean up related comments if any
                    try:
                        comments_df = backend_helper.load_comments_database(drive_service, folder_id)
                        if not comments_df.empty and 'Ticker' in comments_df.columns:
                            updated_comments = comments_df[comments_df['Ticker'] != selected_ticker]
                            backend_helper.save_comments_database(drive_service, updated_comments, folder_id)
                    except Exception as e:
                        print(f"Error cleaning up comments: {e}")
                        
                    st.success(f"Successfully deleted **{selected_row['Company Name']}**!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Failed to update database on Google Drive.")
