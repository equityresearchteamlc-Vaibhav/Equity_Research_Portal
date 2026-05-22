"""
utils.py – Shared helpers for Equity Research Portal
  • is_market_open()  → True/False based on NSE trading hours (Mon–Fri, 09:15–15:30 IST)
  • render_status_bar()  → renders the last-refreshed / next-update / market-status banner
"""

import datetime
import pytz
import streamlit as st

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
    signal      = "🟢 Market Open" if market_open else "🔴 Market Closed"
    signal_color = "#22c55e" if market_open else "#ef4444"

    last_str = now_ist.strftime("%d %b %Y, %I:%M:%S %p IST")
    next_str = next_refresh.strftime("%I:%M:%S %p IST")

    st.markdown(
        f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 24px;
            padding: 8px 16px;
            border-radius: 8px;
            background: var(--secondary-background-color);
            border: 1px solid rgba(255,255,255,0.08);
            font-size: 0.85rem;
            margin-bottom: 12px;
        ">
            <span style="color:{signal_color}; font-weight:700;">{signal}</span>
            <span style="color:var(--text-color); opacity:0.75;">
                🕐 Last refreshed: <strong>{last_str}</strong>
            </span>
            <span style="color:var(--text-color); opacity:0.75;">
                ⏱️ Next update: <strong>{next_str}</strong>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def inject_custom_css():
    """Inject premium CSS to style the portal like a professional financial research terminal."""
    st.markdown(
        """
        <style>
            /* Modernized metric cards - custom fonts and margins */
            div[data-testid="stMetric"] {
                background: rgba(255, 255, 255, 0.03) !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                border-radius: 10px !important;
                padding: 10px 14px !important;
                transition: transform 0.3s ease, border-color 0.3s ease !important;
            }
            div[data-testid="stMetric"]:hover {
                transform: translateY(-2px) !important;
                border-color: rgba(59, 130, 246, 0.4) !important;
            }
            /* Control font sizing inside metrics to prevent truncation with 3 dots */
            div[data-testid="stMetricValue"] {
                font-size: 1.35rem !important;
                font-weight: 700 !important;
                margin-top: 2px !important;
            }
            div[data-testid="stMetricLabel"] {
                font-size: 0.85rem !important;
                font-weight: 500 !important;
                color: rgba(255, 255, 255, 0.7) !important;
            }
            
            /* Professional form styling */
            div[data-testid="stForm"] {
                background: rgba(255, 255, 255, 0.01) !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                border-radius: 12px !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
            }
            
            /* Styled primary buttons */
            button[kind="primary"] {
                background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
                border: none !important;
                color: white !important;
                font-weight: 600 !important;
                border-radius: 6px !important;
                transition: all 0.2s ease !important;
            }
            button[kind="primary"]:hover {
                background: linear-gradient(135deg, #2563eb, #7c3aed) !important;
                transform: translateY(-1px) !important;
            }
            
            /* Glassmorphism sidebar */
            section[data-testid="stSidebar"] {
                background: rgba(15, 17, 26, 0.95) !important;
                border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
            }

            /* ------------------------------------------------- */
            /* Global Full-Screen Glassmorphism Loading Overlay */
            /* ------------------------------------------------- */
            div[data-testid="stStatusWidget"] {
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                background: rgba(10, 12, 20, 0.75) !important; /* Premium dark backdrop */
                backdrop-filter: blur(8px) !important; /* Premium blur */
                -webkit-backdrop-filter: blur(8px) !important;
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
                z-index: 999999 !important;
                transition: all 0.3s ease-in-out !important;
            }

            /* Hide Streamlit's default small spinner inside stStatusWidget */
            div[data-testid="stStatusWidget"] > div {
                display: none !important;
            }

            /* Main glowing outer spinner */
            div[data-testid="stStatusWidget"]::before {
                content: "" !important;
                width: 75px !important;
                height: 75px !important;
                border: 4px solid rgba(255, 255, 255, 0.03) !important;
                border-top: 4px solid #3b82f6 !important;
                border-right: 4px solid #8b5cf6 !important;
                border-bottom: 4px solid #ec4899 !important;
                border-radius: 50% !important;
                animation: spin 1.0s cubic-bezier(0.68, -0.55, 0.27, 1.55) infinite !important;
                box-shadow: 0 0 15px rgba(139, 92, 246, 0.4) !important;
                position: absolute !important;
            }

            /* Floating inner core text */
            div[data-testid="stStatusWidget"]::after {
                content: "Executing Terminal Request..." !important;
                font-family: 'Space Grotesk', 'Outfit', sans-serif !important;
                font-size: 1rem !important;
                font-weight: 600 !important;
                background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899) !important;
                -webkit-background-clip: text !important;
                -webkit-text-fill-color: transparent !important;
                margin-top: 130px !important;
                letter-spacing: 0.5px !important;
                animation: pulse 1.5s ease-in-out infinite !important;
                position: absolute !important;
            }

            /* Hide the default tiny top progress bar */
            [data-testid="stDecoration"] {
                display: none !important;
            }

            /* Style default inline spinners to match theme */
            div[data-testid="stSpinner"] > div {
                border-top-color: #8b5cf6 !important;
                border-right-color: #ec4899 !important;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            @keyframes pulse {
                0%, 100% { opacity: 0.6; transform: scale(0.98); }
                50% { opacity: 1; transform: scale(1.02); }
            }
        </style>
        """,
        unsafe_allow_html=True
    )
