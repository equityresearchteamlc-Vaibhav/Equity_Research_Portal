import streamlit as st
import auth_manager
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="Equity Research Portal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State for Authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "is_first_login" not in st.session_state:
    st.session_state.is_first_login = False

def login_register():
    st.title("🔐 Equity Research Portal")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Team Login")
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="analyst@firm.com")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", type="primary")
            
            if submit:
                if email and password:
                    success, data = auth_manager.verify_login(email, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_email = data['Email']
                        st.session_state.user_name = data['Name']
                        st.session_state.is_first_login = data['Is_First_Login']
                        st.rerun()
                    else:
                        st.error(data)
                else:
                    st.warning("Please enter both email and password.")
                    
    with tab2:
        st.subheader("New User Registration")
        with st.form("register_form"):
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email Address")
            new_password = st.text_input("Password", type="password")
            new_password_confirm = st.text_input("Confirm Password", type="password")
            reg_submit = st.form_submit_button("Register Now")
            
            if reg_submit:
                if new_name and new_email and new_password:
                    if new_password == new_password_confirm:
                        success, msg = auth_manager.register_user(new_name, new_email, new_password)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.error("Passwords do not match!")
                else:
                    st.warning("Please fill in all fields.")

def force_password_reset():
    st.title("⚠️ First-time Login: Password Reset Required")
    st.warning("Since this is your first time logging in, you must change your default password.")
    
    with st.form("reset_form"):
        new_password = st.text_input("New Password", type="password")
        new_password_confirm = st.text_input("Confirm New Password", type="password")
        submit = st.form_submit_button("Update Password", type="primary")
        
        if submit:
            if new_password and new_password == new_password_confirm:
                if auth_manager.change_password(st.session_state.user_email, new_password):
                    st.session_state.is_first_login = False
                    st.success("Password updated successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Error updating password.")
            else:
                st.error("Passwords do not match or are empty.")

def logout():
    st.session_state.authenticated = False
    st.session_state.user_email = ""
    st.session_state.user_name = ""
    st.session_state.is_first_login = False
    st.rerun()

# --- Main Routing ---
if not st.session_state.authenticated:
    # Calling st.navigation here hides the default 'pages/' folder links
    login_page = st.Page(login_register, title="Login / Register", icon="🔐")
    pg = st.navigation([login_page])
    pg.run()
elif st.session_state.is_first_login:
    reset_page = st.Page(force_password_reset, title="Reset Password", icon="⚠️")
    pg = st.navigation([reset_page])
    
    with st.sidebar:
        st.markdown(f"**Logged in as:** {st.session_state.user_name}")
        st.button("Logout", on_click=logout, type="primary")
        
    pg.run()
else:
    # Modern st.navigation and st.Page routing
    pages = {
        "Dashboard": [
            st.Page("pages/dashboard.py", title="Dashboard", icon="📊", default=True),
            st.Page("pages/list_companies.py", title="Company List", icon="🏢"),
        ],
        "Details": [
             st.Page("pages/company_profile.py", title="Company Profile", icon="🔍")
        ]
    }
    
    # Restrict Admin panel to Vaibhav Gupta
    if st.session_state.user_email == "vaibhavgupta@lingualconsultancy.in":
        pages["Admin Tools"] = [
            st.Page("pages/admin_panel.py", title="Admin Panel", icon="⚙️")
        ]
    
    pg = st.navigation(pages)
    
    with st.sidebar:
        st.markdown(f"**Logged in as:** {st.session_state.user_name}")
        st.button("Logout", on_click=logout, type="primary")
    
    pg.run()
