import streamlit as st
import json
import os
from pathlib import Path
from dotenv import load_dotenv

current_dir = Path(__file__).parent.resolve()
load_dotenv(dotenv_path=current_dir / '.env')

from MyWeatherDashboard import WeatherService, OPENWEATHER_API_KEY, aqi_label, aqi_health_advice, component_ch_name, get_component_status
from ai_service import AIWeatherService
from datetime import datetime, timezone, timedelta

# 頁面設定
st.set_page_config(page_title="全球天氣與 AI 穿搭儀表板", page_icon="🌤️", layout="wide")


def load_geo_data():
    try:
        with open(current_dir / 'cities.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("找不到 cities.json 檔案，請確認檔案路徑。")
        return {}


@st.cache_data(ttl=600)
def fetch_weather_data(_service, city_info):
    current = _service.get_current_weather(city_info)
    if not current:
        return None, None, None

    lat, lon = current['coord']['lat'], current['coord']['lon']
    air = _service.get_air_quality(lat, lon)
    forecast = _service.get_daily_forecast(city_info)
    return current, air, forecast


def get_secret(key: str, default: str = "") -> str:
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


def main():
    st.title("🌤️ 全球天氣與 AI 穿搭顧問儀表板")

    api_key = get_secret("OPENWEATHER_API_KEY", OPENWEATHER_API_KEY)
    if not api_key:
        st.error("❌ 找不到 OpenWeather API 金鑰！")
        st.info("本地執行：請確保 .env 檔案中有 OPENWEATHER_API_KEY\n\n雲端部署：請在 Streamlit Cloud 的 Secrets 設定中加入金鑰。")
        return

    try:
        weather_svc = WeatherService(api_key)
    except ValueError as e:
        st.error(f"初始化服務失敗: {e}")
        return

    geo_data = load_geo_data()
    if not geo_data:
        return

    # 側邊欄：地點選擇
    st.sidebar.header("📍 地點選擇")
    regions = list(geo_data.keys())
    selected_region = st.sidebar.selectbox("選擇區域", regions)
    countries = list(geo_data[selected_region].keys())
    selected_country = st.sidebar.selectbox("選擇國家", countries)

    cities_data = geo_data[selected_region][selected_country]
    city_options = {city['name']: (city['en'], city['country']) for city in cities_data}
    selected_country_code = cities_data[0]['country'] if cities_data else ''

    display_names = list(city_options.keys()) + ["手動輸入"]
    selected_option = st.sidebar.selectbox("選擇城市", display_names)

    target_city_info = None
    display_city_name = ""

    if selected_option == "手動輸入":
        manual_city = st.sidebar.text_input("請輸入城市英文名稱", value="London")
        if manual_city:
            target_city_info = (manual_city, selected_country_code) if selected_country_code else manual_city
            display_city_name = manual_city
    else:
        target_city_info = city_options[selected_option]
        display_city_name = selected_option

    # 側邊欄：AI 助理設定
    st.sidebar.markdown("---")
    st.sidebar.header("🤖 AI 助理設定")

    gemini_key = os.getenv("GEMINI_API_KEY", "") or get_secret("GEMINI_API_KEY", "")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "") or get_secret("DEEPSEEK_API_KEY", "")

    available_providers = []
    provider_labels = {}

    if gemini_key:
        available_providers.append("gemini")
        provider_labels["gemini"] = "🔮 Google Gemini"
    if deepseek_key:
        available_providers.append("deepseek")
        provider_labels["deepseek"] = "🧠 DeepSeek"

    available_providers.append("fallback")
    provider_labels["fallback"] = "⚙️ 智慧規則引擎 (免金鑰)"

    if available_providers:
        default_provider = "gemini" if gemini_key else available_providers[0]
        selected_provider = st.sidebar.selectbox(
            "選擇 AI 引擎",
            options=available_providers,
            format_func=lambda x: provider_labels.get(x, x),
            index=available_providers.index(default_provider) if default_provider in available_providers else 0
        )
        ai_provider = selected_provider

        if ai_provider == "gemini":
            st.sidebar.success("🟢 已選取：Google Gemini")
            if deepseek_key:
                st.sidebar.caption("💡 提示：若 Gemini 額度用完，將自動切換到 DeepSeek")
        elif ai_provider == "deepseek":
            st.sidebar.success("🟢 已選取：DeepSeek")
        elif ai_provider == "fallback":
            st.sidebar.info("🟡 已選取：智慧規則引擎（無需 API Key）")
    else:
        ai_provider = "fallback"
        st.sidebar.info("🟡 尚未設定 API Key，使用智慧規則引擎")

    style_preference = st.sidebar.selectbox(
        "個人穿搭風格偏好",
        ["通用日常", "上班通勤/商務風", "休閒出遊/度假風", "運動健身/戶外機能", "極簡防曬/保暖風"]
    )

    # 主要內容
    if target_city_info:
        current, air, forecast = fetch_weather_data(weather_svc, target_city_info)

        if current:
            timezone_offset = current.get('timezone', 0)
            local_time = datetime.now(timezone.utc).astimezone(timezone(timedelta(seconds=timezone_offset)))
            st.subheader(f"📍 {display_city_name} ({current.get('name', '')})")
            st.caption(f"當地時間: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")

            col1, col2, col3, col4, col5 = st.columns(5)
            temp = current['main'].get('temp')
            feels = current['main'].get('feels_like')
            humidity = current['main'].get('humidity')

            col1.metric("氣溫", f"{int(round(temp)) if temp is not None else '--'}°C")
            col2.metric("體感溫度", f"{int(round(feels)) if feels is not None else '--'}°C")
            col3.metric("濕度", f"{humidity}%")

            sunset_ts = current['sys'].get('sunset')
            sunset_local = datetime.fromtimestamp(sunset_ts, tz=timezone.utc).astimezone(
                timezone(timedelta(seconds=timezone_offset))).strftime('%H:%M') if sunset_ts else "--:--"
            col4.metric("日落時間", sunset_local)

            today_pop = 0
            if forecast:
                today_pop = forecast[0].get('pop', 0)
            col5.metric("今日降雨率", f"{today_pop}%")

            # AI 智慧氣象顧問
            st.markdown("---")
            st.subheader("🤖 AI 智慧氣象顧問與生活助理")

            ai_svc = AIWeatherService(
                gemini_api_key=gemini_key,
                deepseek_api_key=deepseek_key,
                provider=ai_provider
            )

            tab_summary, tab_chat = st.tabs(["👔 AI 5天天氣總評與穿搭指南", "💬 AI 天氣生活對話機器人"])

            with tab_summary:
                cache_key = f"ai_summary_{display_city_name}_{style_preference}_{ai_provider}"
                engine_label = {
                    "gemini": "Google Gemini",
                    "deepseek": "DeepSeek",
                    "fallback": "智慧規則模式"
                }.get(ai_provider, ai_provider)

                col_btn, col_info = st.columns([3, 7])
                with col_btn:
                    refresh_ai = st.button("✨ 重新生成 AI 穿搭指南", key="btn_refresh_ai", use_container_width=True)
                with col_info:
                    st.caption(f"目前引擎: **{engine_label}** ｜ 風格偏好: **{style_preference}**")

                if refresh_ai or cache_key not in st.session_state:
                    with st.spinner(f"AI 正在為 {display_city_name} 彙整 5 天天氣趨勢與穿搭建議..."):
                        summary_result = ai_svc.generate_weather_and_outfit_summary(
                            city_name=display_city_name,
                            current_weather=current,
                            forecast_data=forecast,
                            aqi_data=air,
                            style_preference=style_preference
                        )
                        st.session_state[cache_key] = summary_result

                st.markdown(st.session_state[cache_key])

            with tab_chat:
                city_chat_key = f"chat_history_{display_city_name}"

                if city_chat_key not in st.session_state:
                    st.session_state[city_chat_key] = [
                        {
                            "role": "assistant",
                            "content": f"哈囉！我是 **{display_city_name}** 的 AI 天氣與穿搭小助理 🤖。\n我已經掌握了未來的氣溫、降雨機率與空氣品質，隨時想詢問穿搭、帶傘、運動或洗曬衣物都歡迎提問喔！"
                        }
                    ]

                chat_col1, chat_col2 = st.columns([8, 2])
                with chat_col1:
                    st.caption(f"🤖 對話助理已就緒（目前引擎: {engine_label}）")
                with chat_col2:
                    if st.button("🗑️ 清空對話", key=f"clear_chat_{display_city_name}", use_container_width=True):
                        st.session_state[city_chat_key] = [
                            {
                                "role": "assistant",
                                "content": f"哈囉！我是 **{display_city_name}** 的 AI 天氣與穿搭小助理 🤖。\n我已經掌握了未來的氣溫、降雨機率與空氣品質，隨時想詢問穿搭、帶傘、運動或洗曬衣物都歡迎提問喔！"
                            }
                        ]
                        st.rerun()

                st.markdown("**💡 快速提問：**")
                q_cols = st.columns(4)
                quick_prompts = [
                    ("🌂 哪天一定要帶傘？", "請問未來 5 天中哪幾天出門一定要帶雨具？"),
                    ("👔 早晚溫差該怎麼穿？", "未來幾天的早晚溫差如何？建議採用什麼樣的穿搭？"),
                    ("🧺 哪天適合曬衣服？", "這幾天哪一天最晴朗乾燥、最適合洗衣服曬被子？"),
                    ("🏃 適合戶外慢跑嗎？", "以當前的氣候與空氣品質，哪幾天最適合戶外慢跑或運動？")
                ]

                clicked_prompt = None
                for idx, (label, p_text) in enumerate(quick_prompts):
                    if q_cols[idx].button(label, key=f"qp_{display_city_name}_{idx}", use_container_width=True):
                        clicked_prompt = p_text

                for msg in st.session_state[city_chat_key]:
                    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
                        st.markdown(msg["content"])

                user_input = st.chat_input(f"詢問關於 {display_city_name} 的天氣或穿搭問題...")
                prompt_to_process = clicked_prompt or user_input

                if prompt_to_process:
                    st.session_state[city_chat_key].append({"role": "user", "content": prompt_to_process})

                    with st.chat_message("user", avatar="👤"):
                        st.markdown(prompt_to_process)

                    with st.chat_message("assistant", avatar="🤖"):
                        with st.spinner("AI 思考中..."):
                            bot_reply = ai_svc.chat_response(
                                messages=st.session_state[city_chat_key],
                                city_name=display_city_name,
                                current_weather=current,
                                forecast_data=forecast,
                                aqi_data=air,
                                style_preference=style_preference
                            )
                        st.markdown(bot_reply)
                        st.session_state[city_chat_key].append({"role": "assistant", "content": bot_reply})

                    st.rerun()

            # 詳細氣象數據
            st.markdown("---")
            st.subheader("📊 詳細氣象與空氣品質數據")

            if air and 'list' in air:
                aq = air['list'][0]
                aqi = aq['main']['aqi']
                aqi_colors = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴", 5: "🟣"}
                st.info(f"{aqi_colors.get(aqi, '⚪')} **空氣品質 AQI 等級: {aqi} ({aqi_label(aqi)})** ｜ 💡 {aqi_health_advice(aqi)}")

                comps = aq['components']
                comp_cols = st.columns(len(comps))
                for i, (k, v) in enumerate(comps.items()):
                    comp_cols[i].caption(component_ch_name(k))
                    comp_cols[i].write(f"{v}")
                    status = get_component_status(k, v)
                    if status:
                        comp_cols[i].caption(status)

            if forecast:
                st.markdown("##### 📅 未來 5 天氣溫走勢圖")
                chart_data = {
                    "日期": [d['date'] for d in forecast],
                    "最低溫": [d['min_temp'] for d in forecast],
                    "最高溫": [d['max_temp'] for d in forecast]
                }
                st.line_chart(data=chart_data, x="日期", y=["最低溫", "最高溫"])

                st.markdown("##### 逐日詳細氣象清單")
                display_forecast = []
                for d in forecast:
                    display_forecast.append({
                        "日期": d['date'],
                        "最低溫 (°C)": d['min_temp'],
                        "最高溫 (°C)": d['max_temp'],
                        "降雨機率": f"{d['pop']}%",
                        "天氣描述": d['description']
                    })
                st.table(display_forecast)

        else:
            st.error(f"⚠️ 無法取得 '{display_city_name}' 的天氣資料。")
            st.warning("請檢查：\n1. 城市英文名稱是否正確 (例如: London, Taipei)\n2. API 金鑰是否有效\n3. 網路連線是否正常")


if __name__ == "__main__":
    main()