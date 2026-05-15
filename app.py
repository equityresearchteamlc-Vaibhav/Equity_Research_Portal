import streamlit as st

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

def login():
    st.title("🔐 Equity Research Team Login")
    st.markdown("Please enter your team email to access the portal.")
    
    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="analyst@firm.com")
        submit = st.form_submit_button("Login")
        
        if submit:
            # Simple mock authentication logic. 
            # Replace with an actual check against a list of authorized emails if needed.
            if email and "@" in email:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("Please enter a valid email address.")

def logout():
    st.session_state.authenticated = False
    st.session_state.user_email = ""
    st.rerun()

# --- Main Routing ---
if not st.session_state.authenticated:
    login()
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
    
    pg = st.navigation(pages)
    
    with st.sidebar:
        st.markdown(f"**Logged in as:** {st.session_state.user_email}")
        st.button("Logout", on_click=logout)
    
    pg.run()
