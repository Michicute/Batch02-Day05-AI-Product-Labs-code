import json
import math
import ssl
from urllib.parse import urlencode
from urllib.error import URLError
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st
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
          --app-border: #d8dee8;
          --app-muted: #667085;
          --app-surface: #ffffff;
          --app-soft: #f7f9fc;
          --app-shell: #f3f6fa;
          --app-text: #101828;
          --app-accent: #1f7a6b;
          --app-accent-soft: #e8f5f1;
        }

        html, body, [data-testid="stAppViewContainer"], .stApp {
          background: var(--app-shell) !important;
          color: var(--app-text) !important;
        }

        [data-testid="stHeader"] {
          background: rgba(243, 246, 250, 0.92) !important;
          border-bottom: 1px solid rgba(216, 222, 232, 0.72);
        }

        .block-container {
          padding-top: 2rem;
          padding-bottom: 8rem;
          max-width: 1180px;
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

        div[data-testid="stCaptionContainer"] {
          color: var(--app-muted);
        }

        .app-hero {
          background: var(--app-surface);
          border: 1px solid var(--app-border);
          border-radius: 8px;
          border-bottom: 1px solid var(--app-border);
          box-shadow: 0 8px 28px rgba(16, 24, 40, 0.06);
          margin-bottom: 1.2rem;
          padding: 1.2rem 1.25rem;
        }

        .app-kicker {
          color: var(--app-accent);
          font-size: 0.85rem;
          font-weight: 700;
          margin-bottom: 0.25rem;
          text-transform: uppercase;
        }

        .app-title {
          color: var(--app-text);
          font-size: 2rem;
          font-weight: 760;
          line-height: 1.15;
          margin: 0;
        }

        .app-subtitle {
          color: var(--app-muted);
          font-size: 1rem;
          margin-top: 0.45rem;
          max-width: 760px;
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

        div[data-testid="stChatInput"] {
          background: rgba(243, 246, 250, 0.98) !important;
          border-top: 1px solid var(--app-border);
          bottom: 0;
          box-shadow: 0 -10px 30px rgba(16, 24, 40, 0.08);
          left: 0;
          padding: 0.75rem 2rem 0.95rem;
          position: fixed;
          right: 0;
          z-index: 999;
        }

        div[data-testid="stChatInput"] > div {
          margin: 0 auto;
          max-width: 860px;
          width: 100%;
        }

        div[data-testid="stChatInput"] textarea {
          border: 1px solid var(--app-border) !important;
          border-radius: 8px !important;
          box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
          min-height: 46px !important;
        }

        @media (max-width: 900px) {
          div[data-testid="stChatInput"] {
            left: 0;
            padding-left: 1rem;
            padding-right: 1rem;
          }
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
          background: var(--app-accent) !important;
          border-color: var(--app-accent) !important;
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
        <div class="app-hero">
          <div class="app-kicker">Trợ lý hỏi đáp y tế</div>
          <h1 class="app-title">Tra cứu thông tin thuốc, bệnh và cơ sở y tế gần bạn</h1>
          <div class="app-subtitle">
            Hệ thống dùng dữ liệu cục bộ để truy xuất nguồn liên quan, sau đó tạo câu trả lời bằng OpenAI.
          </div>
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


def render_chat_history() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant":
                render_sources(message.get("sources", []))


def render_chat(agent: RagAgent, top_k: int) -> None:
    render_chat_history()

    question = st.chat_input(
        placeholder="Nhập câu hỏi, ví dụ: Thuốc Augmentin 625 Duo có tác dụng phụ gì?",
    )
    if not question:
        if not st.session_state.messages:
            st.markdown(
                """
                <div class="empty-state">
                  Bạn có thể hỏi về triệu chứng, bệnh, hướng điều trị, thành phần thuốc,
                  tác dụng phụ hoặc nhà sản xuất thuốc.
                </div>
                """,
                unsafe_allow_html=True,
            )
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

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
    with st.chat_message("assistant"):
        st.write(result["answer"])
        render_sources(result["sources"])


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

    if "messages" not in st.session_state:
        st.session_state.messages = []

    agent = get_agent()
    top_k = render_sidebar()
    chat_tab, nearby_tab = st.tabs(["Hỏi đáp", "Cơ sở gần tôi"])

    with chat_tab:
        render_chat(agent, top_k)
    with nearby_tab:
        render_nearby_care()


if __name__ == "__main__":
    main()
