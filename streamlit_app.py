import streamlit as st
import json
from pathlib import Path
from MyWeatherDashboard import WeatherService, OPENWEATHER_API_KEY, aqi_label, aqi_health_advice, component_ch_name
from datetime import datetime, timezone, timedelta

# 頁面設定
st.set_page_config(page_title="全球天氣儀表板", page_icon="🌤️", layout="wide")

current_dir = Path(__file__).parent.resolve()

@st.cache_data
def load_geo_data():
    try:
        with open(current_dir / 'cities.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("找不到 cities.json 檔案，請確認檔案路徑。")
        return {}

# 使用快取來減少重複的 API 請求 (設定 TTL 為 600 秒，即 10 分鐘)
@st.cache_data(ttl=600)
def fetch_weather_data(_service, city):
    current = _service.get_current_weather(city)
    if not current:
        return None, None, None
    
    lat, lon = current['coord']['lat'], current['coord']['lon']
    air = _service.get_air_quality(lat, lon)
    forecast = _service.get_daily_forecast(city)
    
    return current, air, forecast

def main():
    st.title("🌤️ 全球天氣與空氣品質儀表板")
    
    if not OPENWEATHER_API_KEY:
        st.error("找不到 API 金鑰，請在 .env 檔案中設定 OPENWEATHER_API_KEY")
        return

    weather_svc = WeatherService(OPENWEATHER_API_KEY)
    geo_data = load_geo_data()
    if not geo_data:
        return

    # 側邊欄選單
    st.sidebar.header("地點選擇")
    regions = list(geo_data.keys())
    selected_region = st.sidebar.selectbox("選擇區域", regions)

    countries = list(geo_data[selected_region].keys())
    selected_country = st.sidebar.selectbox("選擇國家", countries)

    cities = geo_data[selected_region][selected_country]
    selected_city = st.sidebar.selectbox("選擇城市", cities + ["手動輸入"])

    target_city = selected_city
    if selected_city == "手動輸入":
        target_city = st.sidebar.text_input("請輸入城市英文名稱", value="London")

    if st.sidebar.button("開始查詢"):
        with st.spinner(f"正在獲取 {target_city} 的資料..."):
            # 使用優化後的快取函式獲取資料
            current, air, forecast = fetch_weather_data(weather_svc, target_city)

            if current:
                st.subheader(f"📍 {target_city} 當前天氣")
                col1, col2, col3, col4 = st.columns(4)
                
                temp = current['main'].get('temp')
                feels = current['main'].get('feels_like')
                humidity = current['main'].get('humidity')
                
                col1.metric("氣溫", f"{temp}°C")
                col2.metric("體感溫度", f"{feels}°C")
                col3.metric("濕度", f"{humidity}%")
                
                # 日落時間處理
                sunset_ts = current['sys'].get('sunset')
                timezone_offset = current.get('timezone', 0)
                sunset_local = datetime.fromtimestamp(sunset_ts, tz=timezone.utc).astimezone(
                    timezone(timedelta(seconds=timezone_offset))).strftime('%H:%M')
                col4.metric("日落時間", sunset_local)

                # 2. 空氣品質
                if air and 'list' in air:
                    aq = air['list'][0]
                    aqi = aq['main']['aqi']
                    
                    st.markdown("---")
                    st.subheader("🌫️ 空氣品質指標 (AQI)")
                    
                    aqi_colors = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴", 5: "🟣"}
                    st.info(f"{aqi_colors.get(aqi, '⚪')} **AQI 等級: {aqi} ({aqi_label(aqi)})**\n\n💡 {aqi_health_advice(aqi)}")
                    
                    # 污染物詳細數據
                    comps = aq['components']
                    comp_cols = st.columns(len(comps))
                    for i, (k, v) in enumerate(comps.items()):
                        comp_cols[i].caption(component_ch_name(k))
                        comp_cols[i].write(f"{v}")

                # 3. 未來預報
                st.markdown("---")
                st.subheader("📅 未來 5 天天氣預報")
                if forecast:
                    # 轉換為表格顯示
                    st.table(forecast)
            else:
                st.error(f"無法找到城市 '{target_city}' 的資料，請檢查名稱是否正確。")

if __name__ == "__main__":
    main()