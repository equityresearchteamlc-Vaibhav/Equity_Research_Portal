"""
utils.py – Shared helpers for Equity Research Portal
  • is_market_open()  → True/False based on NSE trading hours (Mon–Fri, 09:15–15:30 IST)
  • render_status_bar()  → renders the last-refreshed / next-update / market-status banner
  • inject_custom_css() → injects dark theme CSS with performance optimizations
  • optimize_dataframe() → optimizes dataframe memory usage
"""

import datetime
import pytz
import streamlit as st
import pandas as pd

# NSE market hours in IST
_IST = pytz.timezone("Asia/Kolkata")
_MARKET_OPEN  = datetime.time(9, 15)
_MARKET_CLOSE = datetime.time(15, 30)

# NSE public holidays 2026 (Official List)
_NSE_HOLIDAYS = {
    datetime.date(2026, 1, 15),   # Municipal Corporation Election – Maharashtra
    datetime.date(2026, 1, 26),   # Republic Day
    datetime.date(2026, 3, 3),    # Holi
    datetime.date(2026, 3, 26),   # Shri Ram Navami
    datetime.date(2026, 3, 31),   # Shri Mahavir Jayanti
    datetime.date(2026, 4, 3),    # Good Friday
    datetime.date(2026, 4, 14),   # Dr. Baba Saheb Ambedkar Jayanti
    datetime.date(2026, 5, 1),    # Maharashtra Day
    datetime.date(2026, 5, 28),   # Bakri Id / Eid ul-Adha (Today!)
    datetime.date(2026, 6, 26),   # Muharram
    datetime.date(2026, 9, 14),   # Ganesh Chaturthi
    datetime.date(2026, 10, 2),   # Gandhi Jayanti
    datetime.date(2026, 10, 20),  # Dussehra
    datetime.date(2026, 11, 10),  # Diwali Balipratipada
    datetime.date(2026, 11, 24),  # Guru Nanak Jayanti
    datetime.date(2026, 12, 25),  # Christmas
}


def is_market_open() -> bool:
    """Return True if NSE equity market is currently open."""
    now_ist = datetime.datetime.now(_IST)
    today   = now_ist.date()
    now_t   = now_ist.time()

    # Weekend
    if now_ist.weekday() >= 5:
        return False
    # NSE holiday
    if today in _NSE_HOLIDAYS:
        return False
    # Trading window
    return _MARKET_OPEN <= now_t <= _MARKET_CLOSE


