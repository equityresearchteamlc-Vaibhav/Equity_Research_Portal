import streamlit as st
import auth_manager
import time
from streamlit_cookies_controller import CookieController

# -------------------------------------------------
# Initialise cookie manager (once per session)
# -------------------------------------------------
if "cookie_controller" not in st.session_state:
    st.session_state.cookie_controller = CookieController()
cookies = st.session_state.cookie_controller

# -------------------------------------------------
# Session‑state defaults
# -------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "is_first_login" not in st.session_state:
    st.session_state.is_first_login = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# -------------------------------------------------
# Restore login from cookie (runs on every reload)
# -------------------------------------------------
if not st.session_state.authenticated:
    saved_email = cookies.get("user_email")
    if saved_email:
        user = auth_manager.get_user_by_email(saved_email)
        if user and user["Is_Approved"]:
            st.session_state.authenticated = True
            st.session_state.user_email = user["Email"]
            st.session_state.user_name = user["Name"]
            st.session_state.is_first_login = user["Is_First_Login"]
            st.session_state.is_admin = bool(user.get("Is_Admin", False))
            st.rerun()

# -------------------------------------------------
# Login / Register UI
# -------------------------------------------------
def login_register():
    import utils
    utils.inject_custom_css()
    
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 25px;">
            <svg width="110" height="110" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="50" cy="50" r="45" stroke="url(#paint0_linear)" stroke-width="4.5" stroke-dasharray="280" stroke-dashoffset="40" style="transform-origin: center; animation: spin 20s linear infinite;"/>
                <path d="M28 65 L44 48 L56 57 L74 35" stroke="url(#paint1_linear)" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="74" cy="35" r="4" fill="#ec4899"/>
                <defs>
                    <linearGradient id="paint0_linear" x1="5" y1="5" x2="95" y2="95" gradientUnits="userSpaceOnUse">
                        <stop stop-color="#3b82f6"/>
                        <stop offset="0.5" stop-color="#8b5cf6"/>
                        <stop offset="1" stop-color="#ec4899"/>
                    </linearGradient>
                    <linearGradient id="paint1_linear" x1="28" y1="65" x2="74" y2="35" gradientUnits="userSpaceOnUse">
                        <stop stop-color="#3b82f6"/>
                        <stop offset="1" stop-color="#ec4899"/>
                    </linearGradient>
                </defs>
            </svg>
            <h1 style="
                font-family: 'Space Grotesk', sans-serif;
                background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 2.2rem;
                font-weight: 700;
                margin-top: 15px;
                letter-spacing: -1px;
            ">EQUITY INTEL</h1>
            <p style="font-family: 'Outfit', sans-serif; opacity: 0.75; font-size: 0.95rem; margin-top:-5px;">
                Institutional Equity Research Portal & Database Manager
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    tab1, tab2 = st.tabs(["🔐 Analyst Login", "📝 Register Request"])

    # ---------- Login ----------
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="analyst@firm.com")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login to Terminal", type="primary")
            if submit:
                if email and password:
                    success, data = auth_manager.verify_login(email, password)
                    if success:
                        # ---- set session state ----
                        st.session_state.authenticated = True
                        st.session_state.user_email   = data["Email"]
                        st.session_state.user_name    = data["Name"]
                        st.session_state.is_first_login = data["Is_First_Login"]
                        st.session_state.is_admin      = bool(data.get("Is_Admin", False))

                        # ---- persist via cookie with 24h expire limit ----
                        cookies.set("user_email", data["Email"], max_age=86400, same_site="none", secure=True)

                        st.rerun()
                    else:
                        st.error(data)
                else:
                    st.warning("Please enter both email and password.")

    # ---------- Register ----------
    with tab2:
        st.subheader("New User Registration")
        with st.form("register_form"):
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            new_password_confirm = st.text_input("Confirm Password", type="password")
            reg_submit = st.form_submit_button("Register Now")
            if reg_submit:
                if new_name and new_email and new_password:
                    if new_password == new_password_confirm:
                        success, msg = auth_manager.register_user(
                            new_name, new_email, new_password
                        )
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.error("Passwords do not match!")
                else:
                    st.warning("Please fill in all fields.")

# -------------------------------------------------
# Force password reset on first login
# -------------------------------------------------
def force_password_reset():
    st.title("⚠️ First‑time Login: Password Reset Required")
    st.warning(
        "Since this is your first time logging in, you must change your default password."
    )
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

# -------------------------------------------------
# Logout – clear session + cookie
# -------------------------------------------------
def logout():
    st.session_state.authenticated = False
    st.session_state.user_email = ""
    st.session_state.user_name = ""
    st.session_state.is_first_login = False
    st.session_state.is_admin = False
    cookies.remove("user_email")      # clear persisted cookie
    time.sleep(0.2)
    st.rerun()

# -------------------------------------------------
# Main routing
# -------------------------------------------------
if not st.session_state.authenticated:
    # Show login / register page
    login_page = st.Page(login_register, title="Login / Register", icon="🔐")
    pg = st.navigation([login_page])
    pg.run()
elif st.session_state.is_first_login:
    # Force password change
    reset_page = st.Page(force_password_reset, title="Reset Password", icon="⚠️")
    pg = st.navigation([reset_page])
    with st.sidebar:
        st.markdown(f"**Logged in as:** {st.session_state.user_name}")
        st.button("Logout", on_click=logout, type="primary")
    pg.run()
else:
    # Normal app pages
    if hasattr(auth_manager, 'update_user_activity'):
        auth_manager.update_user_activity(st.session_state.user_email)
    pages = {
        "Dashboard": [
            st.Page("pages/dashboard.py", title="Dashboard", icon="📊", default=True),
            st.Page("pages/list_companies.py", title="Company List", icon="🏢"),
        ],
        "Details": [
            st.Page("pages/company_profile.py", title="Company Profile", icon="🔍")
        ],
    }

    # Admin panel only for administrators
    if st.session_state.get("is_admin", False):
        pages["Admin Tools"] = [
            st.Page("pages/admin_panel.py", title="Admin Panel", icon="⚙️")
        ]

    pg = st.navigation(pages)

    with st.sidebar:
        st.markdown(f"**Logged in as:** {st.session_state.user_name}")
        st.button("Logout", on_click=logout, type="primary")

    pg.run()
