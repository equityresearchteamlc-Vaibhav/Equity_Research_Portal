import streamlit as st
import auth_manager
import time
from streamlit_cookies_controller import CookieController

# -------------------------------------------------
# Initialise cookie manager (once per session)
# -------------------------------------------------
# Initialize cookie manager on every run to maintain React tree correctly
cookies = CookieController()

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
if "cookie_checked" not in st.session_state:
    st.session_state.cookie_checked = False

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
            st.session_state.cookie_checked = True
            st.rerun()
        else:
            # Cookie exists but user not found or not approved -> clear it
            cookies.remove("user_email", path="/")
            st.session_state.cookie_checked = True
            st.rerun()
    else:
        # If we haven't checked/initialized the cookie component yet, we show a loader
        # and let the component mount and send cookies. This prevents the "login flash" 
        # and page redirect.
        if not st.session_state.cookie_checked:
            st.session_state.cookie_checked = True
            st.markdown(
                """
                <div style="
                    display: flex; 
                    flex-direction: column; 
                    justify-content: center; 
                    align-items: center; 
                    height: 80vh;
                    background: transparent;
                ">
                    <div style="
                        width: 75px;
                        height: 75px;
                        border: 4px solid rgba(255, 255, 255, 0.03);
                        border-top: 4px solid #3b82f6;
                        border-right: 4px solid #8b5cf6;
                        border-bottom: 4px solid #ec4899;
                        border-radius: 50%;
                        animation: spin 1.0s cubic-bezier(0.68, -0.55, 0.27, 1.55) infinite;
                        box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
                        position: relative;
                    "></div>
                    <style>
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                        @keyframes pulse {
                            0%, 100% { opacity: 0.6; transform: scale(0.98); }
                            50% { opacity: 1; transform: scale(1.02); }
                        }
                    </style>
                    <p style="
                        font-family: 'Space Grotesk', 'Outfit', sans-serif; 
                        margin-top: 30px; 
                        font-weight: 600;
                        font-size: 1rem;
                        letter-spacing: 0.5px;
                        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        animation: pulse 1.5s ease-in-out infinite;
                    ">
                        Hang On! We Are Loading Your Page
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            # We must stop execution here to let the cookie controller load and trigger rerun.
            st.stop()

# -------------------------------------------------
# Login / Register UI
# -------------------------------------------------
def login_register():
    import utils
    utils.inject_custom_css()
    
    # Additional CSS for login page specifically
    st.markdown(
        """
        <style>
            /* Force dark background on login page */
            .stApp {
                background: linear-gradient(135deg, #0a0e1a 0%, #111827 50%, #0f1419 100%) !important;
            }
            
            /* Ensure form containers are visible */
            section[data-testid="stSidebar"] {
                display: none !important;
            }
            
            /* Center the login content */
            .main .block-container {
                max-width: 600px !important;
                padding-top: 3rem !important;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-10px); }
            }
            @keyframes rotate {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            @keyframes glow {
                0%, 100% { filter: drop-shadow(0 0 10px rgba(139, 92, 246, 0.4)); }
                50% { filter: drop-shadow(0 0 20px rgba(59, 130, 246, 0.6)); }
            }
        </style>
        <div style="text-align: center; margin-bottom: 35px; margin-top: 20px;">
            <div style="animation: float 3s ease-in-out infinite;">
                <svg width="120" height="120" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="animation: glow 2s ease-in-out infinite;">
                    <!-- Outer rotating ring -->
                    <circle cx="50" cy="50" r="45" stroke="url(#paint0_linear)" stroke-width="3" stroke-dasharray="280" stroke-dashoffset="40" style="transform-origin: center; animation: rotate 20s linear infinite;"/>
                    
                    <!-- Inner glow circle -->
                    <circle cx="50" cy="50" r="38" stroke="url(#paint2_radial)" stroke-width="1.5" opacity="0.3"/>
                    
                    <!-- Chart line with gradient -->
                    <path d="M28 65 L44 48 L56 57 L74 35" stroke="url(#paint1_linear)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
                    
                    <!-- Data points -->
                    <circle cx="28" cy="65" r="3" fill="#3b82f6"/>
                    <circle cx="44" cy="48" r="3" fill="#8b5cf6"/>
                    <circle cx="56" cy="57" r="3" fill="#a78bfa"/>
                    <circle cx="74" cy="35" r="4" fill="#ec4899">
                        <animate attributeName="r" values="4;5;4" dur="1.5s" repeatCount="indefinite"/>
                    </circle>
                    
                    <!-- Gradient definitions -->
                    <defs>
                        <linearGradient id="paint0_linear" x1="5" y1="5" x2="95" y2="95" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#3b82f6"/>
                            <stop offset="0.5" stop-color="#8b5cf6"/>
                            <stop offset="1" stop-color="#ec4899"/>
                        </linearGradient>
                        <linearGradient id="paint1_linear" x1="28" y1="65" x2="74" y2="35" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#3b82f6"/>
                            <stop offset="0.5" stop-color="#8b5cf6"/>
                            <stop offset="1" stop-color="#ec4899"/>
                        </linearGradient>
                        <radialGradient id="paint2_radial" cx="50%" cy="50%">
                            <stop offset="0%" stop-color="#8b5cf6" stop-opacity="0.8"/>
                            <stop offset="100%" stop-color="#3b82f6" stop-opacity="0"/>
                        </radialGradient>
                    </defs>
                </svg>
            </div>
            <h1 style="
                font-family: 'Inter', 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 2.5rem;
                font-weight: 800;
                margin-top: 20px;
                letter-spacing: -1.5px;
            ">EQUITY INTEL</h1>
            <p style="
                font-family: 'Inter', 'Segoe UI', sans-serif; 
                color: rgba(249, 250, 251, 0.6); 
                font-size: 0.95rem; 
                margin-top: 8px;
                font-weight: 500;
                letter-spacing: 0.5px;
            ">
                Institutional Equity Research Portal & Database Manager
            </p>
            <div style="
                width: 60px;
                height: 3px;
                background: linear-gradient(90deg, transparent, #8b5cf6, transparent);
                margin: 20px auto 0;
                border-radius: 2px;
            "></div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Additional styling for login/register forms
    st.markdown(
        """
        <style>
            /* Style the tabs */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
                background: rgba(17, 24, 39, 0.4);
                padding: 8px;
                border-radius: 12px;
                margin-bottom: 24px;
            }
            
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                background: transparent;
                border-radius: 8px;
                color: rgba(249, 250, 251, 0.6);
                font-weight: 600;
                font-size: 0.95rem;
            }
            
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2)) !important;
                color: #f9fafb !important;
            }
            
            /* Style input fields on login page */
            .stTextInput > div > div > input {
                background: rgba(17, 24, 39, 0.6) !important;
                border: 1px solid rgba(99, 102, 241, 0.3) !important;
                color: #f9fafb !important;
                font-size: 0.95rem !important;
                padding: 12px !important;
            }
            
            .stTextInput > div > div > input:focus {
                border-color: rgba(139, 92, 246, 0.6) !important;
                box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1) !important;
            }
            
            /* Style labels */
            .stTextInput > label, .stForm label {
                color: rgba(249, 250, 251, 0.8) !important;
                font-weight: 600 !important;
                font-size: 0.9rem !important;
                margin-bottom: 8px !important;
            }
            
            /* Form submit button full width */
            .stForm button[type="submit"] {
                width: 100% !important;
                margin-top: 16px !important;
                padding: 12px !important;
                font-size: 1rem !important;
            }
            
            /* Subheader styling */
            .stForm h3 {
                color: #f9fafb !important;
                font-weight: 700 !important;
                margin-bottom: 20px !important;
            }
        </style>
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
                        cookies.set("user_email", data["Email"], max_age=86400, path="/")

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
    cookies.remove("user_email", path="/")      # clear persisted cookie

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