def render_status_bar(refresh_interval_secs: int = 300):
    """
    Render a compact status bar showing:
      • 🟢/🔴 Market open/closed
      • Last refreshed timestamp
      • Next auto-refresh countdown
    """
    now_ist  = datetime.datetime.now(_IST)
    next_refresh = now_ist + datetime.timedelta(seconds=refresh_interval_secs)

    market_open = is_market_open()
    signal_emoji = "🟢" if market_open else "🔴"
    signal_text  = "Market Open" if market_open else "Market Closed"
    signal_color = "#10b981" if market_open else "#ef4444"

    last_str = now_ist.strftime("%d %b %Y, %I:%M:%S %p IST")
    next_str = next_refresh.strftime("%I:%M:%S %p IST")

    st.markdown(
        f"""
        <div class="custom-status-bar" style="
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: center;
            gap: 20px;
            padding: 12px 20px;
            border-radius: 12px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            font-size: 0.875rem;
            margin-bottom: 20px;
        ">
            <span style="
                color: {signal_color}; 
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 8px;
                text-shadow: 0 0 10px {signal_color}40;
            ">
                <span style="-webkit-text-fill-color: initial; text-fill-color: initial; display: inline-block;">{signal_emoji}</span>
                {signal_text}
            </span>
            <span class="custom-status-bar-text" style="
                display: flex;
                align-items: center;
                gap: 6px;
            ">
                <span style="-webkit-text-fill-color: initial; text-fill-color: initial; font-style: normal; display: inline-block;">🕐</span> Last refreshed: <strong class="custom-status-bar-strong">{last_str}</strong>
            </span>
            <span class="custom-status-bar-text" style="
                display: flex;
                align-items: center;
                gap: 6px;
            ">
                <span style="-webkit-text-fill-color: initial; text-fill-color: initial; font-style: normal; display: inline-block;">⏱️</span> Next update: <strong class="custom-status-bar-strong">{next_str}</strong>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


BASE_CSS = """
            /* ============================================ */
            /* PERFORMANCE OPTIMIZATIONS */
            /* ============================================ */
            * {
                will-change: auto !important;
            }
            
            /* Reduce repaints */
            img, video {
                image-rendering: -webkit-optimize-contrast !important;
            }
            
            /* Ensure main content containers are transparent so stApp background always shines through */
            [data-testid="stAppViewContainer"], .main, [data-testid="stMainBlockContainer"] {
                background-color: transparent !important;
                background: transparent !important;
            }
            
            /* Global Font Family & Emoji Support */
            html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp {
                font-family: 'Calibri', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol" !important;
            }
            
            [data-testid="stDecoration"] {
                display: none !important;
            }
            
            /* Make header background transparent so it integrates beautifully */
            header, [data-testid="stHeader"] {
                background: transparent !important;
                background-color: transparent !important;
            }
            
            /* Hide Streamlit deploy button, connection status, and options menu to keep a clean interface */
            [data-testid="stAppDeployButton"], 
            [data-testid="stConnectionStatus"], 
            #connection-status, 
            [data-testid="stMainMenu"] {
                display: none !important;
                visibility: hidden !important;
                width: 0px !important;
            }
            
            /* Hide Streamlit footer, watermark, and host/viewer badges */
            footer, [data-testid="stViewerBadge"], .viewerBadge, .styles_viewerBadge__, [class*="viewerBadge"], [class*="styles_viewerBadge"] {
                display: none !important;
                visibility: hidden !important;
                height: 0px !important;
            }
            
            /* Adjust top padding since header is hidden */
            .main .block-container, [data-testid="stMainBlockContainer"] {
                padding-top: 1.25rem !important;
            }
            
            /* ============================================ */
            /* DIVIDERS */
            /* ============================================ */
            hr {
                border: none !important;
                height: 1px !important;
                margin: 2rem 0 !important;
            }
            
            /* ============================================ */
            /* ANIMATIONS */
            /* ============================================ */
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 0.6; transform: scale(0.98); }
                50% { opacity: 1; transform: scale(1.02); }
            }
            
            @keyframes fastPageTransition {
                from { opacity: 0; transform: translateY(10px) scale(0.99); }
                to { opacity: 1; transform: translateY(0) scale(1); }
            }
            
            /* Apply ultra-fast, snappy transition to the main content area AND individual elements so it triggers on page switch */
            .main .block-container, [data-testid="stMainBlockContainer"] {
                animation: fastPageTransition 0.2s cubic-bezier(0.1, 0.9, 0.2, 1) forwards !important;
            }
            
            /* This ensures elements that are dynamically swapped also animate in fast */
            [data-testid="element-container"], [data-testid="stVerticalBlock"] > div {
                animation: fastPageTransition 0.25s cubic-bezier(0.1, 0.9, 0.2, 1) forwards !important;
            }
            
            /* ============================================ */
            /* SCROLLBAR */
            /* ============================================ */
            ::-webkit-scrollbar {
                width: 10px !important;
                height: 10px !important;
            }
            
            ::-webkit-scrollbar-track {
                background: rgba(17, 24, 39, 0.5) !important;
            }
            
            ::-webkit-scrollbar-thumb {
                background: linear-gradient(180deg, #3b82f6, #8b5cf6) !important;
                border-radius: 5px !important;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(180deg, #2563eb, #7c3aed) !important;
            }
"""

DARK_CSS = """
            /* ============================================ */
            /* DARK THEME BASE */
            /* ============================================ */
            :root, .stApp, [data-testid="stDataFrame"], [data-testid="stDataFrameResizable"] {
                --primary-bg: #0f1419;
                --secondary-bg: #1a1f2e;
                --card-bg: rgba(26, 31, 46, 0.6);
                --border-color: rgba(99, 102, 241, 0.15);
                --text-primary: #f9fafb;
                --text-secondary: rgba(249, 250, 251, 0.7);
                --accent-blue: #3b82f6;
                --accent-purple: #8b5cf6;
                --accent-pink: #ec4899;
                --success: #10b981;
                --danger: #ef4444;
                
                /* Override Streamlit's theme variables to force dark mode globally */
                --text-color: #f9fafb !important;
                --background-color: #0f1419 !important;
                --secondary-background-color: #1a1f2e !important;
                --primary-color: #8b5cf6 !important;
                --faded-text-60: rgba(249, 250, 251, 0.6) !important;
                --faded-text-40: rgba(249, 250, 251, 0.4) !important;

                /* Streamlit CamelCase variables to force dark mode on Glide Data Grid / Canvas */
                --theme-backgroundColor: #0f1419 !important;
                --theme-secondaryBackgroundColor: #1a1f2e !important;
                --theme-textColor: #f9fafb !important;
                --theme-primaryColor: #8b5cf6 !important;
                --theme-fadedText60: rgba(249, 250, 251, 0.6) !important;
                --theme-fadedText40: rgba(249, 250, 251, 0.4) !important;
            }
            
            /* Force dialogs/modals to have a dark background and white text */
            div[data-testid="stDialog"] [role="dialog"] {
                background-color: #1a1f2e !important;
                border: 1px solid rgba(99, 102, 241, 0.3) !important;
            }
            div[data-testid="stDialog"] [role="dialog"] * {
                color: #f9fafb !important;
            }
            
            /* Force light text color globally on key containers for readability */
            h1, h2, h3, h4, h5, h6, label, [data-testid="stWidgetLabel"] p, .stMarkdown p, .stMarkdown li, [data-testid="stSidebarNavLink"] span, [data-testid="stSidebarNavLink"] p {
                color: rgba(249, 250, 251, 0.95) !important;
            }
            
            /* Active sidebar navigation link text color */
            [data-testid="stSidebarNavLink"][aria-current="page"] span, [data-testid="stSidebarNavLink"][aria-current="page"] p {
                color: #ffffff !important;
                font-weight: 700 !important;
            }
            
            /* Dropdowns and select inputs styling for readability */
            div[data-baseweb="menu"] *, [data-testid="stVirtualDropdown"] *, [data-baseweb="select"] * {
                color: #ffffff !important;
            }
            
            /* Force text input containers to have a dark background and white text */
            div[data-baseweb="input"] {
                background-color: rgba(17, 24, 39, 0.85) !important;
                border: 1px solid rgba(99, 102, 241, 0.3) !important;
                border-radius: 8px !important;
            }
            div[data-baseweb="input"] * {
                color: #ffffff !important;
            }
            
            /* Force selectboxes to have a dark background in all themes for readability */
            div[data-baseweb="select"] > div {
                background-color: rgba(17, 24, 39, 0.9) !important;
                border: 1px solid rgba(99, 102, 241, 0.3) !important;
            }
            
            /* Force dropdown dropdown-menus to have a dark background in all themes */
            div[data-baseweb="menu"] {
                background-color: #1a1f2e !important;
                border: 1px solid rgba(99, 102, 241, 0.3) !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
            }
            
            /* Main app background with subtle gradient */
            .stApp {
                background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #141923 100%) !important;
                background-attachment: fixed !important;
                transition: background 0.5s ease-in-out !important;
            }
            
            /* ANIMATED BACKGROUND PARTICLES */
            .stApp::before {
                content: "" !important;
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100% !important;
                height: 100% !important;
                background-image: 
                    radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.05) 0%, transparent 50%),
                    radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.05) 0%, transparent 50%),
                    radial-gradient(circle at 40% 80%, rgba(236, 72, 153, 0.03) 0%, transparent 50%) !important;
                pointer-events: none !important;
                z-index: 0 !important;
                animation: backgroundShift 20s ease-in-out infinite !important;
            }
            
            @keyframes backgroundShift {
                0%, 100% { opacity: 0.3; transform: scale(1); }
                50% { opacity: 0.5; transform: scale(1.05); }
            }
            
            /* ============================================ */
            /* METRIC CARDS - GLASSMORPHISM */
            /* ============================================ */
            div[data-testid="stMetric"] {
                background: linear-gradient(135deg, rgba(17, 24, 39, 0.8) 0%, rgba(31, 41, 55, 0.6) 100%) !important;
                border: 1px solid rgba(99, 102, 241, 0.2) !important;
                border-radius: 16px !important;
                padding: 18px 20px !important;
                backdrop-filter: blur(10px) !important;
                -webkit-backdrop-filter: blur(10px) !important;
                box-shadow: 
                    0 4px 24px rgba(0, 0, 0, 0.4),
                    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                position: relative !important;
                overflow: hidden !important;
                min-height: 135px !important;
            }
            
            /* Hover glow effect */
            div[data-testid="stMetric"]::before {
                content: "" !important;
                position: absolute !important;
                top: -50% !important;
                left: -50% !important;
                width: 200% !important;
                height: 200% !important;
                background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%) !important;
                opacity: 0 !important;
                transition: opacity 0.3s ease !important;
            }
            
            div[data-testid="stMetric"]:hover::before {
                opacity: 1 !important;
            }
            
            div[data-testid="stMetric"]:hover {
                transform: translateY(-4px) scale(1.02) !important;
                border-color: rgba(99, 102, 241, 0.4) !important;
                box-shadow: 
                    0 8px 32px rgba(59, 130, 246, 0.2),
                    0 0 0 1px rgba(99, 102, 241, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
            }
            
            /* Premium Bordered Containers (Used for single metric + action card) */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: linear-gradient(135deg, rgba(17, 24, 39, 0.8) 0%, rgba(31, 41, 55, 0.6) 100%) !important;
                border: 1px solid rgba(99, 102, 241, 0.2) !important;
                border-radius: 16px !important;
                padding: 16px !important;
                backdrop-filter: blur(10px) !important;
                -webkit-backdrop-filter: blur(10px) !important;
                box-shadow: 
                    0 4px 24px rgba(0, 0, 0, 0.4),
                    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            }
            
            div[data-testid="stVerticalBlockBorderWrapper"]:hover {
                transform: translateY(-4px) scale(1.02) !important;
                border-color: rgba(99, 102, 241, 0.4) !important;
                box-shadow: 
                    0 8px 32px rgba(59, 130, 246, 0.2),
                    0 0 0 1px rgba(99, 102, 241, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
            }
            
            /* Make nested metrics blend seamlessly within the bordered container */
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stMetric"] {
                background: transparent !important;
                border: none !important;
                padding: 0 !important;
                box-shadow: none !important;
                min-height: auto !important;
                backdrop-filter: none !important;
                -webkit-backdrop-filter: none !important;
            }
            
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stMetricValue"] {
                margin-bottom: 8px !important;
            }
            
            div[data-testid="stMetricValue"] {
                font-size: 1.4rem !important;
                font-weight: 700 !important;
                background: linear-gradient(135deg, #f9fafb 0%, #e5e7eb 100%) !important;
                -webkit-background-clip: text !important;
                -webkit-text-fill-color: transparent !important;
                margin-top: 4px !important;
                letter-spacing: -0.5px !important;
                white-space: normal !important;
                word-wrap: break-word !important;
                overflow: visible !important;
                line-height: 1.3 !important;
            }
            
            div[data-testid="stMetricLabel"] {
                font-size: 0.875rem !important;
                font-weight: 600 !important;
                color: rgba(249, 250, 251, 0.6) !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
                white-space: normal !important;
                overflow: visible !important;
                text-overflow: clip !important;
            }
            div[data-testid="stMetricLabel"] * {
                white-space: normal !important;
                word-wrap: break-word !important;
                overflow: visible !important;
                text-overflow: clip !important;
            }
            
            /* Positive delta - green glow */
            div[data-testid="stMetricDelta"] > div[data-testid="stMetricDeltaIcon-Up"] {
                color: #10b981 !important;
            }
            
            div[data-testid="stMetricDelta"] > div:has(div[data-testid="stMetricDeltaIcon-Up"]) {
                color: #10b981 !important;
                text-shadow: 0 0 8px rgba(16, 185, 129, 0.3) !important;
            }
            
            /* Negative delta - red glow */
            div[data-testid="stMetricDelta"] > div[data-testid="stMetricDeltaIcon-Down"] {
                color: #ef4444 !important;
            }
            
            div[data-testid="stMetricDelta"] > div:has(div[data-testid="stMetricDeltaIcon-Down"]) {
                color: #ef4444 !important;
                text-shadow: 0 0 8px rgba(239, 68, 68, 0.3) !important;
            }
            
            /* ============================================ */
            /* BUTTONS - MODERN GRADIENT */
            /* ============================================ */
            button[kind="primary"] {
                background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%) !important;
                background-size: 200% 200% !important;
                border: none !important;
                color: white !important;
                font-weight: 600 !important;
                border-radius: 10px !important;
                padding: 0.6rem 1.5rem !important;
                box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3) !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                position: relative !important;
                overflow: hidden !important;
            }
            
            button[kind="primary"]::before {
                content: "" !important;
                position: absolute !important;
                top: 50% !important;
                left: 50% !important;
                width: 0 !important;
                height: 0 !important;
                border-radius: 50% !important;
                background: rgba(255, 255, 255, 0.2) !important;
                transform: translate(-50%, -50%) !important;
                transition: width 0.6s, height 0.6s !important;
            }
            
            button[kind="primary"]:hover::before {
                width: 300px !important;
                height: 300px !important;
            }
            
            button[kind="primary"]:hover {
                background-position: 100% 0 !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4) !important;
            }
            
            button[kind="primary"]:disabled {
                background: linear-gradient(135deg, rgba(59, 130, 246, 0.35) 0%, rgba(139, 92, 246, 0.35) 50%, rgba(236, 72, 153, 0.35) 100%) !important;
                color: rgba(255, 255, 255, 0.4) !important;
                border: none !important;
                box-shadow: none !important;
                cursor: not-allowed !important;
            }
            
            button[kind="secondary"] {
                background: rgba(17, 24, 39, 0.8) !important;
                border: 1px solid rgba(99, 102, 241, 0.3) !important;
                color: #f9fafb !important;
                border-radius: 10px !important;
                transition: all 0.3s ease !important;
            }
            
            button[kind="secondary"]:hover {
                background: rgba(31, 41, 55, 0.9) !important;
                border-color: rgba(99, 102, 241, 0.5) !important;
                transform: translateY(-1px) !important;
            }
            
            /* ============================================ */
            /* FORMS - GLASSMORPHISM */
            /* ============================================ */
            div[data-testid="stForm"] {
                background: linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%) !important;
                border: 1px solid rgba(99, 102, 241, 0.2) !important;
                border-radius: 20px !important;
                padding: 2rem !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
                box-shadow: 
                    0 8px 32px rgba(0, 0, 0, 0.4),
                    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
            }
            
            /* Input fields */
            input, textarea, select {
                background: rgba(17, 24, 39, 0.8) !important;
                border: 1px solid rgba(99, 102, 241, 0.2) !important;
                border-radius: 8px !important;
                color: #f9fafb !important;
                transition: all 0.3s ease !important;
            }
            
            input:focus, textarea:focus, select:focus {
                border-color: rgba(99, 102, 241, 0.5) !important;
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
                outline: none !important;
            }
            
            /* Force number inputs +/- buttons to be dark */
            div[data-testid="stNumberInput"] button {
                background-color: rgba(31, 41, 55, 0.8) !important;
                color: #f9fafb !important;
                border-color: rgba(99, 102, 241, 0.3) !important;
            }
            
            /* Force date inputs wrapper to be dark */
            div[data-testid="stDateInput"] > div {
                background-color: rgba(17, 24, 39, 0.8) !important;
                border-color: rgba(99, 102, 241, 0.3) !important;
            }
            
            /* Force file uploader section to be dark mode styled */
            div[data-testid="stFileUploader"] > section {
                background-color: rgba(17, 24, 39, 0.8) !important;
                border: 1px dashed rgba(99, 102, 241, 0.4) !important;
            }
            div[data-testid="stFileUploader"] * {
                color: #f9fafb !important;
            }
            
            /* Force slider track and thumbs to have dark theme colors */
            div[data-testid="stSlider"] [role="slider"] {
                background-color: #8b5cf6 !important;
            }
            div[data-testid="stSlider"] > div > div {
                background-color: rgba(99, 102, 241, 0.3) !important;
            }
            
            /* ============================================ */
            /* DATAFRAME - DARK THEME */
            /* ============================================ */
            div[data-testid="stDataFrame"] {
                background: rgba(17, 24, 39, 0.6) !important;
                border: 1px solid rgba(99, 102, 241, 0.15) !important;
                border-radius: 12px !important;
                overflow: hidden !important;
            }
            div[data-testid="stDataFrame"] * {
                color: #ffffff !important;
            }
            
            /* Table headers */
            .stDataFrame thead tr th {
                background: linear-gradient(135deg, rgba(31, 41, 55, 0.9) 0%, rgba(17, 24, 39, 0.9) 100%) !important;
                color: #f9fafb !important;
                font-weight: 600 !important;
                border-bottom: 2px solid rgba(99, 102, 241, 0.3) !important;
            }
            
            /* Table rows */
            .stDataFrame tbody tr {
                background: rgba(17, 24, 39, 0.4) !important;
                transition: background 0.2s ease !important;
            }
            
            .stDataFrame tbody tr:hover {
                background: rgba(31, 41, 55, 0.6) !important;
            }
            
            /* ============================================ */
            /* SIDEBAR - PREMIUM DARK */
            /* ============================================ */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0f1419 0%, #111827 100%) !important;
                border-right: 1px solid rgba(99, 102, 241, 0.15) !important;
                box-shadow: 4px 0 24px rgba(0, 0, 0, 0.5) !important;
                transition: background 0.5s ease-in-out !important;
            }
            
            section[data-testid="stSidebar"] > div {
                background: transparent !important;
            }
            
            /* ============================================ */
            /* TABS */
            /* ============================================ */
            button[data-baseweb="tab"] {
                background: transparent !important;
                border-bottom: 2px solid transparent !important;
                color: rgba(249, 250, 251, 0.85) !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
            }
            
            button[data-baseweb="tab"]:hover {
                color: rgba(249, 250, 251, 0.9) !important;
                border-bottom-color: rgba(99, 102, 241, 0.5) !important;
            }
            
            button[data-baseweb="tab"][aria-selected="true"] {
                color: #f9fafb !important;
                border-bottom-color: #6366f1 !important;
                background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.1)) !important;
            }
            
            hr {
                background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.3), transparent) !important;
            }
            
            /* Status Bar - Dark */
            .custom-status-bar {
                background: linear-gradient(135deg, rgba(17, 24, 39, 0.8) 0%, rgba(31, 41, 55, 0.6) 100%) !important;
                border: 1px solid rgba(99, 102, 241, 0.2) !important;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
            }
            .custom-status-bar-text {
                color: rgba(249, 250, 251, 0.85) !important;
            }
            .custom-status-bar-strong {
                color: #f9fafb !important;
            }
            
            /* Page Subtitle - Dark */
            .custom-page-subtitle {
                color: rgba(249, 250, 251, 0.6) !important;
            }
