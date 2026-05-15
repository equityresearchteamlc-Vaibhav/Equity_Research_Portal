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
