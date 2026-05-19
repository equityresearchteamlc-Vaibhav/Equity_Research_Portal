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
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            /* Apply primary font families */
            html, body, [class*="css"], .stMarkdown, p, span, label, input, button, textarea {
                font-family: 'Outfit', sans-serif !important;
            }
            h1, h2, h3, h4, h5, h6, [data-testid="stHeader"] {
                font-family: 'Space Grotesk', sans-serif !important;
                font-weight: 700 !important;
                letter-spacing: -0.5px !important;
            }
            
            /* Modernized metric cards */
            div[data-testid="stMetric"] {
                background: rgba(255, 255, 255, 0.03) !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                border-radius: 14px !important;
                padding: 20px 24px !important;
                box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2) !important;
                backdrop-filter: blur(8px) !important;
                -webkit-backdrop-filter: blur(8px) !important;
                transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease !important;
            }
            div[data-testid="stMetric"]:hover {
                transform: translateY(-3px) !important;
                border-color: rgba(59, 130, 246, 0.4) !important;
                box-shadow: 0 8px 35px rgba(59, 130, 246, 0.15) !important;
            }
            
            /* Professional form styling */
            div[data-testid="stForm"] {
                background: rgba(255, 255, 255, 0.02) !important;
                border: 1px solid rgba(255, 255, 255, 0.06) !important;
                border-radius: 18px !important;
                padding: 30px !important;
                box-shadow: 0 12px 45px rgba(0, 0, 0, 0.45) !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
            }
            
            /* Styled submit and view buttons */
            button[kind="primary"] {
                background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
                border: none !important;
                color: white !important;
                font-weight: 600 !important;
                border-radius: 8px !important;
                box-shadow: 0 4px 15px rgba(139, 92, 246, 0.25) !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            }
            button[kind="primary"]:hover {
                background: linear-gradient(135deg, #2563eb, #7c3aed) !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4) !important;
            }
            
            /* Glassmorphism sidebar */
            section[data-testid="stSidebar"] {
                background: rgba(15, 17, 26, 0.95) !important;
                border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
            }
            
            /* Form input labels styling */
            div[data-testid="stForm"] label {
                color: rgba(255, 255, 255, 0.85) !important;
                font-weight: 500 !important;
                font-size: 0.9rem !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