"""

LIGHT_CSS = """
            /* ============================================ */
            /* LIGHT THEME BASE */
            /* ============================================ */
            .stApp {
                background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 50%, #d1d5db 100%) !important;
                background-attachment: fixed !important;
                transition: background 0.5s ease-in-out !important;
            }
            
            /* Force light-theme dark text color globally for readability */
            h1, h2, h3, h4, h5, h6, label, [data-testid="stWidgetLabel"] p, .stMarkdown p, .stMarkdown li, [data-testid="stSidebarNavLink"] span, [data-testid="stSidebarNavLink"] p {
                color: #1f2937 !important;
            }
            
            /* Active sidebar navigation link text color */
            [data-testid="stSidebarNavLink"][aria-current="page"] span, [data-testid="stSidebarNavLink"][aria-current="page"] p {
                color: #111827 !important;
                font-weight: 700 !important;
            }
            
            /* Dropdowns and select inputs styling for readability in light mode */
            div[data-baseweb="menu"] *, [data-testid="stVirtualDropdown"] *, [data-baseweb="select"] * {
                color: #1f2937 !important;
            }
            
            /* Force text input containers to have a light background and dark text */
            div[data-baseweb="input"] {
                background-color: #ffffff !important;
                border: 1px solid rgba(0, 0, 0, 0.15) !important;
                border-radius: 8px !important;
            }
            div[data-baseweb="input"] * {
                color: #1f2937 !important;
            }
            
            /* Force selectboxes to have a light background in light theme */
            div[data-baseweb="select"] > div {
                background-color: #ffffff !important;
                border: 1px solid rgba(0, 0, 0, 0.15) !important;
            }
            
            /* Force dropdown menus to have a light background in light theme */
            div[data-baseweb="menu"] {
                background-color: #ffffff !important;
                border: 1px solid rgba(0, 0, 0, 0.1) !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
            }
            
            /* ============================================ */
            /* METRIC CARDS - LIGHT GLASSMORPHISM */
            /* ============================================ */
            div[data-testid="stMetric"] {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.85) 0%, rgba(243, 244, 246, 0.7) 100%) !important;
                border: 1px solid rgba(0, 0, 0, 0.08) !important;
                border-radius: 16px !important;
                padding: 18px 20px !important;
                backdrop-filter: blur(10px) !important;
                -webkit-backdrop-filter: blur(10px) !important;
                box-shadow: 
                    0 4px 20px rgba(0, 0, 0, 0.05),
                    inset 0 1px 0 rgba(255, 255, 255, 0.8) !important;
                min-height: 135px !important;
            }
            
            div[data-testid="stMetric"]:hover {
                transform: translateY(-4px) scale(1.02) !important;
                border-color: rgba(99, 102, 241, 0.3) !important;
                box-shadow: 
                    0 8px 24px rgba(99, 102, 241, 0.1),
                    0 0 0 1px rgba(99, 102, 241, 0.15) !important;
            }
            
            /* Premium Bordered Containers (Used for single metric + action card) */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.85) 0%, rgba(243, 244, 246, 0.7) 100%) !important;
                border: 1px solid rgba(0, 0, 0, 0.08) !important;
                border-radius: 16px !important;
                padding: 16px !important;
                backdrop-filter: blur(10px) !important;
                -webkit-backdrop-filter: blur(10px) !important;
                box-shadow: 
                    0 4px 20px rgba(0, 0, 0, 0.05),
                    inset 0 1px 0 rgba(255, 255, 255, 0.8) !important;
                transition: all 0.3s ease !important;
            }
            
            div[data-testid="stVerticalBlockBorderWrapper"]:hover {
                transform: translateY(-4px) scale(1.02) !important;
                border-color: rgba(99, 102, 241, 0.3) !important;
                box-shadow: 
                    0 8px 24px rgba(99, 102, 241, 0.1),
                    0 0 0 1px rgba(99, 102, 241, 0.15) !important;
            }
            
            /* Make nested metrics blend seamlessly within the bordered container */
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stMetric"] {
                background: transparent !important;
                border: none !important;
                padding: 0 !important;
                box-shadow: none !important;
                min-height: auto !important;
                backdrop-filter: none !important;
                -webkit-backdrop-filter: none !important;
            }
            
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stMetricValue"] {
                margin-bottom: 8px !important;
            }
            
            div[data-testid="stMetricValue"] {
                font-size: 1.4rem !important;
                font-weight: 700 !important;
                color: #111827 !important;
                margin-top: 4px !important;
                letter-spacing: -0.5px !important;
                white-space: normal !important;
                word-wrap: break-word !important;
                overflow: visible !important;
                line-height: 1.3 !important;
            }
            
            div[data-testid="stMetricLabel"] {
                font-size: 0.875rem !important;
                font-weight: 600 !important;
                color: #4b5563 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
                white-space: normal !important;
                overflow: visible !important;
                text-overflow: clip !important;
            }
            div[data-testid="stMetricLabel"] * {
                white-space: normal !important;
                word-wrap: break-word !important;
                overflow: visible !important;
                text-overflow: clip !important;
            }
            
            /* Positive delta - green */
            div[data-testid="stMetricDelta"] > div[data-testid="stMetricDeltaIcon-Up"] {
                color: #10b981 !important;
            }
            div[data-testid="stMetricDelta"] > div:has(div[data-testid="stMetricDeltaIcon-Up"]) {
                color: #10b981 !important;
            }
            
            /* Negative delta - red */
            div[data-testid="stMetricDelta"] > div[data-testid="stMetricDeltaIcon-Down"] {
                color: #ef4444 !important;
            }
            div[data-testid="stMetricDelta"] > div:has(div[data-testid="stMetricDeltaIcon-Down"]) {
                color: #ef4444 !important;
            }
            
            /* ============================================ */
            /* BUTTONS - LIGHT THEME STYLE */
            /* ============================================ */
            button[kind="primary"] {
                background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%) !important;
                background-size: 200% 200% !important;
                border: none !important;
                color: white !important;
                font-weight: 600 !important;
                border-radius: 10px !important;
                padding: 0.6rem 1.5rem !important;
                box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2) !important;
            }
            button[kind="primary"]:hover {
                background-position: 100% 0 !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 8px 24px rgba(139, 92, 246, 0.3) !important;
            }
            button[kind="secondary"] {
                background: #ffffff !important;
                border: 1px solid rgba(0, 0, 0, 0.15) !important;
                color: #1f2937 !important;
                border-radius: 10px !important;
                transition: all 0.3s ease !important;
            }
            button[kind="secondary"]:hover {
                background: #f9fafb !important;
                border-color: rgba(0, 0, 0, 0.25) !important;
                transform: translateY(-1px) !important;
            }
            
            /* ============================================ */
            /* FORMS - LIGHT GLASSMORPHISM */
            /* ============================================ */
            div[data-testid="stForm"] {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(249, 250, 251, 0.6) 100%) !important;
                border: 1px solid rgba(0, 0, 0, 0.08) !important;
                border-radius: 20px !important;
                padding: 2rem !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
                box-shadow: 
                    0 8px 32px rgba(0, 0, 0, 0.05),
                    inset 0 1px 0 rgba(255, 255, 255, 0.8) !important;
            }
            
            /* Input fields */
            input, textarea, select {
                background: #ffffff !important;
                border: 1px solid rgba(0, 0, 0, 0.15) !important;
                border-radius: 8px !important;
                color: #1f2937 !important;
                transition: all 0.3s ease !important;
            }
            input:focus, textarea:focus, select:focus {
                border-color: #3b82f6 !important;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
                outline: none !important;
            }
            
            div[data-testid="stFileUploader"] > section {
                background-color: #f9fafb !important;
                border: 1px dashed rgba(0, 0, 0, 0.15) !important;
            }
            div[data-testid="stFileUploader"] * {
                color: #4b5563 !important;
            }
            div[data-testid="stSlider"] [role="slider"] {
                background-color: #3b82f6 !important;
            }
            div[data-testid="stSlider"] > div > div {
                background-color: rgba(59, 130, 246, 0.2) !important;
            }
            
            /* ============================================ */
            /* DATAFRAME - LIGHT THEME */
            /* ============================================ */
            div[data-testid="stDataFrame"] {
                background: #ffffff !important;
                border: 1px solid rgba(0, 0, 0, 0.08) !important;
                border-radius: 12px !important;
                overflow: hidden !important;
            }
            div[data-testid="stDataFrame"] * {
                color: #1f2937 !important;
            }
            .stDataFrame thead tr th {
                background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%) !important;
                color: #111827 !important;
                font-weight: 600 !important;
                border-bottom: 2px solid rgba(0, 0, 0, 0.1) !important;
            }
            .stDataFrame tbody tr {
                background: #ffffff !important;
                transition: background 0.2s ease !important;
            }
            .stDataFrame tbody tr:hover {
                background: #f3f4f6 !important;
            }
            
            /* ============================================ */
            /* SIDEBAR - LIGHT GRADIENT */
            /* ============================================ */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #ffffff 0%, #f9fafb 100%) !important;
                border-right: 1px solid rgba(0, 0, 0, 0.08) !important;
                box-shadow: 4px 0 24px rgba(0, 0, 0, 0.05) !important;
                transition: background 0.5s ease-in-out !important;
            }
            
            hr {
                background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.1), transparent) !important;
            }
            
            /* ============================================ */
            /* TABS - LIGHT */
            /* ============================================ */
            button[data-baseweb="tab"] {
                background: transparent !important;
                border-bottom: 2px solid transparent !important;
                color: #4b5563 !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
            }
            button[data-baseweb="tab"]:hover {
                color: #111827 !important;
                border-bottom-color: rgba(0, 0, 0, 0.2) !important;
            }
            button[data-baseweb="tab"][aria-selected="true"] {
                color: #111827 !important;
                border-bottom-color: #3b82f6 !important;
                background: linear-gradient(180deg, transparent, rgba(59, 130, 246, 0.05)) !important;
            }
            
            /* Status Bar - Light */
            .custom-status-bar {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.85) 0%, rgba(243, 244, 246, 0.7) 100%) !important;
                border: 1px solid rgba(0, 0, 0, 0.08) !important;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05) !important;
            }
            .custom-status-bar-text {
                color: #4b5563 !important;
            }
            .custom-status-bar-strong {
                color: #111827 !important;
            }
            
            /* Page Subtitle - Light */
            .custom-page-subtitle {
                color: #4b5563 !important;
            }
