import streamlit as st
import importlib
import auth_manager
importlib.reload(auth_manager)
import backend_helper
import utils
import datetime
import pandas as pd

# Inject premium CSS styling
utils.inject_custom_css()

# Display Lingual logo in top right corner
utils.render_lingual_logo(position="top-right", show_tagline=False)

# Modern page header
utils.render_page_header(
    "Admin Panel",
    "Manage users, approvals, and database entries",
    "⚙️"
)

# Create organized tabs
tab_approvals, tab_active, tab_companies = st.tabs([
    "📝 Pending Approvals",
    "👥 Active Users Manager",
    "🗑️ Company Database Manager"
])

# ==========================================
# TAB 1: PENDING APPROVALS
# ==========================================
with tab_approvals:
    st.subheader("Pending User Approvals")
    pending_users = auth_manager.get_pending_approvals()

    if pending_users.empty:
        st.info("No pending user registrations at the moment.")
    else:
        for index, row in pending_users.iterrows():
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"👤 **Name:** {row['Name']}")
                    st.write(f"📧 **Email:** `{row['Email']}`")
                
                with col2:
                    st.write("") # vertical spacing
                    if st.button("✅ Approve", key=f"approve_{row['Email']}", type="primary", use_container_width=True):
                        if auth_manager.approve_user(row['Email']):
                            st.success(f"Approved {row['Email']}!")
                            st.rerun()
                
                with col3:
                    st.write("") # vertical spacing
                    if st.button("❌ Reject", key=f"reject_{row['Email']}", use_container_width=True):
                        if auth_manager.reject_user(row['Email']):
                            st.warning(f"Rejected {row['Email']}.")
                            st.rerun()

# ==========================================
# TAB 2: ACTIVE USERS MANAGER
# ==========================================
with tab_active:
    st.subheader("Active Users Database")
    users_df = auth_manager.get_users_df()
    
    if users_df.empty:
        st.info("No users registered in the database.")
    else:
        active_users = users_df[users_df['Is_Approved'] == True]
        st.write(f"Total Active Users: **{len(active_users)}**")
        
        for index, row in active_users.iterrows():
            status = "🔴 Offline"
            if pd.notna(row.get('Last_Seen')) and str(row.get('Last_Seen')).strip() != "":
                try:
                    last_seen_time = datetime.datetime.strptime(str(row['Last_Seen']), "%Y-%m-%d %H:%M:%S")
                    time_diff = (datetime.datetime.now() - last_seen_time).total_seconds()
                    if abs(time_diff) < 300:
                        status = "🟢 Online"
                    else:
                        status = f"🔴 Offline (Last active: {row['Last_Seen']})"
                except Exception:
                    status = "🔴 Offline"
                    
            with st.container(border=True):
                is_user_admin = bool(row.get('Is_Admin', False))
                role_str = "👑 Admin" if is_user_admin else "👤 Analyst"
                
                col_u1, col_u2 = st.columns([3, 1.5])
                with col_u1:
                    st.write(f"👤 **Name:** {row['Name']}")
                    st.write(f"📧 **Email:** `{row['Email']}`")
                    st.write(f"🏷️ **Role:** `{role_str}`")
                    st.write(f"📶 **Status:** {status}")
                    st.write(f"🔑 **Hashed Password:** `{row['Password'][:35]}...` (Bcrypt encrypted)")
                    
                with col_u2:
                    st.write("") # vertical spacing
                    # Reset Password Expander (Yes/No Confirmation)
                    with st.expander("🔄 Reset Password"):
                        st.warning(f"Reset password for {row['Name']} to default '123456'?")
                        if st.button("Confirm Reset", key=f"confirm_reset_{row['Email']}", type="primary", use_container_width=True):
                            if auth_manager.reset_user_password(row['Email']):
                                st.success("Reset password to '123456'!")
                                st.rerun()
                            else:
                                st.error("Failed to reset password.")
                            
                    # Prevent primary admin from demoting themselves to avoid accidental lockout
                    is_primary = row['Email'] == "vaibhavgupta@lingualconsultancy.in"
                    btn_label = "👤 Remove Admin" if is_user_admin else "👑 Make Admin"
                    btn_help = "Cannot demote primary admin" if is_primary else ("Remove administrator privileges" if is_user_admin else "Grant administrator privileges")
                    
                    # Toggle Admin Expander (Only show for other users)
                    if not is_primary:
                        with st.expander(btn_label):
                            st.warning(f"Change admin role status for {row['Name']}?")
                            if st.button(f"Confirm {btn_label}", key=f"toggle_admin_{row['Email']}", help=btn_help, use_container_width=True, type="primary"):
                                success, new_status = auth_manager.toggle_admin_status(row['Email'])
                                if success:
                                    role_action = "promoted to Admin" if new_status else "demoted to Analyst"
                                    st.success(f"Successfully {role_action} {row['Email']}!")
                                    st.rerun()
                                else:
                                    st.error("Failed to update user role.")
 
                # Remove User Option (Confirm via expander to prevent accidental deletion)
                is_self = row['Email'] == st.session_state.get("user_email")
                if is_self:
                    st.caption("ℹ️ *You cannot remove your own account.*")
                elif is_primary:
                    st.caption("ℹ️ *Primary Administrator account cannot be removed.*")
                else:
                    with st.expander(f"🗑️ Remove User Account ({row['Name']})"):
                        st.warning(f"Are you sure you want to permanently delete **{row['Name']}** ({row['Email']})?")
                        if st.button("🔥 Permanently Delete User", key=f"delete_user_{row['Email']}", type="primary", use_container_width=True):
                            if auth_manager.remove_user(row['Email']):
                                st.success(f"Successfully deleted {row['Name']}!")
                                st.rerun()
                            else:
                                st.error("Failed to delete user.")
 
# ==========================================
# TAB 3: COMPANY DATABASE MANAGER
# ==========================================
with tab_companies:
    st.subheader("Manage Tracked Companies")
    
    try:
        drive_service = backend_helper.get_drive_service()
        folder_id = st.secrets["google_drive"]["folder_id"]
        reports_df = backend_helper.load_csv_database(drive_service, folder_id, 'reports_db.csv')
    except Exception as e:
        reports_df = pd.DataFrame()
        drive_service = None
        folder_id = None
 
    if reports_df.empty:
        st.info("No companies are currently tracked.")
    else:
        st.markdown("Select an uploaded company to permanently delete from the platform database:")
        
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
                    updated_df = reports_df[reports_df['Ticker'] != selected_ticker]
                    updated_df = updated_df.drop(columns=['Display_Name'], errors='ignore')
                    
                    success = backend_helper.save_csv_database(drive_service, updated_df, folder_id, 'reports_db.csv')
                    
                    if success:
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
