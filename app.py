import json
import math
import ssl
from urllib.parse import urlencode
from urllib.error import URLError
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_geolocation import streamlit_geolocation

from src.rag_agent import RagAgent


st.set_page_config(
    page_title="Trợ lý y tế RAG",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="collapsed",
)

USER_AGENT = "Medicine-QA-RAG/1.0"
OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
    "http://overpass-api.de/api/interpreter",
]
IP_LOCATION_ENDPOINTS = [
    "https://ipapi.co/json/",
    "http://ip-api.com/json/",
]
DEFAULT_LOCATION = {
    "label": "Vị trí mặc định khi không lấy được IP: Thành phố Hồ Chí Minh",
    "lat": 10.7769,
    "lon": 106.7009,
}
PLACE_TYPE_OPTIONS = {
    "Tất cả": ["pharmacy", "hospital", "clinic"],
    "Nhà thuốc": ["pharmacy"],
    "Bệnh viện/phòng khám": ["hospital", "clinic"],
}
PLACE_TYPE_LABELS = {
    "pharmacy": "Nhà thuốc",
    "hospital": "Bệnh viện",
    "clinic": "Phòng khám",
}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
          --app-blue: #0875d1;
          --app-blue-dark: #0458a3;
          --app-blue-soft: #e8f4ff;
          --app-border: #d7e2ef;
          --app-muted: #5d6b82;
          --app-surface: #ffffff;
          --app-soft: #f4f9ff;
          --app-shell: #eaf3ff;
          --app-text: #101828;
          --app-accent: #0f8f83;
          --app-accent-soft: #e7faf6;
          --app-warning: #ffb43b;
        }

        html, body, [data-testid="stAppViewContainer"], .stApp {
          background: var(--app-shell) !important;
          color: var(--app-text) !important;
        }

        [data-testid="stHeader"] {
          background: rgba(234, 243, 255, 0.92) !important;
          border-bottom: 1px solid rgba(215, 226, 239, 0.72);
        }

        .block-container {
          max-width: 1120px;
          padding-bottom: 3rem;
          padding-top: 1.2rem;
        }

        [data-testid="stSidebar"] {
          background: #ffffff !important;
          border-right: 1px solid var(--app-border);
        }

        [data-testid="stSidebar"] * {
          color: var(--app-text);
        }

        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
          color: var(--app-muted);
        }

        [data-testid="stSidebar"] section,
        [data-testid="stSidebar"] div {
          border-color: var(--app-border);
        }

        h1, h2, h3 {
          color: var(--app-text);
          letter-spacing: 0;
        }

        p, li, div[data-testid="stCaptionContainer"] {
          color: var(--app-muted);
        }

        .topbar {
          background: linear-gradient(180deg, var(--app-blue), var(--app-blue-dark));
          border-radius: 0 0 8px 8px;
          box-shadow: 0 14px 34px rgba(8, 117, 209, 0.22);
          color: #ffffff;
          margin: -1.2rem calc(50% - 50vw) 1rem;
          padding: 0.65rem max(1rem, calc((100vw - 1120px) / 2));
        }

        .topbar-inner {
          align-items: center;
          display: flex;
          gap: 1rem;
          justify-content: space-between;
        }

        .brand {
          align-items: center;
          display: flex;
          gap: 0.7rem;
          font-weight: 800;
        }

        .brand-mark {
          align-items: center;
          background: #ffffff;
          border-radius: 6px;
          color: var(--app-blue);
          display: flex;
          font-size: 0.9rem;
          font-weight: 900;
          height: 36px;
          justify-content: center;
          width: 36px;
        }

        .brand-sub {
          display: block;
          font-size: 0.72rem;
          font-weight: 600;
          opacity: 0.86;
        }

        .nav {
          display: flex;
          flex-wrap: wrap;
          gap: 0.7rem;
          justify-content: flex-end;
        }

        .nav span {
          background: rgba(255, 255, 255, 0.14);
          border: 1px solid rgba(255, 255, 255, 0.22);
          border-radius: 999px;
          color: #ffffff;
          font-size: 0.83rem;
          padding: 0.35rem 0.7rem;
        }

        .hero-grid {
          display: grid;
          gap: 0.9rem;
          grid-template-columns: 1.65fr 1fr;
          margin-bottom: 0.9rem;
        }

        .hero-main,
        .promo-card,
        .section-card,
        .chat-shell {
          background: var(--app-surface);
          border: 1px solid var(--app-border);
          border-radius: 8px;
          box-shadow: 0 12px 28px rgba(16, 24, 40, 0.08);
        }

        .hero-main {
          background:
            radial-gradient(circle at 86% 20%, rgba(255, 255, 255, 0.25), transparent 24%),
            radial-gradient(circle at 88% 78%, rgba(255, 198, 64, 0.38), transparent 26%),
            linear-gradient(135deg, #03bfe8 0%, #0875d1 52%, #055cad 100%);
          color: #ffffff;
          min-height: 286px;
          overflow: hidden;
          padding: 1.45rem 18rem 1.45rem 1.45rem;
          position: relative;
        }

        .hero-main::after {
          background: rgba(255, 255, 255, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.28);
          border-radius: 8px;
          content: "MED";
          font-size: 2.8rem;
          font-weight: 900;
          line-height: 1;
          padding: 1.65rem 1rem;
          position: absolute;
          right: 1.4rem;
          top: 2.2rem;
          width: 12.8rem;
          text-align: center;
        }

        .app-kicker {
          color: #dcf7ff;
          font-size: 0.83rem;
          font-weight: 800;
          margin-bottom: 0.35rem;
          text-transform: uppercase;
        }

        .app-title {
          color: #ffffff;
          font-size: 2.15rem;
          font-weight: 820;
          line-height: 1.08;
          margin: 0;
          max-width: 620px;
        }

        .app-subtitle {
          color: rgba(255, 255, 255, 0.9);
          font-size: 1rem;
          margin-top: 0.55rem;
          max-width: 540px;
        }

        .hero-badges {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          margin-top: 1.25rem;
        }

        .hero-badges span {
          background: rgba(255, 255, 255, 0.18);
          border: 1px solid rgba(255, 255, 255, 0.28);
          border-radius: 999px;
          color: #ffffff;
          font-size: 0.86rem;
          font-weight: 700;
          padding: 0.38rem 0.75rem;
        }

        .promo-stack {
          display: grid;
          gap: 0.9rem;
        }

        .promo-card {
          min-height: 117px;
          padding: 1rem;
        }

        .promo-card.primary {
          background: linear-gradient(135deg, #fff7db, #ffffff);
        }

        .promo-card.secondary {
          background: linear-gradient(135deg, #e8f4ff, #ffffff);
        }

        .promo-label {
          color: var(--app-blue);
          font-size: 0.76rem;
          font-weight: 800;
          text-transform: uppercase;
        }

        .promo-title {
          color: var(--app-text);
          font-size: 1.1rem;
          font-weight: 780;
          line-height: 1.25;
          margin-top: 0.25rem;
        }

        .promo-note {
          color: var(--app-muted);
          font-size: 0.9rem;
          margin-top: 0.35rem;
        }

        .quick-grid {
          display: grid;
          gap: 0.65rem;
          grid-template-columns: repeat(6, minmax(0, 1fr));
          margin-bottom: 0.9rem;
        }

        .quick-tile {
          align-items: flex-start;
          background: var(--app-surface);
          border: 1px solid var(--app-border);
          border-radius: 8px;
          box-shadow: 0 8px 18px rgba(16, 24, 40, 0.055);
          color: var(--app-text);
          display: flex;
          gap: 0.55rem;
          flex-direction: column;
          min-height: 92px;
          padding: 0.7rem;
        }

        .quick-icon {
          align-items: center;
          background: var(--app-blue-soft);
          border-radius: 6px;
          color: var(--app-blue);
          display: flex;
          flex: 0 0 34px;
          font-size: 0.72rem;
          font-weight: 900;
          height: 34px;
          justify-content: center;
        }

        .quick-title {
          color: var(--app-text);
          font-size: 0.88rem;
          font-weight: 730;
          line-height: 1.25;
        }

        .quick-desc {
          color: var(--app-muted);
          font-size: 0.76rem;
          line-height: 1.28;
        }

        .section-card {
          margin-bottom: 0.9rem;
          padding: 1rem;
        }

        .section-head {
          align-items: baseline;
          display: flex;
          justify-content: space-between;
          margin-bottom: 0.75rem;
        }

        .section-head h2 {
          font-size: 1.15rem;
          margin: 0;
        }

        .section-head span {
          color: var(--app-blue);
          font-size: 0.86rem;
          font-weight: 720;
        }

        .product-grid {
          display: grid;
          gap: 0.7rem;
          grid-template-columns: repeat(5, minmax(0, 1fr));
        }

        .product-card {
          background: #ffffff;
          border: 1px solid var(--app-border);
          border-radius: 8px;
          overflow: hidden;
          position: relative;
        }

        .product-art {
          align-items: center;
          background:
            radial-gradient(circle at 50% 35%, #ffffff 0 28%, transparent 29%),
            linear-gradient(135deg, #e8f4ff, #d8eeff);
          color: var(--app-blue);
          display: flex;
          font-weight: 900;
          height: 112px;
          justify-content: center;
        }

        .sale-badge {
          background: #ff4d5f;
          border-radius: 0 0 6px 0;
          color: #ffffff;
          font-size: 0.72rem;
          font-weight: 820;
          left: 0;
          padding: 0.25rem 0.45rem;
          position: absolute;
          top: 0;
        }

        .product-body {
          padding: 0.75rem;
        }

        .product-name {
          color: var(--app-text);
          font-size: 0.9rem;
          font-weight: 720;
          min-height: 48px;
        }

        .product-price {
          color: var(--app-blue);
          font-size: 0.92rem;
          font-weight: 820;
          margin-top: 0.45rem;
        }

        .product-meta {
          color: var(--app-muted);
          font-size: 0.76rem;
          margin-top: 0.28rem;
        }

        .product-cta {
          background: var(--app-blue);
          border-radius: 6px;
          color: #ffffff;
          font-size: 0.78rem;
          font-weight: 780;
          margin-top: 0.55rem;
          padding: 0.38rem 0.55rem;
          text-align: center;
        }

        .health-band {
          align-items: center;
          background: linear-gradient(135deg, #0b7ee8, #11a8d9);
          border-radius: 8px;
          color: #ffffff;
          display: grid;
          gap: 0.85rem;
          grid-template-columns: 1.2fr repeat(3, 1fr);
          margin-bottom: 0.9rem;
          padding: 1rem;
        }

        .health-band h2 {
          color: #ffffff;
          font-size: 1.15rem;
          margin: 0 0 0.25rem;
        }

        .health-band p {
          color: rgba(255, 255, 255, 0.88);
          margin: 0;
        }

        .health-chip {
          background: rgba(255, 255, 255, 0.16);
          border: 1px solid rgba(255, 255, 255, 0.24);
          border-radius: 8px;
          color: #ffffff;
          font-weight: 720;
          min-height: 72px;
          padding: 0.75rem;
        }

        .chat-shell {
          margin-bottom: 0.9rem;
          padding: 1rem;
        }

        .chat-title-row {
          align-items: center;
          border-bottom: 1px solid var(--app-border);
          display: flex;
          gap: 0.75rem;
          margin-bottom: 0.85rem;
          padding-bottom: 0.8rem;
        }

        .chat-avatar {
          align-items: center;
          background: linear-gradient(135deg, #ff6b73, #ff3f58);
          border-radius: 8px;
          color: #ffffff;
          display: flex;
          font-weight: 900;
          height: 42px;
          justify-content: center;
          width: 42px;
        }

        .chat-heading {
          color: var(--app-text);
          font-size: 1.2rem;
          font-weight: 800;
          line-height: 1.2;
        }

        .chat-subheading {
          color: var(--app-muted);
          font-size: 0.9rem;
          margin-top: 0.15rem;
        }

        .chat-input-box {
          background: var(--app-soft);
          border: 1px solid var(--app-border);
          border-radius: 8px;
          margin-top: 0.85rem;
          padding: 0.8rem;
        }

        div[data-testid="stPopover"] {
          bottom: 6.2rem;
          position: fixed;
          right: 1.25rem;
          width: 44px !important;
          z-index: 1000;
        }

        div[data-testid="stPopover"] > button {
          align-items: center;
          background: linear-gradient(135deg, #0875d1, #0f8f83) !important;
          border: 2px solid #ffffff;
          border-radius: 999px !important;
          box-shadow: 0 16px 34px rgba(8, 117, 209, 0.3);
          color: #ffffff !important;
          display: flex;
          font-weight: 900;
          height: 44px;
          justify-content: center;
          min-height: 44px;
          padding: 0 !important;
          width: 44px !important;
        }

        div[data-testid="stPopover"] > button p {
          color: #ffffff !important;
          font-size: 0 !important;
          font-weight: 900;
          width: 0 !important;
        }

        .mock-row {
          display: grid;
          gap: 0.9rem;
          grid-template-columns: 1.1fr 1fr;
          margin-bottom: 0.9rem;
        }

        .campaign-card {
          background: #ffffff;
          border: 1px solid var(--app-border);
          border-radius: 8px;
          box-shadow: 0 12px 28px rgba(16, 24, 40, 0.08);
          overflow: hidden;
        }

        .campaign-banner {
          background: linear-gradient(135deg, #ffcf54, #ff7a45);
          color: #592300;
          font-size: 1.35rem;
          font-weight: 900;
          padding: 1rem;
          text-align: center;
        }

        .campaign-body {
          display: grid;
          gap: 0.55rem;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          padding: 0.9rem;
        }

        .time-box {
          background: var(--app-soft);
          border: 1px solid var(--app-border);
          border-radius: 8px;
          color: var(--app-text);
          font-weight: 760;
          min-height: 58px;
          padding: 0.65rem;
          text-align: center;
        }

        .article-grid {
          display: grid;
          gap: 0.7rem;
          grid-template-columns: repeat(3, minmax(0, 1fr));
        }

        .article-card {
          background: #ffffff;
          border: 1px solid var(--app-border);
          border-radius: 8px;
          padding: 0.85rem;
        }

        .article-tag {
          color: var(--app-blue);
          font-size: 0.74rem;
          font-weight: 820;
          text-transform: uppercase;
        }

        .article-title {
          color: var(--app-text);
          font-weight: 760;
          line-height: 1.32;
          margin-top: 0.35rem;
        }

        .site-footer {
          background: var(--app-blue);
          border-radius: 8px 8px 0 0;
          color: #ffffff;
          margin-top: 1rem;
          padding: 1rem;
        }

        .site-footer p,
        .site-footer strong {
          color: #ffffff;
        }

        .brand-strip {
          display: grid;
          gap: 0.7rem;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          margin-bottom: 0.9rem;
        }

        .brand-card {
          background: #ffffff;
          border: 1px solid var(--app-border);
          border-radius: 8px;
          box-shadow: 0 8px 18px rgba(16, 24, 40, 0.055);
          color: var(--app-text);
          font-weight: 820;
          padding: 0.85rem;
          text-align: center;
        }

        .empty-state {
          background: var(--app-soft);
          border: 1px solid var(--app-border);
          border-radius: 8px;
          color: var(--app-muted);
          margin-top: 1rem;
          padding: 1rem;
        }

        .loading-card {
          align-items: center;
          background: linear-gradient(90deg, #effaf6, #ffffff);
          border: 1px solid var(--app-border);
          border-radius: 8px;
          color: var(--app-text);
          display: flex;
          gap: 0.8rem;
          margin: 0.75rem 0;
          padding: 0.95rem 1rem;
        }

        .loading-dots {
          display: inline-flex;
          gap: 0.28rem;
        }

        .loading-dots span {
          animation: app-bounce 1s infinite ease-in-out;
          background: var(--app-accent);
          border-radius: 999px;
          display: block;
          height: 0.42rem;
          width: 0.42rem;
        }

        .loading-dots span:nth-child(2) {
          animation-delay: 0.15s;
        }

        .loading-dots span:nth-child(3) {
          animation-delay: 0.3s;
        }

        @keyframes app-bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.45; }
          40% { transform: translateY(-0.35rem); opacity: 1; }
        }

        .care-card {
          background: var(--app-surface);
          border: 1px solid var(--app-border);
          border-radius: 8px;
          box-shadow: 0 4px 16px rgba(16, 24, 40, 0.05);
          margin: 0.75rem 0;
          padding: 1rem;
        }

        .care-title {
          color: var(--app-text);
          font-size: 1rem;
          font-weight: 720;
          margin-bottom: 0.25rem;
        }

        .care-meta {
          color: var(--app-muted);
          font-size: 0.92rem;
          margin-bottom: 0.4rem;
        }

        .care-address {
          color: #344054;
          font-size: 0.94rem;
          margin-bottom: 0.45rem;
        }

        div[data-testid="stTabs"] {
          background: var(--app-surface);
          border: 1px solid var(--app-border);
          border-radius: 8px;
          box-shadow: 0 8px 28px rgba(16, 24, 40, 0.05);
          padding: 0.35rem 1rem 1rem;
        }

        div[data-testid="stTabs"] [role="tablist"] {
          border-bottom: 1px solid var(--app-border);
          gap: 0.25rem;
        }

        div[data-testid="stTabs"] [role="tab"] {
          color: var(--app-muted);
          padding: 0.85rem 0.7rem;
        }

        div[data-testid="stTabs"] [aria-selected="true"] {
          color: var(--app-accent) !important;
          font-weight: 700;
        }

        div[data-testid="stChatMessage"] {
          background: #ffffff;
          border: 1px solid var(--app-border);
          border-radius: 8px;
          box-shadow: 0 3px 14px rgba(16, 24, 40, 0.045);
          margin: 0.75rem 0;
          padding: 0.75rem;
        }

        div[data-testid="stChatMessage"] p,
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stMarkdownContainer"] li {
          color: var(--app-text);
        }

        textarea,
        input,
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea {
          background: #ffffff !important;
          border-color: var(--app-border) !important;
          color: var(--app-text) !important;
        }

        [data-baseweb="input"],
        [data-baseweb="textarea"],
        [data-baseweb="select"] {
          background: #ffffff !important;
          border-color: var(--app-border) !important;
        }

        [data-testid="stSlider"] {
          background: #ffffff;
          border: 1px solid var(--app-border);
          border-radius: 8px;
          padding: 0.7rem 0.8rem 0.35rem;
        }

        .stButton > button,
        .stLinkButton > a,
        button[kind="secondary"] {
          background: #ffffff !important;
          border: 1px solid var(--app-border) !important;
          border-radius: 6px !important;
          color: var(--app-text) !important;
          min-height: 38px;
        }

        .stButton > button[kind="primary"],
        button[kind="primary"] {
          background: var(--app-blue) !important;
          border-color: var(--app-blue) !important;
          color: #ffffff !important;
        }

        .stAlert {
          background: #ffffff !important;
          border: 1px solid var(--app-border) !important;
          color: var(--app-text) !important;
        }

        details {
          background: #ffffff !important;
          border: 1px solid var(--app-border) !important;
          border-radius: 8px !important;
        }

        div[data-testid="stJson"] {
          background: #f8fafc !important;
          border: 1px solid var(--app-border);
          border-radius: 8px;
        }

        [data-testid="stForm"] {
          background: transparent !important;
          border: 0 !important;
          padding: 0 !important;
        }

        @media (max-width: 900px) {
          .hero-grid,
          .mock-row,
          .health-band {
            grid-template-columns: 1fr;
          }

          .quick-grid,
          .product-grid,
          .article-grid,
          .brand-strip {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .hero-main::after {
            display: none;
          }

          .hero-main {
            padding-right: 1.45rem;
          }

          .app-title {
            font-size: 1.8rem;
          }

          .nav {
            justify-content: flex-start;
          }
        }

        @media (max-width: 1180px) {
          .hero-main {
            padding-right: 1.45rem;
          }

          .hero-main::after {
            display: none;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _get_json(url: str, params: dict[str, object] | None = None) -> object:
    if params:
        url = f"{url}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, ssl.SSLCertVerificationError):
            context = ssl._create_unverified_context()
            with urlopen(request, timeout=20, context=context) as response:
                return json.loads(response.read().decode("utf-8"))
        raise


@st.cache_resource(show_spinner="Đang tạo chỉ mục truy xuất...")
def get_agent() -> RagAgent:
    return RagAgent()


@st.cache_data(ttl=1800, show_spinner=False)
def approximate_location_by_ip() -> dict[str, object] | None:
    data = None
    for endpoint in IP_LOCATION_ENDPOINTS:
        try:
            candidate = _get_json(endpoint)
        except Exception:
            continue
        if isinstance(candidate, dict):
            data = candidate
            break

    if not isinstance(data, dict):
        return DEFAULT_LOCATION

    lat = data.get("latitude", data.get("lat"))
    lon = data.get("longitude", data.get("lon"))
    if lat is None or lon is None:
        return DEFAULT_LOCATION

    city = data.get("city") or "khu vực hiện tại"
    region = data.get("region") or data.get("regionName") or ""
    country = data.get("country_name") or data.get("country") or ""
    label = ", ".join(part for part in [city, region, country] if part)
    return {
        "label": f"Vị trí gần đúng theo IP: {label}",
        "lat": float(lat),
        "lon": float(lon),
    }


def resolve_current_location(
    browser_lat: float | None,
    browser_lon: float | None,
    method: str | None,
) -> dict[str, object] | None:
    if browser_lat is not None and browser_lon is not None and method in {
        "browser",
        "browser_cached",
    }:
        label = (
            "Vị trí đã lưu gần đây"
            if method == "browser_cached"
            else "Vị trí hiện tại của bạn"
        )
        return {
            "label": label,
            "lat": browser_lat,
            "lon": browser_lon,
        }
    if method == "ip":
        return approximate_location_by_ip()
    return None


@st.cache_data(ttl=1800, show_spinner=False)
def find_nearby_places(
    lat: float,
    lon: float,
    radius_m: int,
    place_type: str,
) -> list[dict[str, object]]:
    amenity_filter = "|".join(PLACE_TYPE_OPTIONS[place_type])
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"~"^({amenity_filter})$"](around:{radius_m},{lat},{lon});
      way["amenity"~"^({amenity_filter})$"](around:{radius_m},{lat},{lon});
      relation["amenity"~"^({amenity_filter})$"](around:{radius_m},{lat},{lon});
    );
    out center tags 30;
    """
    data = None
    last_error: Exception | None = None
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            data = _get_json(endpoint, {"data": query})
            break
        except Exception as exc:
            last_error = exc
    if data is None:
        raise RuntimeError(f"Không thể kết nối OpenStreetMap Overpass: {last_error}")
    if not isinstance(data, dict):
        return []

    places = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        place_lat = element.get("lat") or element.get("center", {}).get("lat")
        place_lon = element.get("lon") or element.get("center", {}).get("lon")
        if place_lat is None or place_lon is None:
            continue

        amenity = tags.get("amenity", "unknown")
        distance_km = haversine_km(lat, lon, float(place_lat), float(place_lon))
        places.append(
            {
                "name": tags.get("name", "Chưa có tên"),
                "type": PLACE_TYPE_LABELS.get(amenity, "Cơ sở y tế"),
                "distance_km": distance_km,
                "lat": float(place_lat),
                "lon": float(place_lon),
                "address": format_address(tags),
                "phone": tags.get("phone") or tags.get("contact:phone", ""),
                "website": tags.get("website") or tags.get("contact:website", ""),
            }
        )
    return sorted(places, key=lambda place: place["distance_km"])


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return 2 * radius_km * math.asin(math.sqrt(a))


def format_address(tags: dict[str, str]) -> str:
    parts = [
        tags.get("addr:housenumber", ""),
        tags.get("addr:street", ""),
        tags.get("addr:suburb", ""),
        tags.get("addr:city", ""),
    ]
    return ", ".join(part for part in parts if part)


def render_header() -> None:
    st.markdown(
        """
        <div class="topbar">
          <div class="topbar-inner">
            <div class="brand">
              <div class="brand-mark">YT</div>
              <div>
                Trợ lý y tế
                <span class="brand-sub">Tra cứu thuốc và chăm sóc sức khỏe</span>
              </div>
            </div>
            <div class="nav">
              <span>Thuốc</span>
              <span>Bệnh thường gặp</span>
              <span>Cơ sở y tế</span>
              <span>Tư vấn AI</span>
            </div>
          </div>
        </div>

        <div class="hero-grid">
          <div class="hero-main">
            <div class="app-kicker">Nhà thuốc số và trợ lý AI</div>
            <h1 class="app-title">Mua thuốc an tâm, hỏi sức khỏe nhanh trong một nơi</h1>
            <div class="app-subtitle">
              Giao diện bán thuốc mẫu với danh mục, sản phẩm, khuyến mãi và trợ lý y tế mở bằng nút nổi ở góc phải.
            </div>
            <div class="hero-badges">
              <span>Giao nhanh trong ngày</span>
              <span>Tư vấn dược sĩ</span>
              <span>Tra cứu bằng AI</span>
            </div>
          </div>
          <div class="promo-stack">
            <div class="promo-card primary">
              <div class="promo-label">Ưu đãi hôm nay</div>
              <div class="promo-title">Giảm đến 35% nhóm vitamin và chăm sóc tiêu hóa</div>
              <div class="promo-note">Mock data dùng để mô phỏng trang bán thuốc.</div>
            </div>
            <div class="promo-card secondary">
              <div class="promo-label">Trợ lý y tế</div>
              <div class="promo-title">Bấm nút nổi để hỏi thuốc, triệu chứng hoặc tìm cơ sở gần bạn</div>
              <div class="promo-note">Chatbot mở trong popup, không rời khỏi trang hiện tại.</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_storefront_sections() -> None:
    st.markdown(
        """
        <div class="quick-grid">
          <div class="quick-tile"><div class="quick-icon">RX</div><div class="quick-title">Thuốc kê đơn</div><div class="quick-desc">Tư vấn trước khi dùng</div></div>
          <div class="quick-tile"><div class="quick-icon">OTC</div><div class="quick-title">Thuốc không kê đơn</div><div class="quick-desc">Sốt, ho, tiêu hóa</div></div>
          <div class="quick-tile"><div class="quick-icon">VIT</div><div class="quick-title">Vitamin</div><div class="quick-desc">Bổ sung hằng ngày</div></div>
          <div class="quick-tile"><div class="quick-icon">MOM</div><div class="quick-title">Mẹ và bé</div><div class="quick-desc">Chăm sóc gia đình</div></div>
          <div class="quick-tile"><div class="quick-icon">MED</div><div class="quick-title">Thiết bị y tế</div><div class="quick-desc">Máy đo, khẩu trang</div></div>
          <div class="quick-tile"><div class="quick-icon">MAP</div><div class="quick-title">Cơ sở gần bạn</div><div class="quick-desc">Nhà thuốc, bệnh viện</div></div>
        </div>

        <div class="section-card">
          <div class="section-head">
            <h2>Thương hiệu được quan tâm</h2>
            <span>Dữ liệu mẫu</span>
          </div>
          <div class="brand-strip">
            <div class="brand-card">Panadol</div>
            <div class="brand-card">Berocca</div>
            <div class="brand-card">Oresol</div>
            <div class="brand-card">Cetaphil</div>
            <div class="brand-card">Omron</div>
          </div>
        </div>

        <div class="section-card">
          <div class="section-head">
            <h2>Danh mục nổi bật</h2>
            <span>Xem thêm</span>
          </div>
          <div class="product-grid">
            <div class="product-card">
              <div class="sale-badge">-12%</div>
              <div class="product-art">PARA</div>
              <div class="product-body">
                <div class="product-name">Nhóm giảm đau, hạ sốt</div>
                <div class="product-meta">120 sản phẩm</div>
                <div class="product-price">Từ 18.000đ</div>
                <div class="product-cta">Xem nhóm hàng</div>
              </div>
            </div>
            <div class="product-card">
              <div class="sale-badge">Hot</div>
              <div class="product-art">DIGEST</div>
              <div class="product-body">
                <div class="product-name">Tiêu hóa và dạ dày</div>
                <div class="product-meta">Men vi sinh, oresol</div>
                <div class="product-price">Từ 4.000đ</div>
                <div class="product-cta">Xem nhóm hàng</div>
              </div>
            </div>
            <div class="product-card">
              <div class="sale-badge">-25%</div>
              <div class="product-art">VIT</div>
              <div class="product-body">
                <div class="product-name">Vitamin và khoáng chất</div>
                <div class="product-meta">C, D3, kẽm, multivitamin</div>
                <div class="product-price">Từ 79.000đ</div>
                <div class="product-cta">Xem nhóm hàng</div>
              </div>
            </div>
            <div class="product-card">
              <div class="product-art">CARE</div>
              <div class="product-body">
                <div class="product-name">Chăm sóc cá nhân</div>
                <div class="product-meta">Da, tóc, răng miệng</div>
                <div class="product-price">Từ 35.000đ</div>
                <div class="product-cta">Xem nhóm hàng</div>
              </div>
            </div>
            <div class="product-card">
              <div class="sale-badge">New</div>
              <div class="product-art">DEVICE</div>
              <div class="product-body">
                <div class="product-name">Thiết bị theo dõi sức khỏe</div>
                <div class="product-meta">Máy đo huyết áp, nhiệt kế</div>
                <div class="product-price">Từ 129.000đ</div>
                <div class="product-cta">Xem nhóm hàng</div>
              </div>
            </div>
          </div>
        </div>

        <div class="mock-row">
          <div class="campaign-card">
            <div class="campaign-banner">FLASHSALE SỨC KHỎE</div>
            <div class="campaign-body">
              <div class="time-box">08:00 - 12:00<br>Đang mở</div>
              <div class="time-box">12:00 - 18:00<br>Sắp diễn ra</div>
              <div class="time-box">18:00 - 22:00<br>Sắp diễn ra</div>
            </div>
          </div>
          <div class="section-card" style="margin-bottom:0;">
            <div class="section-head">
              <h2>Dịch vụ nhanh</h2>
              <span>Mock data</span>
            </div>
            <div class="quick-grid" style="grid-template-columns:repeat(2,minmax(0,1fr));margin-bottom:0;">
              <div class="quick-tile"><div class="quick-icon">KN</div><div class="quick-title">Kiểm tra nguy cơ</div></div>
              <div class="quick-tile"><div class="quick-icon">DT</div><div class="quick-title">Đặt thuốc tư vấn</div></div>
              <div class="quick-tile"><div class="quick-icon">LH</div><div class="quick-title">Liên hệ cơ sở gần nhất</div></div>
              <div class="quick-tile"><div class="quick-icon">HS</div><div class="quick-title">Lưu lịch sử hỏi đáp</div></div>
            </div>
          </div>
        </div>

        <div class="health-band">
          <div>
            <h2>Kiểm tra sức khỏe cùng trợ lý</h2>
            <p>Nhập câu hỏi bên dưới để nhận gợi ý phù hợp với ngữ cảnh hội thoại.</p>
          </div>
          <div class="health-chip">Tác dụng phụ của thuốc</div>
          <div class="health-chip">Thành phần và công dụng</div>
          <div class="health-chip">Cơ sở y tế gần nhất</div>
        </div>

        <div class="section-card">
          <div class="section-head">
            <h2>Sản phẩm bán chạy</h2>
            <span>Dữ liệu mẫu</span>
          </div>
          <div class="product-grid">
            <div class="product-card">
              <div class="sale-badge">-10%</div>
              <div class="product-art">PARA</div>
              <div class="product-body"><div class="product-name">Paracetamol 500mg hộp 10 vỉ</div><div class="product-meta">Đã bán 2.1k | 4.8/5</div><div class="product-price">28.000đ / hộp</div><div class="product-cta">Thêm vào giỏ</div></div>
            </div>
            <div class="product-card">
              <div class="sale-badge">-8%</div>
              <div class="product-art">ORS</div>
              <div class="product-body"><div class="product-name">Gói bù nước Oresol vị cam</div><div class="product-meta">Đã bán 890 | 4.7/5</div><div class="product-price">4.000đ / gói</div><div class="product-cta">Thêm vào giỏ</div></div>
            </div>
            <div class="product-card">
              <div class="sale-badge">-20%</div>
              <div class="product-art">VIT C</div>
              <div class="product-body"><div class="product-name">Vitamin C 500mg lọ 100 viên</div><div class="product-meta">Đã bán 1.4k | 4.9/5</div><div class="product-price">95.000đ / lọ</div><div class="product-cta">Thêm vào giỏ</div></div>
            </div>
            <div class="product-card">
              <div class="sale-badge">Hot</div>
              <div class="product-art">MEN</div>
              <div class="product-body"><div class="product-name">Men vi sinh hỗ trợ tiêu hóa</div><div class="product-meta">Đã bán 730 | 4.6/5</div><div class="product-price">120.000đ / hộp</div><div class="product-cta">Thêm vào giỏ</div></div>
            </div>
            <div class="product-card">
              <div class="sale-badge">-15%</div>
              <div class="product-art">SALINE</div>
              <div class="product-body"><div class="product-name">Dung dịch nhỏ mũi sinh lý</div><div class="product-meta">Đã bán 610 | 4.8/5</div><div class="product-price">32.000đ / chai</div><div class="product-cta">Thêm vào giỏ</div></div>
            </div>
          </div>
        </div>

        <div class="section-card">
          <div class="section-head">
            <h2>Góc sức khỏe</h2>
            <span>Bài viết mẫu</span>
          </div>
          <div class="article-grid">
            <div class="article-card"><div class="article-tag">Dược phẩm</div><div class="article-title">Dùng thuốc hạ sốt thế nào để tránh quá liều?</div></div>
            <div class="article-card"><div class="article-tag">Tiêu hóa</div><div class="article-title">Khi nào tiêu chảy cần đi khám ngay?</div></div>
            <div class="article-card"><div class="article-tag">Cấp cứu</div><div class="article-title">Các bước cần làm khi uống nhầm hóa chất.</div></div>
          </div>
        </div>

        <div class="site-footer">
          <strong>Hệ thống nhà thuốc mẫu</strong>
          <p>Giao diện demo dùng mock data. Chatbot AI mở bằng nút Trợ lý ở góc phải màn hình.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_loading(slot: st.delta_generator.DeltaGenerator, text: str) -> None:
    slot.markdown(
        f"""
        <div class="loading-card">
          <div class="loading-dots"><span></span><span></span><span></span></div>
          <div>{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> int:
    with st.sidebar:
        st.header("Cài đặt")
        top_k = st.slider("Số nguồn truy xuất", min_value=1, max_value=10, value=5)
        st.caption("Ứng dụng mặc định tạo câu trả lời bằng OpenAI.")
        if st.button("Xóa hội thoại", type="secondary"):
            st.session_state.messages = []
            st.rerun()
    return top_k


def render_sources(sources: list[dict[str, object]]) -> None:
    if not sources:
        return

    with st.expander("Nguồn tham khảo"):
        for idx, source in enumerate(sources, start=1):
            st.markdown(
                f"**{idx}. {source['title']}** | "
                f"{source['source']} | điểm {source['score']}"
            )
            st.json(source["metadata"])


def browser_location_center(location: dict[str, object]) -> dict[str, object]:
    return {
        "label": "Vị trí hiện tại từ trình duyệt",
        "lat": float(location["latitude"]),
        "lon": float(location["longitude"]),
    }


def format_nearby_places_answer(
    center: dict[str, object],
    places: list[dict[str, object]],
) -> str:
    lines = [
        f"Mình tìm được các cơ sở y tế gần bạn dựa trên: {center['label']}.",
    ]
    if not places:
        lines.append("Hiện chưa tìm thấy cơ sở phù hợp trong bán kính mặc định.")
        return "\n\n".join(lines)

    for idx, place in enumerate(places[:5], start=1):
        maps_url = (
            "https://www.google.com/maps/dir/?api=1&destination="
            f"{place['lat']},{place['lon']}"
        )
        address = place["address"] or "Chưa có địa chỉ chi tiết"
        phone = f"\n   Số điện thoại: {place['phone']}" if place["phone"] else ""
        lines.append(
            f"{idx}. **{place['name']}** - {place['type']} - cách khoảng "
            f"{place['distance_km']:.1f} km\n"
            f"   Địa chỉ: {address}{phone}\n"
            f"   [Mở đường đi trên Google Maps]({maps_url})"
        )

    lines.append(
        "Nếu đây là tình huống khẩn cấp, hãy gọi cấp cứu địa phương hoặc đến cơ sở gần nhất ngay."
    )
    return "\n\n".join(lines)


def answer_nearby_care_in_chat(
    center: dict[str, object],
    place_type: str = "Tất cả",
) -> dict[str, object]:
    places = find_nearby_places(
        lat=center["lat"],
        lon=center["lon"],
        radius_m=5000,
        place_type=place_type,
    )
    return {
        "role": "assistant",
        "content": format_nearby_places_answer(center, places),
        "sources": [],
    }


def request_location_for_nearby_care(place_type: str) -> None:
    st.session_state.pending_nearby_care = {"place_type": place_type}
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                "Mình cần quyền truy cập vị trí để tìm cơ sở y tế thật sự gần bạn. "
                "Hãy bấm nút định vị bên dưới và chọn Cho phép."
            ),
            "sources": [],
            "needs_location": True,
        }
    )
    st.rerun()


def is_nearby_care_request(text: str) -> bool:
    q = text.lower().strip()
    care_markers = [
        "cơ sở y tế",
        "nhà thuốc",
        "bệnh viện",
        "phòng khám",
        "hiệu thuốc",
        "hospital",
        "pharmacy",
        "clinic",
    ]
    nearby_markers = [
        "gần",
        "quanh đây",
        "gần đây",
        "gần tôi",
        "near",
        "nearby",
        "around me",
    ]
    return any(marker in q for marker in care_markers) and any(
        marker in q for marker in nearby_markers
    )


def is_emergency_care_help_request(
    text: str,
    messages: list[dict[str, object]],
) -> bool:
    q = text.lower().strip()
    help_markers = [
        "không biết số",
        "không có số",
        "số điện thoại",
        "bạn có thể tìm",
        "bạn giúp",
        "giúp tôi",
        "tìm giúp",
        "liên hệ",
        "gọi ai",
        "call",
        "phone",
        "contact",
        "help me",
    ]
    emergency_markers = [
        "uống nhầm",
        "nhầm thuốc",
        "thuốc tẩy",
        "ngộ độc",
        "khẩn cấp",
        "cấp cứu",
        "poison",
        "poisoning",
        "emergency",
    ]
    recent_text = " ".join(
        str(message.get("content", "")).lower()
        for message in messages[-6:]
    )
    asks_for_help = any(marker in q for marker in help_markers)
    emergency_context = any(marker in recent_text for marker in emergency_markers)
    return asks_for_help and emergency_context


def render_chat_history() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant":
                render_sources(message.get("sources", []))
                if message.get("needs_location") and st.session_state.get(
                    "pending_nearby_care"
                ):
                    render_location_permission_request()


def render_chat_autoscroll() -> None:
    components.html(
        """
        <script>
        const scrollChatToBottom = () => {
          const doc = window.parent.document;
          const input = doc.querySelector('input[aria-label="Câu hỏi"]');
          const target = input?.closest('[data-testid="stVerticalBlock"]')
            || input
            || Array.from(doc.querySelectorAll('[data-testid="stChatMessage"]')).pop();
          if (target) {
            target.scrollIntoView({ behavior: "smooth", block: "end" });
          }

          const scrollables = [
            ...doc.querySelectorAll('[data-testid="stPopover"] + div, [role="dialog"], div[style*="overflow"]')
          ];
          scrollables.forEach((node) => {
            if (node && node.scrollHeight > node.clientHeight) {
              node.scrollTop = node.scrollHeight;
            }
          });
        };

        setTimeout(scrollChatToBottom, 80);
        setTimeout(scrollChatToBottom, 320);
        setTimeout(scrollChatToBottom, 750);
        </script>
        """,
        height=0,
    )


def render_location_permission_request() -> None:
    location = streamlit_geolocation()
    has_browser_location = (
        isinstance(location, dict)
        and location.get("latitude") is not None
        and location.get("longitude") is not None
    )
    if not has_browser_location:
        st.caption("Sau khi cấp quyền, danh sách cơ sở gần bạn sẽ xuất hiện ngay trong chat.")
        return

    pending = st.session_state.get("pending_nearby_care") or {}
    place_type = pending.get("place_type", "Tất cả")
    loading_slot = st.empty()
    render_loading(loading_slot, "Đang tìm cơ sở y tế gần vị trí của bạn...")
    try:
        assistant_message = answer_nearby_care_in_chat(
            center=browser_location_center(location),
            place_type=place_type,
        )
    except Exception as exc:
        loading_slot.empty()
        st.error(f"Không thể tìm cơ sở gần bạn lúc này: {exc}")
        st.stop()
    loading_slot.empty()

    st.session_state.pending_nearby_care = None
    for message in reversed(st.session_state.messages):
        if message.get("needs_location"):
            message["needs_location"] = False
            break
    st.session_state.messages.append(assistant_message)
    st.rerun()


def render_chat(agent: RagAgent, top_k: int) -> None:
    st.markdown(
        """
        <div class="chat-title-row">
          <div class="chat-avatar">AI</div>
          <div>
            <div class="chat-heading">Trợ lý y tế</div>
            <div class="chat-subheading">Hỏi về thuốc, triệu chứng hoặc nhờ tìm cơ sở y tế gần bạn.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_chat_history()
    if st.session_state.messages:
        render_chat_autoscroll()

    if not st.session_state.messages:
        st.markdown(
            """
            <div class="empty-state">
              Bạn có thể hỏi về triệu chứng, bệnh, hướng điều trị, thành phần thuốc,
              tác dụng phụ hoặc nhờ mình tìm cơ sở y tế gần bạn.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        with st.form("medical_chat_form", clear_on_submit=True):
            col_input, col_send = st.columns([8, 1.2])
            with col_input:
                question = st.text_input(
                    "Câu hỏi",
                    placeholder="Ví dụ: Thuốc Augmentin 625 Duo có tác dụng phụ gì?",
                    label_visibility="collapsed",
                )
            with col_send:
                submitted = st.form_submit_button(
                    "Gửi",
                    type="primary",
                    use_container_width=True,
                )

    if not submitted or not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    render_chat_autoscroll()

    if is_nearby_care_request(question):
        request_location_for_nearby_care("Tất cả")
        return

    if is_emergency_care_help_request(question, st.session_state.messages[:-1]):
        request_location_for_nearby_care("Bệnh viện/phòng khám")
        return

    loading_slot = st.empty()
    render_loading(loading_slot, "Đang tìm nguồn phù hợp và tạo câu trả lời...")
    try:
        history = [
            {"role": message["role"], "content": message["content"]}
            for message in st.session_state.messages[:-1]
        ]
        result = agent.answer(
            question,
            top_k=top_k,
            use_llm=True,
            conversation_history=history,
        )
    except Exception as exc:
        loading_slot.empty()
        st.error(f"Không thể tạo câu trả lời: {exc}")
        st.stop()
    loading_slot.empty()

    assistant_message = {
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
    }
    st.session_state.messages.append(assistant_message)
    st.rerun()


def render_chat_launcher(agent: RagAgent, top_k: int) -> None:
    with st.popover(
        "",
        help="Mở trợ lý y tế",
        icon=":material/support_agent:",
    ):
        render_chat(agent, top_k)


def render_nearby_results(
    center: dict[str, object],
    places: list[dict[str, object]],
) -> None:
    st.caption(f"Tâm tìm kiếm: {center['label']}")
    if not places:
        st.info("Không tìm thấy nhà thuốc, bệnh viện hoặc phòng khám trong bán kính đã chọn.")
        return

    display_places = places[:10]
    map_rows = [
        {"lat": center["lat"], "lon": center["lon"], "name": "Vị trí tìm kiếm"}
    ] + [
        {"lat": place["lat"], "lon": place["lon"], "name": place["name"]}
        for place in display_places
    ]
    st.map(pd.DataFrame(map_rows), latitude="lat", longitude="lon")

    for idx, place in enumerate(display_places, start=1):
        maps_url = (
            "https://www.google.com/maps/search/?api=1&query="
            f"{place['lat']},{place['lon']}"
        )
        st.markdown(
            f"""
            <div class="care-card">
              <div class="care-title">{idx}. {place['name']}</div>
              <div class="care-meta">{place['type']} | Cách khoảng {place['distance_km']:.1f} km</div>
              <div class="care-address">{place['address'] or 'Chưa có địa chỉ chi tiết'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_a, col_b, col_c = st.columns([1, 1, 4])
        with col_a:
            st.link_button("Mở bản đồ", maps_url)
        with col_b:
            if place["website"]:
                st.link_button("Trang web", place["website"])
        with col_c:
            if place["phone"]:
                st.caption(f"Số điện thoại: {place['phone']}")

    st.caption(
        "Kết quả lấy từ OpenStreetMap nên có thể chưa đầy đủ. "
        "Nếu là tình huống khẩn cấp, hãy gọi cấp cứu hoặc đến cơ sở y tế gần nhất."
    )


def render_nearby_care() -> None:
    st.subheader("Gợi ý nhà thuốc và bệnh viện gần nhất")
    location = streamlit_geolocation()
    has_browser_location = (
        isinstance(location, dict)
        and location.get("latitude") is not None
        and location.get("longitude") is not None
    )
    location_method = "browser" if has_browser_location else None
    browser_lat = float(location["latitude"]) if has_browser_location else None
    browser_lon = float(location["longitude"]) if has_browser_location else None

    col_a, col_b = st.columns([1, 1])
    with col_a:
        place_type = st.segmented_control(
            "Loại địa điểm",
            list(PLACE_TYPE_OPTIONS.keys()),
            default="Tất cả",
        )
    with col_b:
        radius_km = st.slider("Bán kính tìm kiếm", min_value=1, max_value=15, value=5)

    if has_browser_location:
        st.success("Đã lấy được vị trí hiện tại từ trình duyệt.")
    else:
        st.caption("Bấm nút định vị ở trên và cho phép trình duyệt truy cập vị trí.")
        return

    loading_slot = st.empty()
    render_loading(loading_slot, "Đang tìm các cơ sở y tế gần vị trí của bạn...")
    try:
        geocoded = resolve_current_location(browser_lat, browser_lon, location_method)
        if not geocoded:
            loading_slot.empty()
            st.warning("Không lấy được vị trí hiện tại. Hãy kiểm tra quyền định vị rồi thử lại.")
            st.stop()

        places = find_nearby_places(
            lat=geocoded["lat"],
            lon=geocoded["lon"],
            radius_m=radius_km * 1000,
            place_type=place_type,
        )
    except Exception as exc:
        loading_slot.empty()
        st.error(f"Không thể tìm cơ sở gần bạn lúc này: {exc}")
        st.stop()
    loading_slot.empty()

    render_nearby_results(geocoded, places)


def main() -> None:
    inject_styles()
    render_header()
    render_storefront_sections()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "browser_location" not in st.session_state:
        st.session_state.browser_location = None
    if "pending_nearby_care" not in st.session_state:
        st.session_state.pending_nearby_care = None

    agent = get_agent()
    top_k = render_sidebar()
    render_chat_launcher(agent, top_k)


if __name__ == "__main__":
    main()