"""

GOT_CSS = """
            /* ============================================ */
            /* GAME OF THRONES THEME BASE */
            /* ============================================ */
            :root, .stApp, [data-testid="stDataFrame"], [data-testid="stDataFrameResizable"] {
                --primary-bg: #09090b;
                --secondary-bg: #141416;
                --card-bg: rgba(20, 20, 24, 0.85);
                --border-color: rgba(181, 148, 80, 0.35);
                --text-primary: #dfd5c6; /* parchment */
                --text-secondary: rgba(223, 213, 198, 0.7);
                --accent-gold: #b59450;
                --accent-gold-glow: rgba(181, 148, 80, 0.4);
                --success: #70a1ff; /* Ice Blue */
                --danger: #9b2c2c; /* Targaryen Crimson */
                
                /* Override Streamlit's theme variables to force GoT dark mode globally */
                --text-color: #dfd5c6 !important;
                --background-color: #09090b !important;
                --secondary-background-color: #141416 !important;
                --primary-color: #b59450 !important;
                --faded-text-60: rgba(223, 213, 198, 0.6) !important;
                --faded-text-40: rgba(223, 213, 198, 0.4) !important;

                /* Streamlit CamelCase variables to force GoT dark mode on Glide Data Grid / Canvas */
                --theme-backgroundColor: #09090b !important;
                --theme-secondaryBackgroundColor: #141416 !important;
                --theme-textColor: #dfd5c6 !important;
                --theme-primaryColor: #b59450 !important;
                --theme-fadedText60: rgba(223, 213, 198, 0.6) !important;
                --theme-fadedText40: rgba(223, 213, 198, 0.4) !important;
            }
            
            /* Force dialogs/modals to have a dark background and parchment text */
            div[data-testid="stDialog"] [role="dialog"] {
                background-color: #141416 !important;
                border: 1px solid rgba(181, 148, 80, 0.4) !important;
            }
            div[data-testid="stDialog"] [role="dialog"] * {
                color: #dfd5c6 !important;
            }

            /* Typography & Headings */
            h1, h2, h3, h4, h5, h6, .custom-page-subtitle, [data-testid="stSidebarNavLink"] span, [data-testid="stSidebarNavLink"] p {
                font-family: 'Calibri', 'Calibri', serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol" !important;
                color: #dfd5c6 !important;
            }

            /* Special Title styling */
            h1 span.custom-header-title {
                background: linear-gradient(135deg, #b59450 0%, #e5d5b7 50%, #9a783e 100%) !important;
                -webkit-background-clip: text !important;
                -webkit-text-fill-color: transparent !important;
                text-shadow: 0 0 15px rgba(181, 148, 80, 0.2) !important;
                font-weight: 700 !important;
                display: inline-block !important;
            }

            h1 span.custom-header-icon {
                -webkit-text-fill-color: initial !important;
                text-fill-color: initial !important;
                background: transparent !important;
                display: inline-block !important;
            }

            body, p, li, label, [data-testid="stWidgetLabel"] p, .stMarkdown p, .stMarkdown li {
                font-family: 'Calibri', serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol" !important;
                font-size: 1.15rem !important;
                color: #dfd5c6 !important;
            }


            /* Force light text color globally on key containers for readability */
            label, [data-testid="stWidgetLabel"] p {
                font-size: 1.05rem !important;
                font-weight: 700 !important;
                letter-spacing: 0.5px !important;
                text-transform: uppercase !important;
                color: #b59450 !important;
            }

            /* Active sidebar navigation link text color */
            [data-testid="stSidebarNavLink"][aria-current="page"] span, [data-testid="stSidebarNavLink"][aria-current="page"] p {
                color: #d4af37 !important;
                font-weight: 700 !important;
                text-shadow: 0 0 8px rgba(212, 175, 55, 0.4) !important;
            }

            /* Dropdowns and select inputs styling for readability */
            div[data-baseweb="menu"] *, [data-testid="stVirtualDropdown"] *, [data-baseweb="select"] * {
                color: #dfd5c6 !important;
                font-family: 'Calibri', serif !important;
            }

            /* Force text input containers to have a dark background and white text */
            div[data-baseweb="input"] {
                background-color: rgba(13, 13, 16, 0.95) !important;
                border: 1px solid rgba(181, 148, 80, 0.4) !important;
                border-radius: 4px !important;
                box-shadow: inset 0 0 10px rgba(0,0,0,0.8) !important;
            }
            div[data-baseweb="input"] * {
                color: #dfd5c6 !important;
            }

            /* Force selectboxes to have a dark background in all themes for readability */
            div[data-baseweb="select"] > div {
                background-color: rgba(13, 13, 16, 0.95) !important;
                border: 1px solid rgba(181, 148, 80, 0.4) !important;
                border-radius: 4px !important;
            }

            /* Force dropdown dropdown-menus to have a dark background in all themes */
            div[data-baseweb="menu"] {
                background-color: #141416 !important;
                border: 1px solid rgba(181, 148, 80, 0.5) !important;
                box-shadow: 0 8px 24px rgba(0,0,0,0.8) !important;
            }

            /* Main app background with subtle gradient */
            .stApp {
                background: linear-gradient(135deg, #09090b 0%, #141416 50%, #0c0c0e 100%) !important;
                background-attachment: fixed !important;
            }

            /* Subtle gold-haze background animations */
            .stApp::before {
                content: "" !important;
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100% !important;
                height: 100% !important;
                background-image: 
                    radial-gradient(circle at 10% 20%, rgba(181, 148, 80, 0.04) 0%, transparent 40%),
                    radial-gradient(circle at 90% 80%, rgba(155, 44, 44, 0.03) 0%, transparent 50%) !important;
                pointer-events: none !important;
                z-index: 0 !important;
                animation: backgroundShift 25s ease-in-out infinite !important;
            }

            /* ============================================ */
            /* METRIC CARDS - OBSIDIAN & GOLD */
            /* ============================================ */
            div[data-testid="stMetric"] {
                background: linear-gradient(135deg, rgba(13, 13, 16, 0.95) 0%, rgba(20, 20, 24, 0.8) 100%) !important;
                border: 1px solid rgba(181, 148, 80, 0.3) !important;
                border-radius: 8px !important;
                padding: 18px 20px !important;
                box-shadow: 
                    0 8px 32px rgba(0, 0, 0, 0.6),
                    inset 0 1px 0 rgba(255, 255, 255, 0.02) !important;
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
                min-height: 135px !important;
            }

            div[data-testid="stMetric"]:hover {
                transform: translateY(-4px) !important;
                border-color: rgba(181, 148, 80, 0.6) !important;
                box-shadow: 
                    0 12px 40px rgba(181, 148, 80, 0.15),
                    0 0 15px rgba(181, 148, 80, 0.25) !important;
            }
            
            /* Premium Bordered Containers (Used for single metric + action card) */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: linear-gradient(135deg, rgba(13, 13, 16, 0.95) 0%, rgba(20, 20, 24, 0.8) 100%) !important;
                border: 1px solid rgba(181, 148, 80, 0.3) !important;
                border-radius: 8px !important;
                padding: 16px !important;
                box-shadow: 
                    0 8px 32px rgba(0, 0, 0, 0.6),
                    inset 0 1px 0 rgba(255, 255, 255, 0.02) !important;
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
            }
            
            div[data-testid="stVerticalBlockBorderWrapper"]:hover {
                transform: translateY(-4px) !important;
                border-color: rgba(181, 148, 80, 0.6) !important;
                box-shadow: 
                    0 12px 40px rgba(181, 148, 80, 0.15),
                    0 0 15px rgba(181, 148, 80, 0.25) !important;
            }
            
            /* Make nested metrics blend seamlessly within the bordered container */
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stMetric"] {
                background: transparent !important;
                border: none !important;
                padding: 0 !important;
                box-shadow: none !important;
                min-height: auto !important;
                backdrop-filter: none !important;
                -webkit-backdrop-filter: none !important;
            }
            
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stMetricValue"] {
                margin-bottom: 8px !important;
            }

            div[data-testid="stMetricValue"] {
                font-family: 'Calibri', serif !important;
                font-size: 1.45rem !important;
                font-weight: 700 !important;
                background: linear-gradient(135deg, #dfd5c6 0%, #b59450 100%) !important;
                -webkit-background-clip: text !important;
                -webkit-text-fill-color: transparent !important;
            }

            div[data-testid="stMetricLabel"] {
                font-family: 'Calibri', serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol" !important;
                font-size: 0.85rem !important;
                color: rgba(181, 148, 80, 0.8) !important;
                letter-spacing: 1px !important;
                white-space: normal !important;
                overflow: visible !important;
                text-overflow: clip !important;
            }

            div[data-testid="stMetricLabel"] > div, 
            div[data-testid="stMetricLabel"] *, 
            div[data-testid="stMetricValue"] *, 
            div[data-testid="stMetric"] label, 
            div[data-testid="stMetric"] * {
                white-space: normal !important;
                overflow: visible !important;
                text-overflow: clip !important;
            }


            /* Delta coloring */
            div[data-testid="stMetricDelta"] > div[data-testid="stMetricDeltaIcon-Up"] {
                color: #70a1ff !important; /* Ice Blue */
            }
            div[data-testid="stMetricDelta"] > div:has(div[data-testid="stMetricDeltaIcon-Up"]) {
                color: #70a1ff !important;
                text-shadow: 0 0 8px rgba(112, 161, 255, 0.3) !important;
            }
            div[data-testid="stMetricDelta"] > div[data-testid="stMetricDeltaIcon-Down"] {
                color: #9b2c2c !important; /* Fire Red */
            }
            div[data-testid="stMetricDelta"] > div:has(div[data-testid="stMetricDeltaIcon-Down"]) {
                color: #9b2c2c !important;
                text-shadow: 0 0 8px rgba(155, 44, 44, 0.3) !important;
            }

            /* ============================================ */
            /* BUTTONS - MOLTEN VALYRIAN GOLD */
            /* ============================================ */
            button[kind="primary"] {
                background: linear-gradient(135deg, #8a733f 0%, #b59450 50%, #d4af37 100%) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                color: #09090b !important;
                font-family: 'Calibri', serif !important;
                font-weight: 700 !important;
                border-radius: 4px !important;
                box-shadow: 0 4px 14px rgba(181, 148, 80, 0.25) !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            }

            button[kind="primary"]:hover {
                background: linear-gradient(135deg, #a4894c 0%, #d4af37 50%, #f3e5ab 100%) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4) !important;
            }

            button[kind="secondary"] {
                background: rgba(13, 13, 16, 0.8) !important;
                border: 1px solid rgba(181, 148, 80, 0.4) !important;
                color: #dfd5c6 !important;
                font-family: 'Calibri', serif !important;
                border-radius: 4px !important;
            }

            button[kind="secondary"]:hover {
                background: rgba(20, 20, 24, 0.95) !important;
                border-color: rgba(181, 148, 80, 0.7) !important;
                transform: translateY(-1px) !important;
            }

            /* ============================================ */
            /* FORMS - VALYRIAN STONE */
            /* ============================================ */
            div[data-testid="stForm"] {
                background: linear-gradient(135deg, rgba(13, 13, 16, 0.95) 0%, rgba(20, 20, 24, 0.85) 100%) !important;
                border: 2px solid rgba(181, 148, 80, 0.3) !important;
                border-radius: 8px !important;
                padding: 2rem !important;
                box-shadow: 0 16px 48px rgba(0, 0, 0, 0.7) !important;
            }

            /* Input fields */
            input, textarea, select {
                background: rgba(13, 13, 16, 0.9) !important;
                border: 1px solid rgba(181, 148, 80, 0.3) !important;
                border-radius: 4px !important;
                color: #dfd5c6 !important;
            }

            input:focus, textarea:focus, select:focus {
                border-color: rgba(181, 148, 80, 0.7) !important;
                box-shadow: 0 0 10px rgba(181, 148, 80, 0.2) !important;
            }

            div[data-testid="stNumberInput"] button {
                background-color: rgba(20, 20, 24, 0.9) !important;
                color: #dfd5c6 !important;
                border-color: rgba(181, 148, 80, 0.3) !important;
            }

            div[data-testid="stDateInput"] > div {
                background-color: rgba(13, 13, 16, 0.9) !important;
                border-color: rgba(181, 148, 80, 0.3) !important;
            }

            div[data-testid="stFileUploader"] > section {
                background-color: rgba(13, 13, 16, 0.9) !important;
                border: 1px dashed rgba(181, 148, 80, 0.5) !important;
            }
            div[data-testid="stFileUploader"] * {
                color: #dfd5c6 !important;
            }

            div[data-testid="stSlider"] [role="slider"] {
                background-color: #b59450 !important;
            }
            div[data-testid="stSlider"] > div > div {
                background-color: rgba(181, 148, 80, 0.2) !important;
            }

            /* ============================================ */
            /* DATAFRAME - IRON TABLE */
            /* ============================================ */
            div[data-testid="stDataFrame"] {
                background: rgba(13, 13, 16, 0.9) !important;
                border: 1px solid rgba(181, 148, 80, 0.3) !important;
                border-radius: 8px !important;
            }
            div[data-testid="stDataFrame"] * {
                color: #dfd5c6 !important;
                font-family: 'Calibri', serif !important;
            }

            .stDataFrame thead tr th {
                background: linear-gradient(135deg, #1c1c22 0%, #131316 100%) !important;
                color: #b59450 !important;
                font-family: 'Calibri', serif !important;
                border-bottom: 2px solid rgba(181, 148, 80, 0.4) !important;
            }

            .stDataFrame tbody tr:hover {
                background: rgba(181, 148, 80, 0.06) !important;
            }

            /* ============================================ */
            /* SIDEBAR - CASTLE WALL */
            /* ============================================ */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #09090b 0%, #101013 100%) !important;
                border-right: 2px solid rgba(181, 148, 80, 0.3) !important;
                box-shadow: 8px 0 32px rgba(0, 0, 0, 0.7) !important;
            }

            /* ============================================ */
            /* TABS */
            /* ============================================ */
            button[data-baseweb="tab"] {
                font-family: 'Calibri', serif !important;
                color: rgba(223, 213, 198, 0.6) !important;
                letter-spacing: 0.5px !important;
            }

            button[data-baseweb="tab"]:hover {
                color: #b59450 !important;
                border-bottom-color: rgba(181, 148, 80, 0.5) !important;
            }

            button[data-baseweb="tab"][aria-selected="true"] {
                color: #dfd5c6 !important;
                border-bottom-color: #b59450 !important;
                background: linear-gradient(180deg, transparent, rgba(181, 148, 80, 0.08)) !important;
            }

            hr {
                background: linear-gradient(90deg, transparent, #b59450, transparent) !important;
            }

            /* Status Bar */
            .custom-status-bar {
                background: linear-gradient(135deg, rgba(13, 13, 16, 0.95) 0%, rgba(20, 20, 24, 0.85) 100%) !important;
                border: 1px solid rgba(181, 148, 80, 0.3) !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5) !important;
            }
            .custom-status-bar-text {
                color: rgba(223, 213, 198, 0.75) !important;
            }
            .custom-status-bar-strong {
                color: #dfd5c6 !important;
            }

            .custom-page-subtitle {
                color: rgba(223, 213, 198, 0.5) !important;
            }
"""


def inject_custom_css(theme: str = "Dark"):
    """
    Inject custom theme CSS based on user selection: 'Dark', 'Light', 'System', or 'Game of Thrones'.
    """
    theme = str(theme).strip().lower()
    
    css_to_inject = BASE_CSS
    if theme == "light":
        css_to_inject += LIGHT_CSS
    elif theme == "system":
        css_to_inject += "\n@media (prefers-color-scheme: dark) {\n" + DARK_CSS + "\n}\n"
        css_to_inject += "\n@media (prefers-color-scheme: light) {\n" + LIGHT_CSS + "\n}\n"
    elif theme == "game of thrones":
        css_to_inject += GOT_CSS
    else:  # dark (default)
        css_to_inject += DARK_CSS
        
    st.markdown(f"<style>{css_to_inject}</style>", unsafe_allow_html=True)

    # Programmatically override browser local storage theme settings (stActiveTheme)
    # to prevent system/local settings from overriding our server-side theme selection.
    if theme != "system":
        expected_base = "light" if theme == "light" else "dark"
        js_theme_override = f"""
        <script>
            try {{
                const expectedBase = "{expected_base}";
                const themeKey = "stActiveTheme";
                
                const checkAndSet = (storage) => {{
                    if (!storage) return false;
                    const currentThemeStr = storage.getItem(themeKey);
                    let needsUpdate = false;
                    
                    if (currentThemeStr) {{
                        try {{
                            const currentThemeObj = JSON.parse(currentThemeStr);
                            if (currentThemeObj.base !== expectedBase) {{
                                currentThemeObj.base = expectedBase;
                                storage.setItem(themeKey, JSON.stringify(currentThemeObj));
                                needsUpdate = true;
                            }}
                        }} catch (e) {{
                            storage.setItem(themeKey, JSON.stringify({{ base: expectedBase }}));
                            needsUpdate = true;
                        }}
                    }} else {{
                        storage.setItem(themeKey, JSON.stringify({{ base: expectedBase }}));
                        needsUpdate = true;
                    }}
                    return needsUpdate;
                }};

                let updated = false;
                try {{
                    if (window.localStorage) {{
                        updated = checkAndSet(window.localStorage) || updated;
                    }}
                }} catch (e) {{}}
                
                try {{
                    if (window.parent && window.parent.localStorage) {{
                        updated = checkAndSet(window.parent.localStorage) || updated;
                    }}
                }} catch (e) {{}}

                if (updated) {{
                    if (window.parent && window.parent.location) {{
                        window.parent.location.reload();
                    }} else {{
                        window.location.reload();
                    }}
                }}
            }} catch (err) {{
                console.error("Theme override failed:", err);
            }}
        </script>
        """
        st.markdown(js_theme_override, unsafe_allow_html=True)

    # Self-healing canvas inverter to force dark background on st.dataframe when running in light mode.
    # Runs periodically to cover reruns, dynamic data rendering, and page navigations.
    js_canvas_inverter = """
    <script>
        (function() {
            const checkThemeAndInvert = () => {
                try {
                    const appEl = document.querySelector('.stApp');
                    if (!appEl) return;
                    
                    // Read Streamlit's active theme background from inline styles
                    const inlineBg = appEl.style.getPropertyValue('--theme-backgroundColor');
                    const isLight = inlineBg && (inlineBg.includes('255') || inlineBg.toLowerCase().includes('fff'));
                    
                    const dataframes = document.querySelectorAll('[data-testid="stDataFrame"], [data-testid="stDataFrameResizable"]');
                    dataframes.forEach(df => {
                        if (isLight) {
                            // Invert cells to make them dark, shift colors back so green/red returns remain correct
                            df.style.filter = 'invert(0.92) hue-rotate(180deg)';
                        } else {
                            df.style.filter = 'none';
                        }
                    });
                } catch (e) {}
            };
            if (!window._themeInvertInterval) {
                window._themeInvertInterval = setInterval(checkThemeAndInvert, 400);
            }
        })();
    </script>
    """
    st.markdown(js_canvas_inverter, unsafe_allow_html=True)



def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize dataframe memory usage for faster loading.
    Converts object columns to category where appropriate.
    """
    if df.empty:
        return df
    
    for col in df.columns:
        col_type = df[col].dtype
        
        # Convert object columns with few unique values to category
        if col_type == 'object':
            num_unique = df[col].nunique()
            num_total = len(df[col])
            if num_unique / num_total < 0.5:  # Less than 50% unique values
                df[col] = df[col].astype('category')
        
        # Downcast numeric columns
        elif col_type == 'float64':
            df[col] = pd.to_numeric(df[col], downcast='float')
        elif col_type == 'int64':
            df[col] = pd.to_numeric(df[col], downcast='integer')
    
    return df



def render_page_header(title: str, subtitle: str = "", icon: str = "📊"):
    """
    Render a modern page header with gradient title and optional subtitle.
    """
    subtitle_html = f'<p class="custom-page-subtitle" style="font-size: 1rem; margin-top: 8px; font-weight: 500;">{subtitle}</p>' if subtitle else ""
    
    st.markdown(
        f"""
        <div style="margin-bottom: 30px;">
            <h1 style="
                font-family: 'Calibri', 'Segoe UI', -apple-system, sans-serif;
                font-size: 2.5rem;
                font-weight: 800;
                margin-bottom: 0;
                letter-spacing: -1px;
                display: flex;
                align-items: center;
                gap: 12px;
            ">
                <span class="custom-header-icon" style="
                    -webkit-text-fill-color: initial; 
                    text-fill-color: initial;
                    display: inline-block;
                ">{icon}</span>
                <span class="custom-header-title" style="
                    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    display: inline-block;
                ">{title}</span>
            </h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def _find_logo_path() -> str:
    from pathlib import Path
    logo_file = "lingual_logo.png"
    
    # Try finding the file in several common directories
    possible_paths = [
        Path(logo_file),
        Path(__file__).parent / logo_file,
        Path.cwd() / logo_file,
        Path(__file__).parent.parent / logo_file
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_file():
            return str(path.absolute())
    return ""


_LOGO_BASE64_CACHE = None

def _get_logo_base64(resolved_path: str) -> str:
    global _LOGO_BASE64_CACHE
    if _LOGO_BASE64_CACHE is not None:
        return _LOGO_BASE64_CACHE
        
    if not resolved_path:
        _LOGO_BASE64_CACHE = ""
        return ""
        
    import base64
    try:
        with open(resolved_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            _LOGO_BASE64_CACHE = f"data:image/png;base64,{encoded}"
            return _LOGO_BASE64_CACHE
    except Exception:
        pass
                
    _LOGO_BASE64_CACHE = ""
    return ""


def render_lingual_logo(position: str = "top-right", show_tagline: bool = False):
    """
    Render the Lingual Consultancy logo using high-contrast base64 HTML injection.
    Includes an absolute path st.image fallback, and a text logo if the file is missing.
    
    Args:
        position: "top-right" for fixed floating corner placement, "center" for centered login placement
        show_tagline: If True, shows "Lingual Consultancy Services" below logo
    """
    resolved_path = _find_logo_path()
    base64_logo = _get_logo_base64(resolved_path)
    
    if position == "center":
        if base64_logo:
            # Centered layout on white high-contrast card for login page (HTML/Base64)
            st.markdown(
                f"""
                <div style="
                    text-align: center;
                    margin-bottom: 25px;
                    margin-top: 10px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                ">
                    <div style="
                        background: rgba(255, 255, 255, 0.95);
                        padding: 16px 36px;
                        border-radius: 16px;
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        border: 1px solid rgba(255, 255, 255, 0.3);
                        margin-bottom: 8px;
                    ">
                        <img src="{base64_logo}" style="height: 60px; width: auto; object-fit: contain;">
                    </div>
                    {"<p style='color: rgba(249, 250, 251, 0.75); font-family: \"Calibri\", \"Segoe UI\", sans-serif; font-size: 0.95rem; font-weight: 500; letter-spacing: 0.5px; margin-top: 8px; text-shadow: 0 2px 4px rgba(0,0,0,0.5);'>Lingual Consultancy Services</p>" if show_tagline else ""}
                </div>
                """,
                unsafe_allow_html=True
            )
        elif resolved_path:
            # Native Streamlit Fallback for Centered layout using verified absolute path
            col1, col2, col3 = st.columns([1.2, 2, 1.2])
            with col2:
                with st.container():
                    st.markdown(
                        """
                        <div style="
                            background: rgba(255, 255, 255, 0.95);
                            padding: 16px 20px;
                            border-radius: 16px;
                            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
                            border: 1px solid rgba(255, 255, 255, 0.3);
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            margin-bottom: 8px;
                        ">
                        """,
                        unsafe_allow_html=True
                    )
                    st.image(resolved_path, use_column_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            if show_tagline:
                st.markdown(
                    """
                    <p style="
                        text-align: center;
                        color: rgba(249, 250, 251, 0.75);
                        font-family: 'Calibri', 'Segoe UI', sans-serif;
                        font-size: 0.95rem;
                        font-weight: 500;
                        letter-spacing: 0.5px;
                        margin-top: 8px;
                        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
                    ">Lingual Consultancy Services</p>
                    """,
                    unsafe_allow_html=True
                )
        else:
            # Elegant text-based branding fallback if the logo file is entirely missing
            st.markdown(
                f"""
                <div style="
                    text-align: center;
                    margin-bottom: 25px;
                    margin-top: 10px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                ">
                    <div style="
                        background: rgba(255, 255, 255, 0.95);
                        padding: 20px 40px;
                        border-radius: 16px;
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
                        display: inline-flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        border: 1px solid rgba(255, 255, 255, 0.3);
                        margin-bottom: 8px;
                    ">
                        <span style="
                            font-family: 'Calibri', 'Segoe UI', sans-serif;
                            font-size: 1.5rem;
                            font-weight: 800;
                            color: #0f75bc;
                            letter-spacing: 1px;
                        ">🌐 LINGUAL</span>
                        <span style="
                            font-family: 'Calibri', 'Segoe UI', sans-serif;
                            font-size: 0.8rem;
                            font-weight: 700;
                            color: #3a3a3c;
                            letter-spacing: 4px;
                            margin-top: 2px;
                            text-transform: uppercase;
                        ">Consultancy</span>
                    </div>
                    {"<p style='color: rgba(249, 250, 251, 0.75); font-family: \"Calibri\", \"Segoe UI\", sans-serif; font-size: 0.95rem; font-weight: 500; letter-spacing: 0.5px; margin-top: 8px; text-shadow: 0 2px 4px rgba(0,0,0,0.5);'>Lingual Consultancy Services</p>" if show_tagline else ""}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        if base64_logo:
            # Fixed floating top-right badge with white high-contrast pill container (HTML/Base64)
            st.markdown(
                f"""
                <style>
                    .floating-logo-container {{
                        position: fixed;
                        top: 15px;
                        right: 20px;
                        z-index: 999999;
                        background: rgba(255, 255, 255, 0.96);
                        padding: 6px 14px;
                        border-radius: 24px;
                        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border: 1px solid rgba(0, 0, 0, 0.06);
                        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                        pointer-events: auto;
                    }}
                    .floating-logo-container:hover {{
                        transform: translateY(-2px) scale(1.02);
                        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
                        background: #ffffff;
                    }}
                    .floating-logo-container img {{
                        height: 32px;
                        width: auto;
                        object-fit: contain;
                    }}
                    @media (max-width: 768px) {{
                        .floating-logo-container {{
                            top: 10px;
                            right: 10px;
                            padding: 4px 10px;
                        }}
                        .floating-logo-container img {{
                            height: 24px;
                        }}
                    }}
                </style>
                <div class="floating-logo-container">
                    <img src="{base64_logo}" alt="Lingual Logo">
                </div>
                """,
                unsafe_allow_html=True
            )
        elif resolved_path:
            # Native Streamlit Fallback for Top-Right (renders standard layout component) using absolute path
            col1, col2 = st.columns([5, 1])
            with col2:
                st.markdown(
                    """
                    <div style="
                        background: rgba(255, 255, 255, 0.95);
                        padding: 6px 10px;
                        border-radius: 12px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                        border: 1px solid rgba(0, 0, 0, 0.05);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    ">
                    """,
                    unsafe_allow_html=True
                )
                st.image(resolved_path, use_column_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Text fallback for top-right corner if the logo file is entirely missing
            col1, col2 = st.columns([4.2, 1.8])
            with col2:
                st.markdown(
                    """
                    <div style="
                        background: rgba(255, 255, 255, 0.95);
                        padding: 6px 12px;
                        border-radius: 12px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                        border: 1px solid rgba(0, 0, 0, 0.05);
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                    ">
                        <span style="font-family: 'Calibri', sans-serif; font-size: 0.75rem; font-weight: 800; color: #0f75bc; letter-spacing: 0.5px;">🌐 LINGUAL</span>
                        <span style="font-family: 'Calibri', sans-serif; font-size: 0.45rem; font-weight: 700; color: #3a3a3c; letter-spacing: 1.5px; text-transform: uppercase; margin-top: 1px;">Consultancy</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
