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

# NSE public holidays 2025-26 (add more as needed)
_NSE_HOLIDAYS = {
    datetime.date(2025, 10, 2),   # Gandhi Jayanti
    datetime.date(2025, 10, 24),  # Dussehra
    datetime.date(2025, 11, 5),   # Diwali Laxmi Puja
    datetime.date(2025, 11, 6),   # Diwali Balipratipada
    datetime.date(2025, 12, 25),  # Christmas
    datetime.date(2026, 1, 26),   # Republic Day
    datetime.date(2026, 2, 26),   # Maha Shivaratri
    datetime.date(2026, 3, 20),   # Holi
    datetime.date(2026, 4, 2),    # Ram Navami
    datetime.date(2026, 4, 3),    # Good Friday
    datetime.date(2026, 5, 1),    # Maharashtra Day
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
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            padding: 12px 20px;
            border-radius: 12px;
            background: linear-gradient(135deg, rgba(17, 24, 39, 0.8) 0%, rgba(31, 41, 55, 0.6) 100%);
            border: 1px solid rgba(99, 102, 241, 0.2);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
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
            <span style="
                color: rgba(249, 250, 251, 0.85);
                display: flex;
                align-items: center;
                gap: 6px;
            ">
                <span style="-webkit-text-fill-color: initial; text-fill-color: initial; font-style: normal; display: inline-block;">🕐</span> Last refreshed: <strong style="color: #f9fafb;">{last_str}</strong>
            </span>
            <span style="
                color: rgba(249, 250, 251, 0.85);
                display: flex;
                align-items: center;
                gap: 6px;
            ">
                <span style="-webkit-text-fill-color: initial; text-fill-color: initial; font-style: normal; display: inline-block;">⏱️</span> Next update: <strong style="color: #f9fafb;">{next_str}</strong>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def inject_custom_css():
    """Inject premium dark theme CSS with modern graphics and optimized performance."""
    st.markdown(
        """
        <style>
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
            
            /* ============================================ */
            /* DARK THEME BASE */
            /* ============================================ */
            :root {
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
            }
            
            /* Global Font Family & Emoji Support */
            html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol" !important;
            }
            
            /* Force light text color globally on key containers for readability */
            h1, h2, h3, h4, h5, h6, label, [data-testid="stWidgetLabel"] p, .stMarkdown p, [data-testid="stSidebarNavLink"] span, [data-testid="stSidebarNavLink"] p {
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
            }
            
            /* ============================================ */
            /* ANIMATED BACKGROUND PARTICLES */
            /* ============================================ */
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
                word-wrap: break-word !important;
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
            
            /* ============================================ */
            /* DATAFRAME - DARK THEME */
            /* ============================================ */
            div[data-testid="stDataFrame"] {
                background: rgba(17, 24, 39, 0.6) !important;
                border: 1px solid rgba(99, 102, 241, 0.15) !important;
                border-radius: 12px !important;
                overflow: hidden !important;
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
            }
            
            section[data-testid="stSidebar"] > div {
                background: transparent !important;
            }
            
            /* ============================================ */
            /* LOADING OVERLAY - FULL SCREEN */
            /* ============================================ */
            div[data-testid="stStatusWidget"] {
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                background: rgba(10, 14, 26, 0.95) !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
                z-index: 999999 !important;
            }
            
            div[data-testid="stStatusWidget"] > div {
                display: none !important;
            }
            
            /* Animated spinner */
            div[data-testid="stStatusWidget"]::before {
                content: "" !important;
                width: 80px !important;
                height: 80px !important;
                border: 4px solid rgba(255, 255, 255, 0.05) !important;
                border-top: 4px solid #3b82f6 !important;
                border-right: 4px solid #8b5cf6 !important;
                border-bottom: 4px solid #ec4899 !important;
                border-radius: 50% !important;
                animation: spin 1s cubic-bezier(0.68, -0.55, 0.27, 1.55) infinite !important;
                box-shadow: 
                    0 0 20px rgba(139, 92, 246, 0.4),
                    inset 0 0 20px rgba(59, 130, 246, 0.2) !important;
                position: absolute !important;
            }
            
            div[data-testid="stStatusWidget"]::after {
                content: "Loading Your Data..." !important;
                font-family: 'Inter', 'Segoe UI', sans-serif !important;
                font-size: 1.1rem !important;
                font-weight: 600 !important;
                background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899) !important;
                -webkit-background-clip: text !important;
                -webkit-text-fill-color: transparent !important;
                margin-top: 140px !important;
                letter-spacing: 0.5px !important;
                animation: pulse 1.5s ease-in-out infinite !important;
                position: absolute !important;
            }
            
            [data-testid="stDecoration"] {
                display: none !important;
            }
            
            /* Hide Streamlit Header (Deploy, Fork, Menu, etc.) */
            header, [data-testid="stHeader"] {
                display: none !important;
                visibility: hidden !important;
                height: 0px !important;
            }
            
            /* Hide Streamlit footer, watermark, and host/viewer badges */
            footer, [data-testid="stViewerBadge"], .viewerBadge, .styles_viewerBadge__, [class*="viewerBadge"], [class*="styles_viewerBadge"] {
                display: none !important;
                visibility: hidden !important;
                height: 0px !important;
            }
            
            /* Adjust top padding since header is hidden */
            .main .block-container {
                padding-top: 2rem !important;
            }
            
            /* ============================================ */
            /* DIVIDERS */
            /* ============================================ */
            hr {
                border: none !important;
                height: 1px !important;
                background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.3), transparent) !important;
                margin: 2rem 0 !important;
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
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            /* Apply fade-in to main content */
            .main .block-container {
                animation: fadeIn 0.5s ease-out !important;
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
        </style>
        """,
        unsafe_allow_html=True
    )


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
    subtitle_html = f'<p style="color: rgba(249, 250, 251, 0.6); font-size: 1rem; margin-top: 8px; font-weight: 500;">{subtitle}</p>' if subtitle else ""
    
    st.markdown(
        f"""
        <div style="margin-bottom: 30px;">
            <h1 style="
                font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
                font-size: 2.5rem;
                font-weight: 800;
                margin-bottom: 0;
                letter-spacing: -1px;
                display: flex;
                align-items: center;
                gap: 12px;
            ">
                <span style="
                    -webkit-text-fill-color: initial; 
                    text-fill-color: initial;
                    display: inline-block;
                ">{icon}</span>
                <span style="
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
                    {"<p style='color: rgba(249, 250, 251, 0.75); font-family: \"Inter\", \"Segoe UI\", sans-serif; font-size: 0.95rem; font-weight: 500; letter-spacing: 0.5px; margin-top: 8px; text-shadow: 0 2px 4px rgba(0,0,0,0.5);'>Lingual Consultancy Services</p>" if show_tagline else ""}
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
                        font-family: 'Inter', 'Segoe UI', sans-serif;
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
                            font-family: 'Inter', 'Segoe UI', sans-serif;
                            font-size: 1.5rem;
                            font-weight: 800;
                            color: #0f75bc;
                            letter-spacing: 1px;
                        ">🌐 LINGUAL</span>
                        <span style="
                            font-family: 'Inter', 'Segoe UI', sans-serif;
                            font-size: 0.8rem;
                            font-weight: 700;
                            color: #3a3a3c;
                            letter-spacing: 4px;
                            margin-top: 2px;
                            text-transform: uppercase;
                        ">Consultancy</span>
                    </div>
                    {"<p style='color: rgba(249, 250, 251, 0.75); font-family: \"Inter\", \"Segoe UI\", sans-serif; font-size: 0.95rem; font-weight: 500; letter-spacing: 0.5px; margin-top: 8px; text-shadow: 0 2px 4px rgba(0,0,0,0.5);'>Lingual Consultancy Services</p>" if show_tagline else ""}
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
                        <span style="font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 800; color: #0f75bc; letter-spacing: 0.5px;">🌐 LINGUAL</span>
                        <span style="font-family: 'Inter', sans-serif; font-size: 0.45rem; font-weight: 700; color: #3a3a3c; letter-spacing: 1.5px; text-transform: uppercase; margin-top: 1px;">Consultancy</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
