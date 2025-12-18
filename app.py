import streamlit as st
import requests
import pandas as pd
import datetime
import re
import os

API_BASE = os.getenv("API_BASE_URL", "https://global-public-holiday-api.onrender.com")  # Default if not set

#API_BASE = "https://global-public-holiday-api.onrender.com"  # FastAPI backend URL

st.set_page_config(page_title="祝日と祭りビューア", page_icon="🎌")
st.title("🎌 世界の祝日・祭り検索アプリ")

# -----------------------------
# Country options
# -----------------------------
country_options = {
    "日本（JP）": "JP",
    "アメリカ（US）": "US",
    "イギリス（GB）": "GB",
    "ドイツ（DE）": "DE",
    "フランス（FR）": "FR",
    "シンガポール（SG）": "SG",
    "オーストラリア（AU）": "AU",
    "カナダ（CA）": "CA"
}

country_label = st.selectbox("国を選択してください", list(country_options.keys()))
country_code = country_options[country_label]

year = st.number_input("年を選択してください", min_value=1900, max_value=2100, value=2025)

display_option = st.selectbox(
    "表示したいデータを選択してください",
    ["祝日（公休日）", "伝統的な祭り・行事", "長期休暇"]
)


# -----------------------------
# SESSION STATE
# -----------------------------
if "all_events" not in st.session_state:
    st.session_state.all_events = []

if "expanded" not in st.session_state:
    st.session_state.expanded = False

if "fetched" not in st.session_state:
    st.session_state.fetched = False  # <--- NEW FLAG



# -----------------------------
# FETCH HELPERS
# -----------------------------
def fetch_data(endpoint, params):
    try:
        response = requests.get(f"{API_BASE}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json().get("data", None)
    except requests.RequestException:
        return None


def parse_date_japan_style(date_str):
    today = datetime.date.today()
    match = re.search(r"(\d{1,2})月(\d{1,2})日", date_str)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        try:
            return datetime.date(today.year, month, day)
        except ValueError:
            return None
    return None


def get_upcoming_events(data_list):
    upcoming = []
    for item in data_list:
        date_str = item.get("日付情報") or item.get("日にち")
        if not date_str:
            continue
        event_date = parse_date_japan_style(date_str)
        if event_date and event_date >= datetime.date.today():
            upcoming.append((event_date, item))
    upcoming.sort(key=lambda x: x[0])
    return [i[1] for i in upcoming]


def styled_event(event):
    return f"""
    <div style="
        background-color: #e0f7fa;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 12px;
        color: #006064;
        font-weight: 600;
        line-height: 1.4;
    ">
        <p><strong>イベント名 :</strong> {event.get('名称', event.get('名前', ''))}</p>
        <p><strong>種類 / 説明 :</strong> {event.get('種類','')} {event.get('説明','')}</p>
        <p><strong>日付 :</strong> {event.get('日付情報', event.get('日にち',''))}</p>
    </div>
    """


# -----------------------------
# DATA FETCH BUTTON
# -----------------------------
if st.button("📅 データを取得"):
    st.session_state.fetched = True       # <--- MARK DATA FETCHED
    st.session_state.all_events = []      # reset
    st.session_state.expanded = False     # reset

    # 祝日
    if display_option == "祝日（公休日）":
        data = fetch_data("holidays", {"country": country_code, "year": year})
        if data:
            st.session_state.all_events = [
                {
                    "名称": d["localName"],
                    "日付情報": d["date"].replace("-", "月").replace("-", "日"),  # optional formatting
                    "種類": "祝日",
                    "説明": d["name"]
                }
                for d in data
            ]
        else:
            st.error("祝日のデータが取得できませんでした。")

    # 伝統的な祭り
    elif display_option == "伝統的な祭り・行事":
        data = fetch_data("festivals", {"country": country_code})
        if data and "祭り・文化行事" in data:
            st.session_state.all_events = data["祭り・文化行事"]
        else:
            st.error("祭りデータが取得できませんでした。")

    # 長期休暇
    else:
        data = fetch_data("festivals", {"country": country_code})
        if data and "長期休暇" in data:
            st.session_state.all_events = data["長期休暇"]
        else:
            st.info("※ 長期休暇データが取得できませんでした。")


all_events = st.session_state.all_events

# -----------------------------
# UPCOMING EVENTS (only after fetch)
# -----------------------------
if st.session_state.fetched:
    upcoming = get_upcoming_events(all_events)

    if upcoming:
        st.subheader("⏰ 近日開催のイベント")
        for e in upcoming[:5]:
            st.markdown(styled_event(e), unsafe_allow_html=True)
    else:
        st.info("※ 近日開催予定のイベントはありません。")


# -----------------------------
# LIST ALL EVENTS
# -----------------------------
if st.session_state.fetched:

    st.subheader(f"📌 {display_option}")

    show_count = 6
    for e in all_events[:show_count]:
        st.markdown(styled_event(e), unsafe_allow_html=True)

    if len(all_events) > show_count:
        toggle_label = "折りたたむ" if st.session_state.expanded else "続きを読む"
        if st.button(toggle_label):
            st.session_state.expanded = not st.session_state.expanded

    if st.session_state.expanded:
        for e in all_events[show_count:]:
            st.markdown(styled_event(e), unsafe_allow_html=True)


# -----------------------------
# FOOTER
# -----------------------------
st.info("※ FastAPI が起動していることを確認してください。")
